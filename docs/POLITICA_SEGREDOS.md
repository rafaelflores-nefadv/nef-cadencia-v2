# Política de Gestão de Segredos - NEF Cadência

**Versão:** 1.0  
**Data:** 18 de Março de 2026  
**Status:** Obrigatório para Produção

---

## 1. VISÃO GERAL

Este documento define as políticas e procedimentos para gestão segura de segredos (secrets) no projeto NEF Cadência, incluindo chaves de API, credenciais de banco de dados, tokens de autenticação e outras informações sensíveis.

### Definições

- **Segredo (Secret):** Qualquer informação sensível que, se exposta, pode comprometer a segurança do sistema
- **Credencial:** Par usuário/senha ou token de autenticação
- **Chave de API:** Token de acesso a serviços externos
- **Ambiente:** Contexto de execução (desenvolvimento, staging, produção)

---

## 2. CLASSIFICAÇÃO DE SEGREDOS

### 🔴 CRÍTICOS (Nível 1)

Exposição causa comprometimento total do sistema.

**Segredos:**
- `SECRET_KEY` - Chave secreta do Django
- `DB_PASSWORD` - Senha do banco de dados principal
- `OPENAI_API_KEY` - Chave de API da OpenAI
- Chaves privadas SSL/TLS
- Tokens de autenticação de produção

**Requisitos:**
- ✅ NUNCA commitar no git
- ✅ Rotação obrigatória a cada 90 dias
- ✅ Armazenamento em secrets manager
- ✅ Acesso restrito (apenas ops/admin)
- ✅ Auditoria de acesso
- ✅ Criptografia em repouso

### 🟠 SENSÍVEIS (Nível 2)

Exposição causa comprometimento parcial ou vazamento de dados.

**Segredos:**
- `EMAIL_HOST_PASSWORD` - Senha SMTP
- `LEGACY_PASSWORD` - Senha do banco legado
- `REDIS_URL` (se contém senha)
- Tokens de integrações externas

**Requisitos:**
- ✅ NUNCA commitar no git
- ✅ Rotação recomendada a cada 180 dias
- ✅ Armazenamento seguro
- ✅ Acesso controlado
- ✅ Logs de uso

### 🟡 CONFIGURAÇÕES (Nível 3)

Informações de configuração que podem facilitar ataques.

**Segredos:**
- `DB_HOST` - Hostname do banco de dados
- `DB_USER` - Usuário do banco de dados
- `ALLOWED_HOSTS` - Domínios permitidos
- `EMAIL_HOST` - Servidor SMTP

**Requisitos:**
- ✅ Não commitar valores de produção
- ✅ Pode estar em .env.example (valores genéricos)
- ✅ Documentação adequada

### 🟢 PÚBLICOS (Nível 4)

Informações não sensíveis.

**Exemplos:**
- `DJANGO_ENV` - Ambiente de execução
- `DEBUG` - Flag de debug (sempre False em prod)
- `LANGUAGE_CODE` - Idioma padrão
- `TIME_ZONE` - Fuso horário

**Requisitos:**
- ✅ Pode estar em código-fonte
- ✅ Pode estar em .env.example

---

## 3. ARMAZENAMENTO DE SEGREDOS

### 3.1 Desenvolvimento Local

**Método:** Arquivo `.env` local

```bash
# Criar .env a partir do template
cp .env.example .env

# Restringir permissões (Linux/Mac)
chmod 600 .env

# Editar com valores de desenvolvimento
nano .env
```

**Regras:**
- ✅ Usar valores de desenvolvimento/teste
- ✅ NUNCA usar valores de produção
- ✅ Arquivo `.env` NUNCA deve ser commitado
- ✅ Manter `.env.example` atualizado (sem valores reais)

### 3.2 Produção

**Método Recomendado:** Secrets Manager

#### Opção 1: AWS Secrets Manager (Recomendado)

```python
# settings/production.py
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Carregar secrets
secrets = get_secret('nef-cadencia/production')
SECRET_KEY = secrets['SECRET_KEY']
DB_PASSWORD = secrets['DB_PASSWORD']
OPENAI_API_KEY = secrets['OPENAI_API_KEY']
```

#### Opção 2: HashiCorp Vault

