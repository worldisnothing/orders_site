from django import forms
from django.contrib.auth.models import User
from .models import Order


class UserRegistrationForm(forms.ModelForm):
    """
    Форма регистрации пользователя.
    """
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password', 'password_confirm']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают.')
        return cleaned_data


class OrderForm(forms.ModelForm):
    """
    Форма создания заказа. Динамическая валидация на основе volume_type.
    """
    class Meta:
        model = Order
        fields = ['name', 'volume_type', 'description', 'document', 'quantity']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'volume_type': forms.Select(attrs={'class': 'form-control', 'onchange': 'toggleFields(this)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # helper: скрыть поле
        def hide(name):
            self.fields[name].widget.attrs['style'] = 'display: none;'
            self.fields[name].label = ''

        # helper: показать поле (удаляем style и восстанавливаем label, если нужно)
        def show(name, label=None):
            self.fields[name].widget.attrs.pop('style', None)
            if label is not None:
                self.fields[name].label = label

        # сначала по-умолчанию скрываем все опциональные поля
        hide('document')
        hide('quantity')
        hide('description')

        # попытка получить текущее значение volume_type:
        vol = None
        # 1) если форма связана с POST/GET — берем из self.data
        if self.data:
            # если форма не в formset, имя поля просто 'volume_type'
            vol = self.data.get('volume_type')
        # 2) если initial задано
        if not vol:
            vol = self.initial.get('volume_type') if hasattr(self, 'initial') else None
        # 3) если есть instance (редактирование)
        if not vol and getattr(self, 'instance', None):
            vol = getattr(self.instance, 'volume_type', None)

        # показываем нужные поля
        if vol == 'single':
            show('description', label='Описание (для единичного)')
        elif vol == 'multiple':
            show('document', label='Документ (для множественного)')
            show('quantity', label='Количество (для множественного)')

    def clean(self):
        cleaned_data = super().clean()
        volume_type = cleaned_data.get('volume_type')
        description = cleaned_data.get('description')
        document = cleaned_data.get('document')
        quantity = cleaned_data.get('quantity')

        # используем add_error, чтобы ошибки были рядом с полем
        if volume_type == 'single':
            if not description:
                self.add_error('description', 'Описание обязательно для единичного заказа.')
            if document or quantity:
                self.add_error(None, 'Для единичного заказа не нужны документ и количество.')
        elif volume_type == 'multiple':
            if not document:
                self.add_error('document', 'Документ обязателен для множественного заказа.')
            if not quantity or quantity < 1:
                self.add_error('quantity', 'Количество обязательно и должно быть > 0.')
            if description:
                self.add_error('description', 'Для множественного заказа описание не нужно.')

        return cleaned_data
