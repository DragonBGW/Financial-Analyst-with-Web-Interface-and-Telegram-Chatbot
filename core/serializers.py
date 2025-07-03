# core/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        return user


# core/serializers.py  (add below RegisterSerializer)
from .models import Prediction

class PredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Prediction
        fields = [
            "id", "ticker", "created", "next_price",
            "mse", "rmse", "r2", "plot_closing", "plot_cmp"
        ]
