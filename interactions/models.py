from django.db import models
from django.conf import settings

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.receiver} - {self.content[:30]}"

from properties.models import Property

class BookingRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('checked_in', 'Checked In'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='booking_requests', 
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'tenant'}
    )
    rental_property = models.ForeignKey(Property, related_name='booking_requests', on_delete=models.CASCADE)
    message = models.TextField(blank=True, null=True, help_text="Message from tenant to landlord")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Booking dates
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Landlord response
    landlord_response = models.TextField(blank=True, null=True, help_text="Response from landlord")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['rental_property', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Booking for {self.rental_property.title} by {self.tenant.username} ({self.status})"
    
    @property
    def can_be_approved(self):
        """Check if booking can be approved"""
        return self.status == 'pending'
    
    @property
    def can_be_checked_in(self):
        """Check if tenant can check in"""
        return self.status == 'approved'
    
    @property
    def can_be_completed(self):
        """Check if booking can be completed"""
        return self.status == 'checked_in'
    
    @property
    def is_active(self):
        """Check if booking is in active state"""
        return self.status in ['approved', 'checked_in']

class MaintenanceRequest(models.Model):
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='maintenance_requests', on_delete=models.CASCADE)
    property = models.ForeignKey(Property, related_name='maintenance_requests', on_delete=models.CASCADE)
    description = models.TextField()
    status_choices = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved')
    ]
    status = models.CharField(max_length=15, choices=status_choices, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Maintenance for {self.property} - {self.status}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('booking', 'Booking'),
        ('message', 'Message'),
        ('maintenance', 'Maintenance'),
        ('property', 'Property'),
        ('review', 'Review'),
        ('general', 'General'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    body = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='general')
    is_read = models.BooleanField(default=False)
    data = models.JSONField(blank=True, null=True)  # Store additional context data
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Review(models.Model):
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'tenant'},
        related_name="tenant_reviews"
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="property_reviews"
    )
    rating = models.PositiveSmallIntegerField()  # 1–5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'property')  # one review per tenant per property

    def __str__(self):
        return f"{self.tenant.username} review on {self.property.title}"


class Favorite(models.Model):
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'tenant'},
        related_name="favorites"
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tenant', 'property')  # avoid duplicate favorites

    def __str__(self):
        return f"{self.tenant.username} favorited {self.property.title}"