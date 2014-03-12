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
                "id": 'summarybabyname',
                "url": '| babynames | '
                       'table "First Name" '
                       '| r "events=summary(events)"',
                "name": "Summarize favorite baby names"
            },
            {
                "id": 'summaryinternalsources',
                "url": 'index=_internal '
                       '| head 1000 '
                       '| table source '
                       '| r "events=summary(events)"',
                "name": "Summarize internal event sources"
            }
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