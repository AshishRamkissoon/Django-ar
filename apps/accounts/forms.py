from django import forms


class APIKeyForm(forms.Form):
    api_key = forms.CharField(
        label="OpenAI API Key",
        max_length=200,
        widget=forms.PasswordInput(attrs={
            "placeholder": "sk-...",
            "class": "w-full bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500",
        }),
    )

    def clean_api_key(self):
        key = self.cleaned_data["api_key"].strip()
        if not key.startswith("sk-"):
            raise forms.ValidationError("OpenAI API keys must start with 'sk-'.")
        return key
