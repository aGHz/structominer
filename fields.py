from collections import OrderedDict
import datetime
import functools
import time

from exc import ParsingError
from util import clean_ascii, element_to_string


class ElementsField(object):
    _field_counter = 0

    def __init__(self, xpath=None, filter_empty=True, auto_parse=True, optional=True, *args, **kwargs):
        # TODO add optional field, disabling parsing exceptions
        self._value = None
        self.xpath = xpath
        self.filter_empty = filter_empty
        self.auto_parse = auto_parse
        self.optional = optional

        self._field_counter = ElementsField._field_counter
        ElementsField._field_counter += 1

    def _get_target(self, xpath=None):
        xpath = xpath or self.xpath
        return self._clean_texts(self.etree.xpath(xpath, smart_strings=False))

    def _clean_texts(self, elements):
        """Clean potential text elements returned by the selector"""
        elements = map(lambda e: clean_ascii(e) if e == str(e) else e, elements)
        if self.filter_empty:
            elements = filter(lambda e: len(e) > 0 if e == str(e) else True, elements)
        return elements

    @property
    def target(self):
        return self._get_target()

    def parse(self, etree, document):
        self.etree = etree
        self._value = self._get_target()
        if not self._value and not self.optional:
            raise ParseError('Could not find xpath "{0}" starting from {1}'.format(
                self.xpath, element_to_string(etree)))
        return self._value

    def parser(self, xpath=None):
        # TODO look into using decorator.decorator
        # TODO try to make value a lazy object so that _parse gets called when
        #   fn evaluates it, therefore raising exceptions inside fn
        def decorator(fn):
            if xpath:
                self.xpath = xpath

            self._parse = self.parse
            @functools.wraps(fn)
            def new_parse(field, etree, document):
                value = self._parse(etree, document)
                field._value = fn(value, field, etree, document)
                return field._value
            self.parse = new_parse.__get__(self, self.__class__)

            return fn
        return decorator

class ElementField(ElementsField):
    def parse(self, etree, document):
        elements = super(ElementField, self).parse(etree, document)
        try:
            element = filter(lambda e: hasattr(e, 'xpath'), elements)[0]
        except IndexError:
            element = None
        self._value = element or elements or None # None if elements was empty to begin with
        return self._value


def get_element_stripped_texts(element):
    print 'DEPRECATED'
    return map(lambda s: s.strip(), element.xpath('text()') if hasattr(element, 'xpath') else element)

def get_element_clean_texts(element):
    print 'DEPRECATED'
    return map(clean_ascii, element.xpath('text()') if hasattr(element, 'xpath') else element)

class StringsField(ElementsField):
    def parse(self, etree, document):
        value = super(StringsField, self).parse(etree, document)
        if hasattr(value, 'xpath'):
            value = self._clean_texts(value.xpath('text()'))
            if not value and not self.optional:
                raise ParseError('Could not find any strings for xpath "{0}" starting from {1}'.format(
                    self.xpath, element_to_string(etree)))
        self._value = value
        return self._value

class TextField(StringsField):
    def __init__(self, xpath=None, separator=' ', *args, **kwargs):
        super(TextField, self).__init__(xpath=xpath, *args, **kwargs)
        self.separator = separator

    def parse(self, etree, document):
        value = super(TextField, self).parse(etree, document)
        self._value = clean_ascii(self.separator.join(value)).strip()
        return self._value

class IntField(TextField):
    def __init__(self, xpath=None, *args, **kwargs):
        super(IntField, self).__init__(xpath, separator='', *args, **kwargs)
        self._has_default = 'default' in kwargs
        self.default = kwargs.get('default', None)

    def parse(self, etree, document):
        value = super(IntField, self).parse(etree, document)
        try:
            self._value = int(value)
        except ValueError:
            if self._has_default:
                self._value = self.default
            elif self.optional:
                self._value = None
            else:
                raise ParsingError('Could not convert "{0}" to int for xpath "{1}" starting from {2}'.format(
                    value, self.xpath, element_to_string(etree)))
        return self._value

class FloatField(TextField):
    def __init__(self, xpath=None, *args, **kwargs):
        super(FloatField, self).__init__(xpath, separator='', *args, **kwargs)
        self._has_default = 'default' in kwargs
        self.default = kwargs.get('default', None)

    def parse(self, etree, document):
        value = super(FloatField, self).parse(etree, document)
        try:
            self._value = float(value)
        except ValueError:
            if self._has_default:
                self._value = self.default
            elif self.optional:
                self._value = None
            else:
                raise ParsingError('Could not convert "{0}" to float for xpath "{1}" starting from {2}'.format(
                    value, self.xpath, element_to_string(etree)))
        return self._value

