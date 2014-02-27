import re
import unicodedata


def clean_ascii(utf8_text):
    if not isinstance(utf8_text, basestring):
        return utf8_text

    replacements = {
        # Typography
        "'": [u'\u02bc', u'\u2018', u'\u2019', u'\u201a', u'\u201b', u'\u2039', u'\u203a', u'\u300c', u'\u300d', ],
        '"': [u'\u00ab', u'\u00bb', u'\u201c', u'\u201d', u'\u201e', u'\u201f', u'\u300e', u'\u300f', ],
        '-': [u'\u002d', u'\u2010', u'\u2011', u'\u2012', u'\u2013', u'\u2014', u'\u2015', ],

        # Characters
        '(c)': [u'\u00a9', u'\u24b8', u'\u24d2', ], # Copyright
        '(r)': [u'\u00ae', u'\u24c7', ],            # Registered trademark
        '(p)': [u'\u2117', u'\u24c5', u'\u24df', ], # Sound recording copyright
        '(sm)': [u'\u2120', ],                      # Service mark
        '(tm)': [u'\u2122', ],                      # Trademark

        # Remove
        '': [
                u'\u00ad', # Soft hyphen
            ]
    }

    # Apply the replacement table to the UTF8 text
    for replacement, codes in replacements.iteritems():
        utf8_text = re.sub(u'[{0}]'.format(''.join(codes)), replacement, utf8_text)

    # Normalize non-Latin characters
    if isinstance(utf8_text, unicode):
        ascii_text = unicodedata.normalize('NFKD', utf8_text).encode('ascii', 'ignore')
    else:
        ascii_text = utf8_text

    # Normalize whitespace
    ascii_text = re.sub('\s\s+', ' ', ascii_text)

    # Fix punctuation spacing
    ascii_text = re.sub('\s+([,.;?!])', "\\1", ascii_text)

    return ascii_text


def element_to_string(element):
    attributes = ['{0}="{1}"'.format(*attr) for attr in element.attrib.iteritems()]
    return '<{0}>'.format(' '.join([element.tag] + attributes))
