from splunkdj.setup import forms
from django.core import validators
import os


class PathExistsValidator(object):
    def __call__(self, value):
        if not os.path.exists(value):
            raise validators.ValidationError(
                'Path does not exists'
            )


class PathField(forms.CharField):
    def __init__(self, *args, **kwargs):
        super(PathField, self).__init__(*args, **kwargs)
        self.validators.append(PathExistsValidator())


class SetupForm(forms.Form):
    r_path = PathField(
        endpoint='configs/conf-r',
        entity='paths',
        field='r',
        label='Please specify the library installation path:',
        #widget=forms.TextInput(attrs={
        #    'style': 'width: 90%;'
        #})
    )