# Integrations - Services

O app `integrations` nao possui camada `services` propria no estado atual.

Uso de `Integration` acontece principalmente em:
- `apps.assistant.services.tools_actions`
  - `_get_integration(channel)`
  - dispatch por canal (`email`, `webhook`, `chatseguro` stub)

Diretriz:
- manter `config_json` simples e versionado por ambiente.
