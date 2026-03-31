from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assistant", "0004_assistantauditlog_event_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="assistantconversation",
            name="context_json",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
