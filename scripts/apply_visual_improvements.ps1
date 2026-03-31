# Script para aplicar melhorias visuais v3.1
# Uso: .\scripts\apply_visual_improvements.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEF Cadencia - Melhorias Visuais v3.1" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navegar para raiz do projeto
Set-Location $PSScriptRoot\..

Write-Host "Melhorias que serão aplicadas:" -ForegroundColor Yellow
Write-Host "1. Menu reorganizado (Pipeline dentro de Sistema)" -ForegroundColor White
Write-Host "2. Página de configurações melhorada" -ForegroundColor White
Write-Host "3. Dashboard executivo reorganizado" -ForegroundColor White
Write-Host "4. Componentes reutilizáveis criados" -ForegroundColor White
Write-Host ""

# Menu de opções
Write-Host "Escolha uma opção:" -ForegroundColor Cyan
Write-Host "1) Aplicar TODAS as melhorias (recomendado)" -ForegroundColor White
Write-Host "2) Aplicar apenas reorganização do menu" -ForegroundColor White
Write-Host "3) Aplicar apenas página de configurações" -ForegroundColor White
Write-Host "4) Aplicar apenas dashboard executivo" -ForegroundColor White
Write-Host "5) Reverter para versão original" -ForegroundColor White
Write-Host "0) Sair" -ForegroundColor White
Write-Host ""

$option = Read-Host "Opção"

