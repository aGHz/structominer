from structominer import *

class HNHome(Document):
    content_xpath = '//body/center/table[1]'
    header_xpath = content_xpath + '/tr[1]//table/tr'
    items_xpath = content_xpath + '/tr[3]//table'

    items = ListField(
        items_xpath + '//td[@class="title"]/parent::tr',
        item=StructuredField(
            '.',
            structure=dict(
                title=TextField('.//td[3]/a'),
                url=URLField('.//td[3]/a'),
                domain=TextField('.//td[3]/span[@class="comhead"]'))))

    # TODO clean up item['domain'] to remove parentheses


import requests

response = requests.get('https://news.ycombinator.com/')
hn_home = HNHome(response.text)

# This idiom will greatly improve once fields get a list/dictionary interface
# straight to their values, e.g. you could do hn_home['items'][0]['title'] and get the actual string
for i, item in enumerate(hn_home['items']):
    print '{0}: {1} ({2})'.format(i, item._value['title']._value, item._value['domain']._value)
    print '    {0}'.format(item._value['url']._value)
    print
