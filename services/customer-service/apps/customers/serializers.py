from rest_framework import serializers

from apps.customers.models import Customer


class CustomerRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Customer
        fields = ["id", "email", "full_name", "password"]
        read_only_fields = ["id"]

    def validate_email(self, value):
        if Customer.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        customer = Customer(**validated_data)
        customer.set_password(password)
        customer.save()
        return customer


class CustomerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "email", "full_name", "is_active", "created_at", "updated_at"]
