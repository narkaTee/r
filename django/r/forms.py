from splunkdj.setup import forms


class SetupForm(forms.Form):
    email = forms.CharField(
        endpoint='configs/conf-r',
        entity='paths',
        field='r',
        label='Please specify the library installation path:',
    )