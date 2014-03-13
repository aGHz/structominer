Examples
========

Consider the following HTML snippet

.. literalinclude:: ../examples/simple.py
   :language: html
   :lines: 2-15
   :linenos:

and suppose we want to extract all the useful information from this, so we define a Document:

.. literalinclude:: ../examples/simple.py
   :language: python
   :lines: 18-30
   :linenos:

Notice a few things:

* A StructuredListField takes an xpath that results in a collection of heterogeneous elements.
  It then defines
* asdf

We can then simply write ``project = Project(html)`` and look at ``dict(project)``:

.. literalinclude:: ../examples/simple.py
   :language: json
   :lines: 51-67
   :emphasize-lines: 2,6,11
   :linenos:

