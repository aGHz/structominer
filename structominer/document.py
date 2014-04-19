"""The parent class for all parsers."""

from collections import OrderedDict, Mapping
import inspect
from lxml import etree

from .fields import BiaxialAccessContainer, Field


class Document(BiaxialAccessContainer, Mapping):
    """This is the parent class for all parsers as it contains the mechanism for defining and parsing :class:`Field`\ s.
    The fields are parsed in the order they are defined, and they may rely on this behaviour.

    Fields can be accessed along all three axes:

    * Element access recursively retrieves field values: ``doc[field]``
    * Callable access returns the field object: ``doc(field)``
    * Attribute access is not explicitly mixed in but fields are already
      defined as attributes of the document: ``doc.field``

    :param html: HTML content to parse.
        Optional, if present it will use it to call :meth:`parse`
    """
    def __init__(self, html=None):
        fields = [(name, attr) for (name, attr) in inspect.getmembers(self, lambda attr: isinstance(attr, Field))]
        self._fields = self._value = OrderedDict(sorted(fields, key=lambda tupl: tupl[1]._field_counter))
        if html:
            self.parse(html)

    def parse(self, html):
        """Executes the parsing mechanism. It looks at each field with auto_parse True in order of
        definition, and calls its :meth:`Field.parse` with the etree and a reference to this document.

        :param html: HTML content to parse, passed through :meth:`etree.HTML`
        """
        self.html = html
        self.etree = etree.HTML(html)
        for field in self._fields.values():
            if field.auto_parse:
                field.parse(etree=self.etree, document=self)
