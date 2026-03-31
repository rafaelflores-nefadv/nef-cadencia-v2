# Instalacao no Linux

Este guia cobre instalacao local em Linux (foco em Ubuntu/Debian) para desenvolvimento.

## 1) Pre-requisitos

- Git
- Python 3.11+ e `venv`
- Node.js 18+ e npm
- PostgreSQL (local ou remoto)
- Pacotes de build para libs Python

No Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y git curl build-essential python3 python3-venv python3-pip libpq-dev
```

Para Node.js (se ainda nao tiver):

```bash
sudo apt install -y nodejs npm
```

## 2) Clonar e entrar no projeto

```bash
git clone https://github.com/rafaelflores-nefadv/nef-cadencia-v2.git
cd nef-cadencia-v2
```

## 3) Ambiente Python

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4) Dependencias frontend

```bash
npm install
```

## 5) Configurar variaveis de ambiente

Crie o arquivo `.env` na raiz do projeto:

```dotenv
SECRET_KEY=troque-esta-chave
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=nef_cadencia
DB_USER=postgres
DB_PASSWORD=troque-a-senha
DB_HOST=127.0.0.1
DB_PORT=5432

# OpenAI (obrigatorio para o assistente)
OPENAI_API_KEY=sk-...

# Legacy sync (opcional)
LEGACY_DRIVER=ODBC Driver 18 for SQL Server
LEGACY_SERVER=seu-servidor
LEGACY_PORT=1433
LEGACY_USER=seu-usuario
LEGACY_PASSWORD=sua-senha
LEGACY_DATABASE=seu-banco
LEGACY_SCHEMA=dbo
```

Referencias:
- `docs/configuracao.md`
- `docs/SYNC.md`

## 6) Preparar banco e assets

```bash
python manage.py migrate
npm run build:css
python manage.py createsuperuser
```

## 7) Rodar localmente

```bash
python manage.py runserver
```

Acesse:

- `http://127.0.0.1:8000/login`
- `http://127.0.0.1:8000/admin`

## 8) Comandos uteis

```bash
python manage.py check
python manage.py test
npm run watch:css
```

## 9) Opcional: suporte a SQL Server legado (pyodbc)

Use este bloco apenas se for executar import/sync legado.

1. Instale ODBC no Linux:

```bash
sudo apt install -y unixodbc unixodbc-dev
```

2. Instale `pyodbc` no venv:

```bash
pip install pyodbc
```

3. Garanta que o driver configurado em `LEGACY_DRIVER` exista no host.

Sem `pyodbc`, os comandos de sync legado falham por design.
