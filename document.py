from collections import OrderedDict, MutableMapping
import inspect
from lxml import etree

from fields import ElementsField


class Document(MutableMapping):
    def __init__(self, content=None):
        fields = [(name, attr) for (name, attr) in inspect.getmembers(self, lambda attr: isinstance(attr, ElementsField))]
        self._fields = OrderedDict(sorted(fields, key=lambda tupl: tupl[1]._field_counter))
        if content:
            self.parse(content)

    def parse(self, content):
        self.content = content
        self.etree = etree.HTML(content)
        for field in self._fields.values():
            if field.auto_parse:
                field.parse(etree=self.etree, document=self)

    def __getitem__(self, key):
        try:
            return self._fields[key]._value
        except KeyError:
            raise KeyError('Document {0} has no field "{1}"'.format(self.__class__.__name__, key))

    def __setitem__(self, key, value):
        try:
            self._fields[key]._value = value
        except KeyError:
            raise KeyError('Document {0} has no field "{1}"'.format(self.__class__.__name__, key))

    def __delitem__(self, key):
        try:
            del self._fields[key]
        except KeyError:
            raise KeyError('Document {0} has no field "{1}"'.format(self.__class__.__name__, key))

    def __iter__(self):
        return self._fields.iterkeys()

    def __len__(self):
        return len(self._fields)

#class MyDoc(Document):
#    age = IntField('//*[@id="age"]')
#    sum = IntList() # no xpath: idiomatic indicator that field has a custom parser
#
#    @sum.parser('//ul[@id="qwer"]/li')
#    def sum_items(value, field, etree, document):
#        return sum(value)
#
#
#content = """
#<span id="age">42</span>'
#<ul id="qwer">
#    <li>1</li>
#    <li>2</li>
#    <li>3</li>
#</ul>
#"""
#document = MyDoc(content)
