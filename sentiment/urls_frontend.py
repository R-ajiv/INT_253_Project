from django.urls import path
from .views import ui_home

urlpatterns = [
    path('', ui_home, name='sentiment-ui-home'),
]


