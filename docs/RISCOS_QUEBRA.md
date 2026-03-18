# Análise de Riscos de Quebra

**Data:** 18 de Março de 2026  
**Versão:** 1.0  
**Status:** Proposta sem implementação

---

## 1. Matriz de Riscos

| Ação | Risco | Probabilidade | Impacto | Severidade | Mitigação |
|------|-------|---------------|---------|------------|-----------|
| Criar arquivos vazios | Muito Baixo | 5% | Baixo | ✅ SEGURO | Não afeta código existente |
| Adicionar selectors | Baixo | 10% | Médio | ✅ SEGURO | Testes antes/depois |
| Extrair para services | Médio | 25% | Alto | ⚠️ CUIDADO | Testes unitários + comparação |
| Refatorar views gigantes | Médio | 30% | Alto | ⚠️ CUIDADO | Testes E2E + rollback |
| Alterar models | Alto | 40% | Muito Alto | ❌ EVITAR | Migrations reversíveis |
| Remover código | Muito Alto | 60% | Crítico | ❌ EVITAR | Análise de dependências |

---

## 2. Riscos por Categoria

### 2.1 Riscos de Quebra de Funcionalidade

#### ❌ ALTO RISCO - Evitar

**1. Alterar assinaturas de métodos públicos**
```python
# RISCO: Quebra templates e outros apps
# ANTES
def get_context_data(self, **kwargs):
    context['agents'] = self.get_agents()
    return context

# DEPOIS (QUEBRA!)
def get_context_data(self, **kwargs):
    context['operators'] = self.get_agents()  # Nome mudou!
    return context
```

**Impacto:** Templates quebram, páginas não renderizam  
**Mitigação:** Manter nomes de variáveis de contexto

**2. Remover templates sem substituir**
```python
# RISCO: 404 ou erro de template
# ANTES
template_name = "monitoring/dashboard.html"

# DEPOIS (QUEBRA!)
template_name = "monitoring/new_dashboard.html"  # Template não existe!
```

**Impacto:** Páginas não carregam  
**Mitigação:** Criar novo template antes de mudar referência

**3. Alterar estrutura de dados retornados**
```python
# RISCO: Templates dependem da estrutura
# ANTES
context['agents'] = [
    {'cd_operador': 1, 'nome': 'João'},
]

# DEPOIS (QUEBRA!)
context['agents'] = [
    {'code': 1, 'name': 'João'},  # Chaves mudaram!
]
```

**Impacto:** Templates quebram, dados não aparecem  
**Mitigação:** Manter estrutura ou criar serializer compatível

**4. Mudar queries sem testar**
```python
# RISCO: Resultados diferentes
# ANTES
agents = Agent.objects.filter(ativo=True)

# DEPOIS (PODE QUEBRAR!)
agents = Agent.objects.filter(ativo=True, email__isnull=False)
# Agora retorna menos agentes!
```

**Impacto:** Dados faltando, cálculos errados  
**Mitigação:** Comparar resultados antes/depois

#### ⚠️ MÉDIO RISCO - Cuidado

**1. Extrair lógica para services**
```python
# RISCO: Lógica pode mudar sem querer
# ANTES (em view)
def get_context_data(self):
    total = sum(agent.pausas for agent in agents)
    
# DEPOIS (em service)
def calculate_total_pauses(agents):
    return sum(agent.pausas for agent in agents if agent.ativo)
    # Adicionou filtro sem querer!
```

**Impacto:** Cálculos diferentes  
**Mitigação:** Testes unitários comparando resultados

**2. Refatorar views grandes**
```python
# RISCO: Perder lógica no meio
# ANTES (tudo em um método)
def get_context_data(self):
    # 300 linhas de lógica
    
# DEPOIS (dividido)
def get_context_data(self):
    metrics = self.calculate_metrics()
    alerts = self.build_alerts()
    # Esqueceu de calcular algo?
```

**Impacto:** Funcionalidade incompleta  
**Mitigação:** Checklist de features, testes E2E

**3. Adicionar validações em forms**
```python
# RISCO: Rejeitar dados que antes eram aceitos
# ANTES (sem validação)
cd_operador = form.cleaned_data['cd_operador']

# DEPOIS (com validação)
def clean_cd_operador(self):
    cd = self.cleaned_data['cd_operador']
    if cd <= 0:
        raise ValidationError('Deve ser positivo')
    # Agora rejeita códigos <= 0 que antes passavam!
```

**Impacto:** Usuários não conseguem salvar dados  
**Mitigação:** Validar dados existentes antes, migração de dados se necessário

#### ✅ BAIXO RISCO - Seguro

