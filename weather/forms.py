from django import forms


class WeatherForm(forms.Form):
    city = forms.CharField(label="Город", max_length=120)
    sources = forms.MultipleChoiceField(
        label="Источники",
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        sources = kwargs.pop("sources", [])
        super().__init__(*args, **kwargs)
        self.fields["sources"].choices = sources
