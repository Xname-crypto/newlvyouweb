from rest_framework import serializers
from .models import DataSource

class DataSourceSerializer(serializers.ModelSerializer):
    # Only expose encrypted password on write, never read
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = DataSource
        fields = ['id', 'name', 'type', 'host', 'port', 'user', 'password', 'database_name', 'file_path', 'created_at', 'updated_at']
        extra_kwargs = {
            'password_encrypted': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = super().create(validated_data)
        if password:
            instance.password = password
            instance.save()
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        instance = super().update(instance, validated_data)
        if password:
            instance.password = password
            instance.save()
        return instance
