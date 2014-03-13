from django.contrib.auth.decorators import login_required
from splunkdj.decorators.render import render_to
from .forms import SetupForm
from django.core.urlresolvers import reverse
from splunkdj.setup import config_required
from splunkdj.setup import create_setup_view_context

app_id = "r"
app_label = "R - Statistical Computing"

@render_to(app_id + ':home.html')
@login_required
@config_required
def home(request):
    return {
        "app_id": app_id,
        "app_label": app_label,
        "samples": [
            {
                "id": 'buildsimpletable',
                "url": '| r "output=data.frame('
                       'Name=c(\'A\',\'B\',\'C\'),'
                       'Value=c(1,2,3)'
                       ')"',
                "name": "Generate a simple data table",
                "description": "This example doesn't receive data from a Splunk search. "
                               "It just creates a small table with 2 columns (Name, Value) "
                               "and 3 rows. "
                               "After creating the table, it is returned to Splunk by assigning "
                               "to the <code>output</code> variable."
            },
            {
                "id": 'summaryinternalsources',
                "url": 'index=_internal '
                       '| head 1000 '
                       '| table source '
                       '| r "output=summary(input)"',
                "name": "Summarize internal event sources"
            },
            {
                "id": 'summarybabyname',
                "url": '| babynames | '
                       'table "First Name" '
                       '| r "output=summary(input)"',
                "name": "Summarize favorite baby names"
            },
        ],
    }

@render_to(app_id + ':setup.html')
@login_required
def setup(request):
    return create_setup_view_context(
        request,
        SetupForm,
        reverse(app_id + ':home')
    )