Struct-o-Miner
==============

Python package for extracting structured data from XML/HTML documents. **Work in progress**.

Install
-------
Struct-o-miner depends only on [lxml](http://lxml.de/installation.html), which in turn requires libxml2 2.6.21 or later and libxslt 1.1.15 or later.

While waiting for proper Python packaging (issue [#2](../../issues/2)), you can clone this repository as `structominer` into the root of your Python project: `git clone https://github.com/aGHz/structominer.git structominer`.

Usage
-----
To start using Struct-o-miner, subclass `structominer.Document`. In your subclass, target the information you want to extract using attributes set to objects of the various field types, wrapping XPath 1.0 selectors. For example:

```python
class MyDoc(Document):
    name = TextField('//body/div[@class="user"]/span[@id="name"]')
```

See [fields.py](fields.py) for all the available field types.

You can specify custom code to be executed for each field to alter the parsed value. The custom parser will be passed the following arguments: `value` contains the parsed value, `field` references the field that's being parsed, `etree` contains the ElementTree that's being parsed, and `document` the parent document instance. You only need to add the arguments you're interested in to your parser's signature, but make sure to leave `*args, **kwargs` for the rest. Then simply return the modified value. For example:

```python
    @name.parser()
    def _capitalize_name(value, *args, **kwargs):
        return value.upper()
```

Finally, instantiate your document class with the HTML you want to parse:

```python
import requests
response = requests.get('http://example.com/')
mydoc = MyDoc(response.text)
```

The parsed data is now available via normal Python element access:

```python
print mydoc['name']
```

Examples
--------
More examples can be found in the [examples](examples/) directory. To run them while waiting for proper python packaging:

    # install libxml2 using your native package manager
    git clone https://github.com/aGHz/structominer.git structominer
    cd structominer
    virtualenv --distribute --no-site-packages .
    . bin/activate
    pip install lxml requests
    PYTHONPATH="../" python examples/hn.py
