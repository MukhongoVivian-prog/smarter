from rest_framework import serializers
from .models import Property

class PropertyListSerializer(serializers.ModelSerializer):
    landlord_name = serializers.CharField(source="landlord.username", read_only=True)

    class Meta:
        model = Property
        fields = [
            "id", "title", "price", "location", "property_type",
            "image", "landlord_name"
        ]


class PropertyDetailSerializer(serializers.ModelSerializer):
    landlord_name = serializers.CharField(source="landlord.username", read_only=True)
    landlord_email = serializers.EmailField(source="landlord.email", read_only=True)
    reviews = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id", "title", "description", "price", "location", "property_type",
            "bedrooms", "bathrooms", "amenities", "availability", "image",
            "landlord_name", "landlord_email", "reviews", "favorites_count"
        ]

    def get_reviews(self, obj):
        return [
            {
                "tenant": review.tenant.username,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at
            }
            for review in obj.reviews.all()
        ]

    def get_favorites_count(self, obj):
        return obj.favorites.count()


class PropertyCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = [
            "title", "description", "price", "location", "property_type",
            "bedrooms", "bathrooms", "amenities", "availability", "image"
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["landlord"] = request.user
        return super().create(validated_data)
