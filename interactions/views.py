from rest_framework import generics, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Message, BookingRequest, Review, Favorite, Notification, MaintenanceRequest
from .serializers import (
    MessageSerializer, BookingRequestSerializer, BookingRequestCreateSerializer, 
    BookingRequestUpdateSerializer, ReviewSerializer, FavoriteSerializer, 
    NotificationSerializer, NotificationListSerializer, MaintenanceRequestSerializer
)
from .filters import (
    MessageFilter, BookingRequestFilter, ReviewFilter, FavoriteFilter,
    NotificationFilter, MaintenanceRequestFilter
)
from users.permissions import (
    IsTenant, IsLandlord, IsAdmin, IsMessageParticipant, 
    IsTenantOrLandlordOfProperty, CanAccessUserData
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from utils.sms_utils import send_sms

class BookingRequestCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookingRequestSerializer

    def perform_create(self, serializer):
        booking_request = serializer.save()
        # Send SMS to user
        phone_number = booking_request.user.phone_number
        message = f"Your booking request for {booking_request.property.title} has been received."
        send_sms(phone_number, message)
        return Response(serializer.data)
# ------------------- MESSAGES -------------------
class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = MessageFilter
    search_fields = ['content', 'sender__username', 'receiver__username']
    ordering_fields = ['timestamp', 'is_read']
    ordering = ['-timestamp']

    def get_queryset(self):
        user = self.request.user
        # Users can only see messages they sent or received
        return Message.objects.filter(receiver=user) | Message.objects.filter(sender=user)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class MessageDetailView(generics.RetrieveAPIView):
    serializer_class = MessageSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsMessageParticipant]
    queryset = Message.objects.all()


# ------------------- BOOKINGS -------------------
class BookingRequestListCreateView(generics.ListCreateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = BookingRequestFilter
    search_fields = ['property__title', 'property__location', 'tenant__username', 'message']
    ordering_fields = ['created_at', 'status', 'property__price', 'check_in_date']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return BookingRequestCreateSerializer
        return BookingRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return BookingRequest.objects.select_related('tenant', 'property', 'property__owner').all()
        elif user.role == 'landlord':
            return BookingRequest.objects.select_related('tenant', 'property').filter(property__owner=user)
        elif user.role == 'tenant':
            return BookingRequest.objects.select_related('property', 'property__owner').filter(tenant=user)
        return BookingRequest.objects.none()

    def perform_create(self, serializer):
        # Only tenants can create booking requests
        if self.request.user.role != 'tenant':
            raise permissions.PermissionDenied("Only tenants can create booking requests")
        serializer.save(tenant=self.request.user)

class BookingRequestDetailView(generics.RetrieveAPIView):
    serializer_class = BookingRequestSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsTenantOrLandlordOfProperty]
    
    def get_queryset(self):
        return BookingRequest.objects.select_related('tenant', 'property', 'property__owner').all()

class BookingRequestApprovalView(generics.UpdateAPIView):
    """Dedicated endpoint for landlord approval/decline of booking requests"""
    serializer_class = BookingRequestUpdateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only landlords can access their property bookings
        if self.request.user.role == 'landlord':
            return BookingRequest.objects.filter(property__owner=self.request.user)
        elif self.request.user.role == 'admin':
            return BookingRequest.objects.all()
        return BookingRequest.objects.none()
    
    def perform_update(self, serializer):
        booking = self.get_object()
        
        # Validate that only pending bookings can be approved/declined
        if booking.status != 'pending':
            raise permissions.PermissionDenied(
                f"Cannot modify booking with status '{booking.status}'. Only pending bookings can be approved or declined."
            )
        
        # Only allow approved/declined status changes
        new_status = serializer.validated_data.get('status')
        if new_status not in ['approved', 'declined']:
            raise permissions.PermissionDenied(
                "This endpoint only allows approving or declining booking requests."
            )
        
        serializer.save()

class BookingRequestCheckInView(generics.UpdateAPIView):
    """Endpoint for tenant check-in"""
    serializer_class = BookingRequestUpdateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only tenants can check in to their own bookings
        if self.request.user.role == 'tenant':
            return BookingRequest.objects.filter(tenant=self.request.user)
        elif self.request.user.role == 'admin':
            return BookingRequest.objects.all()
        return BookingRequest.objects.none()
    
    def perform_update(self, serializer):
        booking = self.get_object()
        
        # Validate that only approved bookings can be checked in
        if booking.status != 'approved':
            raise permissions.PermissionDenied(
                f"Cannot check in to booking with status '{booking.status}'. Only approved bookings can be checked in."
            )
        
        # Force status to checked_in
        serializer.save(status='checked_in')

