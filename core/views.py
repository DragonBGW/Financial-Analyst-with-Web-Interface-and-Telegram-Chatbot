from django.shortcuts import render

# Create your views here.
# core/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer

# core/views.py  (add below RegisterView)
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.response import Response
from .serializers import PredictionSerializer
from .utils import run_prediction
from .models import Prediction


class RegisterView(APIView):
    permission_classes = []  # Allow anyone to register

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




class PredictView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ticker = request.data.get("ticker")
        if not ticker:
            return Response({"detail": "ticker is required"}, status=400)
        try:
            pred = run_prediction(request.user, ticker)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)
        return Response(PredictionSerializer(pred).data, status=201)

class PredictionListView(generics.ListAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Prediction.objects.filter(user=self.request.user)
        ticker = self.request.query_params.get("ticker")
        date   = self.request.query_params.get("date")
        if ticker:
            qs = qs.filter(ticker__iexact=ticker)
        if date:
            qs = qs.filter(created__date=date)
        return qs