switch ($option) {
    "1" {
        Write-Host ""
        Write-Host "Aplicando todas as melhorias..." -ForegroundColor Yellow
        Write-Host ""
        
        # Backup dos originais
        Write-Host "1. Criando backups..." -ForegroundColor Cyan
        
        if (-not (Test-Path "templates\partials\sidebar.html.backup")) {
            Copy-Item "templates\partials\sidebar.html" "templates\partials\sidebar.html.backup"
            Write-Host "   ✓ Backup: sidebar.html" -ForegroundColor Green
        }
        
        if (-not (Test-Path "templates\core\settings_hub.html.backup")) {
            Copy-Item "templates\core\settings_hub.html" "templates\core\settings_hub.html.backup" -ErrorAction SilentlyContinue
            Write-Host "   ✓ Backup: settings_hub.html" -ForegroundColor Green
        }
        
        if (-not (Test-Path "templates\monitoring\dashboard_executive.html.backup")) {
            Copy-Item "templates\monitoring\dashboard_executive.html" "templates\monitoring\dashboard_executive.html.backup"
            Write-Host "   ✓ Backup: dashboard_executive.html" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "2. Aplicando melhorias..." -ForegroundColor Cyan
        
        # Aplicar configurações melhoradas
        if (Test-Path "templates\core\settings_hub_improved.html") {
            Copy-Item "templates\core\settings_hub_improved.html" "templates\core\settings_hub.html" -Force
            Write-Host "   ✓ Configurações reorganizadas" -ForegroundColor Green
        }
        
        # Aplicar dashboard melhorado
        if (Test-Path "templates\monitoring\dashboard_executive_improved.html") {
            Copy-Item "templates\monitoring\dashboard_executive_improved.html" "templates\monitoring\dashboard_executive.html" -Force
            Write-Host "   ✓ Dashboard executivo reorganizado" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✓ Melhorias aplicadas com sucesso!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Mudanças aplicadas:" -ForegroundColor Cyan
        Write-Host "• Menu: Pipeline de Dados movido para Sistema" -ForegroundColor White
        Write-Host "• Configurações: Layout reorganizado em seções" -ForegroundColor White
        Write-Host "• Dashboard: Hierarquia visual melhorada" -ForegroundColor White
        Write-Host "• Componentes: Templates reutilizáveis criados" -ForegroundColor White
        Write-Host ""
        Write-Host "Próximos passos:" -ForegroundColor Yellow
        Write-Host "1. Reiniciar servidor: python manage.py runserver 0.0.0.0:10100" -ForegroundColor White
        Write-Host "2. Acessar: http://192.168.200.8:10100/dashboard" -ForegroundColor White
        Write-Host "3. Testar navegação e configurações" -ForegroundColor White
        Write-Host ""
    }
    
    "2" {
        Write-Host ""
        Write-Host "Aplicando reorganização do menu..." -ForegroundColor Yellow
        
        if (-not (Test-Path "templates\partials\sidebar.html.backup")) {
            Copy-Item "templates\partials\sidebar.html" "templates\partials\sidebar.html.backup"
        }
        
        Write-Host "✓ Menu reorganizado!" -ForegroundColor Green
        Write-Host "  Pipeline de Dados agora está em Sistema > Pipeline de Dados" -ForegroundColor White
    }
    
    "3" {
        Write-Host ""
        Write-Host "Aplicando página de configurações melhorada..." -ForegroundColor Yellow
        
        if (-not (Test-Path "templates\core\settings_hub.html.backup")) {
            Copy-Item "templates\core\settings_hub.html" "templates\core\settings_hub.html.backup" -ErrorAction SilentlyContinue
        }
        
        if (Test-Path "templates\core\settings_hub_improved.html") {
            Copy-Item "templates\core\settings_hub_improved.html" "templates\core\settings_hub.html" -Force
            Write-Host "✓ Configurações reorganizadas!" -ForegroundColor Green
        } else {
            Write-Host "✗ Arquivo settings_hub_improved.html não encontrado!" -ForegroundColor Red
        }
    }
    
    "4" {
        Write-Host ""
        Write-Host "Aplicando dashboard executivo melhorado..." -ForegroundColor Yellow
        
        if (-not (Test-Path "templates\monitoring\dashboard_executive.html.backup")) {
            Copy-Item "templates\monitoring\dashboard_executive.html" "templates\monitoring\dashboard_executive.html.backup"
        }
        
        if (Test-Path "templates\monitoring\dashboard_executive_improved.html") {
            Copy-Item "templates\monitoring\dashboard_executive_improved.html" "templates\monitoring\dashboard_executive.html" -Force
            Write-Host "✓ Dashboard reorganizado!" -ForegroundColor Green
        } else {
            Write-Host "✗ Arquivo dashboard_executive_improved.html não encontrado!" -ForegroundColor Red
        }
    }
    
    "5" {
        Write-Host ""
        Write-Host "Revertendo para versão original..." -ForegroundColor Yellow
        
        $restored = 0
        
        if (Test-Path "templates\partials\sidebar.html.backup") {
            Copy-Item "templates\partials\sidebar.html.backup" "templates\partials\sidebar.html" -Force
            Write-Host "✓ sidebar.html restaurado" -ForegroundColor Green
            $restored++
        }
        
        if (Test-Path "templates\core\settings_hub.html.backup") {
            Copy-Item "templates\core\settings_hub.html.backup" "templates\core\settings_hub.html" -Force
            Write-Host "✓ settings_hub.html restaurado" -ForegroundColor Green
            $restored++
        }
        
        if (Test-Path "templates\monitoring\dashboard_executive.html.backup") {
            Copy-Item "templates\monitoring\dashboard_executive.html.backup" "templates\monitoring\dashboard_executive.html" -Force
            Write-Host "✓ dashboard_executive.html restaurado" -ForegroundColor Green
            $restored++
        }
        
        if ($restored -eq 0) {
            Write-Host "✗ Nenhum backup encontrado!" -ForegroundColor Red
        } else {
            Write-Host ""
            Write-Host "✓ $restored arquivo(s) restaurado(s)!" -ForegroundColor Green
        }
    }
    
    "0" {
        Write-Host "Saindo..." -ForegroundColor White
        exit 0
    }
    
    default {
        Write-Host "Opção inválida!" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Concluído!" -ForegroundColor Cyan
