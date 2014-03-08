from structominer import Document, DictField, ListField, TextField, IntField, StructuredField

html = """
<ul>
  <li>
    <ol> <li>1</li> <li>2</li> <li>3</li> </ol>
  </li>
  <li>
    <ol> <li>10</li> <li>20</li> </ol>
  </li>
  <li>
    <ol> <li>100</li> <li>250</li> <li>200</li> <li>300</li> </ol>
  </li>
</ul>
"""

class MyDoc(Document):
    things = ListField(
        '//ul/li',
        item=ListField(
            './/ol/li',
            item=IntField('.')
        )
    )

mydoc = MyDoc(html)

# Element access returns the values directly:
print 'Things:', mydoc['things']
print 'First thing:', mydoc['things'][0]
print 'First thing\'s second thing:', mydoc['things'][0][1]

# Calling returns the Field object:
print 'Things xpath:', mydoc('things').xpath
print 'First thing\'s element:', mydoc('things')(0).target
print 'First thing\'s first thing\'s element:', mydoc('things')(0)(0).target

# Mixing field and value access:
print 'Straight to third thing\'s second thing:', mydoc('things')(2)[1]
