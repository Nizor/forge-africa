app_name = 'notifications'
from django.urls import path
from . import views
urlpatterns = [
    path('mark-read/<uuid:pk>/', views.MarkReadView.as_view(), name='mark_read'),
    path('mark-all-read/', views.MarkAllReadView.as_view(), name='mark_all_read'),
]
