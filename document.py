from collections import OrderedDict, Mapping
import inspect
from lxml import etree

from fields import BiaxialAccessContainer, Field


class Document(BiaxialAccessContainer, Mapping):
    def __init__(self, content=None):
        fields = [(name, attr) for (name, attr) in inspect.getmembers(self, lambda attr: isinstance(attr, Field))]
        self._fields = self._value = OrderedDict(sorted(fields, key=lambda tupl: tupl[1]._field_counter))
        if content:
            self.parse(content)

    def parse(self, content):
        self.content = content
        self.etree = etree.HTML(content)
        for field in self._fields.values():
            if field.auto_parse:
                field.parse(etree=self.etree, document=self)
