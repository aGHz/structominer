from collections import OrderedDict, Mapping, Sequence
import copy
import datetime
import functools
import time

from exc import ParsingError
from util import clean_ascii, clean_strings, element_to_string


class BiaxialAccessContainer(object):
    def __call__(self, key):
        """The field access axis: field(key) points to the subfield"""
        try:
            return self._value[key]
        except KeyError:
            raise KeyError('{0} has no key "{1}"'.format(self.__class__.__name__, key))
        except IndexError:
            raise IndexError('{0} has no item "{1}"'.format(self.__class__.__name__, key))

    def __getitem__(self, key):
        """The value access axis: field[key] points directly to the subfield's value"""
        try:
            return self._value[key].value
        except KeyError:
            raise KeyError('{0} has no key "{1}"'.format(self.__class__.__name__, key))
        except IndexError:
            raise IndexError('{0} has no item "{1}"'.format(self.__class__.__name__, key))

    def __iter__(self):
        if isinstance(self._value, list):
            return (item.value for item in self._value)
        elif isinstance(self._value, dict):
            return self._value.iterkeys()

    def __len__(self):
        return len(self._value)


class Field(object):
    _field_counter = 0

    def __init__(self, auto_parse=True, optional=True, *args, **kwargs):
        self.auto_parse = auto_parse
        self.optional = optional

        self._value = None
        self._preprocessors = []
        self._postprocessors = []

        self._field_counter = Field._field_counter
        Field._field_counter += 1

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def parse(self, etree, document):
        self.etree = etree
        self.document = document

        # Kick off the super._parse chain by calling the object's class's super without a value argument
        # If a field class doesn't add its own _parse and wishes to use the parent's, it must set
        #   a _masquerades_ attribute to the parent class
        parent = getattr(self, '_masquerades_', self.__class__)
        value = super(parent, self)._parse()

        # Apply preprocessors
        value = reduce(
            lambda value, preprocessor: preprocessor(
                value=value,
                field=self,
                etree=self.etree,
                document=self.document),
            self._preprocessors, value)

        # The main call to the object's _parse
        value = self._parse(value=value)

        # Apply postprocessors
        value = reduce(
            lambda value, postprocessor: postprocessor(
                value=value,
                field=self,
                etree=self.etree,
                document=self.document),
            self._postprocessors, value)

        self.value = value
        return value

    def preprocessor(self):
        def decorator(fn):
            self._preprocessors.append(fn)
            return fn
        return decorator

    def postprocessor(self):
        def decorator(fn):
            self._postprocessors.append(fn)
            return fn
        return decorator


class ElementsField(Field):
    def __init__(self, xpath=None, filter_empty=True, *args, **kwargs):
        super(ElementsField, self).__init__(*args, **kwargs)
        self.xpath = xpath
        self.filter_empty = filter_empty
        self.target = None

    def _parse(self, **kwargs):
        self.target = clean_strings(self.etree.xpath(self.xpath, smart_strings=False), self.filter_empty)
        if not self.target and not self.optional:
            raise ParsingError('Could not find xpath "{0}" starting from {1}'.format(
                self.xpath, element_to_string(self.etree)))
        return self.target


class ElementField(ElementsField):
    def _parse(self, **kwargs):
        elements = kwargs.get('value', super(ElementField, self)._parse())
        try:
            element = filter(lambda e: hasattr(e, 'xpath'), elements)[0]
        except IndexError:
            if len(elements):
                return elements
            elif self.optional:
                return None
            else:
                raise ParsingError('Could not find element for xpath "{0}" starting from {1}'.format(
                    self.xpath, element_to_string(self.etree)))
        else:
            return element


class StringsField(ElementField):
    def _parse(self, **kwargs):
        value = kwargs.get('value', super(StringsField, self)._parse())
        if hasattr(value, 'xpath'):
            value = clean_strings(value.xpath('text()'), self.filter_empty)
        if not value and not self.optional:
            raise ParsingError('Could not find any strings for xpath "{0}" starting from {1}'.format(
                self.xpath, element_to_string(etree)))
        return value

