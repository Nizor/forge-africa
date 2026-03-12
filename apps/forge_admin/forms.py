from django import forms
from apps.rfqs.models import RFQ, ServiceCategory
from django.utils.text import slugify


class RFQApproveForm(forms.ModelForm):
    class Meta:
        model = RFQ
        fields = ['admin_notes', 'bidding_deadline']
        widgets = {
            'bidding_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'admin_notes': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'admin_notes': 'Internal Notes (optional)',
            'bidding_deadline': 'Bidding Deadline (optional)',
        }


class RFQRejectForm(forms.Form):
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Rejection Reason',
        help_text='This will be sent to the client in the rejection email.'
    )


class SelectBidForm(forms.Form):
    forge_margin_percentage = forms.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100,
        initial=0, required=False, label='Forge Africa Margin (%)',
    )
    final_price = forms.DecimalField(
        max_digits=12, decimal_places=2,
        label='Final Price to Show Client (₦)',
    )
    deposit_percentage = forms.IntegerField(
        min_value=0, max_value=100, initial=30,
        label='Deposit Required (%)',
    )
    admin_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label='Message to Client',
        required=False
    )


class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description', 'icon', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            obj.slug = slugify(obj.name)
        if commit:
            obj.save()
        return obj