**1. Criar novos arquivos**
```python
# SEGURO: Não afeta código existente
# Criar selectors.py, forms.py, etc.
```

**2. Adicionar testes**
```python
# SEGURO: Não afeta código de produção
# Criar tests/test_*.py
```

**3. Adicionar docstrings**
```python
# SEGURO: Apenas documentação
def calculate_metrics():
    """Calcula métricas de operadores."""
    pass
```

---

### 2.2 Riscos de Performance

#### ⚠️ MÉDIO RISCO

**1. Queries N+1**
```python
# RISCO: Performance degradada
# ANTES
agents = Agent.objects.filter(ativo=True)
for agent in agents:
    print(agent.events.count())  # Query por agente!

# MELHOR
agents = Agent.objects.filter(ativo=True).annotate(
    event_count=Count('events')
)
```

**Impacto:** Dashboards lentos  
**Mitigação:** Usar select_related, prefetch_related, annotate

**2. Queries sem índices**
```python
# RISCO: Queries lentas
# ANTES
events = AgentEvent.objects.filter(
    dt_inicio__gte=start,
    nm_pausa='ALMOCO'  # Sem índice!
)
```

**Impacto:** Timeout, dashboards lentos  
**Mitigação:** Adicionar índices, profiling

**3. Cálculos em Python vs. Database**
```python
# RISCO: Lento para muitos dados
# ANTES (lento)
total = sum(event.duracao_seg for event in events)

# MELHOR (rápido)
total = events.aggregate(Sum('duracao_seg'))['duracao_seg__sum']
```

**Impacto:** Dashboards lentos  
**Mitigação:** Usar agregações do banco

---

### 2.3 Riscos de Migrations

#### ❌ ALTO RISCO

**1. Migrations irreversíveis**
```python
# RISCO: Não pode fazer rollback
class Migration(migrations.Migration):
    operations = [
        migrations.RunSQL(
            "DELETE FROM monitoring_agent WHERE ativo = false",
            # Sem reverse_sql!
        ),
    ]
```

**Impacto:** Rollback impossível, dados perdidos  
**Mitigação:** Sempre adicionar reverse_sql

**2. Migrations com perda de dados**
```python
# RISCO: Dados perdidos
class Migration(migrations.Migration):
    operations = [
        migrations.RemoveField(
            model_name='agent',
            name='nr_ramal',  # Dados perdidos!
        ),
    ]
```

**Impacto:** Dados irrecuperáveis  
**Mitigação:** Backup antes, migration de dados

**3. Migrations que travam tabelas**
```python
# RISCO: Downtime
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='agentevent',  # Tabela grande!
            name='new_field',
            field=models.CharField(max_length=100, default=''),
        ),
    ]
```

**Impacto:** Aplicação travada durante migration  
**Mitigação:** Migrations em horário de baixo uso, campos nullable

---

### 2.4 Riscos de Segurança

#### ⚠️ MÉDIO RISCO

**1. Permissions mal configuradas**
```python
# RISCO: Acesso não autorizado
# ANTES (protegido)
class DashboardView(LoginRequiredMixin, TemplateView):
    pass

# DEPOIS (VULNERÁVEL!)
class DashboardView(TemplateView):  # Esqueceu LoginRequiredMixin!
    pass
```

**Impacto:** Dados expostos  
**Mitigação:** Testes de permissões, code review

**2. Validação insuficiente**
```python
# RISCO: SQL injection, XSS
# VULNERÁVEL
def search_agents(query):
    return Agent.objects.raw(f"SELECT * FROM agent WHERE nome LIKE '%{query}%'")

# SEGURO
def search_agents(query):
    return Agent.objects.filter(nm_agente__icontains=query)
```

**Impacto:** Vulnerabilidades de segurança  
**Mitigação:** Usar ORM, validar inputs

---

## 3. Estratégias de Mitigação

### 3.1 Antes de Refatorar

**1. Criar testes para comportamento atual**
```python
# Documentar comportamento esperado
class DashboardViewTest(TestCase):
    def test_dashboard_returns_active_agents(self):
        # Criar dados de teste
        Agent.objects.create(cd_operador=1, ativo=True)
        Agent.objects.create(cd_operador=2, ativo=False)
        
        # Chamar view
        response = self.client.get('/dashboard')
        
        # Verificar resultado
        self.assertEqual(len(response.context['agents']), 1)
        self.assertEqual(response.context['agents'][0].cd_operador, 1)
```

**2. Fazer backup de dados**
```bash
# Backup antes de migrations
python manage.py dumpdata > backup_before_refactor.json

# Backup do banco
pg_dump alive_platform > backup_$(date +%Y%m%d).sql
```

