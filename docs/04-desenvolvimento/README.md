# 🔧 Desenvolvimento

Guias e referências para desenvolvedores do NEF Cadencia v2.

## 📚 Documentos Disponíveis

### [MANAGEMENT_COMMANDS.md](./MANAGEMENT_COMMANDS.md)
Comandos de gerenciamento Django
- Importação de dados (`import_lh_all`, `import_lh_pause_events`, `import_lh_workday`)
- Sincronização (`sync_legacy_events`)
- Rebuild de estatísticas (`rebuild_agent_day_stats`)
- Limpeza de dados (`wipe_lh_import`)
- Geração de dados fictícios (`generate_mock_data`)

### [TESTES.md](./TESTES.md)
Sistema de testes
- Testes unitários
- Testes de integração
- Fixtures e mocks
- Cobertura de código
- Como executar testes

### [API_AUTH.md](./API_AUTH.md)
API e autenticação
- Endpoints disponíveis
- Autenticação JWT/Session
- Permissões
- Rate limiting

### [PERMISSOES.md](./PERMISSOES.md)
Sistema de permissões
- Grupos de usuários
- Permissões por módulo
- Decorators customizados
- Mixins de permissão

### [RBAC.md](./RBAC.md)
Role-Based Access Control
- Roles disponíveis
- Hierarquia de permissões
- Atribuição de roles

### [SYNC.md](./SYNC.md)
Sincronização com legado
- Configuração de conexão
- Estratégia de sync
- Tratamento de erros
- Monitoramento

## 🎯 Comandos Mais Usados

### Importação de Dados
```bash
# Importar dados de hoje
python manage.py import_lh_all --today

# Importar período específico
python manage.py import_lh_all --from 2026-03-01 --to 2026-03-27

# Gerar dados fictícios para teste
python manage.py generate_mock_data --days 7
```

### Estatísticas
```bash
# Recalcular stats de hoje
python manage.py rebuild_agent_day_stats --today

# Recalcular período
python manage.py rebuild_agent_day_stats --from 2026-03-01 --to 2026-03-27
```

### Testes
```bash
# Executar todos os testes
python manage.py test

# Testar módulo específico
python manage.py test apps.monitoring

# Com cobertura
coverage run --source='.' manage.py test
coverage report
```

## 🛠️ Ferramentas de Desenvolvimento

### Django Shell
```bash
python manage.py shell

# Com IPython
pip install ipython
python manage.py shell
```

### Migrations
```bash
# Criar migrations
python manage.py makemigrations

# Aplicar migrations
python manage.py migrate

# Ver SQL de uma migration
python manage.py sqlmigrate monitoring 0001
```

### Debug
```bash
# Modo debug
DEBUG=True python manage.py runserver

# Com django-debug-toolbar
pip install django-debug-toolbar
```

## 📖 Padrões de Código

### Services
- Lógica de negócio em `services/`
- Funções puras quando possível
- Documentação inline

### Views
- Views simples, delegam para services
- Mixins para comportamento comum
- Context processors para dados globais

### Models
- Métodos de instância para lógica do objeto
- Managers customizados para queries complexas
- Meta classes para configuração

### Templates
- Componentização
- Reutilização via includes
- Template tags customizados

## 🔍 Debugging

### Logs
```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Django Debug Toolbar
```python
# settings.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

### Print Debugging
```python
# Em views
print(f"Context: {context}")

# Em templates
{{ variable|pprint }}
```

## 📊 Performance

### Query Optimization
```python
# Usar select_related para ForeignKey
Agent.objects.select_related('workspace')

# Usar prefetch_related para ManyToMany
Workspace.objects.prefetch_related('members')

# Evitar N+1 queries
stats = AgentDayStats.objects.select_related('agent')
```

### Caching
```python
from django.core.cache import cache

# Set cache
cache.set('key', value, timeout=300)

# Get cache
value = cache.get('key')
```
