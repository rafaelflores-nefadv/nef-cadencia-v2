# Checklist de Produção - NEF Cadência

**Data:** 18 de Março de 2026  
**Versão:** 1.0.0  
**Status:** 🔄 EM PREPARAÇÃO

---

## 🔐 SEGURANÇA

### Variáveis de Ambiente

- [ ] `DJANGO_SECRET_KEY` configurada (nunca commitar)
- [ ] `DB_PASSWORD` configurada
- [ ] `EMAIL_HOST_PASSWORD` configurada
- [ ] `DJANGO_ALLOWED_HOSTS` configurada
- [ ] `CORS_ALLOWED_ORIGINS` configurada
- [ ] Arquivo `.env` no `.gitignore`
- [ ] `.env.example` atualizado (sem valores reais)

### Django Settings

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` vindo de variável de ambiente
- [ ] `ALLOWED_HOSTS` configurado corretamente
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_HSTS_SECONDS` configurado
- [ ] `X_FRAME_OPTIONS = 'DENY'`

### HTTPS

- [ ] Certificado SSL instalado
- [ ] Redirect HTTP → HTTPS configurado
- [ ] HSTS habilitado
- [ ] Mixed content resolvido

### CORS

- [ ] Apenas domínios de produção permitidos
- [ ] `CORS_ALLOW_CREDENTIALS = True` se necessário
- [ ] Testar requests cross-origin

### JWT

- [ ] Tokens com expiração adequada
- [ ] Refresh token rotation habilitado
- [ ] Token blacklist habilitado
- [ ] Signing key segura

### Senhas

- [ ] Bcrypt configurado
- [ ] Política de senhas fortes
- [ ] Rate limiting em login

---

## 🗄️ BANCO DE DADOS

### PostgreSQL

- [ ] Backup automático configurado
- [ ] Connection pooling habilitado
- [ ] Índices criados
- [ ] Queries otimizadas
- [ ] Statement timeout configurado

### Migrations

- [ ] Todas as migrations aplicadas
- [ ] Migrations testadas em staging
- [ ] Rollback plan preparado

### Seed Data

- [ ] Dados iniciais criados
- [ ] Usuário admin criado
- [ ] Workspaces de exemplo criados

---

## 🚀 DEPLOY

### Servidor

- [ ] Python 3.11+ instalado
- [ ] PostgreSQL 14+ instalado
- [ ] Redis instalado (cache)
- [ ] Nginx instalado (reverse proxy)
- [ ] Supervisor/Systemd configurado (process manager)

### Aplicação

- [ ] Dependências instaladas (`requirements.txt`)
- [ ] Static files coletados (`collectstatic`)
- [ ] Migrations aplicadas
- [ ] Gunicorn/uWSGI configurado
- [ ] Workers configurados (2-4 por core)

### Nginx

- [ ] Reverse proxy configurado
- [ ] SSL/TLS configurado
- [ ] Gzip habilitado
- [ ] Static files servidos diretamente
- [ ] Rate limiting configurado

### Systemd/Supervisor

- [ ] Service file criado
- [ ] Auto-restart habilitado
- [ ] Logs configurados

---

## 📊 MONITORAMENTO

### Logs

- [ ] Logging configurado
- [ ] Rotação de logs habilitada
- [ ] Logs de erro separados
- [ ] Logs acessíveis

### Métricas

- [ ] Monitoramento de CPU/RAM
- [ ] Monitoramento de disco
- [ ] Monitoramento de banco de dados
- [ ] Alertas configurados

### Erro Tracking

- [ ] Sentry/Rollbar configurado (opcional)
- [ ] Email de erros configurado
- [ ] Erros 500 monitorados

### Performance

- [ ] APM configurado (opcional)
- [ ] Queries lentas monitoradas
- [ ] Response time monitorado

---

## 🧪 TESTES

### Backend

- [ ] Testes unitários passando
- [ ] Testes de integração passando
- [ ] Coverage > 70%
- [ ] Testes de segurança

### Frontend

- [ ] Testes E2E (opcional)
- [ ] Testes de responsividade
- [ ] Testes em diferentes navegadores
- [ ] Testes de acessibilidade

### Staging

- [ ] Deploy em staging realizado
- [ ] Testes manuais completos
- [ ] Performance testada
- [ ] Carga testada (opcional)

---

## 📁 CÓDIGO

