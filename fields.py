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
        self._value = None
        self.xpath = xpath
        self.filter_empty = filter_empty
        self.auto_parse = auto_parse
        self.optional = optional

        self._field_counter = ElementsField._field_counter
        ElementsField._field_counter += 1

    @property
    def _value_(self):
        return self._value

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
        self._value = self._target_
        if not self._value and not self.optional:
            raise ParsingError('Could not find xpath "{0}" starting from {1}'.format(
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
                field._value = fn(value=value, field=field, etree=etree, document=document)
                return field._value
            self.parse = new_parse.__get__(self, self.__class__)

            return fn
        return decorator

    def update(self, value):
        # Useful for @map to have a uniform way of updating field values
        self._value = value


class ElementField(ElementsField):
    def parse(self, etree, document):
        elements = super(ElementField, self).parse(etree, document)
        try:
            element = filter(lambda e: hasattr(e, 'xpath'), elements)[0]
        except IndexError:
            self._value = elements if len(elements) else None
        else:
            self._value = element
        return self._value


class StringsField(ElementField):
    def parse(self, etree, document):
        value = super(StringsField, self).parse(etree, document)
        if hasattr(value, 'xpath'):
            value = self._clean_texts(value.xpath('text()'))
            if not value and not self.optional:
                raise ParsingError('Could not find any strings for xpath "{0}" starting from {1}'.format(
                    self.xpath, element_to_string(etree)))
        self._value = value
        return self._value

class TextField(StringsField):
    def __init__(self, xpath=None, separator=' ', *args, **kwargs):
        super(TextField, self).__init__(xpath=xpath, *args, **kwargs)
        self.separator = separator

    def parse(self, etree, document):
        value = super(TextField, self).parse(etree, document)
        self._value = clean_ascii(self.separator.join(value)).strip() if value is not None else None
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
        if not hasattr(element, 'attrib'):
            self._value = ''.join(element) if type(element) is list and len(element) else None
        else:
            self._value = element.attrib.get(
                'src',
                element.attrib.get(
                    'href',
                    clean_ascii(''.join(element.xpath('text()'))).strip()))
        if not self._value and not self.optional:
            raise ParsingError('Could not find any URL for xpath "{0}" starting from {1}'.format(
                self.xpath, element_to_string(etree)))
        return self._value

class StructuredField(MutableMapping, ElementField):
    def __init__(self, xpath=None, structure=None, *args, **kwargs):
        super(StructuredField, self).__init__(xpath=xpath, *args, **kwargs)
        self.structure = structure

    def parse(self, etree, document):
        element = super(StructuredField, self).parse(etree, document)
        value = OrderedDict()
        for key, field in self.structure.iteritems():
            value[key] = copy.deepcopy(field)
            try:
                value[key].parse(element, document)
            except Exception as e:
                raise ParsingError('Failed to parse "{0}" for xpath "{1}": {2}'.format(key, self.xpath, e.message))
        self._value = value
        return self._value

    def update(self, value):
        self._value.update(value)

    @property
    def _value_(self):
        return {key: item._value_ for (key, item) in self._value.iteritems()}

    def __getitem__(self, key):
        try:
            return self._value[key]._value_
        except KeyError:
            raise KeyError('StructuredField has no key "{0}"'.format(key))

    def __call__(self, key):
        try:
            return self._value[key]
        except KeyError:
            raise KeyError('StructuredField has no key "{0}"'.format(key))

    def __setitem__(self, key, value):
        try:
            self._value[key]._value = value
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

    def parse(self, etree, document):
        elements = super(ListField, self).parse(etree, document)
        value = []
        for i, element in enumerate(elements):
            item = copy.deepcopy(self.item)
            try:
                item.parse(element, document)
            except Exception as e:
                raise ParsingError('Failed to parse item {0} for xpath "{1}": {2}'.format(i, self.xpath, e.message))
            if self._filter(value=item._value,
                            item=item,
                            field=self,
                            etree=etree,
                            document=document):
                value.append(item)
        self._value = value
        return self._value

    def map(self):
        def decorator(fn):
            # Decorated function only need declare the arguments it's interested in:
            # value, item, field, etree, document
            # It needs to return a value that the item field can use for update()
            self._parse = self.parse
            @functools.wraps(fn) # decorator.decorator?
            def new_parse(field, etree, document):
                items = self._parse(etree, document)
                map(lambda item: item.update(fn(value=item._value,
                                                item=item,
                                                field=field,
                                                etree=etree,
                                                document=document)), items)
                field._value = items
                return field._value
            self.parse = new_parse.__get__(self, self.__class__)

            return fn
        return decorator

    def filter(self):
        def decorator(fn):
            # Decorated function only need declare the arguments it's interested in:
            # value, item, field, etree, document
            # It needs to return a truthy or falsey value
            self._filter = fn
            return fn
        return decorator

    @staticmethod
    def _filter(value=None, item=None, field=None, etree=None, document=None):
        return True

    @property
    def _value_(self):
        return [item._value_ for item in self._value]

    def __getitem__(self, i):
        try:
            return self._value[i]._value_
        except IndexError:
            raise IndexError('ListField has no item {0}'.format(i))

    def __call__(self, i):
        try:
            return self._value[i]
        except IndexError:
            raise IndexError('ListField has no item {0}'.format(i))

    def __setitem__(self, i, value):
        try:
            self._value[i]._value = value
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

    def parse(self, etree, document):
        elements = super(DictField, self).parse(etree, document)
        value = OrderedDict()
        for i, element in enumerate(elements):
            item = copy.deepcopy(self.item)
            if isinstance(self.key, ElementsField):
                # Parse the key first, then the item
                key = copy.deepcopy(self.key)
                try:
                    key.parse(element, document)
                except Exception as e:
                    raise ParsingError('Failed to parse key {0} for xpath "{1}": {2}'.format(i, self.xpath, e.message))
                key = key._value
                try:
                    item.parse(element, document)
                except Exception as e:
                    raise ParsingError('Failed to parse item "{0}" for xpath "{1}": {2}'.format(key._value, self.xpath, e.message))
            elif isinstance(self.key, basestring):
                # Parse item first, then extract key from it via element access
                try:
                    item.parse(element, document)
                except Exception as e:
                    raise ParsingError('Failed to parse item {0} for xpath "{1}": {2}'.format(i, self.xpath, e.message))
                key = item
                for index in self.key.split('/'):
                    key = key[index]
                if hasattr(key, '_value'):
                    # Depending how element access is implemened, key might be an actual value or a field
                    key = key._value
            value[key] = item
        self._value = value
        return self._value

    @property
    def _value_(self):
        return {key: item._value_ for (key, item) in self._value.iteritems()}

    def __getitem__(self, key):
        try:
            return self._value[key]._value_
        except KeyError:
            raise KeyError('DictField has no key "{0}"'.format(key))

    def __call__(self, key):
        try:
            return self._value[key]
        except KeyError:
            raise KeyError('DictField has no key "{0}"'.format(key))

    def __setitem__(self, key, value):
        try:
            self._value[key]._value = value
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


# TODO: the following fields are no longer part of the intended class structure and must be removed

class DEP_StructuredList(ElementsField):
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

class DEP_IndexedStructuredList(ElementsField):
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

class DEP_DictField(ElementsField):
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
