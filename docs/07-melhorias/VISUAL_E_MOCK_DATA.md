# Melhorias Visuais e Dados Fictícios

## 📋 Resumo das Melhorias

Este documento descreve as melhorias implementadas para resolver problemas de:
1. **Quebra de dados do banco legado** - Sistema de dados fictícios para testes
2. **Desorganização visual** - Novo layout com melhor hierarquia de informações
3. **Excesso de informações** - Dashboard reorganizado em seções claras

---

## 🎲 Sistema de Dados Fictícios

### Comando: `generate_mock_data`

Gera dados realistas para testes quando o banco legado está indisponível ou quebrado.

#### Características:
- ✅ Usa agentes existentes no banco
- ✅ Gera jornadas de trabalho realistas (7h-9h até 16h-18h)
- ✅ Cria pausas variadas (almoço, lanche, banheiro, reunião, etc.)
- ✅ Calcula estatísticas automaticamente
- ✅ Suporta múltiplos períodos

#### Uso Básico:

```bash
# Gerar dados para hoje
python manage.py generate_mock_data --today

# Gerar para data específica
python manage.py generate_mock_data --date 2026-03-27

# Gerar para período
python manage.py generate_mock_data --from 2026-03-20 --to 2026-03-27

# Gerar últimos 7 dias
python manage.py generate_mock_data --days 7

# Gerar para todos os agentes ativos
python manage.py generate_mock_data --today

# Gerar apenas para 10 agentes (aleatórios)
python manage.py generate_mock_data --today --agents 10

# Limpar dados existentes antes de gerar
python manage.py generate_mock_data --today --clear
```

#### Tipos de Pausas Geradas:

| Tipo | Duração Mínima | Duração Máxima |
|------|----------------|----------------|
| ALMOÇO | 1h | 1h15 |
| LANCHE | 10min | 15min |
| BANHEIRO | 3min | 7min |
| TREINAMENTO | 30min | 1h |
| REUNIÃO | 30min | 1h30 |
| PAUSA TÉCNICA | 5min | 15min |
| SUPORTE TI | 10min | 30min |

#### Exemplo Completo:

```bash
# 1. Ativar ambiente virtual
cd /opt/nef-cadencia-v2
source venv/bin/activate

# 2. Gerar dados fictícios para a última semana
python manage.py generate_mock_data --days 7 --clear

# 3. Verificar dados gerados
python manage.py shell
>>> from apps.monitoring.models import AgentDayStats
>>> AgentDayStats.objects.filter(source="MOCK").count()
>>> exit()

# 4. Acessar dashboard
python manage.py runserver 0.0.0.0:10100
# Abrir: http://192.168.200.8:10100/dashboard
```

---

## 🎨 Melhorias Visuais

### Novo Layout do Dashboard

Criado arquivo: `templates/monitoring/dashboard_executive_improved.html`

#### Principais Mudanças:

### 1. **Hero Section Simplificado**
- ✅ Apenas 4 métricas principais (antes eram 5+)
- ✅ Valores maiores e mais legíveis
- ✅ Espaçamento melhorado
- ✅ Foco em Health Score, Produtividade, Agentes e Alertas

### 2. **Organização em Seções Claras**

#### 📊 Visão Geral
- Health Score detalhado com gauge
- Métricas rápidas em formato lista
- Informações essenciais sem poluição visual

#### 📈 Análise de Pausas
- Apenas 2 gráficos focados
- Distribuição por tipo (donut)
- Maiores pausas (barras)

#### ⚠️ Tendências e Alertas
- Evolução por hora (linha)
- Radar de criticidade
- Foco em identificar problemas

#### 🏆 Rankings e Insights
- 3 colunas compactas
- Top agentes (top 5)
- Alertas recentes (top 5)
- Insights automáticos

### 3. **Melhorias de UX**

- ✅ Títulos de seção com barra colorida lateral
- ✅ Cards com hover effect
- ✅ Ícones emoji para insights rápidos
- ✅ Scroll independente em listas longas
- ✅ Badges de status mais visíveis
- ✅ Espaçamento consistente (8px base)

---

## 🔄 Como Ativar o Novo Layout

### Opção 1: Substituir o arquivo original (recomendado)

```bash
cd /opt/nef-cadencia-v2

# Backup do original
cp templates/monitoring/dashboard_executive.html templates/monitoring/dashboard_executive_backup.html

# Substituir pelo novo
cp templates/monitoring/dashboard_executive_improved.html templates/monitoring/dashboard_executive.html

# Reiniciar servidor
python manage.py runserver 0.0.0.0:10100
```

