# Deploy

## Pre-requisitos
- Python 3 com dependencias de `requirements.txt`.
- Node/npm para build do CSS.
- PostgreSQL acessivel pelo ambiente.
- Variaveis de ambiente configuradas (ver `docs/configuracao.md`).

## Passos recomendados
1. Instalar dependencias Python:
```bash
pip install -r requirements.txt
```

2. Instalar dependencias frontend:
```bash
npm install
```

3. Build de CSS:
```bash
npm run build:css
```

4. Aplicar migracoes:
```bash
python manage.py migrate
```

5. Validar projeto:
```bash
python manage.py check
```

6. (Opcional) criar superusuario:
```bash
python manage.py createsuperuser
```

7. Coletar static (ambiente de producao):
```bash
python manage.py collectstatic --noinput
```

## Validacoes pos deploy
- Login em `/login`.
- Dashboard em `/dashboard`.
- Rotas de monitoring (`/agents`, `/runs`).
- Widget do assistente fora do admin.
- Admin em `/admin/` sem widget do assistente.

## Observacoes operacionais
- O projeto inclui WSGI/ASGI (`alive_platform/wsgi.py` e `alive_platform/asgi.py`), mas a escolha do servidor de producao nao esta definida no repositorio.
- O comando de sync legado pode ser executado manualmente:
```bash
python manage.py sync_legacy_events
```
