# Gerenciar Conversas do Eustácio no Admin

## 📋 Funcionalidades Adicionadas

O painel admin do Django agora possui **3 ações** para gerenciar conversas do Eustácio:

### **1. 🗑️ Excluir conversas selecionadas**
Exclui apenas as conversas que você selecionar na lista.

### **2. 🗑️ Excluir TODAS conversas dos usuários selecionados**
Exclui **todas** as conversas dos usuários que possuem as conversas selecionadas.

### **3. 🧹 Limpar conversas antigas (>30 dias)**
Exclui conversas com mais de 30 dias de inatividade.

---

## 🚀 Como Usar

### **Acessar o Admin**

```
http://192.168.200.8:10100/admin/assistant/assistantconversation/
```

### **Excluir Conversas Específicas**

1. Marcar checkbox das conversas que deseja excluir
2. Selecionar ação: **"🗑️ Excluir conversas selecionadas"**
3. Clicar em **"Ir"**
4. Confirmar exclusão

**Resultado:**
```
✓ 5 conversa(s) excluída(s) com sucesso: 3 de admin, 2 de mauricio
```

---

### **Excluir Todas as Conversas de um Usuário**

1. Marcar **qualquer conversa** do usuário
2. Selecionar ação: **"🗑️ Excluir TODAS conversas dos usuários selecionados"**
3. Clicar em **"Ir"**
4. Confirmar

**Resultado:**
```
ℹ Excluídas 15 conversas de admin
ℹ Excluídas 8 conversas de mauricio
✓ Total: 23 conversas excluídas de 2 usuário(s)
```

⚠️ **ATENÇÃO:** Esta ação exclui **TODAS** as conversas do usuário, não apenas as selecionadas!

---

### **Limpar Conversas Antigas**

1. Selecionar conversas (ou selecionar todas)
2. Selecionar ação: **"🧹 Limpar conversas antigas (>30 dias)"**
3. Clicar em **"Ir"**
4. Confirmar

**Resultado:**
```
✓ 12 conversa(s) antiga(s) excluída(s): 8 de admin, 4 de mauricio
```

Ou se não houver conversas antigas:
```
ℹ Nenhuma conversa com mais de 30 dias encontrada
```

---

## 📊 Melhorias na Listagem

### **Coluna "Mensagens"**

Agora mostra a quantidade de mensagens com cores:

- **0 msgs** (cinza) - Conversa vazia
- **1-4 msgs** (azul) - Poucas mensagens
- **5+ msgs** (verde negrito) - Conversa ativa

### **Hierarquia de Data**

Adicionado filtro por data de criação no topo da página para facilitar navegação.

---

## 🔍 Filtros Disponíveis

### **Buscar por:**
- ID da conversa
- Título
- Nome de usuário

### **Filtrar por:**
- Origem (page, widget)
- Status (active, archived)
- Persistente (sim/não)
- Data de criação

---

## 💡 Casos de Uso

### **1. Limpar conversas de teste**
```
1. Buscar por usuário "test" ou "admin"
2. Selecionar conversas
3. Ação: "Excluir conversas selecionadas"
```

### **2. Resetar conversas de um usuário**
```
1. Buscar pelo nome do usuário
2. Selecionar qualquer conversa dele
3. Ação: "Excluir TODAS conversas dos usuários selecionados"
```

### **3. Manutenção mensal**
```
1. Selecionar todas (checkbox no topo)
2. Ação: "Limpar conversas antigas (>30 dias)"
3. Executar mensalmente
```

### **4. Liberar espaço no banco**
```
1. Filtrar por "is_persistent = Não"
2. Selecionar todas
3. Ação: "Excluir conversas selecionadas"
```

---

## ⚠️ Avisos Importantes

### **Exclusão é Permanente**
- Não há como recuperar conversas excluídas
- Sempre confirme antes de executar

### **Mensagens Também São Excluídas**
- Ao excluir uma conversa, todas as mensagens são excluídas
- Logs de auditoria são mantidos

### **Backup Recomendado**
Antes de exclusões em massa:
```bash
# Backup do banco
pg_dump nef_cadencia > backup_$(date +%Y%m%d).sql

# Ou apenas conversas
python manage.py dumpdata assistant.AssistantConversation > conversas_backup.json
```

---

## 🔧 Código Implementado

### **Ações Customizadas**

```python
# apps/assistant/admin.py

def delete_selected_conversations(modeladmin, request, queryset):
    """Excluir conversas selecionadas"""
    count = queryset.count()
    user_counts = {}
    
    for conversation in queryset:
        username = conversation.created_by.username if conversation.created_by else "Sem usuário"
        user_counts[username] = user_counts.get(username, 0) + 1
    
    queryset.delete()
    
    details = ", ".join([f"{count} de {user}" for user, count in user_counts.items()])
    messages.success(request, f"{count} conversa(s) excluída(s): {details}")
```

### **Admin Customizado**

```python
@admin.register(AssistantConversation)
class AssistantConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "created_by", 
        "origin", 
        "status", 
        "is_persistent", 
        "message_count_display",  # Nova coluna
        "updated_at", 
        "title"
    )
    actions = [
        delete_selected_conversations,
        delete_user_conversations,
        delete_old_conversations,
    ]
    date_hierarchy = "created_at"  # Navegação por data
```

---

## 📈 Estatísticas

### **Ver Total de Conversas por Usuário**

No shell do Django:
```python
from apps.assistant.models import AssistantConversation
from django.db.models import Count

stats = AssistantConversation.objects.values('created_by__username').annotate(
    total=Count('id')
).order_by('-total')

for stat in stats:
    print(f"{stat['created_by__username']}: {stat['total']} conversas")
```

### **Ver Conversas Antigas**

```python
from datetime import timedelta
from django.utils import timezone

cutoff = timezone.now() - timedelta(days=30)
old = AssistantConversation.objects.filter(updated_at__lt=cutoff)

print(f"Conversas antigas: {old.count()}")
```

---

## 🎯 Próximas Melhorias

- [ ] Exportar conversas para CSV/JSON
- [ ] Arquivar conversas em vez de excluir
- [ ] Estatísticas de uso por usuário
- [ ] Gráfico de conversas ao longo do tempo
- [ ] Busca por conteúdo das mensagens

---

**Versão:** 1.0  
**Data:** 27/03/2026  
**Status:** ✅ Implementado
