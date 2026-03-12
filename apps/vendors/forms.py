from django import forms
from apps.vendors.models import VendorProfile
from apps.bids.models import Bid
from apps.clients.forms import MultipleFileField


class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = VendorProfile
        fields = [
            'company_name', 'phone', 'address', 'city', 'state',
            'description', 'logo', 'service_categories', 'years_in_business'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'service_categories': forms.CheckboxSelectMultiple(),
        }


class BidForm(forms.ModelForm):
    attachments = MultipleFileField(
        required=False,
        help_text='Upload any supporting documents or samples (optional)'
    )

    class Meta:
        model = Bid
        fields = ['price', 'timeline_days', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'price': 'Your Quote Price (₦)',
            'timeline_days': 'Estimated Delivery (working days)',
        }