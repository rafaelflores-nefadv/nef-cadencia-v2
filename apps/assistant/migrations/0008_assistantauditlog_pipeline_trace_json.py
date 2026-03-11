from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assistant", "0007_assistantmessage_payload_json"),
    ]

    operations = [
        migrations.AddField(
            model_name="assistantauditlog",
            name="pipeline_trace_json",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
