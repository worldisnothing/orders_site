from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.OrderListView.as_view(), name='order_list'),
    path('orders/new/', views.OrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('download/<int:order_number>/', views.download_document, name='download_document'),
]