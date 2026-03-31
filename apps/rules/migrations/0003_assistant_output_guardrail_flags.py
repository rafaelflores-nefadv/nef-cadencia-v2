from django.db import migrations


def seed_assistant_output_guardrail_flags(apps, schema_editor):
    SystemConfig = apps.get_model("rules", "SystemConfig")

    default_configs = (
        (
            "ASSISTANT_OUTPUT_SCOPE_GUARDRAIL_ENABLED",
            "true",
            "Habilita ou desabilita o filtro de escopo da resposta do assistente IA.",
        ),
        (
            "ASSISTANT_OUTPUT_TRUTHFULNESS_GUARDRAIL_ENABLED",
            "true",
            "Habilita ou desabilita a validacao de veracidade da resposta do assistente IA.",
        ),
    )

    for config_key, config_value, description in default_configs:
        SystemConfig.objects.update_or_create(
            config_key=config_key,
            defaults={
                "config_value": config_value,
                "value_type": "bool",
                "description": description,
            },
        )


def unseed_assistant_output_guardrail_flags(apps, schema_editor):
    SystemConfig = apps.get_model("rules", "SystemConfig")
    SystemConfig.objects.filter(
        config_key__in=(
            "ASSISTANT_OUTPUT_SCOPE_GUARDRAIL_ENABLED",
            "ASSISTANT_OUTPUT_TRUTHFULNESS_GUARDRAIL_ENABLED",
        )
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("rules", "0002_assistant_guardrail_flags"),
    ]

    operations = [
        migrations.RunPython(
            seed_assistant_output_guardrail_flags,
            reverse_code=unseed_assistant_output_guardrail_flags,
        ),
    ]
