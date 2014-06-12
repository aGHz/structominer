from mock import patch, Mock, MagicMock, ANY
from nose.tools import istest
from unittest import TestCase

from structominer import Document, Field


class FieldTests(TestCase):

    @istest
    def fields_should_be_assigned_ordered_creation_counters(self):
        class Doc1(Document):
            one = Field(None)
            two = Field(None)

        class Doc2(Document):
            three = Field(None)
            four = Field(None)

        doc1 = Doc1()
        doc2 = Doc2()
        doc1a = Doc1()

        self.assertTrue(doc1.one._field_counter < doc1.two._field_counter)
        self.assertTrue(doc1a.one._field_counter < doc1a.two._field_counter)
        self.assertTrue(doc2.three._field_counter < doc2.four._field_counter)

    @istest
    def creating_field_with_field_source_should_keep_source_as_is(self):
        source = Mock(Field)
        field = Field(source)

        self.assertEquals(field.source, source)

    @istest
    def creating_field_with_nonfield_source_should_use_default_source_class(self):
        class DefaultField(Field):
            default_source = Mock(return_value='foo')

        field = DefaultField('bar')

        field.default_source.assert_called_with('bar', optional=ANY, auto_parse=ANY)
        self.assertEquals(field.source, 'foo')

    @istest
    def creating_field_without_default_source_should_cast_source_to_string(self):
        source = MagicMock()
        source.__unicode__.return_value = u'foo'
        class Doc(Document):
            one = Field(source)

        self.assertTrue(source.__unicode__.called)
        self.assertEquals(Doc.one.source, u'foo')

    @istest
    def parsing_field_with_field_source_should_parse_the_source_first(self):
        source = Mock(Field)
        source.parse.return_value = 'foo'
        class Doc(Document)
            one = Field(source)

