from django.contrib import messages
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from jinja2 import Environment


def url(viewname, *args, **kwargs):
    """
    Jinja2-friendly wrapper around Django's reverse().
    Allows: url('app:view', pk=1) instead of reverse('app:view', kwargs={'pk': 1})
    """
    if kwargs:
        return reverse(viewname, args=args or None, kwargs=kwargs)
    if args:
        return reverse(viewname, args=args)
    return reverse(viewname)


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': url,
        'now': timezone.now,
        'get_messages': messages.get_messages,
        'get_unread_notifications': _get_unread_notifications,
    })
    return env


def _get_unread_notifications(user):
    if not user or not user.is_authenticated:
        return []
    from apps.notifications.models import Notification
    return Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:10]
