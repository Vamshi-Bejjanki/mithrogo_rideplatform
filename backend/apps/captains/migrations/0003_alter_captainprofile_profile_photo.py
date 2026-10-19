from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("captains", "0002_initial")]

    operations = [
        migrations.AlterField(
            model_name="captainprofile",
            name="profile_photo",
            field=models.FileField(blank=True, null=True, upload_to="captains/photos/"),
        ),
    ]