class TextField(StringsField):
    def __init__(self, xpath=None, separator=' ', *args, **kwargs):
        super(TextField, self).__init__(xpath=xpath, *args, **kwargs)
        self.separator = separator

    def _parse(self, **kwargs):
        strings = kwargs.get('value', super(TextField, self)._parse())
        value = clean_ascii(self.separator.join(strings)).strip() if strings is not None else None
        if not value and not self.optional:
            raise ParsingError('Could not find any text for xpath "{0}" starting from {1}'.format(
                self.xpath, element_to_string(etree)))
        return value

class IntField(TextField):
    def __init__(self, xpath=None, *args, **kwargs):
        super(IntField, self).__init__(xpath, separator='', *args, **kwargs)
        self._has_default = 'default' in kwargs
        self.default = kwargs.get('default', None)

    def _parse(self, **kwargs):
        text = kwargs.get('value', super(IntField, self)._parse())
        try:
            value = int(text)
        except ValueError:
            if self._has_default:
                return self.default
            elif self.optional:
                return None
            else:
                raise ParsingError('Could not convert "{0}" to int for xpath "{1}" starting from {2}'.format(
                    text, self.xpath, element_to_string(self.etree)))
        return value

class FloatField(TextField):
    def __init__(self, xpath=None, *args, **kwargs):
        super(FloatField, self).__init__(xpath, separator='', *args, **kwargs)
        self._has_default = 'default' in kwargs
        self.default = kwargs.get('default', None)

    def _parse(self, **kwargs):
        text = kwargs.get('value', super(FloatField, self)._parse())
        try:
            value = float(text)
        except ValueError:
            if self._has_default:
                return self.default
            elif self.optional:
                return None
            else:
                raise ParsingError('Could not convert "{0}" to float for xpath "{1}" starting from {2}'.format(
                    text, self.xpath, element_to_string(self.etree)))
        return value

class DateField(TextField):
    MURICAH = '%m/%d/%Y'
    ISO_8601 = '%Y-%m-%d'

    def __init__(self, xpath=None, format=ISO_8601, *args, **kwargs):
        super(DateField, self).__init__(xpath, separator='', *args, **kwargs)
        self.format = format

    def _parse(self, **kwargs):
        text = kwargs.get('value', super(DateField, self)._parse())
        try:
            value = datetime.date(*time.strptime(text, self.format)[0:3])
        except ValueError:
            if self.optional:
                return None
            else:
                raise ParsingError(
                    'Could not convert "{0}" to date format {1} for xpath "{2}" starting from {3}'.format(
                        text, self.format, self.xpath, element_to_string(self.etree)))
        return value

class DateTimeField(DateField):
    pass # TODO

class StructuredTextField(TextField):
    """Declares intent to define custom processors that extract information from the element's text."""
    _masquerades_ = TextField

class URLField(ElementField):
    def _parse(self, **kwargs):
        element = kwargs.get('value', super(URLField, self)._parse())
        if not hasattr(element, 'attrib'):
            value = ''.join(element) if type(element) is list and len(element) else None
        else:
            value = element.attrib.get(
                'src',
                element.attrib.get(
                    'href',
                    clean_ascii(''.join(element.xpath('text()'))).strip()))
        if not value and not self.optional:
            raise ParsingError('Could not find any URL for xpath "{0}" starting from {1}'.format(
                self.xpath, element_to_string(self.etree)))
        return value

class StructuredField(BiaxialAccessContainer, Mapping, ElementField):
    def __init__(self, xpath=None, structure=None, *args, **kwargs):
        super(StructuredField, self).__init__(xpath=xpath, *args, **kwargs)
        self.structure = structure

    def _parse(self, **kwargs):
        element = kwargs.get('value', super(StructuredField, self)._parse())
        value = OrderedDict()
        for key, field in self.structure.iteritems():
            value[key] = copy.deepcopy(field)
            try:
                value[key].parse(element, self.document)
            except Exception as e:
                raise ParsingError('Failed to parse "{0}" for xpath "{1}": {2}'.format(key, self.xpath, e.message))
        return value

    @Field.value.getter
    def value(self):
        return {key: item.value for (key, item) in self._value.iteritems()}


