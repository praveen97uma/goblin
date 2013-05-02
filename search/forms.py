import wtforms

from mediagoblin.tools.translate import lazy_pass_to_ugettext as _

class SearchForm(wtforms.Form):
    query = wtforms.TextField(
        _('Search'),
        [wtforms.validators.Length(min=0, max=500)])
