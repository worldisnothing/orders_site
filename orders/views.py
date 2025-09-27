from django.http import FileResponse, Http404
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from .models import Order
from .forms import OrderForm, UserRegistrationForm


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
        """
        Хешируем пароль и сохраняем пользователя
        """
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        # Автоматический вход после регистрации
        login(self.request, user)
        return redirect(self.success_url)


class OrderCreateView(LoginRequiredMixin, CreateView):
    """
    Создание нового заказа
    """
    model = Order
    form_class = OrderForm
    template_name = 'orders/order_form.html'
    success_url = reverse_lazy('order_list')

    def form_valid(self, form):
        """
        Добавляем текущего пользователя к созданному заказу
        """
        form.instance.user = self.request.user
        return super().form_valid(form)


class OrderListView(LoginRequiredMixin, ListView):
    """
    Общая страница заказов. Отображает список заказов (своих или всех для админа).
    Фильтрация по статусу заказов.
    """
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        """
        Фильтруем по статусу заказа и пользователю (если админ - показываем все, иначе - только свои)
        :return:
        """
        queryset = super().get_queryset()
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Фильтрация по пользователю
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        """
        Добавляем в контекст информацию о статусах
        """
        data = super().get_context_data(**kwargs)
        data['status_filter'] = self.request.GET.get('status', '')
        data['statuses'] = Order.STATUS_CHOICES
        return data


class OrderDetailView(LoginRequiredMixin, DetailView):
    """
    Просмотр деталей заказа. Только админ имеет доступ к деталям всех заказов
    """
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        """
        Если пользователь не админ - показываем только свои заказы
        """
        if self.request.user.is_superuser:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)


def download_document(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not order.document:  # Проверка на наличие файла
        raise Http404("Файл не найден")

    file_path = order.document.path
    filename = order.document.name.split('/')[-1]

    response = FileResponse(
        open(file_path, 'rb'),
        as_attachment=True,
        filename=filename,
        content_type='application/octet-stream'
    )
    return response
