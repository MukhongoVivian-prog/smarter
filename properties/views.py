# properties/views.py
from rest_framework import generics, permissions, filters
from rest_framework.pagination import PageNumberPagination
from .models import Property
from .serializers import PropertyListSerializer, PropertyDetailSerializer
from .filters import PropertyFilter
from users.permissions import IsLandlord, IsAdmin, IsOwnerOrReadOnly

# Custom pagination
class PropertyPagination(PageNumberPagination):
    page_size = 10  # default items per page
    page_size_query_param = 'page_size'
    max_page_size = 100

class PropertyListView(generics.ListAPIView):
    serializer_class = PropertyListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PropertyPagination
    filterset_class = PropertyFilter
    
    # Add search and ordering
    search_fields = ['title', 'location', 'description']
    ordering_fields = ['price', 'created_at', 'updated_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        # Return only available properties for public listing
        return Property.objects.filter(status='available')

class PropertyDetailView(generics.RetrieveAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertyDetailSerializer
    permission_classes = [permissions.AllowAny]

class PropertyCreateView(generics.CreateAPIView):
    serializer_class = PropertyDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(landlord=self.request.user)

class PropertyUpdateView(generics.UpdateAPIView):
    serializer_class = PropertyDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Property.objects.filter(landlord=self.request.user)

class PropertyDeleteView(generics.DestroyAPIView):
    serializer_class = PropertyDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Property.objects.filter(landlord=self.request.user)
