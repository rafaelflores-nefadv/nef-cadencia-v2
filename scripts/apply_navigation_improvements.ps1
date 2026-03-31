# Script para aplicar melhorias de navegação e Eustácio v3.2
# Uso: .\scripts\apply_navigation_improvements.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEF Cadencia - Melhorias v3.2" -ForegroundColor Cyan
Write-Host "Navegação + Assistente Eustácio" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Navegar para raiz do projeto
Set-Location $PSScriptRoot\..

Write-Host "Melhorias disponíveis:" -ForegroundColor Yellow
Write-Host "1. Nova interface do Assistente Eustácio" -ForegroundColor White
Write-Host "   - Ícones Lucide em todos os elementos" -ForegroundColor Gray
Write-Host "   - Avatares para usuário e bot" -ForegroundColor Gray
Write-Host "   - Breadcrumb de navegação" -ForegroundColor Gray
Write-Host "   - Feedback visual melhorado" -ForegroundColor Gray
Write-Host "   - 5 sugestões de perguntas" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Componentes de navegação reutilizáveis" -ForegroundColor White
Write-Host "   - Breadcrumb (_breadcrumb.html)" -ForegroundColor Gray
Write-Host "   - Page Header (_page_header.html)" -ForegroundColor Gray
Write-Host ""

# Menu de opções
Write-Host "Escolha uma opção:" -ForegroundColor Cyan
Write-Host "1) Aplicar nova interface do Eustácio" -ForegroundColor White
Write-Host "2) Apenas criar componentes de navegação" -ForegroundColor White
Write-Host "3) Aplicar TUDO (recomendado)" -ForegroundColor White
Write-Host "4) Reverter Eustácio para original" -ForegroundColor White
Write-Host "0) Sair" -ForegroundColor White
Write-Host ""

$option = Read-Host "Opção"

switch ($option) {
    "1" {
        Write-Host ""
        Write-Host "Aplicando nova interface do Eustácio..." -ForegroundColor Yellow
        
        # Backup
        if (-not (Test-Path "templates\assistant\page.html.backup")) {
            Copy-Item "templates\assistant\page.html" "templates\assistant\page.html.backup"
            Write-Host "✓ Backup criado: page.html.backup" -ForegroundColor Green
        }
        
        # Aplicar
        if (Test-Path "templates\assistant\page_improved.html") {
            Copy-Item "templates\assistant\page_improved.html" "templates\assistant\page.html" -Force
            Write-Host "✓ Nova interface aplicada!" -ForegroundColor Green
            Write-Host ""
            Write-Host "Melhorias aplicadas:" -ForegroundColor Cyan
            Write-Host "  • Breadcrumb de navegação" -ForegroundColor White
            Write-Host "  • Avatares para usuário/bot" -ForegroundColor White
            Write-Host "  • Ícones Lucide em tudo" -ForegroundColor White
            Write-Host "  • 5 sugestões de perguntas" -ForegroundColor White
            Write-Host "  • Feedback visual melhorado" -ForegroundColor White
            Write-Host "  • Dicas de uso" -ForegroundColor White
        } else {
            Write-Host "✗ Arquivo page_improved.html não encontrado!" -ForegroundColor Red
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "Componentes já criados em templates/components/:" -ForegroundColor Green
        Write-Host "  ✓ _breadcrumb.html" -ForegroundColor White
        Write-Host "  ✓ _page_header.html" -ForegroundColor White
        Write-Host "  ✓ _config_card.html" -ForegroundColor White
        Write-Host "  ✓ _section_header.html" -ForegroundColor White
        Write-Host "  ✓ _stat_grid.html" -ForegroundColor White
        Write-Host ""
        Write-Host "Use-os em seus templates com:" -ForegroundColor Yellow
        Write-Host "  {% include 'components/_breadcrumb.html' with items=breadcrumb_items %}" -ForegroundColor Gray
    }
    
    "3" {
        Write-Host ""
        Write-Host "Aplicando TODAS as melhorias..." -ForegroundColor Yellow
        Write-Host ""
        
        # Backup
        Write-Host "1. Criando backups..." -ForegroundColor Cyan
        if (-not (Test-Path "templates\assistant\page.html.backup")) {
            Copy-Item "templates\assistant\page.html" "templates\assistant\page.html.backup"
            Write-Host "   ✓ Backup: page.html" -ForegroundColor Green
        }
        
        # Aplicar Eustácio
        Write-Host ""
        Write-Host "2. Aplicando nova interface do Eustácio..." -ForegroundColor Cyan
        if (Test-Path "templates\assistant\page_improved.html") {
            Copy-Item "templates\assistant\page_improved.html" "templates\assistant\page.html" -Force
            Write-Host "   ✓ Interface do Eustácio atualizada" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✓ Todas as melhorias aplicadas!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Resumo das mudanças:" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Assistente Eustácio:" -ForegroundColor Yellow
        Write-Host "  • Breadcrumb de navegação" -ForegroundColor White
        Write-Host "  • Avatares coloridos (user/bot)" -ForegroundColor White
        Write-Host "  • Ícones Lucide em todos os elementos" -ForegroundColor White
        Write-Host "  • 5 sugestões de perguntas com ícones" -ForegroundColor White
        Write-Host "  • Indicador 'pensando' mais visível" -ForegroundColor White
        Write-Host "  • Radar operacional com checklist" -ForegroundColor White
        Write-Host "  • Dicas de uso" -ForegroundColor White
        Write-Host ""
        Write-Host "Componentes Criados:" -ForegroundColor Yellow
        Write-Host "  • _breadcrumb.html (navegação)" -ForegroundColor White
        Write-Host "  • _page_header.html (cabeçalho + voltar)" -ForegroundColor White
        Write-Host "  • _config_card.html (cards de config)" -ForegroundColor White
        Write-Host "  • _section_header.html (seções)" -ForegroundColor White
        Write-Host "  • _stat_grid.html (estatísticas)" -ForegroundColor White
        Write-Host ""
        Write-Host "Próximos passos:" -ForegroundColor Yellow
        Write-Host "1. Reiniciar servidor: python manage.py runserver 0.0.0.0:10100" -ForegroundColor White
        Write-Host "2. Acessar Eustácio: http://192.168.200.8:10100/assistant" -ForegroundColor White
        Write-Host "3. Testar nova interface e navegação" -ForegroundColor White
        Write-Host "4. Verificar se responde múltiplas perguntas" -ForegroundColor White
        Write-Host ""
    }
    
    "4" {
        Write-Host ""
        Write-Host "Revertendo Eustácio para original..." -ForegroundColor Yellow
        
        if (Test-Path "templates\assistant\page.html.backup") {
            Copy-Item "templates\assistant\page.html.backup" "templates\assistant\page.html" -Force
            Write-Host "✓ Eustácio restaurado para versão original" -ForegroundColor Green
        } else {
            Write-Host "✗ Backup não encontrado!" -ForegroundColor Red
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
Write-Host ""
Write-Host "Documentação completa em:" -ForegroundColor Yellow
Write-Host "  docs/07-melhorias/MELHORIAS_NAVEGACAO_E_EUSTACIO.md" -ForegroundColor White
