from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assistant", "0005_assistantconversation_context_json"),
    ]

    operations = [
        migrations.AddField(
            model_name="assistantauditlog",
            name="semantic_resolution_json",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
