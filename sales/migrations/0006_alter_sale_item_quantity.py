from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'), # Cambia esto por el nombre de tu última migración en sales/migrations/
    ]

    operations = [
        migrations.AlterField(
            model_name='saleitem',
            name='quantity',
            field=models.IntegerField(default=1),
        ),
    ]