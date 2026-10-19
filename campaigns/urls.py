from django.urls import path
from .views import ActiveCampaignProjectionView

urlpatterns = [
    path('active-projection/', ActiveCampaignProjectionView.as_view(), name='active-projection'),
]