class ListField(BiaxialAccessContainer, Sequence, ElementsField):
    def __init__(self, xpath=None, item=None, *args, **kwargs):
        super(ListField, self).__init__(xpath=xpath, *args, **kwargs)
        self.item = item
        self._filters = []

    def _parse(self, **kwargs):
        elements = kwargs.get('value', super(ListField, self)._parse())
        value = []
        for i, element in enumerate(elements):
            item = copy.deepcopy(self.item)
            try:
                item.parse(element, self.document)
            except Exception as e:
                raise ParsingError('Failed to parse item {0} for xpath "{1}": {2}'.format(i, self.xpath, e.message))
            # Apply all the filters in definition order and reject as soon as one fails
            accepted = reduce(
                lambda accepted, filter_fn: False if not accepted else filter_fn(
                    value=item.value,
                    item=item,
                    field=self,
                    etree=self.etree,
                    document=self.document),
                self._filters, True)
            if accepted:
                value.append(item)
        return value

    def filter(self):
        def decorator(fn):
            # Decorated function only need declare the arguments it's interested in:
            # value, item, field, etree, document
            # It needs to return a truthy or falsey value
            self._filters.append(fn)
            return fn
        return decorator

    @Field.value.getter
    def value(self):
        return [item.value for item in self._value]


class DictField(BiaxialAccessContainer, Mapping, ElementsField):
    def __init__(self, xpath=None, item=None, key=None, *args, **kwargs):
        super(DictField, self).__init__(xpath=xpath, *args, **kwargs)
        self.item = item
        self.key = key
        self._filters = []

    def _parse(self, **kwargs):
        elements = kwargs.get('value', super(DictField, self)._parse())
        value = OrderedDict()
        for i, element in enumerate(elements):
            item = copy.deepcopy(self.item)
            if isinstance(self.key, Field):
                # Parse the key first, then the item
                key = copy.deepcopy(self.key)
                try:
                    key.parse(element, self.document)
                except Exception as e:
                    raise ParsingError('Failed to parse key {0} for xpath "{1}": {2}'.format(i, self.xpath, e.message))
                try:
                    item.parse(element, self.document)
                except Exception as e:
                    raise ParsingError('Failed to parse item "{0}" for xpath "{1}": {2}'.format(key.value, self.xpath, e.message))
            elif isinstance(self.key, basestring):
                # Parse item first, then extract key from it via element access
                try:
                    item.parse(element, self.document)
                except Exception as e:
                    raise ParsingError('Failed to parse item {0} for xpath "{1}": {2}'.format(i, self.xpath, e.message))
                key = item
                for index in self.key.split('/'):
                    key = key(index)
            # Apply all the filters in definition order and reject as soon as one fails
            accepted = reduce(
                lambda accepted, filter_fn: False if not accepted else filter_fn(
                    key=key.value,
                    value=item.value,
                    item=item,
                    field=self,
                    etree=self.etree,
                    document=self.document),
                self._filters, True)
            if accepted:
                value[key.value] = item
        return value

    def filter(self):
        def decorator(fn):
            # Decorated function only need declare the arguments it's interested in:
            # key, value, item, field, etree, document
            # It needs to return a truthy or falsey value
            self._filters.append(fn)
            return fn
        return decorator

    @Field.value.getter
    def value(self):
        return {key: item.value for (key, item) in self._value.iteritems()}


class StructuredListField(ListField):
    _masquerades_ = ListField

    def __init__(self, xpath=None, structure=None, *args, **kwargs):
        super(StructuredListField, self).__init__(
            xpath=xpath,
            item=StructuredField(xpath='.', structure=structure))


class StructuredDictField(DictField):
    _masquerades_ = DictField

    def __init__(self, xpath=None, structure=None, key=None, *args, **kwargs):
        super(StructuredDictField, self).__init__(
            xpath=xpath,
            item=StructuredField(xpath='.', structure=structure),
            key=key, *args, **kwargs)


class ElementsOperation(ElementsField):
    """Declares intent to perform some operation on selected elements without caring for the result."""
    _masquerades_ = ElementsField
