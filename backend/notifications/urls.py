from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "notifications"
urlpatterns = [
    path("twilio/incoming-sms/", views.IncomingTextMessageView.as_view(), name="incoming-sms"),
    path(
        "newsletter/",
        TemplateView.as_view(template_name="notifications/newsletter.html", extra_context={"title": "Newsletter"}),
        name="newsletter",
    ),
]