class DateField(TextField):
    MURICAH = '%m/%d/%Y'
    ISO_8601 = '%Y-%m-%d'

    def __init__(self, xpath=None, format=ISO_8601, *args, **kwargs):
        super(DateField, self).__init__(xpath, separator='', *args, **kwargs)
        self.format = format

    def parse(self, etree, document):
        value = super(DateField, self).parse(etree, document)
        try:
            self._value = datetime.date(*time.strptime(value, self.format)[0:3])
        except ValueError:
            if self.optional:
                self._value = None
            else:
                raise ParsingError(
                    'Could not convert "{0}" to date format {1} for xpath "{2}" starting from {3}'.format(
                        value, self.format, self.xpath, element_to_string(etree)))
        return self._value

class DateTimeField(DateField):
    pass # TODO

class StructuredTextField(TextField):
    """Declares intent to define a custom parser that extracts information from the element's text."""
    pass

class URLField(ElementField):
    def parse(self, etree, document):
        element = super(URLField, self).parse(etree, document)
        self._value = element.attrib.get(
            'src',
            element.attrib.get(
                'href',
                clean_ascii(''.join(element.xpath('text()'))).strip()))
        if not self._value and not self.optional:
            raise ParseError('Could not find any URL for xpath "{0}" starting from {1}'.format(
                self.xpath, element_to_string(etree)))
        return self._value

class StructuredField(ElementField):
    def __init__(self, xpath=None, structure, *args, **kwargs):
        super(DictField, self).__init__(xpath=xpath, *args, **kwargs)
        self.structure = structure

    def parse(self, etree, document):
        pass # TODO


class StructuredList(ElementsField):
    # TODO wip restructuring field classes
    def __init__(self, xpath, structure, *args, **kwargs):
        super(StructuredList, self).__init__(xpath=xpath, *args, **kwargs)
        self.structure = structure
        self._filter = lambda (value, field, etree, document): True

    def parse(self, etree, document):
        elements = super(StructuredList, self).parse(etree, document)
        value = []
        for i, element in enumerate(elements):
            structure = {name: field.parse(element, document) for name, field in self.structure.iteritems()}
            if self._filter(structure, self, etree, document):
                value.append(structure)

        self._value = value
        return self._value

    def map(self, xpath=None):
        def decorator(fn):
            if xpath:
                self.xpath = xpath

            self._parse = self.parse
            @functools.wraps(fn)
            def new_parse(field, etree, document):
                value = self._parse(etree, document)
                map(lambda v: v.update(fn(v, field, etree, document)), value.values())
                field._value = value
                return field._value
            self.parse = new_parse.__get__(self, self.__class__)

            return fn
        return decorator

    def filter(self):
        def decorator(fn):
            self._filter = fn # Unbound to keep arguments consistent with @parser
            return fn
        return decorator

class IndexedStructuredList(ElementsField):
    # TODO wip restructuring field classes
    def __init__(self, xpath, structure, key_name=None, *args, **kwargs):
        super(IndexedStructuredList, self).__init__(xpath=xpath, *args, **kwargs)
        self.structure = structure
        self.key_name = key_name
        self._filter = lambda value, field, etree, document: True

    def parse(self, etree, document):
        elements = super(IndexedStructuredList, self).parse(etree, document)
        value = OrderedDict()
        for i, element in enumerate(elements):
            # TODO keep a reference to the fields so that map can use them
            # maybe have them in self._value, with self[field] going straight to their value
            structure = {name: field.parse(element, document) for name, field in self.structure.iteritems()}
            if self._filter(structure, self, etree, document):
                if self.key_name:
                    value[structure[self.key_name]] = structure
                else:
                    value[i] = structure

        self._value = value
        return self._value

    def map(self, xpath=None):
        def decorator(fn):
            if xpath:
                self.xpath = xpath

            self._parse = self.parse
            @functools.wraps(fn)
            def new_parse(field, etree, document):
                value = self._parse(etree, document)
                map(lambda v: v.update(fn(v, field, etree, document)), value.values())
                if self.key_name:
                    # TODO update the keys in case fn updated the field used for keys
                    pass
                field._value = value
                return field._value
            self.parse = new_parse.__get__(self, self.__class__)

            return fn
        return decorator

    def filter(self):
        def decorator(fn):
            self._filter = fn # Unbound to keep arguments consistent with @parser
            return fn
        return decorator

class DictField(ElementsField):
    # TODO wip restructuring field classes
    def __init__(self, xpath, key, value, *args, **kwargs):
        super(DictField, self).__init__(xpath=xpath, *args, **kwargs)
        self.key_field = key
        self.value_field = value

    def parse(self, etree, document):
        elements = super(DictField, self).parse(etree, document)
        value = OrderedDict()
        for i, element in enumerate(elements):
            k = self.key_field.parse(element, document)
            v = self.value_field.parse(element, document)
            if self._filter(k, v, self, etree, document):
                value[k] = v

        self._value = value
        return self._value

    def filter(self):
        def decorator(fn):
            self._filter = fn # Unbound to keep arguments consistent with @parser
            return fn
        return decorator

    def _filter(value, field, etree, document):
        return True


class ElementsOperation(ElementsField):
    """Declares intent to perform some operation on selected elements without caring for the result."""
    pass
