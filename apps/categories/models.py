from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL-идентификатор')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name='Изображение категории')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_all_parameters(self):
        """Возвращает словарь всех параметров этой категории с учётом наследования от предков."""
        params_dict = {}
        if self.parent:
            params_dict.update(self.parent.get_all_parameters())
        for p in self.parameters.all():
            params_dict[p.slug] = p
        return params_dict

    def get_descendants_ids(self, include_self=True):
        """
        Возвращает список id всех потомков (рекурсивно).
        Если include_self=True, включает и свой id.
        """
        ids = []
        if include_self:
            ids.append(self.id)
        for child in self.children.all():
            ids.extend(child.get_descendants_ids(include_self=True))
        return ids

class CategoryParameter(models.Model):
    PARAMETER_TYPES = (
        ('choice', 'Выбор из списка'),
        ('boolean', 'Да/Нет'),
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(max_length=100, verbose_name='URL-ключ')
    param_type = models.CharField(max_length=10, choices=PARAMETER_TYPES, default='choice', verbose_name='Тип')
    choices = models.TextField(blank=True, help_text='Варианты через запятую или с новой строки', verbose_name='Варианты')

    class Meta:
        unique_together = ('category', 'slug')
        verbose_name = 'Параметр категории'
        verbose_name_plural = 'Параметры категорий'

    def __str__(self):
        return f"{self.category.name} → {self.name}"

    def get_choices_list(self):
        if self.param_type == 'choice' and self.choices.strip():
            raw = self.choices.replace('\r\n', '\n').replace('\r', '\n')
            parts = []
            for line in raw.split('\n'):
                for part in line.split(','):
                    part = part.strip()
                    if part:
                        parts.append(part)
            return parts
        return []

    def get_descendants_ids(self, include_self=True):
        """
        Возвращает список id всех потомков (рекурсивно).
        Если include_self=True, включает и свой id.
        """
        ids = []
        if include_self:
            ids.append(self.id)
        for child in self.children.all():
            ids.extend(child.get_descendants_ids(include_self=True))
        return ids