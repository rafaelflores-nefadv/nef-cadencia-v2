# 🚀 Início Rápido

Guias para começar a usar o NEF Cadencia v2.

## 📚 Documentos Disponíveis

### [INSTALL_LINUX.md](./INSTALL_LINUX.md)
Guia completo de instalação no Linux (Ubuntu/Debian)
- Pré-requisitos
- Instalação do Python, Node.js, PostgreSQL
- Configuração do ambiente virtual
- Instalação de dependências

### [CONFIGURACAO.md](./CONFIGURACAO.md)
Configuração inicial do sistema
- Variáveis de ambiente
- Configuração do banco de dados
- Chaves de API
- Configurações do Django

### [SETUP_DATABASE.md](./SETUP_DATABASE.md)
Setup e configuração do banco de dados
- Criação do banco PostgreSQL
- Migrations
- Seed de dados iniciais
- Comandos úteis

### [VARIAVEIS_AMBIENTE.md](./VARIAVEIS_AMBIENTE.md)
Referência completa de variáveis de ambiente
- Variáveis obrigatórias
- Variáveis opcionais
- Exemplos de configuração
- Segurança

### [CONFIGURACAO_SETTINGS.md](./CONFIGURACAO_SETTINGS.md)
Detalhes sobre configurações do Django
- Settings de desenvolvimento
- Settings de produção
- Apps instalados
- Middleware

## 🎯 Ordem Recomendada

1. **Primeiro:** [INSTALL_LINUX.md](./INSTALL_LINUX.md) - Instalar o sistema
2. **Segundo:** [CONFIGURACAO.md](./CONFIGURACAO.md) - Configurar variáveis
3. **Terceiro:** [SETUP_DATABASE.md](./SETUP_DATABASE.md) - Preparar banco
4. **Quarto:** Iniciar servidor e testar

## ⚡ Quick Start

```bash
# 1. Clonar repositório
git clone https://github.com/rafaelflores-nefadv/nef-cadencia-v2.git
cd nef-cadencia-v2

# 2. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt
npm install

# 4. Configurar .env
cp .env.example .env
# Editar .env com suas configurações

# 5. Preparar banco
python manage.py migrate
python manage.py createsuperuser

# 6. Compilar CSS
npm run build:css

# 7. Iniciar servidor
python manage.py runserver
```

## 🆘 Problemas Comuns

### Erro de conexão com PostgreSQL
- Verificar se PostgreSQL está rodando
- Conferir credenciais no `.env`
- Verificar se o banco foi criado

### Erro ao instalar dependências
- Atualizar pip: `pip install --upgrade pip`
- Instalar build-essentials: `sudo apt install build-essential`

### Erro ao compilar CSS
- Verificar se Node.js está instalado
- Executar: `npm install`
- Tentar: `npm run build:css`

## 📖 Próximos Passos

Após a instalação:
- Ver [Arquitetura](../02-arquitetura/) para entender o sistema
- Ver [Comandos](../04-desenvolvimento/MANAGEMENT_COMMANDS.md) para operações
- Ver [Deploy](../06-deploy/) para produção
