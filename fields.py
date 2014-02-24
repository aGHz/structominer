from collections import OrderedDict
import datetime
import functools
import time

from exc import ParsingError
from util import clean_ascii


class ElementsField(object):
    _field_counter = 0

    def __init__(self, xpath=None, auto_parse=True, *args, **kwargs):
        # TODO add optional field, disabling parsing exceptions
        self._value = None
        self.xpath = xpath
        self.auto_parse = auto_parse

        self._field_counter = ElementsField._field_counter
        ElementsField._field_counter += 1

    def _get_element(self, xpath=None):
        xpath = xpath or self.xpath
        return self.etree.xpath(xpath, smart_strings=False)

    @property
    def element(self):
        return self._get_element()

    @property
    def value(self):
        return self._value

    def parse(self, etree, document):
        self.etree = etree
        self._value = self._get_element()
        return self._value

    def parser(self, xpath=None):
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


def get_element_stripped_texts(element):
    return map(lambda s: s.strip(), element.xpath('text()') if hasattr(element, 'xpath') else element)

def get_element_clean_texts(element):
    return map(clean_ascii, element.xpath('text()') if hasattr(element, 'xpath') else element)

class StringsField(ElementsField):
    def __init__(self, xpath=None, filter_empty=True, *args, **kwargs):
        super(StringsField, self).__init__(xpath=xpath, *args, **kwargs)
        self.filter_empty = filter_empty

    def parse(self, etree, document):
        element = super(StringsField, self).parse(etree, document)
        if len(element) == 0:
            self._value = []
            return self._value
        elif type(element[0]) not in (str, unicode):
            element = element[0]

        self._value = get_element_clean_texts(element)
        if type(self._value) == list and self.filter_empty:
            self._value = filter(len, self._value)

        return self._value

class TextField(StringsField):
    def __init__(self, xpath=None, separator=' ', *args, **kwargs):
        super(TextField, self).__init__(xpath=xpath, *args, **kwargs)
        self.separator = separator

    def parse(self, etree, document):
        value = super(TextField, self).parse(etree, document)
        self._value = clean_ascii(self.separator.join(value).strip() if type(value) == list else value)
        return self._value

class IntField(TextField):
    def __init__(self, xpath=None, *args, **kwargs):
        super(IntField, self).__init__(xpath, separator='', *args, **kwargs)
        self._has_default = 'default' in kwargs
        self.default = kwargs.get('default', None)

    def parse(self, etree, document):
        try:
            self._value = int(super(IntField, self).parse(etree, document))
        except ValueError as e:
            if self._has_default:
                self._value = self.default
            else:
                raise ParsingError(e.message)
        return self._value

class FloatField(TextField):
    def __init__(self, xpath=None, *args, **kwargs):
        super(FloatField, self).__init__(xpath, separator='', *args, **kwargs)
        self._has_default = 'default' in kwargs
        self.default = kwargs.get('default', None)

    def parse(self, etree, document):
        try:
            self._value = float(super(FloatField, self).parse(etree, document))
        except ValueError as e:
            if self._has_default:
                self._value = self.default
            else:
                raise ParsingError(e.message)
        return self._value

class DateField(TextField):
    MURICAH = '%m/%d/%Y'
    ISO_8601 = '%Y-%m-%d'

    def __init__(self, xpath=None, date_format=ISO_8601, *args, **kwargs):
        super(DateField, self).__init__(xpath, separator='', *args, **kwargs)
        self.date_format = date_format

    def parse(self, etree, document):
        value = super(DateField, self).parse(etree, document)
        self._value = datetime.date(*time.strptime(value, self.date_format)[0:3])
        return self._value


class URLField(ElementsField):
    def parse(self, etree, document):
        try:
            element = super(URLField, self).parse(etree, document)[0]
        except IndexError as e:
            raise ParsingError(e.message)

        self._value = element.attrib.get('src', element.attrib.get('href', element.text.strip() if element.text else None))
        return self._value


class StringsList(ElementsField):
    def parse(self, etree, document):
        elements = super(StringsList, self).parse(etree, document)
        self._value = map(get_element_clean_texts, elements)
        return self._value

class TextList(StringsList):
    def __init__(self, xpath=None, separator=' ', *args, **kwargs):
        super(TextList, self).__init__(xpath=xpath, *args, **kwargs)
        self.separator = separator

    def parse(self, etree, document):
        strings = super(TextList, self).parse(etree, document)
        self._value = map(lambda element_strings: clean_ascii(self.separator.join(element_strings).strip()), strings)
        return self._value

class IntList(TextList):
    def __init__(self, *args, **kwargs):
        super(IntList, self).__init__(separator='', *args, **kwargs)

    def parse(self, etree, document):
        texts = super(IntList, self).parse(etree, document)
        try:
            self._value = map(int, texts)
        except ValueError:
            raise ParsingError(e.message)
        return self._value


class StructuredField(TextField):
    # Declares intent to define a custom parser that returns a dict
    # TODO dict interface to access value fields directly
    pass

class StructuredList(ElementsField):
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
        return value

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
        return value

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
        return value

    def filter(self):
        def decorator(fn):
            self._filter = fn # Unbound to keep arguments consistent with @parser
            return fn
        return decorator

    def _filter(value, field, etree, document):
        return True


class ElementsOperation(ElementsField):
    # Declares intent to perform some operation on selected elements without caring for the result
    pass
