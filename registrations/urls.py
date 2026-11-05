from django.urls import path

from . import views

urlpatterns = [
    path(
        "attachments/<int:attachment_id>/download/",
        views.registration_attachment,
        name="registration-attachment",
    ),
    path(
        "attachments/repeat-orders/<int:repeat_order_id>/<str:letter>/download/",
        views.repeat_order_letter,
        name="repeat-order-letter",
    ),
]
