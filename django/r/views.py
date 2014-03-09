from django.contrib.auth.decorators import login_required
from splunkdj.decorators.render import render_to

app_name = "r"
app_title = "The R Project"

@render_to('r:home.html')
@login_required
def home(request):
    return {
        "app_name": app_name,
        "app_title": app_title,
        "samples": [
            {"url": "../summary/", "name": "Summary Command"}
        ],
    }

@render_to('r:summary.html')
@login_required
def summary(request):
    return {
        "app_name": app_name,
        "app_title": app_title,
    }