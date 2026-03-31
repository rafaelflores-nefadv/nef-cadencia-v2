# Troubleshooting - Assistente Eustácio

## 🐛 Problemas Comuns e Soluções

### 1. Área Central Vazia / Tela Preta

**Sintomas:**
- Área central do chat aparece vazia
- Mensagens não aparecem
- Estado vazio não mostra ícones

**Causa:**
- JavaScript renderizando sem avatares
- Ícones Lucide não inicializados após renderização dinâmica

**Solução Aplicada (v3.2.1):**
```javascript
// Adicionar avatares nas mensagens
var flexContainer = document.createElement("div");
flexContainer.className = "flex items-start gap-3";

var avatar = document.createElement("div");
avatar.className = "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0";

var avatarIcon = document.createElement("i");
avatarIcon.setAttribute("data-lucide", message.role === "user" ? "user" : "bot");

// Inicializar Lucide após renderização
if (window.lucide) {
  window.lucide.createIcons();
}
```

**Verificação:**
1. Abrir console do navegador (F12)
2. Verificar se `window.lucide` está definido
3. Verificar se há erros de JavaScript

---

### 2. Botão "Nova Conversa" Não Funciona

**Sintomas:**
- Clicar em "Nova conversa" não cria conversa
- Nenhum feedback visual
- Console mostra erro 403/CSRF

**Causas Possíveis:**
- Token CSRF inválido
- Limite de conversas atingido
- Erro no backend

**Soluções:**

#### A. Verificar Token CSRF
```javascript
// No console do navegador
document.cookie.split(';').find(c => c.includes('csrftoken'))
```

#### B. Verificar Limite
```python
# apps/assistant/services/conversation_store.py
def get_user_conversation_limit(user):
    # Verificar se não está retornando 0
    return 100  # ou valor configurado
```

#### C. Ver Logs
```bash
# Django
tail -f logs/django.log | grep assistant

# Ou
python manage.py runserver --verbosity 2
```

---

### 3. Eustácio Não Responde Após Primeira Pergunta

**Sintomas:**
- Primeira pergunta funciona
- Perguntas seguintes não recebem resposta
- Indicador "pensando" fica travado

**Causas Possíveis:**
- Timeout na API OpenAI
- Erro não tratado no backend
- Problema de estado no JavaScript

**Diagnóstico:**

#### Passo 1: Verificar Logs
```bash
tail -f logs/django.log | grep -A 10 "assistant"
```

#### Passo 2: Testar API OpenAI
```python
from openai import OpenAI
client = OpenAI()

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "teste"}],
        timeout=30
    )
    print("OK:", response.choices[0].message.content)
except Exception as e:
    print("ERRO:", str(e))
```

#### Passo 3: Verificar Variáveis de Ambiente
```bash
echo $OPENAI_API_KEY
# Deve retornar a chave
```

**Soluções:**

#### A. Adicionar Timeout
```python
# apps/assistant/services/assistant_service.py
from openai import OpenAI

client = OpenAI(timeout=30.0)  # 30 segundos

response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    max_tokens=500,  # Limitar resposta
    timeout=30
)
```

#### B. Melhorar Tratamento de Erros
```python
# apps/assistant/views.py
import logging
logger = logging.getLogger(__name__)

@require_POST
def assistant_chat_view(request):
    try:
        # ... código existente ...
        logger.info(f"Chat request: {text[:50]}...")
        
        result = run_chat(...)
        
        logger.info(f"Chat response: {result.get('answer', '')[:50]}...")
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return JsonResponse({
            "detail": f"Erro ao processar: {str(e)}"
        }, status=500)
```

---

### 4. Ícones Lucide Não Aparecem

**Sintomas:**
- Ícones aparecem como `[icon]` ou texto
- Avatares sem ícones
- Sugestões sem ícones

**Causa:**
- Lucide não carregado
- `createIcons()` não chamado

**Solução:**

#### Verificar base.html
```html
<!-- Antes do </body> -->
<script src="https://unpkg.com/lucide@latest"></script>
<script>
  document.addEventListener('DOMContentLoaded', function() {
    lucide.createIcons();
  });
</script>
```

#### Verificar Renderização Dinâmica
```javascript
// Após adicionar elementos com data-lucide
if (window.lucide) {
  window.lucide.createIcons();
}
```

---

### 5. Erro CORS no Console

**Sintomas:**
- Console mostra erro CORS
- Status 200 mas erro
- Cross-Origin Request Blocked

**Causa:**
- Configuração de CORS no Django
- Headers incorretos

**Solução:**

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:10100",
    "http://192.168.200.8:10100",
]

