# Rules - Fluxos

## Leitura de configuracao tipada
```text
Modulo consumidor (assistant/monitoring)
     |
     v
rules.services.system_config.get_*
     |
     v
SystemConfig (PostgreSQL)
     |
     v
valor tipado + fallback
```

## Atualizacao operacional
```text
Admin Django
     |
     v
edicao SystemConfig
     |
     v
efeito em runtime nos modulos consumidores
```
