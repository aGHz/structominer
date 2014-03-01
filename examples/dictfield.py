from structominer import Document, DictField, ListField, TextField, IntField, StructuredField

html = """
<ul>
  <li>
    <span class="name">Foo</span>
    <ol class="values"> <li>1</li> <li>2</li> <li>3</li> </ol>
  </li>
  <li>
    <span class="name">Bar</span>
    <ol class="values"> <li>10</li> <li>20</li> </ol>
  </li>
  <li>
    <span class="name">Baz</span>
    <ol class="values"> <li>100</li> <li>250</li> <li>200</li> <li>300</li> </ol>
  </li>
</ul>
"""

class MyDoc(Document):
    things = DictField(
        '//ul/li',
        key=TextField('.//span[@class="name"]'),
        item=ListField(
            './/ol/li',
            item=IntField('.')
        )
    )
    things_by_name = DictField(
        '//ul/li',
        item=StructuredField(
            '.',
            structure=dict(
                name=TextField('.//span[@class="name"]'),
                values=ListField(
                    './/ol/li',
                    item=IntField('.')
                )
            )
        ),
        key='name' # matches structure['name']
    )


mydoc = MyDoc(html)

# Iterating returns the values directly:
for key, values in mydoc['things'].iteritems():
    print '{0}: [{1}]'.format(key, ', '.join(str(value) for value in values))

# Element access returns the values directly:
print 'Foo[0] + Baz[2] - Bar[1] =', (mydoc['things']['Foo'][0] + mydoc['things']['Baz'][2] - mydoc['things']['Bar'][1])

# Calling returns the Field object:
print 'Foo xpath:', mydoc('things')('Foo').xpath
print 'Foo\'s first thing\'s element:', mydoc('things')('Foo')(0)._target_

# Mixing field and value access:
print 'Straight to Baz\'s first thing:', mydoc('things')('Baz')[0]
