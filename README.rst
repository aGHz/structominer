Struct-o-Miner
==============

*The high-class document scraper.*

Struct-o-Miner is an elegant Python library for extracting structured data from HTML or XML documents.
With Struct-o-Miner, you won't get your hands dirty selecting elements and pulling out their contents
in a distatestful mess of code. Instead, you declaratively specify the data you're interested in,
much in the same way you would write an SQLAlchemy model or a Django form, and the Struct-o-Miner
takes care of all the details. And if you need to have your data just so, you can always micromanage it
using simple decorators for pre- or post-processing field results.

What sets Struct-o-Miner apart, other than its rich declarative syntax, is that it never presumes to
prescribe how it best be employed.
With no strings attached, you can use it inside a web spider, a dashboard aggregator or a log parser that
might need to know XML. Simply define your document and pass it a string to parse, no questions asked.

Overview
--------

The complete documentation is available on `ReadTheDocs <https://readthedocs.org/projects/structominer/>`_.

For a quick example though, let's consider the following HTML snippet:

.. code-block:: html
   :linenos:

    <div>
        <span class="foo">Foo</span> <a href="http://example.com/bar">Example: Bar</a>
        <ul>
            <li><span>2014-03-01</span>:  1 (one)</li>
            <li><span>2014-03-05</span>: 3 (three)</li>
        </ul>
    </div>

We can extract all the data using this document:

.. code-block:: python
   :linenos:

    class Stuff(Document):
        foo = TextField('//div/span[@class="foo"]')
        bar_name = TextField('//div/a')
        bar_url = URLField('//div/a')
        things = StructuredListField(xpath='//div/ul/li', structure=dict(
            date = DateField('./span'),
            number = IntField('.')))

        @bar_name.postprocessor()
        def _extract_the_bar_name(value, **kwargs):
            return value.split(' ')[-1]

        @things.number.preprocessor()
        def _clean_numbers(value, **kwargs):
            return value.strip(': ').split(' ')[0]

    data = Stuff(html)

* Notice how bar_name and bar_url share an xpath, but URLField will look for the href.
* The StructuredListField takes an xpath selecting a list of heterogeneous elements, and creates
  a StructuredField for each in turn. The subfield xpaths are relative to each selected element.
* The bar_name post-processor will remove the 'Example: ' part after the field was parsed.
* The number pre-processor will make sure to keep only the numeric part for IntField to work.

All fields expose mapping or sequence interfaces as appropriate. Furthermore, they implement
access along three axes: *element access* returns data values, *calling* returns the actual field,
and *attribute access*, where appropriate, returns the structure subfield definition (notice how
the last two DateFields at the end are distinct):

.. code-block:: pycon

    >>> pprint(dict(data))
    {'bar_name': 'Bar',
     'bar_url': 'http://example.com/bar',
      'foo': 'Foo',
       'things': [{'date': datetime.date(2014, 3, 1), 'number': 1},
                   {'date': datetime.date(2014, 3, 5), 'number': 3}]}

    >>> data('foo')
    <structominer.fields.TextField object at 0x10efa1190>
    >>> data.foo
    <structominer.fields.TextField object at 0x10efa1190>
    >>> data['foo']
    'Foo'

    >>> data['things'][0]['date']
    datetime.date(2014, 3, 1)
    >>> data('things')(0)['date']
    datetime.date(2014, 3, 1)
    >>> data('things')(0)('date')
    <structominer.fields.DateField object at 0x10efae7d0>
    >>> data.things.date
    <structominer.fields.DateField object at 0x10efa1250>

Install
-------

You can install Struct-o-Miner from PyPI with `pip <http://www.pip-installer.org/>`_:

.. code-block:: sh

    $ pip install structominer

or from `GitHub <https://github.com/aGHz/structominer>`_ with git:

.. code-block:: sh

    $ git clone https://github.com/aGHz/structominer.git
    $ cd structominer && python setup.py install
