from django.contrib.auth.decorators import login_required
from splunkdj.decorators.render import render_to
from .forms import SetupForm
from django.core.urlresolvers import reverse
from splunkdj.setup import config_required
from splunkdj.setup import create_setup_view_context

app_name = "r"
app_title = "The R Project"

@render_to(app_name + ':home.html')
@login_required
@config_required
def home(request):
    return {
        "app_name": app_name,
        "app_title": app_title,
        "samples": [
            {"url": "../summary/", "name": "Summary Command"}
        ],
    }

@render_to(app_name + ':summary.html')
@login_required
@config_required
def summary(request):
    return {
        "app_name": app_name,
        "app_title": app_title,
    }

@render_to(app_name + ':setup.html')
@login_required
def setup(request):
    return create_setup_view_context(
        request,
        SetupForm,
        reverse(app_name + ':home')
    )