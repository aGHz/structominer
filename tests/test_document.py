from mock import patch, Mock
from nose.tools import istest
from unittest import TestCase

from structominer import Document, Field


class DocumentTests(TestCase):
    
    @istest
    def creating_document_object_with_string_should_automatically_parse(self):
        html = '<html></html>'

        with patch('structominer.Document.parse') as mocked_parse:
            doc = Document(html)
            mocked_parse.assert_called_with(html)

    @istest
    def document_should_store_fields_in_order(self):
        class Doc(Document):
            three = Mock(Field, _field_counter=3)
            two = Mock(Field, _field_counter=2)
            one = Mock(Field, _field_counter=1)

        doc = Doc()
        self.assertEquals([field._field_counter for field in doc._fields.values()], [1, 2, 3])

    @istest
    def document_should_only_parse_fields_with_auto_parse_attributes(self):
        html = '<html></html>'
        class Doc(Document):
            one = Mock(Field, _field_counter=1, auto_parse=True)
            two = Mock(Field, _field_counter=2, auto_parse=False)

        doc = Doc(html)
        self.assertTrue(doc.one.parse.called)
        self.assertFalse(doc.two.parse.called)


