from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import User
from properties.models import Property
from interactions.models import Favorite, Review

# 🔹 Tenant Dashboard
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tenant_dashboard(request):
    if request.user.role != 'Tenant':
        return Response({'error': 'Access denied'}, status=403)

    favorites_count = Favorite.objects.filter(user=request.user).count()
    reviews_count = Review.objects.filter(user=request.user).count()
    available_properties = Property.objects.filter(is_available=True).count()

    return Response({
        "dashboard": "Tenant Dashboard",
        "favorites_count": favorites_count,
        "reviews_count": reviews_count,
        "available_properties": available_properties
    })

# 🔹 Landlord Dashboard
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def landlord_dashboard(request):
    if request.user.role != 'Landlord':
        return Response({'error': 'Access denied'}, status=403)

    my_properties = Property.objects.filter(owner=request.user)
    total_properties = my_properties.count()
    available_count = my_properties.filter(is_available=True).count()
    unavailable_count = total_properties - available_count

    return Response({
        "dashboard": "Landlord Dashboard",
        "total_properties": total_properties,
        "available_count": available_count,
        "unavailable_count": unavailable_count
    })

# 🔹 Admin Dashboard
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    if request.user.role != 'Admin':
        return Response({'error': 'Access denied'}, status=403)

    total_users = User.objects.count()
    total_properties = Property.objects.count()
    total_reviews = Review.objects.count()

    return Response({
        "dashboard": "Admin Dashboard",
        "total_users": total_users,
        "total_properties": total_properties,
        "total_reviews": total_reviews
    })
