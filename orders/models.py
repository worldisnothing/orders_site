from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os
from django.utils import timezone


def user_document_path(instance, filename):
    base, ext = os.path.splitext(filename)
    ts = int(timezone.now().timestamp() * 1000)
    return os.path.join("documents", str(instance.user.id), f"{base}_{ts}{ext}")


class Order(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создан'),
        ('processing', 'Обрабатывается'),
        ('assembling', 'Собирается'),
        ('delivering', 'Доставляется'),
        ('ready', 'Готов'),
    ]

    VOLUME_TYPE_CHOICES = [
        ('single', 'Единичный'),
        ('multiple', 'Множественный'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.AutoField(primary_key=True)
    created_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    name = models.CharField(max_length=255, verbose_name='Наименование')
    volume_type = models.CharField(max_length=20, choices=VOLUME_TYPE_CHOICES, verbose_name='Тип объёма')
    description = models.TextField(blank=True, null=True, verbose_name='Описание (для единичного)')
    document = models.FileField(upload_to=user_document_path, blank=True, null=True,
                                verbose_name='Документ (для множественного)')
    quantity = models.PositiveIntegerField(blank=True, null=True, verbose_name='Количество (для множественного)')
    ready_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата готовности')

    class Meta:
        ordering = ['-created_date']
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def save(self, *args, **kwargs):
        """
        Автоматическая установка даты при смене статуса на 'ready'.
        """
        if self.status == 'ready' and not self.ready_date:
            self.ready_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Заказ #{self.order_number} - {self.name}'
