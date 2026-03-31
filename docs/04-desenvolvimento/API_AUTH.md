# API de Autenticação JWT - NEF Cadência

**Data:** 18 de Março de 2026  
**Objetivo:** Documentar API REST de autenticação com JWT  
**Status:** ✅ IMPLEMENTADO

---

## VISÃO GERAL

API REST completa para autenticação usando **JWT (JSON Web Tokens)** e **bcrypt** para hashing de senhas.

**Características:**
- ✅ Login com username ou email
- ✅ Tokens JWT (access + refresh)
- ✅ Bcrypt para senhas
- ✅ Retorna user + workspaces
- ✅ Middleware JWT
- ✅ Proteção de rotas
- ✅ Expiração de tokens
- ✅ Tratamento de erros padronizado
- ✅ Arquitetura em camadas

---

## ENDPOINTS

### Base URL
```
http://localhost:8000/api
```

---

### 1. POST /api/auth/login

**Descrição:** Realizar login e obter tokens JWT

**Request:**
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "Sistema",
    "full_name": "Admin Sistema",
    "phone": "",
    "avatar": null,
    "bio": "",
    "is_staff": true,
    "is_active": true,
    "date_joined": "2026-03-18T16:00:00Z"
  },
  "workspaces": [
    {
      "id": 1,
      "name": "Workspace Principal",
      "slug": "principal",
      "description": "Ambiente principal de produção",
      "role": "admin",
      "members_count": 15,
      "is_default": true,
      "created_at": "2026-03-18T16:00:00Z"
    },
    {
      "id": 2,
      "name": "Workspace de Testes",
      "slug": "testes",
      "description": "Ambiente de testes",
      "role": "admin",
      "members_count": 8,
      "is_default": false,
      "created_at": "2026-03-18T16:00:00Z"
    }
  ]
}
```

**Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": "Credenciais inválidas"
}
```

**Notas:**
- Aceita `username` ou `email` no campo username
- Senha é comparada com bcrypt
- Access token expira em 1 hora
- Refresh token expira em 7 dias

---

### 2. POST /api/auth/refresh

**Descrição:** Atualizar access token usando refresh token

**Request:**
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Refresh token inválido"
}
```

---

### 3. POST /api/auth/verify

**Descrição:** Verificar se token JWT é válido

**Request:**
```http
POST /api/auth/verify
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "valid": true,
  "user_id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_staff": true
}
```

**Response (401 Unauthorized):**
```json
{
  "valid": false,
  "error": "Token inválido: Token has expired"
}
```

---

### 4. GET /api/auth/me

**Descrição:** Obter dados do usuário autenticado

**Request:**
```http
GET /api/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "Sistema",
    "full_name": "Admin Sistema",
    "phone": "",
    "avatar": null,
    "bio": "",
    "is_staff": true,
    "is_active": true,
    "date_joined": "2026-03-18T16:00:00Z"
  },
  "workspaces": [...]
}
```

**Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": "Authentication credentials were not provided.",
  "status_code": 401
}
```

---

### 5. POST /api/auth/logout

**Descrição:** Fazer logout (blacklist do refresh token)

**Request:**
```http
POST /api/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "message": "Logout realizado com sucesso"
}
```

---

### 6. GET /api/workspaces

**Descrição:** Listar workspaces do usuário autenticado

**Request:**
```http
GET /api/workspaces
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "workspaces": [
    {
      "id": 1,
      "name": "Workspace Principal",
      "slug": "principal",
      "description": "Ambiente principal",
      "role": "admin",
      "members_count": 15,
      "is_default": true,
      "created_at": "2026-03-18T16:00:00Z"
    }
  ]
}
```

---

### 7. POST /api/workspaces/select

**Descrição:** Selecionar workspace ativo

**Request:**
```http
POST /api/workspaces/select
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "workspace_id": 1
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "workspace": {
    "id": 1,
    "name": "Workspace Principal",
    "slug": "principal",
    "description": "Ambiente principal",
    "role": "admin",
    "members_count": 15,
    "is_default": true,
    "created_at": "2026-03-18T16:00:00Z"
  }
}
```

