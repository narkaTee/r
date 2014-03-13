import django
from django.contrib.auth.decorators import login_required
from splunkdj.decorators.render import render_to
from .forms import SetupForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from splunkdj.setup import config_required
from splunkdj.setup import create_setup_view_context
import os

app_id = "r"
app_label = "R - Statistical Computing"


@render_to(app_id + ':home.html')
@login_required
@config_required
def home(request):
    return {
        "request": request,
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


@render_to(app_id + ':scripts.html')
@login_required
@config_required
def scripts(request):

    upload_new_script_action = 'upload_new_script'
    new_script_field_name = 'new_script'
    delete_script_action_prefix = 'delete_script_'
    dirname, filename = os.path.split(os.path.abspath(__file__))
    scripts_directory_path = os.path.join(os.path.dirname(os.path.dirname(dirname)), 'local', 'scripts')

    if request.method == 'POST':
        #save script in local folder
        if upload_new_script_action in request.POST:
            if not os.path.exists(scripts_directory_path):
                os.makedirs(scripts_directory_path)
            source_file = request.FILES[new_script_field_name]
            if source_file.name.endswith('.r'):
                with open(os.path.join(scripts_directory_path, source_file.name), 'wb+') as destination_file:
                    for chunk in source_file.chunks():
                        destination_file.write(chunk)
        #delete script
        else:
            for key in request.POST:
                if key.startswith(delete_script_action_prefix):
                    file_name = key[len(delete_script_action_prefix):]
                    file_path = os.path.join(scripts_directory_path, file_name)
                    os.remove(file_path)
        return HttpResponseRedirect('')

    #scan for R scripts in app local folder
    r_scripts = []
    if os.path.exists(scripts_directory_path):
        for file_name in os.listdir(scripts_directory_path):
            if file_name.endswith(".r"):
                r_scripts.append({
                    'file_name': file_name,
                    'is_local': True
                })

    return {
        'scripts': r_scripts,
        'app_title': app_label,
        'request': request,
        'new_script_field_name': new_script_field_name,
        'upload_new_script_action': upload_new_script_action,
        'delete_script_action_prefix': delete_script_action_prefix,
    }