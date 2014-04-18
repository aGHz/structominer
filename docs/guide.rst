Guide
=====

Document
--------

The document is the entry point to the Struct-o-Miner machinery:
it is how you instruct the miner on the location of data to extract.
Start by subclassing :class:`Document`, and therein define the fields
you are interested in as attributes with values derived from :class:`Field`.

.. note::

    The names of the attributes are irrelevant but their **order** matters.
    The parsing mechanism will seek out each field in order of definition,
    so references to earlier fields can be used inside processors.

The document is also where you define additional operations the miner should
perform for each field. There are three kinds of operations: pre-processors,
post-processors and error handlers. These operations are described in more
detail in the Processors section below.

..
    They are defined by wrapping document
    methods with the desired decorator associated with the appropriate field.
    These decorators will not alter the method but return it untouched so that
    it may be unit tested or otherwise manipulated as wished.

Once the document defined, it must be instantiated with a string containing the markup.
This performs the parsing, and the document can then be queried like any mapping in order to access the parsed values,
using field names as keys.
The field objects themselves can be accessed as attributes of the document.

Fields
------

Fields represent individual units of data you wish to extract from the document.
They are objects subclassing :class:`Field` and assigned to attributes inside
documents.

Advanced Fields
---------------

Some fields are less commonly useful and exist mainly to provide a clear
separation of concerns along the inheritance chain.
