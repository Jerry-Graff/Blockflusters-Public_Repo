from django import forms


class AnswerForm(forms.Form):
    image_id = forms.IntegerField(widget=forms.HiddenInput())
    answer = forms.CharField(max_length=255, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter movie here!',
        'autocomplete': 'off'
    }))
