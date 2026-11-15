from django.urls import path
from .views import ActiveCampaignProjectionView

urlpatterns = [
    path('active-campaign/', ActiveCampaignProjectionView.as_view(), name='active-campaign'),
]