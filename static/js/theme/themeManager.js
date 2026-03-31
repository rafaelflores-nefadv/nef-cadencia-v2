/**
 * Theme Manager - Gerenciamento de Tema (Light/Dark)
 * 
 * Responsabilidades:
 * - Alternar entre light e dark mode
 * - Persistir preferência do usuário
 * - Detectar preferência do sistema
 * - Aplicar tema automaticamente
 */

class ThemeManager {
  constructor() {
    this.STORAGE_KEY = 'nef_theme';
    this.THEMES = {
      LIGHT: 'light',
      DARK: 'dark',
      AUTO: 'auto'
    };
    
    this.currentTheme = this.getStoredTheme() || this.THEMES.AUTO;
  }
  
  /**
   * Inicializar tema
   */
  init() {
    // Aplicar tema inicial
    this.applyTheme(this.currentTheme);
    
    // Escutar mudanças de preferência do sistema
    this.watchSystemPreference();
    
    console.log('ThemeManager: Initialized with theme', this.currentTheme);
  }
  
  /**
   * Obter tema armazenado
   */
  getStoredTheme() {
    try {
      return localStorage.getItem(this.STORAGE_KEY);
    } catch (error) {
      console.error('Error getting stored theme:', error);
      return null;
    }
  }
  
  /**
   * Salvar tema
   */
  setStoredTheme(theme) {
    try {
      localStorage.setItem(this.STORAGE_KEY, theme);
    } catch (error) {
      console.error('Error storing theme:', error);
    }
  }
  
  /**
   * Obter preferência do sistema
   */
  getSystemPreference() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return this.THEMES.DARK;
    }
    return this.THEMES.LIGHT;
  }
  
  /**
   * Obter tema efetivo (resolvendo 'auto')
   */
  getEffectiveTheme(theme = this.currentTheme) {
    if (theme === this.THEMES.AUTO) {
      return this.getSystemPreference();
    }
    return theme;
  }
  
  /**
   * Aplicar tema no DOM
   */
  applyTheme(theme) {
    const effectiveTheme = this.getEffectiveTheme(theme);
    
    // Aplicar no atributo data-theme
    document.documentElement.setAttribute('data-theme', effectiveTheme);
    
    // Aplicar classe no body (para compatibilidade)
    document.body.classList.remove('theme-light', 'theme-dark');
    document.body.classList.add(`theme-${effectiveTheme}`);
    
    // Atualizar meta theme-color
    this.updateMetaThemeColor(effectiveTheme);
    
    // Disparar evento
    window.dispatchEvent(new CustomEvent('theme:changed', {
      detail: {
        theme: theme,
        effectiveTheme: effectiveTheme
      }
    }));
    
    console.log('ThemeManager: Applied theme', effectiveTheme);
  }
  
  /**
   * Atualizar meta theme-color
   */
  updateMetaThemeColor(theme) {
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      const color = theme === this.THEMES.DARK ? '#0f172a' : '#ffffff';
      metaThemeColor.setAttribute('content', color);
    }
  }
  
  /**
   * Alternar tema
   */
  toggle() {
    const effectiveTheme = this.getEffectiveTheme();
    const newTheme = effectiveTheme === this.THEMES.DARK ? this.THEMES.LIGHT : this.THEMES.DARK;
    this.setTheme(newTheme);
  }
  
  /**
   * Definir tema
   */
  setTheme(theme) {
    if (!Object.values(this.THEMES).includes(theme)) {
      console.error('Invalid theme:', theme);
      return;
    }
    
    this.currentTheme = theme;
    this.setStoredTheme(theme);
    this.applyTheme(theme);
  }
  
  /**
   * Obter tema atual
   */
  getTheme() {
    return this.currentTheme;
  }
  
  /**
   * Obter tema efetivo atual
   */
  getCurrentEffectiveTheme() {
    return this.getEffectiveTheme();
  }
  
  /**
   * Verificar se está em dark mode
   */
  isDark() {
    return this.getEffectiveTheme() === this.THEMES.DARK;
  }
  
  /**
   * Verificar se está em light mode
   */
  isLight() {
    return this.getEffectiveTheme() === this.THEMES.LIGHT;
  }
  
  /**
   * Escutar mudanças de preferência do sistema
   */
  watchSystemPreference() {
    if (!window.matchMedia) return;
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Listener para mudanças
    const handler = (e) => {
      if (this.currentTheme === this.THEMES.AUTO) {
        this.applyTheme(this.THEMES.AUTO);
      }
    };
    
    // Adicionar listener
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handler);
    } else if (mediaQuery.addListener) {
      // Fallback para navegadores antigos
      mediaQuery.addListener(handler);
    }
  }
  
  /**
   * Criar toggle button
   */
  createToggleButton() {
    const button = document.createElement('button');
    button.className = 'theme-toggle-btn';
    button.setAttribute('aria-label', 'Alternar tema');
    button.setAttribute('title', 'Alternar tema');
    
    // Ícones
    const sunIcon = `
      <svg class="theme-icon theme-icon-light" width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 3V1M10 19V17M17 10H19M1 10H3M15.657 4.343L17.071 2.929M2.929 17.071L4.343 15.657M15.657 15.657L17.071 17.071M2.929 2.929L4.343 4.343M14 10C14 12.2091 12.2091 14 10 14C7.79086 14 6 12.2091 6 10C6 7.79086 7.79086 6 10 6C12.2091 6 14 7.79086 14 10Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    `;
    
    const moonIcon = `
      <svg class="theme-icon theme-icon-dark" width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    `;
    
    button.innerHTML = sunIcon + moonIcon;
    
    // Click handler
    button.addEventListener('click', () => {
      this.toggle();
      this.updateToggleButton(button);
    });
    
    // Atualizar estado inicial
    this.updateToggleButton(button);
    
    return button;
  }
  
  /**
   * Atualizar estado do toggle button
   */
  updateToggleButton(button) {
    const isDark = this.isDark();
    
    button.classList.toggle('theme-dark', isDark);
    button.classList.toggle('theme-light', !isDark);
    
    const lightIcon = button.querySelector('.theme-icon-light');
    const darkIcon = button.querySelector('.theme-icon-dark');
    
    if (lightIcon && darkIcon) {
      lightIcon.style.display = isDark ? 'none' : 'block';
      darkIcon.style.display = isDark ? 'block' : 'none';
    }
  }
  
  /**
   * Adicionar toggle button ao DOM
   */
  addToggleButton(container) {
    const button = this.createToggleButton();
    
    if (typeof container === 'string') {
      const element = document.querySelector(container);
      if (element) {
        element.appendChild(button);
      }
    } else if (container instanceof HTMLElement) {
      container.appendChild(button);
    }
    
    return button;
  }
}

// Criar instância singleton
const themeManager = new ThemeManager();

// Exportar
export { themeManager, ThemeManager };

// Tornar disponível globalmente
window.themeManager = themeManager;
window.ThemeManager = ThemeManager;
