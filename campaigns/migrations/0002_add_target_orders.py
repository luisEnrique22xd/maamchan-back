from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('campaigns', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='targetbyteam',
            name='target_orders',
            field=models.IntegerField(default=0),
        ),
    ]