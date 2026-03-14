from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


class ClientRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError('Passwords do not match.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = User.CLIENT
        if commit:
            user.save()
        return user


class VendorRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    # Company fields
    company_name = forms.CharField(max_length=255)
    phone = forms.CharField(max_length=20)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}))
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError('Passwords do not match.')
        return cleaned

    def save(self, commit=True):
        from apps.vendors.models import VendorProfile
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = User.VENDOR
        if commit:
            user.save()
            VendorProfile.objects.create(
                user=user,
                company_name=self.cleaned_data['company_name'],
                phone=self.cleaned_data['phone'],
                address=self.cleaned_data['address'],
                city=self.cleaned_data['city'],
                state=self.cleaned_data['state'],
                is_verified=False,
            )
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={'autofocus': True})
    )