CORS_ALLOW_CREDENTIALS = True

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Primeiro
    'django.middleware.common.CommonMiddleware',
    # ...
]
```

---

### 6. Conversas Não Abrem ao Clicar

**Sintomas:**
- Clicar em conversa não abre
- URL muda mas conteúdo não
- Console sem erros

**Causa:**
- JavaScript não interceptando cliques
- Event listener não registrado

**Solução:**

```javascript
// Verificar se está registrado
listEl.addEventListener("click", function (event) {
  var link = event.target.closest("[data-conversation-link]");
  if (!link) return;
  
  event.preventDefault();
  var conversationId = link.getAttribute("data-conversation-id");
  if (!conversationId) return;
  
  loadConversation(conversationId, true);
});
```

**Debug:**
```javascript
// No console
document.getElementById('assistant-page-list').onclick = function(e) {
  console.log('Clicked:', e.target);
}
```

---

### 7. Mensagens Sem Avatar

**Sintomas:**
- Mensagens aparecem mas sem avatar
- Apenas texto da mensagem

**Causa:**
- Template HTML sem estrutura flex
- JavaScript não criando avatares

**Solução Aplicada (v3.2.1):**

Template corrigido:
```django
{% for message in selected_conversation.messages %}
  <div class="assistant-page__message assistant-page__message--{{ message.role }}">
    <div class="flex items-start gap-3">
      {% if message.role == 'user' %}
        <div class="w-8 h-8 rounded-full bg-sky-500/20 flex items-center justify-center flex-shrink-0">
          <i data-lucide="user" class="w-4 h-4 text-sky-400"></i>
        </div>
      {% else %}
        <div class="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center flex-shrink-0">
          <i data-lucide="bot" class="w-4 h-4 text-violet-400"></i>
        </div>
      {% endif %}
      <div class="assistant-page__bubble">{{ message.content }}</div>
    </div>
  </div>
{% endfor %}
```

JavaScript corrigido (ver arquivo completo).

---

## 🔍 Comandos de Debug

### Ver Logs em Tempo Real
```bash
# Django
tail -f logs/django.log

# Filtrar por assistant
tail -f logs/django.log | grep assistant

# Com contexto (10 linhas antes/depois)
tail -f logs/django.log | grep -A 10 -B 10 assistant
```

### Testar Endpoint Diretamente
```bash
# Criar conversa
curl -X POST http://localhost:10100/assistant/conversations/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TOKEN" \
  -d '{}'

# Enviar mensagem
curl -X POST http://localhost:10100/assistant/chat \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: TOKEN" \
  -d '{"text": "teste", "conversation_id": 1, "origin": "page"}'
```

### Verificar Estado do JavaScript
```javascript
// No console do navegador (F12)

// Verificar Lucide
console.log(window.lucide);

// Verificar estado da página
console.log(document.getElementById('assistant-page-root').dataset);

// Verificar conversas
var data = JSON.parse(document.getElementById('assistant-page-initial-data').textContent);
console.log(data);
```

---

## 📊 Checklist de Verificação

Após atualizar o código, verificar:

- [ ] Página carrega sem erros no console
- [ ] Ícones Lucide aparecem corretamente
- [ ] Botão "Nova conversa" funciona
- [ ] Criar conversa mostra feedback visual
- [ ] Área central mostra estado vazio com ícone
- [ ] Enviar mensagem funciona
- [ ] Mensagem aparece com avatar
- [ ] Resposta do Eustácio aparece com avatar
- [ ] Múltiplas mensagens funcionam
- [ ] Clicar em conversa abre corretamente
- [ ] Excluir conversa funciona
- [ ] Sugestões têm ícones
- [ ] Breadcrumb funciona
- [ ] Responsividade OK (mobile/tablet/desktop)

---

## 🚀 Versões e Correções

### v3.2.1 (27/03/2026)
**Correções:**
- ✅ Área central vazia corrigida
- ✅ Avatares adicionados em mensagens
- ✅ Ícones Lucide em estados vazios
- ✅ Inicialização de ícones após renderização dinâmica
- ✅ Lista vazia com ícone inbox

**Arquivos Modificados:**
- `static/assistant/assistant_page.js`
- `templates/assistant/page.html`

### v3.2 (27/03/2026)
**Melhorias:**
- ✅ Interface completamente redesenhada
- ✅ Breadcrumb de navegação
- ✅ 5 sugestões com ícones
- ✅ Radar operacional
- ✅ Dicas de uso

---

## 📞 Suporte

Se o problema persistir após seguir este guia:

1. **Coletar informações:**
   - Logs do Django
   - Console do navegador (F12)
   - Screenshot do erro
   - Versão do navegador

2. **Verificar:**
   - Código está atualizado (`git pull`)
   - Servidor reiniciado
   - Cache do navegador limpo (Ctrl+Shift+R)

3. **Testar em:**
   - Navegador diferente
   - Modo anônimo/privado
   - Dispositivo diferente

---

**Última atualização:** 27/03/2026  
**Versão:** 3.2.1  
**Status:** ✅ Funcional
