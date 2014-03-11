from structominer import Document, ErrorHandlingFailure, StructuredListField, TextField, URLField, IntField

class HNHome(Document):
    content_xpath = '//body/center/table[1]'
    header_xpath = content_xpath + '/tr[1]//table/tr'
    items_xpath = content_xpath + '/tr[3]//table'
    item_details = './following-sibling::tr[1]/td[2]'


    items = StructuredListField(
        items_xpath + '//td[contains(., ".")]/parent::tr',
        structure=dict(
            title=TextField('.//td[3]/a'),
            url=URLField('.//td[3]/a'),
            domain=TextField('.//td[3]/span[@class="comhead"]'),
            item_id=TextField(item_details + '/span/@id'),
            points=TextField(item_details + '/span'),
            user=TextField(item_details + '/a[1]'),
            user_url=URLField(item_details + '/a[1]'),
            age=TextField(item_details + '/text()[position()=last()]'),
            comments=IntField(item_details + '/a[2]'),
            details_url=URLField(item_details + '/a[2]')
        )
    )

    @items.item.domain.postprocessor()
    def _clean_item_domain(value, **kwargs):
        return value[1:-1] if value is not None else ''

    @items.item.item_id.postprocessor()
    def _extract_item_id(value, **kwargs):
        return value.split('_')[1] if value is not None else None

    @items.item.points.postprocessor()
    def _extract_points(value, **kwargs):
        return value.split(' ')[0] if value is not None else None

    @items.item.age.postprocessor()
    def _extract_age(value, **kwargs):
        duration, unit = value.split(' ', 1)
        return '{0}{1}'.format(duration, unit[0])

    @items.item.comments.preprocessor()
    def _sanitize_comments(value, **kwargs):
        if value.lower() == 'discuss':
            return 0
        return value.split(' ')[0]

    @items.item.comments.error_handler()
    def _handle_missing_comments(value, **kwargs):
        if value is None:
            return None
        raise ErrorHandlingFailure


# Request, parse and output a list of the front page entries

import requests
from urlparse import urljoin

hn_url = 'https://news.ycombinator.com/'
hn_response = requests.get(hn_url)
hn_home = HNHome(hn_response.text)

for i, item in enumerate(hn_home('items')):
    # Prepare the components to print on the first line
    parts = ['{0: >2}:'.format(i + 1)]
    if item['points'] is not None:
        parts.append('({0})'.format(item['points']))
    parts.append(item['title'])
    parts.append('--')
    # Prepare the details to print on the first line
    details = []
    if item['user'] is not None:
        details.append('@' + item['user'])
    details.append(item['age'])
    if item['comments'] is not None:
        details.append('{0} comments'.format(item['comments']))
    parts.append(', '.join(details))

    print ' '.join(parts)
    if 'http' in item['url']:
        # Ask/Show HN items have relative URLs identical to details_url
        print ' ' * 4 + item['url']
    if item['details_url'] is not None:
        print ' ' * 4 + urljoin(hn_url, item['details_url'])
    print