```python
import hvac

client = hvac.Client(url='https://vault.example.com')
client.auth.approle.login(role_id='...', secret_id='...')

secrets = client.secrets.kv.v2.read_secret_version(path='nef-cadencia/prod')
SECRET_KEY = secrets['data']['data']['SECRET_KEY']
```

#### Opção 3: Variáveis de Ambiente do Sistema (Mínimo Aceitável)

```bash
# /etc/environment ou systemd service
export SECRET_KEY="..."
export DB_PASSWORD="..."
```

**Regras de Produção:**
- ✅ NUNCA usar arquivo `.env` em produção
- ✅ Usar secrets manager sempre que possível
- ✅ Se usar variáveis de ambiente, configurar no systemd/supervisor
- ✅ Restringir acesso ao servidor
- ✅ Habilitar auditoria de acesso

### 3.3 Staging/QA

**Método:** Variáveis de ambiente ou secrets manager

**Regras:**
- ✅ Usar secrets separados de produção
- ✅ Rotação menos frequente (180 dias)
- ✅ Pode usar valores de teste para integrações

---

## 4. GERAÇÃO DE SEGREDOS

### 4.1 SECRET_KEY (Django)

**Requisitos:**
- Mínimo 50 caracteres
- Caracteres aleatórios
- Único por ambiente

**Geração:**

```bash
# Método 1: Django
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Método 2: Python secrets
python -c 'import secrets; print(secrets.token_urlsafe(50))'

# Método 3: OpenSSL
openssl rand -base64 50
```

**Exemplo de saída:**
```
django-insecure-8k#2p9$x@m5n&q7w!e3r4t5y6u7i8o9p0a1s2d3f4g5h6j7k8l9
```

### 4.2 Senhas de Banco de Dados

**Requisitos:**
- Mínimo 16 caracteres
- Letras maiúsculas e minúsculas
- Números
- Símbolos especiais
- Sem palavras do dicionário

**Geração:**

```bash
# Método 1: OpenSSL (recomendado)
openssl rand -base64 32

# Método 2: Python
python -c 'import secrets, string; chars = string.ascii_letters + string.digits + "!@#$%^&*"; print("".join(secrets.choice(chars) for _ in range(24)))'

# Método 3: pwgen (se instalado)
pwgen -s 24 1
```

**Exemplo de saída:**
```
Kj8#mP2$nQ9@xR5!wE7&tY3
```

### 4.3 Chaves de API

**OpenAI:**
- Obter em: https://platform.openai.com/api-keys
- Formato: `sk-...`
- Configurar limites de uso
- Usar chaves diferentes por ambiente

**Outras APIs:**
- Seguir documentação do provedor
- Sempre usar chaves de produção separadas
- Configurar IP whitelisting quando disponível

---

## 5. ROTAÇÃO DE SEGREDOS

### 5.1 Cronograma de Rotação

| Segredo | Frequência | Responsável |
|---------|-----------|-------------|
| SECRET_KEY | 90 dias | DevOps |
| DB_PASSWORD | 90 dias | DBA/DevOps |
| OPENAI_API_KEY | 180 dias | DevOps |
| EMAIL_HOST_PASSWORD | 180 dias | DevOps |
| LEGACY_PASSWORD | 180 dias | DevOps |
| SSL Certificates | 365 dias | DevOps |

### 5.2 Processo de Rotação

#### Passo 1: Gerar Novo Segredo

```bash
# Gerar novo SECRET_KEY
NEW_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
echo "Novo SECRET_KEY: $NEW_SECRET_KEY"
```

#### Passo 2: Atualizar Secrets Manager

```bash
# AWS Secrets Manager
aws secretsmanager update-secret \
    --secret-id nef-cadencia/production \
    --secret-string "{\"SECRET_KEY\":\"$NEW_SECRET_KEY\"}"
```

#### Passo 3: Reiniciar Aplicação

```bash
# Systemd
sudo systemctl restart nef-cadencia

# Docker
docker-compose restart web

# Kubernetes
kubectl rollout restart deployment/nef-cadencia
```

#### Passo 4: Validar

