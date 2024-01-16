from django import forms

class ChatMessageForm(forms.Form):
    user = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)