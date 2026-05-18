from django.db import migrations, models

import listings.models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0013_listing_is_urgent'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='contact_phone',
            field=models.CharField(
                blank=True,
                default='',
                max_length=20,
                verbose_name='Контактный телефон объявления',
            ),
        ),
        migrations.AddField(
            model_name='listing',
            name='external_id',
            field=models.CharField(
                default=listings.models.default_external_id,
                max_length=50,
                unique=True,
                verbose_name='Внешний ID',
            ),
        ),
    ]
