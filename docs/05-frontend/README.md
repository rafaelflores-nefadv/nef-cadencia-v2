# 🎨 Frontend

Interface e experiência do usuário do NEF Cadencia v2.

## 📚 Documentos Disponíveis

### [GUIA_VISUAL.md](./GUIA_VISUAL.md)
Guia de identidade visual
- Paleta de cores
- Tipografia
- Componentes
- Espaçamento
- Ícones

### [INTEGRACAO.md](./INTEGRACAO.md)
Integração Frontend-Backend
- Como templates recebem dados
- Context processors
- Template tags
- Filtros customizados

### [NAVEGACAO.md](./NAVEGACAO.md)
Sistema de navegação
- Menu principal
- Breadcrumbs
- Rotas protegidas
- Redirecionamentos

### [REORGANIZACAO_FRONTEND.md](./REORGANIZACAO_FRONTEND.md)
Reorganização do frontend
- Nova estrutura de templates
- Componentes reutilizáveis
- Sistema de temas

## 🎨 Stack Frontend

- **Templates:** Django Templates
- **CSS:** Tailwind CSS 3.x
- **JavaScript:** Vanilla JS + Alpine.js (futuro)
- **Gráficos:** ApexCharts
- **Ícones:** Lucide Icons

## 📁 Estrutura de Templates

```
templates/
├── base.html                 # Template base
├── layouts/
│   ├── auth.html            # Layout de autenticação
│   └── dashboard.html       # Layout de dashboard
├── components/
│   ├── _navbar.html         # Barra de navegação
│   ├── _sidebar.html        # Menu lateral
│   └── _footer.html         # Rodapé
├── monitoring/
│   ├── dashboard_executive.html
│   ├── dashboard_productivity.html
│   └── ...
└── accounts/
    ├── login.html
    └── ...
```

## 🎨 Sistema de Cores

### Tema Dark (Padrão)
```css
--color-bg: #0a0e1a
--color-card: #0f172a
--color-text: #e2e8f0
--color-primary: #38bdf8
--color-success: #22c55e
--color-warning: #f59e0b
--color-danger: #ef4444
```

### Tema Light
```css
--color-bg: #ffffff
--color-card: #f8fafc
--color-text: #1e293b
--color-primary: #0ea5e9
```

## 🧩 Componentes

### Cards
```html
<div class="ds-panel p-5">
  <h3 class="text-base font-semibold">Título</h3>
  <p class="text-sm text-[color:var(--color-text-muted)]">Conteúdo</p>
</div>
```

### Badges
```html
<span class="ds-badge ds-badge--ok">Sucesso</span>
<span class="ds-badge ds-badge--warn">Atenção</span>
<span class="ds-badge ds-badge--crit">Crítico</span>
```

### Botões
```html
<button class="btn btn-primary">Primário</button>
<button class="btn btn-secondary">Secundário</button>
```

## 📊 Gráficos com ApexCharts

```javascript
const chart = new ApexCharts(element, {
  chart: { type: 'line', height: 300 },
  series: [{ name: 'Série', data: [1, 2, 3] }],
  xaxis: { categories: ['A', 'B', 'C'] },
  colors: ['#38bdf8']
});
chart.render();
```

## 🎯 Tailwind CSS

### Classes Úteis
```html
<!-- Espaçamento -->
<div class="p-4 m-2 space-y-4">

<!-- Grid -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

<!-- Flexbox -->
<div class="flex items-center justify-between gap-2">

<!-- Cores -->
<div class="bg-sky-500 text-white">

<!-- Responsivo -->
<div class="hidden md:block">
```

### Compilar CSS
```bash
# Desenvolvimento (watch)
npm run watch:css

# Produção (minificado)
npm run build:css
```

## 🔄 Interatividade

### HTMX (Futuro)
```html
<button hx-get="/api/data" hx-target="#result">
  Carregar
</button>
<div id="result"></div>
```

### Alpine.js (Futuro)
```html
<div x-data="{ open: false }">
  <button @click="open = !open">Toggle</button>
  <div x-show="open">Conteúdo</div>
</div>
```

## 📱 Responsividade

### Breakpoints
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

### Mobile First
```html
<!-- Mobile: 1 coluna, Desktop: 3 colunas -->
<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
```

## 🎨 Melhorias Visuais (v3.0)

### Novo Dashboard
- ✅ Hero simplificado (4 métricas)
- ✅ Seções organizadas por tema
- ✅ Hierarquia visual clara
- ✅ Menos poluição
- ✅ Cards com hover effects

### Componentes
- ✅ Badges de status
- ✅ Progress bars
- ✅ Tooltips
- ✅ Modals
- ✅ Dropdowns
