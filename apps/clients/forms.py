from django import forms
from apps.rfqs.models import RFQ, ServiceCategory


class MultipleFileInput(forms.FileInput):
    """
    FileInput that supports multiple file selection.
    allow_multiple_selected = True lifts Django 4.2+'s guard.
    We inject the 'multiple' HTML attr via build_attrs, not __init__.
    """
    allow_multiple_selected = True

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs['multiple'] = True
        return attrs

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)


class MultipleFileField(forms.FileField):
    def clean_deadline(self):
        from datetime import date
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline <= date.today():
            raise forms.ValidationError('Deadline must be a future date.')
        return deadline

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            return []
        parent = super()
        return [parent.clean(f, initial) for f in data]


class RFQForm(forms.ModelForm):
    attachments = MultipleFileField(
        required=False,
        help_text='Upload drawings, references, specs (PDF, DXF, DWG, JPG, PNG). Max 10MB each.'
    )

    class Meta:
        model = RFQ
        fields = [
            'title', 'category', 'description',
            'quantity', 'materials', 'deadline',
            'budget_min', 'budget_max', 'additional_notes',
        ]
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'additional_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_deadline(self):
        from datetime import date
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline <= date.today():
            raise forms.ValidationError('Deadline must be a future date.')
        return deadline

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ServiceCategory.objects.filter(is_active=True)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.FileInput)):
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent'
                })
