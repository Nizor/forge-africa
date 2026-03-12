from django.db import models
from django.conf import settings
from apps.rfqs.models import ServiceCategory


class VendorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vendor_profile'
    )
    company_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='vendor_logos/', null=True, blank=True)
    service_categories = models.ManyToManyField(ServiceCategory, related_name='vendors', blank=True)
    is_verified = models.BooleanField(default=False)
    years_in_business = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vendor Profile'

    def __str__(self):
        return self.company_name
