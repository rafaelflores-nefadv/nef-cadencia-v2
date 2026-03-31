# 📦 Módulos

Documentação detalhada de cada módulo do sistema.

## 📂 Módulos Disponíveis

### [monitoring/](./monitoring/)
**Monitoramento de Agentes**
- Dashboard executivo e operacional
- Importação de dados do legado (LH)
- Cálculo de estatísticas diárias
- Sistema de alertas e riscos
- Classificação de pausas

**Principais arquivos:**
- `models.py` - Agent, AgentEvent, AgentDayStats
- `views.py` - Dashboards e visualizações
- `services/` - Lógica de negócio
- `management/commands/` - Comandos CLI

### [assistant/](./assistant/)
**Assistente IA**
- Chat conversacional com OpenAI
- Tools para ações no sistema
- Histórico de conversas
- Auditoria de ações
- Preferências de usuário

**Principais arquivos:**
- `models.py` - Conversation, Message, ActionLog
- `views.py` - API de chat
- `services/` - Integração OpenAI
- `tools/` - Ferramentas disponíveis

### [messaging/](./messaging/)
**Templates de Mensagens**
- Templates dinâmicos
- Renderização com variáveis
- Versionamento de templates
- Canais de notificação

**Principais arquivos:**
- `models.py` - MessageTemplate
- `services.py` - Renderização

### [rules/](./rules/)
**Configurações Dinâmicas**
- SystemConfig (chave-valor)
- Configurações globais
- Sem necessidade de deploy

**Principais arquivos:**
- `models.py` - SystemConfig
- `admin.py` - Interface admin

### [integrations/](./integrations/)
**Conectores Externos**
- Configuração de integrações
- Credenciais seguras
- Status de conectores

**Principais arquivos:**
- `models.py` - IntegrationConfig

### [accounts/](./accounts/)
**Autenticação e Usuários**
- Login/Logout
- Workspaces (multi-tenant)
- Permissões
- Context processors

**Principais arquivos:**
- `models.py` - User, Workspace
- `views.py` - Autenticação
- `middleware.py` - Workspace context

## 🔗 Relacionamentos entre Módulos

```
accounts (User, Workspace)
    ↓
monitoring (Agent, AgentEvent)
    ↓
assistant (Conversation, Tools)
    ↓
messaging (Templates)
    ↓
rules (SystemConfig)
```

## 📖 Como Usar Esta Documentação

1. **Entender um módulo:** Ler o README.md do módulo
2. **Ver modelos de dados:** Consultar models.md
3. **Entender serviços:** Ver services.md
4. **Comandos disponíveis:** Ver commands.md

## 🎯 Módulo Mais Importante

O módulo **monitoring** é o core do sistema:
- Importa dados do legado
- Calcula estatísticas
- Gera dashboards
- Sistema de alertas

Comece por ele se quiser entender o sistema.
