from django.forms.widgets import Input

class MultipleFileInput(Input):
    input_type = 'file'
    needs_multipart_form = True

    def __init__(self, attrs=None):
        default_attrs = {'multiple': True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['multiple'] = True
        return context

    def value_from_datadict(self, data, files, name):
        # Возвращаем список файлов
        return files.getlist(name)