from splunkdj.setup import forms


class SetupForm(forms.Form):
    email = forms.CharField(
        endpoint='configs/conf-r',
        entity='paths',
        field='r',
        label='Library Path',
        help_text=r'Local path to the R library executable '
                  r'(for example C:\Program Files\R\R-3.0.3\bin\R.exe or '
                  r'/Library/Frameworks/R.framework/Versions/Current/Resources/bin/R). '
                  '\nYou can download R from http://www.r-project.org/'
    )