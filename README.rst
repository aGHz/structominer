Struct-o-Miner
==============

Python package for extracting structured data from XML/HTML documents. **Work in progress**.

Install
-------

Struct-o-miner depends only on `lxml <http://lxml.de/installation.html>`_,
which in turn requires libxml2 2.6.21 or later and libxslt 1.1.15 or later.

Struct-o-miner is soon coming to PyPI, follow issue `#2 <http://github.com/aGHz/structominer/issues/2>`_ for updates.

Usage
-----

To start using Struct-o-miner, subclass ``structominer.Document``.
In your subclass, target the information you want to extract using attributes set to objects of the various field types, wrapping XPath 1.0 selectors.
For example:

.. code-block:: python

  class MyDoc(Document):
      name = TextField('//body/div[@class="user"]/span[@id="name"]')

See `fields.py <fields.py>`_ for all the available field types.

You can specify custom code to be executed for each field to alter the parsed value.
The custom processor will be passed the following arguments:
``value`` contains the parsed value,
``field`` references the field that's being parsed,
``etree`` contains the ElementTree that's being parsed, and
``document`` the parent document instance.
You only need to add the arguments you're interested in to your function's signature, but make sure to leave ``*args, **kwargs`` for the rest.
Then simply return the modified value. For example, in MyDoc you could add:

.. code-block:: python

  @name.postprocessor()
  def _capitalize_name(value, *args, **kwargs):
      return value.upper()

Finally, instantiate your document class with the HTML you want to parse:

.. code-block:: python

  import requests
  response = requests.get('http://example.com/')
  mydoc = MyDoc(response.text)

The parsed data is now available via normal Python element access:

.. code-block:: python

  print mydoc['name']

Examples
--------
More examples can be found in the `examples <examples/>`_ directory. To run them while waiting for proper python packaging:

.. code-block:: sh

  # install libxml2 using your native package manager
  git clone https://github.com/aGHz/structominer.git structominer
  cd structominer
  virtualenv --distribute --no-site-packages .
  . bin/activate
  pip install lxml requests
  PYTHONPATH="." python examples/hn.py

