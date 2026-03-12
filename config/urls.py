from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts.views import HomeRedirectView

urlpatterns = [
    path('django-admin/', admin.site.urls),

    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('client/', include('apps.clients.urls', namespace='clients')),
    path('vendor/', include('apps.vendors.urls', namespace='vendors')),
    path('forge/', include('apps.forge_admin.urls', namespace='forge_admin')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),

    path('go/', include('apps.public.urls')),

    # Root redirect — authenticated users go to dashboard
    path('', HomeRedirectView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