### Limpeza

- [ ] Imports não utilizados removidos
- [ ] Arquivos não utilizados removidos
- [ ] Comentários de debug removidos
- [ ] Console.logs removidos
- [ ] TODOs resolvidos ou documentados

### Organização

- [ ] Estrutura de pastas consistente
- [ ] Nomes de arquivos consistentes
- [ ] Convenções de código seguidas
- [ ] Documentação atualizada

### Versionamento

- [ ] Git tags criadas
- [ ] CHANGELOG.md atualizado
- [ ] README.md atualizado
- [ ] Documentação versionada

---

## 🌐 FRONTEND

### Assets

- [ ] Imagens otimizadas
- [ ] CSS minificado
- [ ] JavaScript minificado
- [ ] Fonts carregados corretamente

### Performance

- [ ] Lazy loading implementado
- [ ] Code splitting (se aplicável)
- [ ] Cache de assets configurado
- [ ] CDN configurado (opcional)

### SEO

- [ ] Meta tags configuradas
- [ ] Open Graph configurado
- [ ] Sitemap.xml criado
- [ ] Robots.txt configurado

### PWA (Opcional)

- [ ] Service worker configurado
- [ ] Manifest.json criado
- [ ] Ícones configurados

---

## 📧 EMAIL

### Configuração

- [ ] SMTP configurado
- [ ] Templates de email criados
- [ ] Email de boas-vindas
- [ ] Email de reset de senha
- [ ] Email de notificações

### Testes

- [ ] Envio de emails testado
- [ ] Templates renderizando corretamente
- [ ] Links funcionando

---

## 🔄 BACKUP

### Banco de Dados

- [ ] Backup automático diário
- [ ] Backup armazenado off-site
- [ ] Restore testado
- [ ] Retenção de 30 dias

### Arquivos

- [ ] Media files com backup
- [ ] Static files com backup
- [ ] Logs com backup

---

## 📚 DOCUMENTAÇÃO

### Técnica

- [ ] README.md completo
- [ ] Guia de instalação
- [ ] Guia de deploy
- [ ] Arquitetura documentada
- [ ] API documentada

### Usuário

- [ ] Manual do usuário
- [ ] FAQ
- [ ] Tutoriais
- [ ] Vídeos (opcional)

---

## 🔧 MANUTENÇÃO

### Atualizações

- [ ] Plano de atualização de dependências
- [ ] Plano de atualização de Django
- [ ] Plano de atualização de PostgreSQL

### Suporte

- [ ] Canal de suporte definido
- [ ] SLA definido
- [ ] Equipe de suporte treinada

---

## ✅ FINAL

### Pré-Deploy

- [ ] Todos os itens acima verificados
- [ ] Staging testado completamente
- [ ] Rollback plan preparado
- [ ] Equipe notificada

### Deploy

- [ ] Deploy realizado
- [ ] Smoke tests passando
- [ ] Monitoramento ativo
- [ ] Logs sendo gerados

### Pós-Deploy

- [ ] Funcionalidades principais testadas
- [ ] Performance monitorada
- [ ] Erros monitorados
- [ ] Usuários notificados

---

## 📋 CHECKLIST RÁPIDO

```
[ ] Segurança configurada
[ ] Banco de dados pronto
[ ] Deploy configurado
[ ] Monitoramento ativo
[ ] Testes passando
[ ] Código limpo
[ ] Frontend otimizado
[ ] Email configurado
[ ] Backup configurado
[ ] Documentação completa
```

---

## 🚨 CRÍTICO (Não pode faltar)

1. ✅ `DEBUG = False`
2. ✅ `SECRET_KEY` segura
3. ✅ `ALLOWED_HOSTS` configurado
4. ✅ HTTPS habilitado
5. ✅ Backup de banco de dados
6. ✅ Logs configurados
7. ✅ Migrations aplicadas
8. ✅ Static files coletados

---

## 📞 CONTATOS DE EMERGÊNCIA

```
Desenvolvedor: [Nome] - [Email] - [Telefone]
DevOps: [Nome] - [Email] - [Telefone]
Suporte: [Email] - [Telefone]
```

---

**Status:** 🔄 **EM PREPARAÇÃO**

Completar todos os itens antes de fazer deploy em produção!

---

**Documento criado em:** 18 de Março de 2026  
**Última atualização:** 18 de Março de 2026
