from django import forms


class UploadResultsForm(forms.Form):
    csv_file = forms.FileField()
