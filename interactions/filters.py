# interactions/filters.py
import django_filters
from django.db import models
from .models import Message, BookingRequest, Review, Favorite, Notification, MaintenanceRequest

class MessageFilter(django_filters.FilterSet):
    """Filter for messages with search and date range capabilities"""
    content = django_filters.CharFilter(lookup_expr='icontains')
    sender_username = django_filters.CharFilter(field_name='sender__username', lookup_expr='icontains')
    receiver_username = django_filters.CharFilter(field_name='receiver__username', lookup_expr='icontains')
    date_from = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    is_read = django_filters.BooleanFilter()
    
    class Meta:
        model = Message
        fields = ['content', 'sender_username', 'receiver_username', 'is_read']

class BookingRequestFilter(django_filters.FilterSet):
    """Filter for booking requests with comprehensive search options"""
    status = django_filters.ChoiceFilter(choices=BookingRequest.STATUS_CHOICES)
    property_title = django_filters.CharFilter(field_name='property__title', lookup_expr='icontains')
    property_location = django_filters.CharFilter(field_name='property__location', lookup_expr='icontains')
    property_type = django_filters.CharFilter(field_name='property__property_type')
    tenant_username = django_filters.CharFilter(field_name='tenant__username', lookup_expr='icontains')
    landlord_username = django_filters.CharFilter(field_name='property__owner__username', lookup_expr='icontains')
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    price_min = django_filters.NumberFilter(field_name='property__price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='property__price', lookup_expr='lte')
    
    class Meta:
        model = BookingRequest
        fields = ['status', 'property_title', 'property_location', 'property_type']

class ReviewFilter(django_filters.FilterSet):
    """Filter for property reviews"""
    rating = django_filters.NumberFilter()
    rating_min = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    rating_max = django_filters.NumberFilter(field_name='rating', lookup_expr='lte')
    property_title = django_filters.CharFilter(field_name='property__title', lookup_expr='icontains')
    property_location = django_filters.CharFilter(field_name='property__location', lookup_expr='icontains')
    tenant_username = django_filters.CharFilter(field_name='tenant__username', lookup_expr='icontains')
    comment = django_filters.CharFilter(lookup_expr='icontains')
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Review
        fields = ['rating', 'property_title', 'comment']

class FavoriteFilter(django_filters.FilterSet):
    """Filter for user favorites"""
    property_title = django_filters.CharFilter(field_name='property__title', lookup_expr='icontains')
    property_location = django_filters.CharFilter(field_name='property__location', lookup_expr='icontains')
    property_type = django_filters.CharFilter(field_name='property__property_type')
    price_min = django_filters.NumberFilter(field_name='property__price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='property__price', lookup_expr='lte')
    date_added_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_added_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Favorite
        fields = ['property_title', 'property_location', 'property_type']

class NotificationFilter(django_filters.FilterSet):
    """Filter for user notifications"""
    notification_type = django_filters.ChoiceFilter(choices=Notification.NOTIFICATION_TYPES)
    is_read = django_filters.BooleanFilter()
    title = django_filters.CharFilter(lookup_expr='icontains')
    body = django_filters.CharFilter(lookup_expr='icontains')
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Notification
        fields = ['notification_type', 'is_read', 'title']

class MaintenanceRequestFilter(django_filters.FilterSet):
    """Filter for maintenance requests"""
    status = django_filters.ChoiceFilter(choices=MaintenanceRequest.status_choices)
    property_title = django_filters.CharFilter(field_name='property__title', lookup_expr='icontains')
    property_location = django_filters.CharFilter(field_name='property__location', lookup_expr='icontains')
    tenant_username = django_filters.CharFilter(field_name='tenant__username', lookup_expr='icontains')
    landlord_username = django_filters.CharFilter(field_name='property__owner__username', lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    date_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = MaintenanceRequest
        fields = ['status', 'property_title', 'description']
