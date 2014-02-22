from .document import Document
from .fields import ElementsField,
    StringsField, TextField, IntField, DateField, URLField, StructuredField,
    StringsList, TextList, IntList, StructuredList, IndexedStructuredList,
    ElementsOperation


class ParsingError(Exception):
    pass
