from django.contrib.auth.decorators import login_required
from splunkdj.decorators.render import render_to, ajax_request
from ..forms import SetupForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponseServerError
from splunkdj.setup import config_required
from splunkdj.setup import create_setup_view_context
import os
import sys
import errors
import shutil

# allow imports from bin directory
bin_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bin')
sys.path += bin_path

import scripts as scriptlib
import packages as packagelib

app_id = "r"


@login_required
@config_required
@render_to(app_id + ':examples.html')
def examples(request):
    return {
        "request": request,
        "app_id": app_id,
        "app_label": request.service.apps[app_id].label,
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


@login_required
@render_to(app_id + ':setup.html')
def setup(request):
    return create_setup_view_context(
        request,
        SetupForm,
        reverse(app_id + ':home')
    )


@login_required
@config_required
@render_to(app_id + ':scripts.html')
def scripts(request):

    upload_new_script_action = 'upload_new_script'
    new_script_field_name = 'new_script'
    delete_script_action_prefix = 'delete_script_'

    if request.method == 'POST':
        try:
            # add script stanza
            if upload_new_script_action in request.POST:
                if new_script_field_name in request.FILES:
                    source_file = request.FILES[new_script_field_name]
                    if source_file.name.lower().endswith('.r'):
                        source_file_noext, _ = os.path.splitext(source_file.name)
                        scriptlib.add(request.service, source_file_noext, source_file.read())
                    else:
                        raise errors.Error('Wrong file extension. It has to be \'r\'.')
                else:
                    raise errors.Error('File missing')
            # delete script stanza
            else:
                for key in request.POST:
                    if key.startswith(delete_script_action_prefix):
                        file_name = key[len(delete_script_action_prefix):]
                        source_file_noext, _ = os.path.splitext(file_name)
                        scriptlib.remove(request.service, source_file_noext)
        except errors.Error as e:
            return HttpResponseRedirect('./?add_error=%s' % str(e))
        except Exception as e:
            return HttpResponseRedirect('./?add_fatal_error=%s' % str(e))
        return HttpResponseRedirect('./')

    # scan for R script stanzas
    r_scripts = []
    for stanza, name in scriptlib.iter_stanzas(request.service):
        r_scripts.append({
            'file_name': name+'.r',
            'name': name,
            'is_removable': stanza.access['removable'] == '1',
            'owner': stanza.access['owner'],
        })

    return {
        'scripts': r_scripts,
        'app_label': request.service.apps[app_id].label,
        'request': request,
        'can_upload': scriptlib.can_upload(request.service),
        'new_script_field_name': new_script_field_name,
        'upload_new_script_action': upload_new_script_action,
        'delete_script_action_prefix': delete_script_action_prefix,
        'add_error': request.GET.get('add_error', ''),
        'add_fatal_error': request.GET.get('add_fatal_error', ''),
    }


@login_required
@config_required
@render_to(app_id + ':packages.html')
def packages(request):
    add_package_action = 'add_package'
    add_package_field_name = 'add_package_name'
    delete_package_action_prefix = 'delete_package_'
    upload_package_action = 'upload_package'
    upload_package_field_name = 'package_file'

    if request.method == 'POST':
        try:
            # raise errors.Error(packagelib.get_packages_path())
            # add package stanza
            if add_package_action in request.POST:
                package_name = request.POST[add_package_field_name]
                packagelib.get_package_description_lines(package_name)
                packagelib.add(request.service, package_name)
            # upload package and add package stanza
            elif upload_package_action in request.POST:
                if upload_package_field_name in request.FILES:
                    archive_file = request.FILES[upload_package_field_name]
                    package_name = packagelib.get_package_name_from_archive_file(archive_file.name, archive_file)
                    target_archive_path = os.path.join(packagelib.get_packages_path(), packagelib.get_local_package_filename(package_name))
                    archive_file.seek(0)
                    data = archive_file.read()
                    with open(target_archive_path, 'w') as f:
                        f.write(data)
                    packagelib.add(request.service, package_name)
                else:
                    raise errors.Error('File missing')
            # delete package stanza
            else:
                for key in request.POST:
                    if key.startswith(delete_package_action_prefix):
                        package_name = key[len(delete_package_action_prefix):]
                        packagelib.remove(request.service, package_name)
        except errors.Error as e:
            return HttpResponseRedirect('./?add_error=%s' % str(e))
        except Exception as e:
            return HttpResponseRedirect('./?add_fatal_error=%s' % str(e))
        return HttpResponseRedirect('./')

    # scan for package stanzas
    r_packages = []
    for stanza, package_name in packagelib.iter_stanzas(request.service):
        r_packages.append({
            'name': package_name,
            'is_removable': stanza.access['removable'] == '1',
            'owner': stanza.access['owner'],
            'state': packagelib.get_package_state(package_name),
        })

    return {
        'packages': r_packages,
        'app_label': request.service.apps[app_id].label,
        'request': request,
        'can_add': packagelib.can_add(request.service),
        'add_package_field_name': add_package_field_name,
        'add_package_action': add_package_action,
        'delete_package_action_prefix': delete_package_action_prefix,
        'add_error': request.GET.get('add_error', ''),
        'add_fatal_error': request.GET.get('add_fatal_error', ''),
        'not_installed': packagelib.metadata_package_not_installed,
        'upload_package_action': upload_package_action,
        "upload_package_field_name": upload_package_field_name
    }


@ajax_request
def install_package(request):
    if not request.user.is_authenticated():
        return HttpResponseServerError('User not authenticated')
    if not request.is_ajax():
        return HttpResponseServerError('Is not a AJAX request')
    if request.method != 'POST':
        return HttpResponseServerError('Only POST is supported')

    package_name = request.POST['package-name']

    try:
        packagelib.install_package(request.service, package_name)
    except packagelib.PackageInstallError as e:
        return {
            'state': packagelib.get_package_state(package_name),
            'error': str(e)
        }

    return {
        'state': packagelib.get_package_state(package_name),
    }


@ajax_request
def package_state(request):
    if not request.user.is_authenticated():
        return HttpResponseServerError('User not authenticated')
    if not request.is_ajax():
        return HttpResponseServerError('Is not a AJAX request')
    if request.method != 'GET':
        return HttpResponseServerError('Only GET is supported')

    package_name = request.GET['package-name']

    return {
        'state': packagelib.get_package_state(package_name),
    }


@login_required
@config_required
@render_to(app_id + ':script.html')
def script(request, name):

    if request.method == 'POST':
        try:
            if 'cancel' in request.POST:
                return HttpResponseRedirect('../../scripts/')
            elif 'save' in request.POST:
                content = request.POST['content']
                scriptlib.add(request.service, name, content)
                return HttpResponseRedirect('../../scripts/')
        except Exception as e:
            return HttpResponseRedirect('./?add_error=%s' % str(e))
        return HttpResponseRedirect('./')

    return {
        'app_label': request.service.apps[app_id].label,
        'request': request,
        'name': name,
        'script': scriptlib.get(request.service, name),
        'file_name': name+'.r',
        'add_error': request.GET.get('add_error', ''),
        'add_unknown_error': request.GET.get('add_unknown_error', ''),
    }


@login_required
@config_required
def default(request):
    return HttpResponseRedirect('../../../app/r/overview')