html = """
<div>
  Project: Struct-o-Miner <br/>
  Commits:
  <ul>
    <li>
      <span class="date">2014-02-22</span> <span class="author">aGHz</span>: First draft
    </li>
    <li>
      <span class="date">2014-02-28</span> <span class="author">aGHz</span>:
      Wrote a basic quick and dirty Hacker News example
    </li>
  </ul>
  Link: <a href="https://github.com/aGHz/structominer">GitHub</a>
</div>
"""

from structominer import Document, StructuredListField, TextField, DateField, URLField

class Project(Document):
    name = TextField('//div')
    commits = StructuredListField(
        xpath='//div/ul/li',
        structure=dict(
            date=DateField('./span[@class="date"]'),
            author=TextField('./span[@class="author"]'),
            message=TextField('.')
        ))
    home_provider = TextField('//div/a')
    home_url = URLField('//div/a')

    @name.preprocessor()
    def _use_name_line_only(value, **kwargs):
        return value[0:1]

    @name.postprocessor()
    def _extract_name(value, **kwargs):
        return value.split(': ', 1)[1]

    @commits.message.postprocessor()
    def _clean_commit_message(value, **kwargs):
        return value[2:]

project = Project(html)

import json
print json.dumps(dict(project), indent=2,
                 default=lambda obj: obj.strftime(DateField.ISO_8601) if hasattr(obj, 'strftime') else obj)

"""
{
  "name": "Project: Struct-o-Miner Commits: Link:"
  "commits": [
    {
      "date": "2014-02-22",
      "message": ": First draft",
      "author": "aGHz"
    },
    {
      "date": "2014-02-28",
      "message": ": Wrote a basic quick and dirty Hacker News example",
      "author": "aGHz"
    }
  ],
  "home_provider": "GitHub",
  "home_url": "https://github.com/aGHz/structominer",
}
"""
