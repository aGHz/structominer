from collections import OrderedDict, MutableMapping, MutableSequence
import copy
import datetime
import functools
import time

from exc import ParsingError
from util import clean_ascii, element_to_string


class ElementsField(object):
    _field_counter = 0

    def __init__(self, xpath=None, filter_empty=True, auto_parse=True, optional=True, *args, **kwargs):
        self.xpath = xpath
        self.filter_empty = filter_empty
        self.auto_parse = auto_parse
        self.optional = optional

        self._value = None
        self._preprocessors = []
        self._postprocessors = []

        self._field_counter = ElementsField._field_counter
        ElementsField._field_counter += 1

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @property
    def _target_(self):
        return self._get_target()

    def _get_target(self, xpath=None):
        xpath = xpath or self.xpath
        return self._clean_texts(self.etree.xpath(xpath, smart_strings=False))

    def _clean_texts(self, elements):
        """Clean potential text elements returned by the selector"""
        elements = map(lambda e: clean_ascii(e) if isinstance(e, basestring) else e, elements)
        if self.filter_empty:
            elements = filter(lambda e: len(e) > 0 if isinstance(e, basestring) or isinstance(e, list) else True,
                              elements)
        return elements

    def parse(self, etree, document):
        self.etree = etree
        self.document = document

        # Kick off the super._parse chain by calling the object's class's super without a value argument
        value = super(self.__class__, self)._parse()

        # Apply preprocessors in reverse order of declaration
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
            # Save preprocessors in reverse order so they can be defined in order from the outside in
            self._preprocessors.insert(0, fn)
            return fn
        return decorator

    def postprocessor(self):
        def decorator(fn):
            self._postprocessors.append(fn)
            return fn
        return decorator

    def _parse(self, **kwargs):
        value = self._target_
        if not value and not self.optional:
            raise ParsingError('Could not find xpath "{0}" starting from {1}'.format(
                self.xpath, element_to_string(self.etree)))
        return value

    # DEPRECATED
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
                field._value = fn(value=value, field=field, etree=etree, document=document)
                return field._value
            self.parse = new_parse.__get__(self, self.__class__)

            return fn
        return decorator


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
            value = self._clean_texts(value.xpath('text()'))
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
    def _parse(self, **kwargs):
        return kwargs.get('value', super(StructuredTextField, self)._parse())

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

class StructuredField(MutableMapping, ElementField):
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

    @ElementsField.value.getter
    def value(self):
        return {key: item.value for (key, item) in self._value.iteritems()}

    def __getitem__(self, key):
        try:
            return self._value[key].value
        except KeyError:
            raise KeyError('StructuredField has no key "{0}"'.format(key))

    def __call__(self, key):
        try:
            return self._value[key]
        except KeyError:
            raise KeyError('StructuredField has no key "{0}"'.format(key))

    def __setitem__(self, key, value):
        try:
            self._value[key].value = value
        except KeyError:
            raise KeyError('StructuredField has no key "{0}"'.format(key))

    def __delitem__(self, key):
        try:
            del self._value[key]
        except KeyError:
            raise KeyError('StructuredField has no key "{0}"'.format(key))

    def __iter__(self):
        return self._value.iterkeys()

    def __len__(self):
        return len(self._value)


class ListField(MutableSequence, ElementsField):
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

    @ElementsField.value.getter
    def value(self):
        return [item.value for item in self._value]

    def __getitem__(self, i):
        try:
            return self._value[i].value
        except IndexError:
            raise IndexError('ListField has no item {0}'.format(i))

    def __call__(self, i):
        try:
            return self._value[i]
        except IndexError:
            raise IndexError('ListField has no item {0}'.format(i))

    def __setitem__(self, i, value):
        try:
            self._value[i].value = value
        except IndexError:
            raise IndexError('ListField has no item {0}'.format(i))

    def __delitem__(self, i):
        try:
            del self._value[i]
        except IndexError:
            raise IndexError('ListField has no item {0}'.format(i))

    def __len__(self):
        return len(self._value)

    def insert(self, i, value):
        self._value.insert(i, value)


class DictField(MutableMapping, ElementsField):
    def __init__(self, xpath=None, item=None, key=None, *args, **kwargs):
        super(DictField, self).__init__(xpath=xpath, *args, **kwargs)
        self.item = item
        self.key = key

    def _parse(self, **kwargs):
        elements = kwargs.get('value', super(DictField, self)._parse())
        value = OrderedDict()
        for i, element in enumerate(elements):
            item = copy.deepcopy(self.item)
            if isinstance(self.key, ElementsField):
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
            value[key.value] = item
        return value

    @ElementsField.value.getter
    def value(self):
        return {key: item.value for (key, item) in self._value.iteritems()}

    def __getitem__(self, key):
        try:
            return self._value[key].value
        except KeyError:
            raise KeyError('DictField has no key "{0}"'.format(key))

    def __call__(self, key):
        try:
            return self._value[key]
        except KeyError:
            raise KeyError('DictField has no key "{0}"'.format(key))

    def __setitem__(self, key, value):
        try:
            self._value[key].value = value
        except KeyError:
            raise KeyError('DictField has no key "{0}"'.format(key))

    def __delitem__(self, key):
        try:
            del self._value[key]
        except KeyError:
            raise KeyError('DictField has no key "{0}"'.format(key))

    def __iter__(self):
        return self._value.iterkeys()

    def __len__(self):
        return len(self._value)


class ElementsOperation(ElementsField):
    """Declares intent to perform some operation on selected elements without caring for the result."""
    pass
