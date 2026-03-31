# Script para reorganizar documentação em estrutura hierárquica
# Uso: .\scripts\reorganize_docs.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Reorganizando Documentação" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navegar para raiz do projeto
Set-Location $PSScriptRoot\..

# 1. INÍCIO RÁPIDO
Write-Host "1. Movendo documentos de Início..." -ForegroundColor Yellow
Move-Item -Force "docs\INSTALL_LINUX.md" "docs\01-inicio\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\configuracao.md" "docs\01-inicio\CONFIGURACAO.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\SETUP_DATABASE.md" "docs\01-inicio\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\VARIAVEIS_AMBIENTE.md" "docs\01-inicio\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\CONFIGURACAO_SETTINGS.md" "docs\01-inicio\" -ErrorAction SilentlyContinue

# 2. ARQUITETURA
Write-Host "2. Movendo documentos de Arquitetura..." -ForegroundColor Yellow
Move-Item -Force "docs\ARCHITECTURE.md" "docs\02-arquitetura\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\arquitetura.md" "docs\02-arquitetura\VISAO_GERAL.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\ARQUITETURA_BACKEND_DJANGO.md" "docs\02-arquitetura\BACKEND.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\ARQUITETURA_BACKEND_PROFISSIONAL.md" "docs\02-arquitetura\BACKEND_PROFISSIONAL.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\DATABASE.md" "docs\02-arquitetura\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\DATABASE_MULTITENANT.md" "docs\02-arquitetura\MULTITENANT.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\estrutura_do_projeto.md" "docs\02-arquitetura\ESTRUTURA.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\PROPOSTA_ORGANIZACAO_PASTAS.md" "docs\02-arquitetura\" -ErrorAction SilentlyContinue

# 3. MÓDULOS (mover pasta inteira)
Write-Host "3. Organizando Módulos..." -ForegroundColor Yellow
if (Test-Path "docs\modules") {
    Move-Item -Force "docs\modules\*" "docs\03-modulos\" -ErrorAction SilentlyContinue
}
Move-Item -Force "docs\assistente_ia.md" "docs\03-modulos\assistant\README.md" -ErrorAction SilentlyContinue

# 4. DESENVOLVIMENTO
Write-Host "4. Movendo documentos de Desenvolvimento..." -ForegroundColor Yellow
Move-Item -Force "docs\MANAGEMENT_COMMANDS.md" "docs\04-desenvolvimento\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\TESTES_IMPLEMENTADOS.md" "docs\04-desenvolvimento\TESTES.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\API_AUTHENTICATION.md" "docs\04-desenvolvimento\API_AUTH.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\SISTEMA_PERMISSOES.md" "docs\04-desenvolvimento\PERMISSOES.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\RBAC_SISTEMA.md" "docs\04-desenvolvimento\RBAC.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\PROTECAO_ROTAS.md" "docs\04-desenvolvimento\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\AUTH_CONTEXT_GUIA.md" "docs\04-desenvolvimento\" -ErrorAction SilentlyContinue

# 5. FRONTEND
Write-Host "5. Movendo documentos de Frontend..." -ForegroundColor Yellow
if (Test-Path "docs\frontend") {
    Move-Item -Force "docs\frontend\*" "docs\05-frontend\" -ErrorAction SilentlyContinue
}
Move-Item -Force "docs\GUIA_VISUAL_FRONTEND.md" "docs\05-frontend\GUIA_VISUAL.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\INTEGRACAO_FRONTEND_BACKEND.md" "docs\05-frontend\INTEGRACAO.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\INTEGRACAO_AUTENTICACAO_FRONTEND.md" "docs\05-frontend\INTEGRACAO_AUTH.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\REFATORACAO_NAVEGACAO.md" "docs\05-frontend\NAVEGACAO.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\REORGANIZACAO_FRONTEND.md" "docs\05-frontend\" -ErrorAction SilentlyContinue

