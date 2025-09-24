from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Order
from .forms import OrderForm, UserRegistrationForm
from .serializers import OrderSerializer


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')


class RegisterView(CreateView):
    """
    Регистрация пользователя и автоматический вход.
    """
    form_class = UserRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('order_list')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        # Автоматический вход после регистрации
        login(self.request, user)
        return redirect(self.success_url)


class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'
    success_url = reverse_lazy('order_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        status_filter = self.request.GET.get('status')
        if status_filter:
            data['orders'] = data['orders'].filter(status=status_filter)
        data['status_filter'] = status_filter
        data['statuses'] = Order.STATUS_CHOICES
        return data


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)


@api_view(['GET'])
def api_order_list(request):
    queryset = Order.objects.filter(user=request.user) if not request.user.is_superuser else Order.objects.all()
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status=status)
    serializer = OrderSerializer(queryset, many=True)
    return Response(serializer.data)