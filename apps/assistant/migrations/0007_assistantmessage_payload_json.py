from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assistant", "0006_assistantauditlog_semantic_resolution_json"),
    ]

    operations = [
        migrations.AddField(
            model_name="assistantmessage",
            name="payload_json",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
