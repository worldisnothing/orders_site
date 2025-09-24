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
        self.fields['volume_type'].widget.attrs['onchange'] = 'toggleFields(this)'
        # Изначально скрыть поля для множественного
        self.fields['document'].widget.attrs['style'] = 'display: none;'
        self.fields['document'].widget.attrs['disabled'] = True
        self.fields['quantity'].widget.attrs['style'] = 'display: none;'
        self.fields['description'].widget.attrs['style'] = 'display: block;'

    def clean(self):
        cleaned_data = super().clean()
        volume_type = cleaned_data.get('volume_type')
        description = cleaned_data.get('description')
        document = cleaned_data.get('document')
        quantity = cleaned_data.get('quantity')

        if volume_type == 'single':
            if not description:
                raise forms.ValidationError('Описание обязательно для единичного заказа.')
            if document or quantity:
                raise forms.ValidationError('Для единичного заказа не нужны документ и количество.')
        elif volume_type == 'multiple':
            if not document:
                raise forms.ValidationError('Документ обязателен для множественного заказа.')
            if not quantity or quantity < 1:
                raise forms.ValidationError('Количество обязательно и должно быть > 0.')
            if description:
                raise forms.ValidationError('Для множественного заказа описание не нужно.')
        return cleaned_data