from django import forms


class SuggestionForm(forms.Form):
    article_slug = forms.CharField(widget=forms.HiddenInput(), required=False)
    suggestion = forms.CharField(
        label="Ваше предложение",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Опишите вашу идею или правку…"
        }),
        max_length=2000
    )
    submitter_name = forms.CharField(label="Ваше имя", max_length=100, required=False)
    submitter_email = forms.EmailField(label="Ваш email", required=False)
