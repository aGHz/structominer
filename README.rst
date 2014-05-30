Struct-o-Miner
==============

*Data scraping for a more civilized age*

Struct-o-Miner is an elegant Python library for extracting structured data from HTML or XML documents.
It's ideal for situations where you have your document in a string and just want the data out of it,
something like a fancy type casting operation.


Features
--------

**Declarative syntax.** The format of data is static, so any imperative code you have to write to
extract it is just boilerplate. Instead, declare the structures you're interested in much in the same
way you define models in Django or SQLAlchemy, and let Struct-o-Miner take care of the boring parts.

**Rich data types.** Obtain your data directly as Python types using fields like TextField, IntField
or DateTimeField. You can even have lists of dictionaries using StructuredListField.

**Organized.** The most cumbersome part of scraping is data cleanup. All the exceptional cases and
real-world considerations can rapidly degenerate into complicated and unmaintanable spaghetti.
Struct-o-Miner provides tools to separate this code by field and by semantic concern.

**Focused.** Struct-o-Miner adheres to the Unix philosophy of doing one thing and doing it well:
you give it a document and it gives you structured data. Scraping is not exclusively part of
web crawling, and Struct-o-Miner is a small library that enables you to do it in any project,
with no additional cruft.


Overview
--------

For a quick example, consider the following HTML snippet:

.. code-block:: html

    <div>
        <span class="foo">Foo</span> <a href="http://example.com/bar">Example: Bar</a>
        <ul>
            <li><span>2014-03-01</span>: 1 (one)</li>
            <li><span>2014-03-05</span>: 3 (three)</li>
        </ul>
    </div>

Here is a document that targets some of the data we might be interested in:

.. code-block:: python

    class Stuff(Document):
        foo = TextField('//div/span[@class="foo"]')
        bar_name = TextField('//div/a')
        bar_url = URLField('//div/a')  # Same xpath, but URLField extracts the href
        things = StructuredListField('//div/ul/li', structure=dict(
            # A StructuredField for each element selected by the xpath above
            # Sub-element xpaths are relative to their respective parent
            date = DateField('./span'),
            number = IntField('.')))

        @bar_name.postprocessor
        def _extract_the_bar_name(value, **kwargs):
            # Remove 'Example: ' after the field is parsed
            return value.split(' ')[-1]

        @bar_name.postprocessor
        def _uppercase_the_bar_name(value, **kwargs):
            # Handle the field after the previous processor ran
            return value.upper()

        @things.number.preprocessor
        def _clean_numbers(value, **kwargs):
            # Isolate the numeric part before the field is parsed as an int
            return value.strip(': ').split(' ')[0]

Now we just pass the HTML to this object for parsing, and data is then available using typical Python element access.
In Struct-o-Miner, we call this **value access**.

.. code-block:: pycon

    >>> data = Stuff(html)

    >>> pprint(dict(data))
    {'bar_name': 'Bar',
     'bar_url': 'http://example.com/bar',
     'foo': 'Foo',
     'things': [{'date': datetime.date(2014, 3, 1), 'number': 1},
                {'date': datetime.date(2014, 3, 5), 'number': 3}]}

    >>> data['things'][0]['date']
    datetime.date(2014, 3, 1)

You can also reach the field object for each datum using parentheses (i.e. function calls).
**Field access** may seem un-pythonic at first, but every field containing some kind of structure
(ListField, DictField, StructuredField and variants) is also a callable that returns the
requested child object.

.. code-block:: pycon

    >>> data('things')(0)['date']
    datetime.date(2014, 3, 1)

    >>> data('things')(0)('date')
    <structominer.fields.DateField object at 0x10efae7d0>

Finally, the third axis of access allows you to reach the objects used as structural
templates in fields such as lists and dictionaries. **Structure access** is what enabled us
to define the preprocessor on `things.number`. Notice how the following are distinct:

.. code-block:: pycon

    >>> data.things.date
    <structominer.fields.DateField object at 0x10efa1250>

    >>> data('things')(0)('date')
    <structominer.fields.DateField object at 0x10efae7d0>


Alternatives
------------

The Python ecosystem is rich in solutions for or related to data scraping and web crawling.
This is a survey of possible alternatives, highlighting the unique ways Struct-o-Miner contributes to the scene.

`lxml <http://lxml.de/>`_ and `Beautifoul Soup <http://www.crummy.com/software/BeautifulSoup/>`_ are the
standard building blocks of Python scrapers: they both parse markup documents and provide an interface
to query and manipulate them. Using them directly can be cumbersome though, as data needs to be selected
manually. Struct-o-Miner provides a declarative interface for targetting the elements, then uses lxml
under the hood to select all the data.

`pyquery <http://pythonhosted.org/pyquery/>`_ wraps lxml.etree with a jQuery-inspired API more familiar to web developers.
Apart from the convenience of selecting elements using CSS, pyquery provides little advantage in scraping over lxml.
Similarly, `cssselect <http://pythonhosted.org/cssselect/>`_ converts CSS selectors to XPath queries
which can then be used with lxml. There are plans to support it directly within Struct-o-Miner so that
fields can be specified using CSS.

`Scrapy <http://scrapy.org/>`_ is a complete web crawling framework.
It can be used to build a reliable crawling operation and benefits from a large community as well as
commercial support from `ScrapingHub <http://scrapinghub.com/>`_, including a PaaS for running massive Scrapy projects.
Despite differences in stylistic approach, Struct-o-Miner is comparable in purpose to Scrapy Items and ItemLoaders.
It was however designed to provide this functionality as a standalone library,
with an arguably more pythonic flavour.

`Colander <http://colander.readthedocs.org/>`_ can be used in a similar way to Struct-o-miner when dealing with JSON data.
It can extract data from a structure composed of lists, mappings and strings (think `json.loads`) into an object that
you define using a schema. It can also validate the data and serialize an object back into the original format.


Install
-------

You can install Struct-o-Miner from PyPI with `pip <http://www.pip-installer.org/>`_:

.. code-block:: sh

    $ pip install structominer

or from `GitHub <https://github.com/aGHz/structominer>`_ with git:

.. code-block:: sh

    $ git clone https://github.com/aGHz/structominer.git
    $ cd structominer && python setup.py install
