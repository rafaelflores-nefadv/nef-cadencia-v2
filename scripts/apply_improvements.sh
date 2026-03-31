#!/bin/bash
# Script para aplicar melhorias visuais e configurar dados fictícios
# Uso: bash scripts/apply_improvements.sh

set -e

echo "=========================================="
echo "NEF Cadencia - Aplicação de Melhorias"
echo "=========================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar se está no diretório correto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Erro: Execute este script da raiz do projeto!${NC}"
    exit 1
fi

# Verificar se venv está ativado
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Ativando ambiente virtual...${NC}"
    source venv/bin/activate
fi

echo -e "${GREEN}✓${NC} Ambiente virtual ativado"
echo ""

# Menu de opções
echo "Escolha uma opção:"
echo "1) Aplicar novo layout visual (recomendado)"
echo "2) Gerar dados fictícios para teste"
echo "3) Aplicar layout + gerar dados (completo)"
echo "4) Reverter para layout original"
echo "5) Limpar dados fictícios"
echo "0) Sair"
echo ""
read -p "Opção: " option

case $option in
    1)
        echo ""
        echo -e "${YELLOW}Aplicando novo layout...${NC}"
        
        # Backup do original
        if [ ! -f "templates/monitoring/dashboard_executive_backup.html" ]; then
            cp templates/monitoring/dashboard_executive.html templates/monitoring/dashboard_executive_backup.html
            echo -e "${GREEN}✓${NC} Backup criado: dashboard_executive_backup.html"
        fi
        
        # Aplicar novo layout
        cp templates/monitoring/dashboard_executive_improved.html templates/monitoring/dashboard_executive.html
        echo -e "${GREEN}✓${NC} Novo layout aplicado!"
        echo ""
        echo "Reinicie o servidor para ver as mudanças:"
        echo "  python manage.py runserver 0.0.0.0:10100"
        ;;
        
    2)
        echo ""
        echo -e "${YELLOW}Gerando dados fictícios...${NC}"
        echo ""
        read -p "Quantos dias? (padrão: 7): " days
        days=${days:-7}
        
        read -p "Limpar dados fictícios existentes? (s/N): " clear_data
        
        cmd="python manage.py generate_mock_data --days $days"
        
        if [[ $clear_data == "s" || $clear_data == "S" ]]; then
            cmd="$cmd --clear"
        fi
        
        echo ""
        echo "Executando: $cmd"
        echo ""
        $cmd
        
        echo ""
        echo -e "${GREEN}✓${NC} Dados fictícios gerados!"
        ;;
        
    3)
        echo ""
        echo -e "${YELLOW}Aplicando melhorias completas...${NC}"
        echo ""
        
        # Backup do original
        if [ ! -f "templates/monitoring/dashboard_executive_backup.html" ]; then
            cp templates/monitoring/dashboard_executive.html templates/monitoring/dashboard_executive_backup.html
            echo -e "${GREEN}✓${NC} Backup criado"
        fi
        
        # Aplicar novo layout
        cp templates/monitoring/dashboard_executive_improved.html templates/monitoring/dashboard_executive.html
        echo -e "${GREEN}✓${NC} Novo layout aplicado"
        
        # Gerar dados
        echo ""
        echo "Gerando dados fictícios para últimos 7 dias..."
        python manage.py generate_mock_data --days 7 --clear
        
        echo ""
        echo -e "${GREEN}=========================================="
        echo "✓ Melhorias aplicadas com sucesso!"
        echo "==========================================${NC}"
        echo ""
        echo "Próximos passos:"
        echo "1. Iniciar servidor: python manage.py runserver 0.0.0.0:10100"
        echo "2. Acessar: http://192.168.200.8:10100/dashboard"
        echo ""
        ;;
        
    4)
        echo ""
        echo -e "${YELLOW}Revertendo para layout original...${NC}"
        
        if [ -f "templates/monitoring/dashboard_executive_backup.html" ]; then
            cp templates/monitoring/dashboard_executive_backup.html templates/monitoring/dashboard_executive.html
            echo -e "${GREEN}✓${NC} Layout original restaurado!"
        else
            echo -e "${RED}Erro: Backup não encontrado!${NC}"
            exit 1
        fi
        ;;
        
    5)
        echo ""
        echo -e "${YELLOW}Limpando dados fictícios...${NC}"
        
        python manage.py shell << EOF
from apps.monitoring.models import AgentEvent, AgentWorkday, AgentDayStats

eventos = AgentEvent.objects.filter(source="MOCK").count()
jornadas = AgentWorkday.objects.filter(source="MOCK").count()
stats = AgentDayStats.objects.filter(source="MOCK").count()

print(f"Removendo {eventos} eventos...")
AgentEvent.objects.filter(source="MOCK").delete()

print(f"Removendo {jornadas} jornadas...")
AgentWorkday.objects.filter(source="MOCK").delete()

print(f"Removendo {stats} estatísticas...")
AgentDayStats.objects.filter(source="MOCK").delete()

print("✓ Dados fictícios removidos!")
EOF
        ;;
        
    0)
        echo "Saindo..."
        exit 0
        ;;
        
    *)
        echo -e "${RED}Opção inválida!${NC}"
        exit 1
        ;;
esac

echo ""
echo "Concluído!"