### Opção 2: Criar rota separada para testar

Editar `apps/monitoring/urls.py`:

```python
urlpatterns = [
    # ... rotas existentes ...
    path("dashboard/improved/", DashboardImprovedView.as_view(), name="dashboard_improved"),
]
```

Criar view em `apps/monitoring/views.py`:

```python
class DashboardImprovedView(DashboardView):
    template_name = "monitoring/dashboard_executive_improved.html"
```

Acessar: `http://192.168.200.8:10100/dashboard/improved/`

---

## 📊 Comparação: Antes vs Depois

### Antes:
- ❌ 15+ cards na primeira dobra
- ❌ Informações duplicadas
- ❌ Difícil identificar prioridades
- ❌ Gráficos misturados com métricas
- ❌ Sem hierarquia visual clara

### Depois:
- ✅ 4 métricas principais no hero
- ✅ Seções organizadas por tema
- ✅ Hierarquia visual clara (títulos com barras)
- ✅ Gráficos agrupados por contexto
- ✅ Fácil navegação e escaneamento

---

## 🧪 Workflow Completo de Teste

```bash
# 1. Conectar ao servidor
ssh nabarrete@192.168.200.8
sudo -i

# 2. Ir para o projeto
cd /opt/nef-cadencia-v2
source venv/bin/activate

# 3. Gerar dados fictícios
python manage.py generate_mock_data --days 7 --clear

# 4. Verificar dados
python manage.py shell
>>> from apps.monitoring.models import AgentDayStats, AgentEvent
>>> print(f"Stats: {AgentDayStats.objects.filter(source='MOCK').count()}")
>>> print(f"Eventos: {AgentEvent.objects.filter(source='MOCK').count()}")
>>> exit()

# 5. Ativar novo layout
cp templates/monitoring/dashboard_executive_improved.html templates/monitoring/dashboard_executive.html

# 6. Iniciar servidor
python manage.py runserver 0.0.0.0:10100

# 7. Acessar no navegador
# http://192.168.200.8:10100/dashboard
```

---

## 🎯 Próximos Passos Recomendados

### Curto Prazo:
1. ✅ Testar novo layout com dados reais
2. ✅ Ajustar cores/espaçamentos conforme feedback
3. ✅ Aplicar mesmo padrão nos outros dashboards (produtividade, pipeline)

### Médio Prazo:
1. Criar dashboard mobile-first
2. Adicionar filtros rápidos (hoje, semana, mês)
3. Implementar refresh automático de dados

### Longo Prazo:
1. Sistema de notificações em tempo real
2. Exportação de relatórios PDF
3. Dashboards personalizáveis por usuário

---

## 🐛 Troubleshooting

### Dados fictícios não aparecem no dashboard

```bash
# Verificar se foram criados
python manage.py shell
>>> from apps.monitoring.models import AgentDayStats
>>> AgentDayStats.objects.filter(source="MOCK").count()
```

Se retornar 0, regerar:
```bash
python manage.py generate_mock_data --today --clear
```

### Layout não mudou após substituir arquivo

```bash
# Limpar cache do navegador (Ctrl+Shift+R)
# Ou reiniciar servidor
pkill -f "manage.py runserver"
python manage.py runserver 0.0.0.0:10100
```

### Gráficos não aparecem

Verificar se ApexCharts está carregando:
- Abrir console do navegador (F12)
- Procurar por erros de JavaScript
- Verificar se `https://cdn.jsdelivr.net/npm/apexcharts` está acessível

---

## 📝 Notas Importantes

1. **Dados fictícios são marcados com `source="MOCK"`**
   - Fácil de identificar e limpar
   - Não interferem com dados reais do legado

2. **Novo layout é 100% compatível com dados existentes**
   - Mesmas variáveis de contexto
   - Mesma lógica de backend
   - Apenas reorganização visual

3. **Performance melhorada**
   - Menos elementos DOM
   - Gráficos renderizados sob demanda
   - Scroll independente em listas

---

## 🤝 Contribuindo

Para sugerir melhorias no layout ou comando de dados fictícios:

1. Testar mudanças localmente
2. Documentar alterações
3. Criar backup antes de aplicar em produção
4. Validar com usuários finais

---

**Criado em:** 27/03/2026  
**Versão:** 1.0  
**Autor:** Sistema NEF Cadencia
