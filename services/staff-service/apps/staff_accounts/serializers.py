from rest_framework import serializers

from apps.staff_accounts.models import StaffUser


class StaffRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = StaffUser
        fields = ["id", "email", "full_name", "password", "role"]
        read_only_fields = ["id", "role"]

    def validate_email(self, value):
        if StaffUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = StaffUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class StaffLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class StaffProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffUser
        fields = ["id", "email", "full_name", "role", "is_active", "created_at", "updated_at"]