**Response (403 Forbidden):**
```json
{
  "error": "Você não tem acesso a este workspace"
}
```

---

## AUTENTICAÇÃO

### Header Authorization

Todas as rotas protegidas requerem o header:

```http
Authorization: Bearer <access_token>
```

**Exemplo:**
```http
GET /api/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzEwNzg5NjAwLCJpYXQiOjE3MTA3ODYwMDAsImp0aSI6IjEyMzQ1Njc4OTAiLCJ1c2VyX2lkIjoxfQ.abc123
```

---

## TOKENS JWT

### Access Token

**Expiração:** 1 hora  
**Uso:** Autenticação de requests  
**Claims:**
```json
{
  "token_type": "access",
  "exp": 1710789600,
  "iat": 1710786000,
  "jti": "1234567890",
  "user_id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_staff": true
}
```

### Refresh Token

**Expiração:** 7 dias  
**Uso:** Renovar access token  
**Rotação:** Sim (novo refresh token a cada uso)  
**Blacklist:** Sim (tokens antigos são invalidados)

---

## SEGURANÇA

### Bcrypt

Senhas são hasheadas com **BCryptSHA256**:

```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
```

**Exemplo de hash:**
```
$2b$12$KIXxLVZ9qJ8YvZ9qJ8YvZ9qJ8YvZ9qJ8YvZ9qJ8YvZ9qJ8YvZ9qJ
```

### HTTPS

**⚠️ IMPORTANTE:** Em produção, usar **HTTPS** obrigatoriamente!

```python
# settings.py (produção)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### CORS

Configurado para aceitar requests de:
- `http://localhost:3000` (frontend dev)
- `http://localhost:8000` (mesmo domínio)

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
]
```

---

## TRATAMENTO DE ERROS

### Formato Padrão

Todos os erros seguem o formato:

```json
{
  "success": false,
  "error": "Mensagem de erro",
  "status_code": 400
}
```

### Códigos de Status

| Código | Significado | Exemplo |
|--------|-------------|---------|
| 200 | OK | Login bem-sucedido |
| 400 | Bad Request | Dados inválidos |
| 401 | Unauthorized | Token inválido/expirado |
| 403 | Forbidden | Sem permissão |
| 404 | Not Found | Recurso não encontrado |
| 500 | Internal Server Error | Erro no servidor |

---

## ARQUITETURA EM CAMADAS

### Controller (API Views)

```python
# apps/accounts/api_views.py
class LoginAPIView(APIView):
    def post(self, request):
        # Validar entrada
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Chamar service
        result = AuthService.login(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        
        # Retornar resposta
        return Response(result, status=200)
```

### Service (Business Logic)

```python
# apps/accounts/services.py
class AuthService:
    @staticmethod
    def login(username, password):
        # Autenticar
        user = AuthService.authenticate_user(username, password)
        
        # Gerar tokens
        tokens = AuthService.generate_tokens(user)
        
        # Buscar workspaces
        workspaces = workspace_selectors.get_workspaces_for_api(user)
        
        return {
            'token': tokens['access'],
            'refresh': tokens['refresh'],
            'user': user,
            'workspaces': workspaces
        }
```

### Selector (Repository - Read)

```python
# apps/workspaces/selectors.py
def get_workspaces_for_api(user):
    workspaces = get_user_workspaces(user)
    
    result = []
    for workspace in workspaces:
        result.append({
            'id': workspace.id,
            'name': workspace.name,
            'slug': workspace.slug,
            'role': workspace.user_membership[0].role,
            'members_count': workspace.members_count
        })
    
    return result
```

---

## EXEMPLOS DE USO

### JavaScript (Fetch API)

```javascript
// Login
async function login(username, password) {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Salvar token
    localStorage.setItem('access_token', data.token);
    localStorage.setItem('refresh_token', data.refresh);
    localStorage.setItem('user', JSON.stringify(data.user));
    localStorage.setItem('workspaces', JSON.stringify(data.workspaces));
    
    return data;
  } else {
    throw new Error(data.error);
  }
}

// Request autenticado
async function getMe() {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}

