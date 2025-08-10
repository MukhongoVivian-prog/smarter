# properties/filters.py
import django_filters
from django.db import models
from .models import Property

class PropertyFilter(django_filters.FilterSet):
    """Comprehensive filter for properties with advanced search capabilities"""
    
    # Basic filters
    title = django_filters.CharFilter(lookup_expr='icontains')
    location = django_filters.CharFilter(lookup_expr='icontains')
    property_type = django_filters.ChoiceFilter(choices=Property.PROPERTY_TYPES)
    status = django_filters.ChoiceFilter(choices=Property.STATUS_CHOICES)
    
    # Price range filters
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    price_exact = django_filters.NumberFilter(field_name='price')
    
    # Owner/Landlord filters
    owner_username = django_filters.CharFilter(field_name='owner__username', lookup_expr='icontains')
    owner_email = django_filters.CharFilter(field_name='owner__email', lookup_expr='icontains')
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='lte')
    
    # Availability filter
    available_only = django_filters.BooleanFilter(method='filter_available_only')
    
    # Advanced filters
    has_image = django_filters.BooleanFilter(method='filter_has_image')
    min_reviews = django_filters.NumberFilter(method='filter_min_reviews')
    min_rating = django_filters.NumberFilter(method='filter_min_rating')
    
    class Meta:
        model = Property
        fields = [
            'title', 'location', 'property_type', 'status', 'price_min', 'price_max',
            'owner_username', 'available_only', 'has_image'
        ]
    
    def filter_available_only(self, queryset, name, value):
        """Filter to show only available properties"""
        if value:
            return queryset.filter(status='available')
        return queryset
    
    def filter_has_image(self, queryset, name, value):
        """Filter properties that have images"""
        if value:
            return queryset.exclude(image__isnull=True).exclude(image='')
        return queryset
    
    def filter_min_reviews(self, queryset, name, value):
        """Filter properties with minimum number of reviews"""
        if value is not None:
            return queryset.annotate(
                review_count=models.Count('property_reviews')
            ).filter(review_count__gte=value)
        return queryset
    
    def filter_min_rating(self, queryset, name, value):
        """Filter properties with minimum average rating"""
        if value is not None:
            return queryset.annotate(
                avg_rating=models.Avg('property_reviews__rating')
            ).filter(avg_rating__gte=value)
        return queryset
