from rest_framework import serializers
from .models import Message, BookingRequest, Review, Favorite, Notification, MaintenanceRequest

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['sender', 'timestamp']


class BookingRequestSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.username', read_only=True)
    tenant_email = serializers.CharField(source='tenant.email', read_only=True)
    property_title = serializers.CharField(source='property.title', read_only=True)
    property_location = serializers.CharField(source='property.location', read_only=True)
    property_price = serializers.DecimalField(source='property.price', max_digits=10, decimal_places=2, read_only=True)
    landlord_name = serializers.CharField(source='property.owner.username', read_only=True)
    landlord_email = serializers.CharField(source='property.owner.email', read_only=True)
    
    # Status properties
    can_be_approved = serializers.ReadOnlyField()
    can_be_checked_in = serializers.ReadOnlyField()
    can_be_completed = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    class Meta:
        model = BookingRequest
        fields = [
            'id', 'tenant', 'tenant_name', 'tenant_email', 'property', 'property_title', 
            'property_location', 'property_price', 'landlord_name', 'landlord_email',
            'message', 'status', 'check_in_date', 'check_out_date', 'landlord_response',
            'created_at', 'updated_at', 'approved_at', 'checked_in_at', 'completed_at',
            'can_be_approved', 'can_be_checked_in', 'can_be_completed', 'is_active'
        ]
        read_only_fields = [
            'tenant', 'created_at', 'updated_at', 'approved_at', 
            'checked_in_at', 'completed_at'
        ]

class BookingRequestCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating booking requests"""
    class Meta:
        model = BookingRequest
        fields = ['property', 'message', 'check_in_date', 'check_out_date']
        
    def validate(self, data):
        """Validate booking request data"""
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        
        if check_in and check_out:
            if check_in >= check_out:
                raise serializers.ValidationError("Check-out date must be after check-in date")
                
        # Check if property is available
        property_obj = data.get('property')
        if property_obj and property_obj.status != 'available':
            raise serializers.ValidationError("Property is not available for booking")
            
        return data

class BookingRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for landlord updates to booking requests"""
    class Meta:
        model = BookingRequest
        fields = ['status', 'landlord_response']
        
    def validate_status(self, value):
        """Validate status transitions"""
        instance = self.instance
        if not instance:
            return value
            
        # Define valid status transitions
        valid_transitions = {
            'pending': ['approved', 'declined'],
            'approved': ['checked_in', 'cancelled'],
            'checked_in': ['completed', 'cancelled'],
            'declined': [],
            'completed': [],
            'cancelled': [],
        }
        
        current_status = instance.status
        if value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from '{current_status}' to '{value}'"
            )
            
        return value


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['tenant', 'created_at']


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'
        read_only_fields = ['tenant', 'added_at']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'notification_type', 'is_read', 'data', 'created_at']
        read_only_fields = ['created_at']

class NotificationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for notification lists"""
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'notification_type', 'is_read', 'created_at']


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRequest
        fields = '__all__'
        read_only_fields = ['tenant', 'status', 'created_at']