class BookingRequestCompleteView(generics.UpdateAPIView):
    """Endpoint for completing bookings"""
    serializer_class = BookingRequestUpdateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Both tenants and landlords can complete bookings
        if self.request.user.role == 'tenant':
            return BookingRequest.objects.filter(tenant=self.request.user)
        elif self.request.user.role == 'landlord':
            return BookingRequest.objects.filter(property__owner=self.request.user)
        elif self.request.user.role == 'admin':
            return BookingRequest.objects.all()
        return BookingRequest.objects.none()
    
    def perform_update(self, serializer):
        booking = self.get_object()
        
        # Validate that only checked-in bookings can be completed
        if booking.status != 'checked_in':
            raise permissions.PermissionDenied(
                f"Cannot complete booking with status '{booking.status}'. Only checked-in bookings can be completed."
            )
        
        # Force status to completed
        serializer.save(status='completed')

class BookingRequestCancelView(generics.UpdateAPIView):
    """Endpoint for cancelling bookings"""
    serializer_class = BookingRequestUpdateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Both tenants and landlords can cancel bookings
        if self.request.user.role == 'tenant':
            return BookingRequest.objects.filter(tenant=self.request.user)
        elif self.request.user.role == 'landlord':
            return BookingRequest.objects.filter(property__owner=self.request.user)
        elif self.request.user.role == 'admin':
            return BookingRequest.objects.all()
        return BookingRequest.objects.none()
    
    def perform_update(self, serializer):
        booking = self.get_object()
        
        # Validate that only active bookings can be cancelled
        if booking.status in ['completed', 'declined', 'cancelled']:
            raise permissions.PermissionDenied(
                f"Cannot cancel booking with status '{booking.status}'."
            )
        
        # Force status to cancelled
        serializer.save(status='cancelled')

class BookingRequestStatsView(generics.GenericAPIView):
    """Get booking statistics for the current user"""
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if user.role == 'tenant':
            bookings = BookingRequest.objects.filter(tenant=user)
        elif user.role == 'landlord':
            bookings = BookingRequest.objects.filter(property__owner=user)
        elif user.role == 'admin':
            bookings = BookingRequest.objects.all()
        else:
            bookings = BookingRequest.objects.none()
        
        stats = {
            'total': bookings.count(),
            'pending': bookings.filter(status='pending').count(),
            'approved': bookings.filter(status='approved').count(),
            'declined': bookings.filter(status='declined').count(),
            'checked_in': bookings.filter(status='checked_in').count(),
            'completed': bookings.filter(status='completed').count(),
            'cancelled': bookings.filter(status='cancelled').count(),
        }
        
        # Add role-specific stats
        if user.role == 'landlord':
            stats['properties_with_bookings'] = bookings.values('property').distinct().count()
            stats['active_bookings'] = bookings.filter(status__in=['approved', 'checked_in']).count()
        elif user.role == 'tenant':
            stats['properties_booked'] = bookings.values('property').distinct().count()
            stats['active_bookings'] = bookings.filter(status__in=['approved', 'checked_in']).count()
        
        return Response(stats)


# ------------------- REVIEWS -------------------
class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsTenant | IsAdmin]

    def get_queryset(self):
        return Review.objects.all()

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user)


# ------------------- FAVORITES -------------------
class FavoriteListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsTenant | IsAdmin]

    def get_queryset(self):
        return Favorite.objects.filter(tenant=self.request.user)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user)


# ------------------- NOTIFICATIONS -------------------
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = NotificationFilter
    search_fields = ['title', 'body']
    ordering_fields = ['created_at', 'is_read', 'notification_type']
    ordering = ['-created_at']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class NotificationDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, CanAccessUserData]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def perform_update(self, serializer):
        # Users can only update is_read field of their own notifications
        allowed_fields = ['is_read']
        for field in serializer.validated_data:
            if field not in allowed_fields:
                raise permissions.PermissionDenied(f"You can only update: {', '.join(allowed_fields)}")
        serializer.save()

class NotificationMarkAllReadView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Mark all notifications as read for the current user"""
        updated_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'message': f'Marked {updated_count} notifications as read',
            'updated_count': updated_count
        })

class NotificationStatsView(generics.GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get notification statistics for the current user"""
        user_notifications = Notification.objects.filter(user=request.user)
        
        stats = {
            'total': user_notifications.count(),
            'unread': user_notifications.filter(is_read=False).count(),
            'by_type': {}
        }
        
        # Count by notification type
        for notification_type, _ in Notification.NOTIFICATION_TYPES:
            count = user_notifications.filter(notification_type=notification_type).count()
            if count > 0:
                stats['by_type'][notification_type] = count
        
        return Response(stats)


# ------------------- MAINTENANCE REQUESTS -------------------
class MaintenanceRequestListCreateView(generics.ListCreateAPIView):
    serializer_class = MaintenanceRequestSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = MaintenanceRequestFilter
    search_fields = ['description', 'property__title', 'property__location']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return MaintenanceRequest.objects.all()
        elif user.role == 'landlord':
            return MaintenanceRequest.objects.filter(property__owner=user)
        elif user.role == 'tenant':
            return MaintenanceRequest.objects.filter(tenant=user)
        return MaintenanceRequest.objects.none()

    def perform_create(self, serializer):
        # Only tenants can create maintenance requests
        if self.request.user.role != 'tenant':
            raise permissions.PermissionDenied("Only tenants can create maintenance requests")
        serializer.save(tenant=self.request.user)
