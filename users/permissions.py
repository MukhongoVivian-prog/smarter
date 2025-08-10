from rest_framework.permissions import BasePermission

class IsLandlord(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'landlord'

class IsTenant(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'tenant'

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user

class IsPropertyOwner(BasePermission):
    """
    Permission to check if user owns the property.
    For use with property-related objects.
    """
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == 'admin':
            return True
            
        # Check if object has property attribute
        if hasattr(obj, 'property'):
            return obj.property.owner == request.user
        
        # Check if object is a property itself
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
            
        return False

class IsTenantOrLandlordOfProperty(BasePermission):
    """
    Permission for interactions that involve both tenants and landlords
    related to a specific property.
    """
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == 'admin':
            return True
            
        # If object has a tenant field, check if user is that tenant
        if hasattr(obj, 'tenant') and obj.tenant == request.user:
            return True
            
        # If object has a property field, check if user owns that property
        if hasattr(obj, 'property') and obj.property.owner == request.user:
            return True
            
        return False

class IsMessageParticipant(BasePermission):
    """
    Permission for message access - only sender and receiver can access.
    """
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == 'admin':
            return True
            
        # Only sender and receiver can access the message
        return obj.sender == request.user or obj.receiver == request.user

class CanAccessUserData(BasePermission):
    """
    Permission for user data access - users can only access their own data.
    """
    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.role == 'admin':
            return True
            
        # Users can only access their own data
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # If the object is a user itself
        return obj == request.user
