from django.urls import path
from .views import (
    MessageListCreateView, MessageDetailView, BookingRequestListCreateView, 
    BookingRequestDetailView, BookingRequestApprovalView, BookingRequestCheckInView,
    BookingRequestCompleteView, BookingRequestCancelView, BookingRequestStatsView,
    ReviewListCreateView, FavoriteListCreateView, 
    NotificationListView, NotificationDetailView, NotificationMarkAllReadView, 
    NotificationStatsView, MaintenanceRequestListCreateView
)

urlpatterns = [
    path('messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('messages/<int:pk>/', MessageDetailView.as_view(), name='message-detail'),
    path('bookings/', BookingRequestListCreateView.as_view(), name='booking-list-create'),
    path('bookings/<int:pk>/', BookingRequestDetailView.as_view(), name='booking-detail'),
    path('bookings/<int:pk>/approve/', BookingRequestApprovalView.as_view(), name='booking-approve'),
    path('bookings/<int:pk>/checkin/', BookingRequestCheckInView.as_view(), name='booking-checkin'),
    path('bookings/<int:pk>/complete/', BookingRequestCompleteView.as_view(), name='booking-complete'),
    path('bookings/<int:pk>/cancel/', BookingRequestCancelView.as_view(), name='booking-cancel'),
    path('bookings/stats/', BookingRequestStatsView.as_view(), name='booking-stats'),
    path('reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    path('favorites/', FavoriteListCreateView.as_view(), name='favorite-list-create'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('notifications/stats/', NotificationStatsView.as_view(), name='notification-stats'),
    path('maintenance/', MaintenanceRequestListCreateView.as_view(), name='maintenance-list-create'),
]
