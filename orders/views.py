from django.http import FileResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login
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
    paginate_by = 10  # Опционально: пагинация на 10 заказов на страницу

    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Фильтрация по пользователю
        if not self.request.user.is_superuser:  # Или self.request.user.is_staff, если админы — это staff
            queryset = queryset.filter(user=self.request.user)  # Только свои заказы
        return queryset

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['status_filter'] = self.request.GET.get('status', '')
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


def download_document(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not order.document:  # Проверка на наличие файла
        # Можно вернуть 404 или редирект
        from django.http import Http404
        raise Http404("Файл не найден")

    # Для FileField не нужно .open(), если это не ImageField
    file_path = order.document.path  # Полный путь к файлу на сервере
    filename = order.document.name.split('/')[-1]  # Имя файла для скачивания

    response = FileResponse(
        open(file_path, 'rb'),  # Открываем в бинарном режиме
        as_attachment=True,  # Ключевой параметр: attachment вместо inline
        filename=filename,  # Имя файла в диалоге сохранения
        content_type='application/octet-stream'  # Универсальный тип для force-download (или оставьте автоопределение)
    )
    return response