```bash
# Verificar que aplicação iniciou corretamente
curl https://seu-dominio.com/health/

# Verificar logs
tail -f /var/log/nef-cadencia/django.log
```

#### Passo 5: Revogar Segredo Antigo

```bash
# Aguardar 24-48h para garantir que não há problemas
# Depois, remover/revogar o segredo antigo
```

### 5.3 Rotação de Emergência

Em caso de comprometimento:

1. **Imediato (< 1 hora):**
   - Gerar novos segredos
   - Atualizar produção
   - Reiniciar aplicação
   - Revogar segredos comprometidos

2. **Curto Prazo (< 24 horas):**
   - Investigar escopo do comprometimento
   - Revisar logs de acesso
   - Notificar stakeholders
   - Documentar incidente

3. **Médio Prazo (< 1 semana):**
   - Implementar controles adicionais
   - Revisar políticas de segurança
   - Treinar equipe

---

## 6. CONTROLE DE ACESSO

### 6.1 Quem Pode Acessar Segredos

| Segredo | Desenvolvimento | Staging | Produção |
|---------|----------------|---------|----------|
| SECRET_KEY | Todos devs | DevOps | DevOps Lead |
| DB_PASSWORD | Todos devs | DevOps | DBA/DevOps Lead |
| OPENAI_API_KEY | Todos devs | DevOps | DevOps Lead |
| EMAIL_PASSWORD | Todos devs | DevOps | DevOps |

### 6.2 Princípio do Menor Privilégio

- Desenvolvedores: Acesso apenas a segredos de desenvolvimento
- DevOps: Acesso a staging e produção (com aprovação)
- DevOps Lead: Acesso total (com auditoria)

### 6.3 Auditoria de Acesso

**Registrar:**
- Quem acessou
- Quando acessou
- Qual segredo
- De onde (IP)
- Motivo (ticket/issue)

**Ferramentas:**
- AWS CloudTrail (para AWS Secrets Manager)
- Vault Audit Log (para HashiCorp Vault)
- Logs do sistema operacional

---

## 7. VALIDAÇÃO E DETECÇÃO

### 7.1 Validação no Startup

O sistema valida segredos críticos no startup (implementado em `production.py`):

```python
# Validações automáticas:
✅ SECRET_KEY não é valor padrão
✅ SECRET_KEY tem mínimo 50 caracteres
✅ ALLOWED_HOSTS não contém localhost
✅ DB_PASSWORD está definido
✅ OPENAI_API_KEY tem formato correto (sk-...)
```

### 7.2 Detecção de Vazamento

**Git Hooks (Pre-commit):**

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Detectar segredos em commits
if git diff --cached | grep -E "(SECRET_KEY|PASSWORD|API_KEY|TOKEN)" | grep -v "example"; then
    echo "❌ ERRO: Possível segredo detectado no commit!"
    echo "Revise as alterações antes de commitar."
    exit 1
fi
```

**Ferramentas Recomendadas:**
- [git-secrets](https://github.com/awslabs/git-secrets)
- [truffleHog](https://github.com/trufflesecurity/trufflehog)
- [detect-secrets](https://github.com/Yelp/detect-secrets)

**GitHub/GitLab:**
- Habilitar secret scanning
- Configurar alertas de segurança
- Revisar periodicamente

### 7.3 Monitoramento

**Alertas:**
- Tentativas de acesso não autorizado
- Falhas de autenticação repetidas
- Uso anormal de API keys
- Acesso de IPs não reconhecidos

---

## 8. RESPOSTA A INCIDENTES

### 8.1 Segredo Commitado no Git

**Ação Imediata:**

```bash
# 1. Revogar segredo imediatamente
# 2. Gerar novo segredo
# 3. Atualizar produção

# 4. Remover do git (se commit recente)
git reset --soft HEAD~1
git reset HEAD arquivo-com-segredo
git checkout -- arquivo-com-segredo

# 5. Se já foi pushed, reescrever histórico
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch arquivo-com-segredo' \
  --prune-empty --tag-name-filter cat -- --all