// Refresh token
async function refreshToken() {
  const refresh = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://localhost:8000/api/auth/refresh', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ refresh })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    localStorage.setItem('access_token', data.access);
    return data.access;
  } else {
    // Token expirado, fazer login novamente
    window.location.href = '/login';
  }
}
```

### Python (Requests)

```python
import requests

# Login
response = requests.post('http://localhost:8000/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})

data = response.json()
access_token = data['token']

# Request autenticado
response = requests.get('http://localhost:8000/api/auth/me', headers={
    'Authorization': f'Bearer {access_token}'
})

user_data = response.json()
```

### cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Request autenticado
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## INTEGRAÇÃO COM FRONTEND

### Atualizar authService.js

```javascript
// static/js/services/authService.js
import { api } from './api.js';

class AuthService {
  async login(username, password) {
    const result = await api.post('/api/auth/login', {
      username,
      password
    });
    
    if (result.success) {
      // Salvar tokens
      localStorage.setItem('access_token', result.data.token);
      localStorage.setItem('refresh_token', result.data.refresh);
      
      return {
        success: true,
        user: result.data.user,
        workspaces: result.data.workspaces
      };
    }
    
    return result;
  }
  
  async getUserWorkspaces() {
    const result = await api.get('/api/workspaces');
    
    if (result.success) {
      return {
        success: true,
        workspaces: result.data.workspaces
      };
    }
    
    return result;
  }
}

export const authService = new AuthService();
```

### Atualizar api.js

```javascript
// static/js/services/api.js
class API {
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
        // Tentar novamente com novo token
        options.headers['Authorization'] = `Bearer ${newToken}`;
        return await fetch(url, options);
      }
    }
    
    return response;
  }
  
  async refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return null;
    
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh })
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access);
      return data.access;
    }
    
    return null;
  }
}
```

---

## TESTES

### Testar com cURL

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.token')

echo "Token: $TOKEN"

# 2. Obter dados do usuário
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 3. Listar workspaces
curl -X GET http://localhost:8000/api/workspaces \
  -H "Authorization: Bearer $TOKEN"
```

### Testar com Postman

1. **Login:**
   - Method: POST
   - URL: `http://localhost:8000/api/auth/login`
   - Body (JSON):
     ```json
     {
       "username": "admin",
       "password": "admin123"
     }
     ```

2. **Copiar token** da resposta

3. **Request autenticado:**
   - Method: GET
   - URL: `http://localhost:8000/api/auth/me`
   - Headers:
     - Key: `Authorization`
     - Value: `Bearer <token>`

---

## CONFIGURAÇÃO

### 1. Instalar Dependências

```bash
pip install -r requirements-jwt.txt
```

### 2. Adicionar ao settings.py

```python
# No final do settings.py
from .settings_jwt import *
```

### 3. Adicionar URLs

```python
# alive_platform/urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('alive_platform.urls_api')),  # API REST
    path('', include('apps.core.urls')),
]
```

### 4. Rodar Migrations

```bash
python manage.py migrate
```

### 5. Testar

```bash
python manage.py runserver

# Em outro terminal
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

---

## RESUMO

### ✅ Implementado

- [x] Endpoint POST /api/auth/login
- [x] Validação de credenciais
- [x] Comparação de senha com bcrypt
- [x] Geração de JWT (access + refresh)
- [x] Retorno de user + workspaces
- [x] Middleware JWT
- [x] Proteção de rotas
- [x] Expiração de tokens
- [x] Tratamento de erros padronizado
- [x] Arquitetura em camadas

### 📊 Estrutura

```
Controller (API Views)
    ↓
Service (Business Logic)
    ↓
Selector (Repository - Read)
    ↓
Model (Domain)
```

### 🔐 Segurança

- ✅ Bcrypt para senhas
- ✅ JWT com expiração
- ✅ Refresh token rotation
- ✅ Token blacklist
- ✅ CORS configurado
- ✅ HTTPS ready

---

**Status:** ✅ **AUTENTICAÇÃO JWT IMPLEMENTADA**

A API REST está completa e pronta para integração com o frontend!

---

**Documento criado em:** 18 de Março de 2026  
**API de autenticação JWT implementada com sucesso.**
