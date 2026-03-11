# Deployment e Instalacao

## 1) Instalacao local (desenvolvimento)

### Pre-requisitos
- Python 3.11+
- Node.js 18+
- PostgreSQL
- (Opcional) SQL Server ODBC para comandos LH

### Passos
```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
npm install
python manage.py migrate
npm run build:css
python manage.py runserver
```

## 2) Instalacao em VPS Linux (Ubuntu/Debian)

### Pacotes base
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential libpq-dev nginx
```

### Dependencias ODBC (quando usar legado)
```bash
sudo apt install -y unixodbc unixodbc-dev
# Instalar Microsoft ODBC Driver 18 conforme repositorio oficial da Microsoft
```

### Aplicacao
```bash
git clone <repo>
cd nef-cadencia-v2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
npm run build:css
python manage.py migrate
python manage.py collectstatic --noinput
```

## 3) Variaveis de ambiente essenciais

### Core
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`

### PostgreSQL
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

### OpenAI
- `OPENAI_API_KEY`

### SQL Server legado (quando aplicavel)
- `LEGACY_DRIVER`
- `LEGACY_SERVER`
- `LEGACY_PORT`
- `LEGACY_USER`
- `LEGACY_PASSWORD`
- `LEGACY_DATABASE`
- `LEGACY_SCHEMA`
- `LEGACY_EVENTS_TABLE` (sync incremental)

## 4) Execucao em producao (referencia)
- Aplicacao Django via WSGI (`alive_platform/wsgi.py`).
- Reverse proxy via Nginx.
- Processo Python (exemplo: gunicorn) supervisionado por systemd.

## 5) Checklist pos deploy
```bash
python manage.py check
python manage.py test
```
Verificar:
- `/login`
- `/dashboard`
- `/runs`
- `/assistant/chat`
- `/admin/`

## 6) Operacao
- Rodar imports/sync por agendamento (cron/systemd timer) conforme estrategia do time.
- Monitorar `JobRun` para falhas e tempos de execucao.
