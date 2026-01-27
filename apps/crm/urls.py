from django.urls import path
from .views import lead, showing

app_name = 'crm'

urlpatterns = [
    # Leads
    path('leads/', lead.LeadListView.as_view(), name='lead_list'),
    path('leads/add/', lead.LeadCreateView.as_view(), name='lead_add'),
    path('leads/<uuid:pk>/edit/', lead.LeadUpdateView.as_view(), name='lead_edit'),
    
    # Showings
    path('showings/', showing.ShowingListView.as_view(), name='showing_list'),
    path('showings/add/', showing.ShowingCreateView.as_view(), name='showing_add'),
]
