# Setup JWT Authentication - NEF Cadência

**Guia rápido para configurar autenticação JWT**

---

## PASSO A PASSO

### 1. Instalar Dependências

```bash
pip install -r requirements-jwt.txt
```

**Pacotes instalados:**
- `djangorestframework==3.14.0`
- `djangorestframework-simplejwt==5.3.1`
- `django-cors-headers==4.3.1`
- `bcrypt==4.1.2`

---

### 2. Rodar Migrations

```bash
# Criar tabelas do token blacklist
python manage.py migrate
```

**Tabelas criadas:**
- `token_blacklist_outstandingtoken`
- `token_blacklist_blacklistedtoken`

---

### 3. Testar API

```bash
# Iniciar servidor
python manage.py runserver

# Em outro terminal, testar login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Resposta esperada:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    ...
  },
  "workspaces": [...]
}
```

---

### 4. Testar Request Autenticado

```bash
# Copiar o token da resposta anterior
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Fazer request autenticado
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## ENDPOINTS DISPONÍVEIS

### Autenticação

- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/verify` - Verificar token
- `GET /api/auth/me` - Dados do usuário
- `POST /api/auth/logout` - Logout

### Workspaces

- `GET /api/workspaces` - Listar workspaces
- `POST /api/workspaces/select` - Selecionar workspace

---

## INTEGRAÇÃO COM FRONTEND

### Atualizar authService.js

```javascript
// static/js/services/authService.js
async getUserWorkspaces() {
  // Mudar para usar API REST
  const result = await api.get('/api/workspaces');
  
  if (result.success) {
    return {
      success: true,
      workspaces: result.data.workspaces
    };
  }
  
  return result;
}
```

### Atualizar api.js

```javascript
// static/js/services/api.js
async request(url, options = {}) {
  // Adicionar token JWT
  const token = localStorage.getItem('access_token');
  if (token) {
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    };
  }
  
  const response = await fetch(url, options);
  
  // Se 401, tentar refresh
  if (response.status === 401) {
    const newToken = await this.refreshToken();
    if (newToken) {
      options.headers['Authorization'] = `Bearer ${newToken}`;
      return await fetch(url, options);
    }
  }
  
  return response;
}
```

---

## VERIFICAÇÃO

### ✅ Checklist

- [ ] Dependências instaladas
- [ ] Migrations rodadas
- [ ] Servidor iniciado
- [ ] Login funciona
- [ ] Token retornado
- [ ] Request autenticado funciona
- [ ] Workspaces retornados

---

## TROUBLESHOOTING

### Erro: "No module named 'rest_framework'"

**Solução:**
```bash
pip install djangorestframework
```

### Erro: "No module named 'rest_framework_simplejwt'"

**Solução:**
```bash
pip install djangorestframework-simplejwt
```

### Erro: "No module named 'corsheaders'"

**Solução:**
```bash
pip install django-cors-headers
```

### Erro: "relation 'token_blacklist_outstandingtoken' does not exist"

**Solução:**
```bash
python manage.py migrate
```

---

## DOCUMENTAÇÃO COMPLETA

Ver: `docs/API_AUTHENTICATION.md`

---

**Status:** ✅ **PRONTO PARA USAR**

A API JWT está configurada e funcionando!