# 6. Force push (CUIDADO!)
git push origin --force --all
```

**Ação Subsequente:**
- Notificar equipe
- Documentar incidente
- Revisar processo
- Implementar controles adicionais

### 8.2 Segredo Exposto Publicamente

**Severidade: CRÍTICA**

1. **Imediato (< 15 minutos):**
   - Revogar segredo
   - Gerar novo
   - Atualizar produção
   - Remover exposição pública

2. **Curto Prazo (< 1 hora):**
   - Revisar logs de acesso
   - Identificar uso não autorizado
   - Bloquear IPs suspeitos
   - Notificar stakeholders

3. **Médio Prazo (< 24 horas):**
   - Análise forense completa
   - Relatório de incidente
   - Plano de remediação
   - Comunicação externa (se necessário)

---

## 9. CHECKLIST DE SEGURANÇA

### Desenvolvimento

- [ ] `.env` está no `.gitignore`
- [ ] `.env.example` não contém valores reais
- [ ] Valores de desenvolvimento são diferentes de produção
- [ ] Pre-commit hooks configurados
- [ ] Documentação atualizada

### Deploy

- [ ] Segredos de produção gerados
- [ ] Segredos armazenados em secrets manager
- [ ] Validações de startup passando
- [ ] Acesso restrito configurado
- [ ] Auditoria habilitada
- [ ] Backup de segredos (criptografado)
- [ ] Plano de rotação documentado

### Operação

- [ ] Rotação agendada
- [ ] Monitoramento ativo
- [ ] Alertas configurados
- [ ] Logs sendo revisados
- [ ] Equipe treinada
- [ ] Plano de resposta a incidentes atualizado

---

## 10. FERRAMENTAS E RECURSOS

### Gestão de Segredos

- **AWS Secrets Manager:** https://aws.amazon.com/secrets-manager/
- **HashiCorp Vault:** https://www.vaultproject.io/
- **Azure Key Vault:** https://azure.microsoft.com/en-us/services/key-vault/
- **Google Secret Manager:** https://cloud.google.com/secret-manager

### Detecção de Vazamento

- **git-secrets:** https://github.com/awslabs/git-secrets
- **truffleHog:** https://github.com/trufflesecurity/trufflehog
- **GitGuardian:** https://www.gitguardian.com/

### Geração de Segredos

- **1Password:** https://1password.com/
- **LastPass:** https://www.lastpass.com/
- **KeePass:** https://keepass.info/

---

## 11. RESPONSABILIDADES

| Papel | Responsabilidades |
|-------|------------------|
| **Desenvolvedor** | - Nunca commitar segredos<br>- Usar .env local<br>- Reportar vazamentos |
| **DevOps** | - Gerenciar segredos de staging/prod<br>- Implementar rotação<br>- Monitorar acessos |
| **DevOps Lead** | - Aprovar acessos<br>- Revisar políticas<br>- Responder a incidentes |
| **DBA** | - Gerenciar senhas de banco<br>- Implementar rotação de DB<br>- Auditoria de acesso |
| **Security** | - Revisar políticas<br>- Auditorias periódicas<br>- Treinamento da equipe |

---

## 12. TREINAMENTO

### Onboarding de Novos Desenvolvedores

1. Ler esta política completa
2. Configurar .env local
3. Instalar git-secrets
4. Revisar .gitignore
5. Quiz de segurança (aprovação obrigatória)

### Treinamento Anual

- Revisão de políticas
- Simulação de incidentes
- Atualização de procedimentos
- Certificação de segurança

---

## 13. REVISÃO E ATUALIZAÇÃO

**Frequência:** Trimestral

**Responsável:** DevOps Lead + Security

**Processo:**
1. Revisar incidentes do trimestre
2. Avaliar eficácia das políticas
3. Incorporar novas ameaças
4. Atualizar documentação
5. Comunicar mudanças à equipe

---

## ANEXOS

### Anexo A: Template de .env para Produção

Ver: `.env.example`

### Anexo B: Comandos de Geração de Segredos

Ver: Seção 4 deste documento

### Anexo C: Processo de Rotação Detalhado

Ver: Seção 5 deste documento

### Anexo D: Plano de Resposta a Incidentes

Ver: Seção 8 deste documento

---

**Última Atualização:** 18 de Março de 2026  
**Versão:** 1.0  
**Aprovado por:** DevOps Lead  
**Próxima Revisão:** Junho de 2026
