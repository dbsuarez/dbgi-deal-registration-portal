from django.urls import path

from . import views

urlpatterns = [
    path(
        "attachments/<int:attachment_id>/download/",
        views.registration_attachment,
        name="registration-attachment",
    ),
]
