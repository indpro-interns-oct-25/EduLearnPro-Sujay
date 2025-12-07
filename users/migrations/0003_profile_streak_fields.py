from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_user_role_alter_user_phone_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='current_streak',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='last_activity_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='longest_streak',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