# 6. DEPLOY
Write-Host "6. Movendo documentos de Deploy..." -ForegroundColor Yellow
Move-Item -Force "docs\DEPLOYMENT.md" "docs\06-deploy\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\deploy.md" "docs\06-deploy\GUIA_RAPIDO.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\DEPLOY_VPS.md" "docs\06-deploy\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\FLUXO_DEPLOY.md" "docs\06-deploy\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\CHECKLIST_PRODUCAO.md" "docs\06-deploy\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\POLITICA_SEGREDOS.md" "docs\06-deploy\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\ARQUIVOS_NAO_DEPLOY.md" "docs\06-deploy\" -ErrorAction SilentlyContinue

# 7. MELHORIAS
Write-Host "7. Movendo documentos de Melhorias..." -ForegroundColor Yellow
Move-Item -Force "docs\MELHORIAS_VISUAL_E_DADOS_FICTICIOS.md" "docs\07-melhorias\VISUAL_E_MOCK_DATA.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\PLANO_REFATORACAO.md" "docs\07-melhorias\PLANO_REFATORACAO.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\REORGANIZACAO_IMPLEMENTADA.md" "docs\07-melhorias\REFATORACOES.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\RESUMO_IMPLEMENTACAO_BACKEND.md" "docs\07-melhorias\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\LIMPEZA_TECNICA.md" "docs\07-melhorias\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\ESTRUTURA_FINAL.md" "docs\07-melhorias\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\CONFIGURACOES_IMPLEMENTADAS.md" "docs\07-melhorias\" -ErrorAction SilentlyContinue

# 8. ANÁLISES
Write-Host "8. Movendo documentos de Análises..." -ForegroundColor Yellow
Move-Item -Force "docs\ANALISE_COMPLETA_PROJETO.md" "docs\08-analises\ANALISE_COMPLETA.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\DIAGNOSTICO_TECNICO.md" "docs\08-analises\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\AUDITORIA_PRODUCAO.md" "docs\08-analises\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\RISCOS_QUEBRA.md" "docs\08-analises\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\ARQUIVOS_PRIORIDADE.md" "docs\08-analises\" -ErrorAction SilentlyContinue

# Outros documentos técnicos
Write-Host "9. Organizando documentos técnicos..." -ForegroundColor Yellow
Move-Item -Force "docs\SYNC.md" "docs\04-desenvolvimento\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\INTEGRATIONS.md" "docs\03-modulos\integrations\README.md" -ErrorAction SilentlyContinue
Move-Item -Force "docs\BACKEND_CONFIGURACOES_REAL.md" "docs\02-arquitetura\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\SETTINGS_MIGRATION_SUMMARY.md" "docs\07-melhorias\" -ErrorAction SilentlyContinue
Move-Item -Force "docs\MULTI_TENANT_FLUXO.md" "docs\02-arquitetura\" -ErrorAction SilentlyContinue

# Mover pasta API se existir
if (Test-Path "docs\api") {
    Move-Item -Force "docs\api\*" "docs\04-desenvolvimento\api\" -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Reorganização Concluída!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Estrutura criada:" -ForegroundColor Cyan
Write-Host "  docs/" -ForegroundColor White
Write-Host "    01-inicio/         - Instalação e configuração inicial" -ForegroundColor Gray
Write-Host "    02-arquitetura/    - Estrutura e design do sistema" -ForegroundColor Gray
Write-Host "    03-modulos/        - Documentação por módulo" -ForegroundColor Gray
Write-Host "    04-desenvolvimento/- Guias para desenvolvedores" -ForegroundColor Gray
Write-Host "    05-frontend/       - Interface e UX" -ForegroundColor Gray
Write-Host "    06-deploy/         - Implantação e produção" -ForegroundColor Gray
Write-Host "    07-melhorias/      - Atualizações e refatorações" -ForegroundColor Gray
Write-Host "    08-analises/       - Diagnósticos e auditorias" -ForegroundColor Gray
Write-Host ""
Write-Host "Próximo passo: Revisar docs/README.md" -ForegroundColor Yellow
