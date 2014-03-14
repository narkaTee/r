from django.contrib.auth.decorators import login_required
from splunkdj.decorators.render import render_to
from .forms import SetupForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from splunkdj.setup import config_required
from splunkdj.setup import create_setup_view_context
import os
import base64
import calendar
import datetime

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

    r_config = request.service.confs.create('r')

    upload_new_script_action = 'upload_new_script'
    new_script_field_name = 'new_script'
    delete_script_action_prefix = 'delete_script_'
    script_stanza_prefix = 'script://'

    if request.method == 'POST':
        #save script in local folder
        if upload_new_script_action in request.POST:
            source_file = request.FILES[new_script_field_name]
            if source_file.name.endswith('.r'):
                source_file_noext, _ = os.path.splitext(source_file.name)
                stanza_name = script_stanza_prefix+source_file_noext
                for stanza in r_config.list():
                    if stanza.name == stanza_name:
                        stanza.delete()
                script_stanza = r_config.create(stanza_name)
                script_stanza.submit({
                    'content': base64.encodestring(source_file.read()).replace('\n', ''),
                    'uploaded': calendar.timegm(datetime.datetime.now().utctimetuple())
                })
        #delete script
        else:
            for key in request.POST:
                if key.startswith(delete_script_action_prefix):
                    file_name = key[len(delete_script_action_prefix):]
                    source_file_noext, _ = os.path.splitext(file_name)
                    stanza_name = script_stanza_prefix+source_file_noext
                    for stanza in r_config.list():
                        if stanza.name == stanza_name:
                            stanza.delete()
        return HttpResponseRedirect('')

    #scan for R scripts in app local folder
    r_scripts = []
    for stanza in r_config.list():
        if stanza.name.startswith(script_stanza_prefix):
            r_scripts.append({
                'file_name': stanza.name[len(script_stanza_prefix):]+'.r',
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