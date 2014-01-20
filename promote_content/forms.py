from django import forms

from .widgets import CurateWidget


class CuratedBaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CuratedBaseForm, self).__init__(*args, **kwargs)
        self.fields['curation'].widget.form_instance = self

    curation = forms.IntegerField(widget=CurateWidget(), required=False)
