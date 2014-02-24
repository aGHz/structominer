from collections import OrderedDict
import inspect
from lxml import etree

from fields import ElementsField


class Document(object):
    def __init__(self, content=None):
        fields = [(name, attr) for (name, attr) in inspect.getmembers(self, lambda attr: isinstance(attr, ElementsField))]
        self._fields = OrderedDict(sorted(fields, key=lambda tupl: tupl[1]._field_counter))
        if content:
            self.parse(content)

    def parse(self, content):
        self.content = content
        self.etree = etree.HTML(content)
        for field in self._fields.values():
            field.parse(etree=self.etree, document=self)

    def __dict__(self):
        return {key: getattr(self, key).value for key in self._fields.keys()}

    # TODO dict interface to access the value of fields directly


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
