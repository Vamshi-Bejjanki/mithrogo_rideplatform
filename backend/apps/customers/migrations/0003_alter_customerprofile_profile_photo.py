from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("customers", "0002_initial")]

    operations = [
        migrations.AlterField(
            model_name="customerprofile",
            name="profile_photo",
            field=models.FileField(blank=True, null=True, upload_to="customers/photos/"),
        ),
    ]