**3. Criar branch separada**
```bash
git checkout -b refactor/architecture
# Trabalhar na branch, não em main
```

### 3.2 Durante Refatoração

**1. Commits pequenos e frequentes**
```bash
# Commit após cada mudança pequena
git commit -m "refactor: extract get_active_agents to selectors"
git commit -m "test: add tests for get_active_agents"
git commit -m "refactor: use get_active_agents in DashboardView"
```

**2. Testes após cada mudança**
```bash
# Rodar testes após cada commit
python manage.py test

# Verificar manualmente
python manage.py runserver
# Acessar dashboards
```

**3. Comparar resultados**
```python
# Script para comparar antes/depois
def compare_dashboard_results():
    # Chamar versão antiga
    old_result = old_dashboard_view()
    
    # Chamar versão nova
    new_result = new_dashboard_view()
    
    # Comparar
    assert old_result == new_result, "Resultados diferentes!"
```

### 3.3 Após Refatoração

**1. Testes E2E**
```python
# Testar fluxos completos
class DashboardE2ETest(TestCase):
    def test_full_dashboard_flow(self):
        # Login
        self.client.login(username='user', password='pass')
        
        # Acessar dashboard
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Verificar dados
        self.assertContains(response, 'Agentes Ativos')
        self.assertContains(response, 'Score Operacional')
```

**2. Testes de performance**
```python
# Comparar performance
import time

def test_dashboard_performance():
    start = time.time()
    response = self.client.get('/dashboard')
    duration = time.time() - start
    
    # Deve ser rápido
    assert duration < 2.0, f"Dashboard lento: {duration}s"
```

**3. Monitoramento em staging**
```bash
# Deploy em staging primeiro
git push origin refactor/architecture
# Deploy automático para staging

# Monitorar por 1-2 dias
# Verificar logs, erros, performance
```

---

## 4. Plano de Rollback

### 4.1 Rollback de Código

**Se algo quebrar:**
```bash
# Reverter último commit
git revert HEAD

# Ou voltar para commit anterior
git reset --hard <commit_hash>

# Deploy da versão anterior
git push origin main --force
```

### 4.2 Rollback de Migrations

**Se migration quebrar:**
```bash
# Reverter migration
python manage.py migrate monitoring 0010_previous_migration

# Ou restaurar backup
psql alive_platform < backup_20260318.sql
```

### 4.3 Feature Flags

**Desabilitar feature nova:**
```python
# settings.py
FEATURE_FLAGS = {
    'use_new_selectors': False,  # Desabilitar
}

# Em views
if settings.FEATURE_FLAGS['use_new_selectors']:
    agents = get_active_agents()  # Novo
else:
    agents = Agent.objects.filter(ativo=True)  # Antigo (fallback)
```

---

## 5. Checklist de Segurança

### Antes de Cada Deploy

- [ ] Todos os testes passam
- [ ] Testes E2E passam
- [ ] Performance aceitável
- [ ] Code review aprovado
- [ ] Backup de banco feito
- [ ] Migrations revisadas
- [ ] Rollback plan documentado
- [ ] Feature flags configuradas
- [ ] Monitoramento configurado

### Após Deploy

- [ ] Verificar logs de erro
- [ ] Verificar métricas de performance
- [ ] Verificar dashboards funcionando
- [ ] Verificar usuários conseguem usar
- [ ] Monitorar por 24h
- [ ] Comunicar equipe

---

## 6. Sinais de Alerta

### 🚨 Reverter Imediatamente Se:

- Taxa de erro > 5%
- Tempo de resposta > 5s
- Usuários reportando bugs críticos
- Dados incorretos nos dashboards
- Perda de dados

### ⚠️ Investigar Se:

- Taxa de erro > 1%
- Tempo de resposta > 3s
- Usuários reportando bugs menores
- Performance degradada

### ✅ Tudo OK Se:

- Taxa de erro < 0.5%
- Tempo de resposta < 2s
- Sem reports de bugs
- Performance igual ou melhor

---

## 7. Contatos de Emergência

### Em Caso de Problema Crítico

1. **Reverter deploy imediatamente**
2. **Notificar equipe**
3. **Investigar causa raiz**
4. **Documentar incidente**
5. **Planejar correção**

---

## 8. Lições Aprendidas (Atualizar Após Refatoração)

### O Que Funcionou Bem
- [ ] A ser preenchido

### O Que Não Funcionou
- [ ] A ser preenchido

### O Que Fazer Diferente
- [ ] A ser preenchido

---

**Documento gerado automaticamente pela análise técnica do projeto.**  
**Nenhuma alteração foi feita no código durante esta análise.**
