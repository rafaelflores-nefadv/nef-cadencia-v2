(function () {
  var THEME_STORAGE_KEY = 'nef_theme_preference';
  var THEMES = ['blue', 'dark', 'light'];

  function qs(sel, root){ return (root||document).querySelector(sel); }
  function qsa(sel, root){ return Array.prototype.slice.call((root||document).querySelectorAll(sel)); }
  function isVisible(el){ return !!el && !el.classList.contains('hidden'); }
  function resolveTheme(theme) {
    return THEMES.indexOf(theme) >= 0 ? theme : 'blue';
  }
  function applyTheme(theme) {
    var nextTheme = resolveTheme(theme);
    document.documentElement.setAttribute('data-theme', nextTheme);
    document.body.setAttribute('data-theme', nextTheme);
    qsa('[data-theme-option]').forEach(function (button) {
      var isActive = button.getAttribute('data-theme-option') === nextTheme;
      button.classList.toggle('is-active', isActive);
      button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
    document.dispatchEvent(new CustomEvent('app:theme-change', { detail: { theme: nextTheme } }));
  }
  function initTheme() {
    var storedTheme = null;
    try {
      storedTheme = window.localStorage ? window.localStorage.getItem(THEME_STORAGE_KEY) : null;
    } catch (_error) {
      storedTheme = null;
    }
    applyTheme(resolveTheme(storedTheme || document.documentElement.getAttribute('data-theme')));
    qsa('[data-theme-option]').forEach(function (button) {
      button.addEventListener('click', function () {
        var selectedTheme = resolveTheme(button.getAttribute('data-theme-option'));
        applyTheme(selectedTheme);
        try {
          if (window.localStorage) window.localStorage.setItem(THEME_STORAGE_KEY, selectedTheme);
        } catch (_error) {}
      });
    });
  }

  function initMicroInteractions() {
    qsa('.ds-panel, .ds-kpi, .list-card').forEach(function (card) {
      card.addEventListener('click', function () {
        card.classList.add('is-active-cue');
        window.setTimeout(function () {
          card.classList.remove('is-active-cue');
        }, 260);
      });
    });

    qsa('button, .menu-item, .menu-subitem, .profile-menu__item, .topbar-mainmenu-button').forEach(function (node) {
      node.addEventListener('pointerdown', function () {
        node.classList.add('is-pressed');
      });
      function clearPressed() { node.classList.remove('is-pressed'); }
      node.addEventListener('pointerup', clearPressed);
      node.addEventListener('pointerleave', clearPressed);
      node.addEventListener('pointercancel', clearPressed);
    });

    qsa('#executiveTrendChart, #executiveComparisonChart, #executiveRiskPieChart, #executiveProductivityRangeChart, #executiveHealthGaugeChart, #riskRadarChart, #alertSeverityChart').forEach(function (chartRoot, index) {
      chartRoot.classList.add('ux-chart-enter');
      window.setTimeout(function () {
        chartRoot.classList.add('is-visible');
      }, 70 + (index * 35));
    });
  }

  function initIcons() {
    if (window.lucide && typeof window.lucide.createIcons === 'function') {
      window.lucide.createIcons();
    }
  }

  function initProfileMenu() {
    var menuRoot = qs('[data-profile-menu]');
    if (!menuRoot) return;

    var trigger = qs('[data-profile-menu-button]', menuRoot);
    var panel = qs('[data-profile-menu-panel]', menuRoot);
    if (!trigger || !panel) return;

    function menuItems() {
      return qsa('[role="menuitem"]', panel);
    }

    function setExpanded(open) {
      trigger.setAttribute('aria-expanded', open ? 'true' : 'false');
      panel.classList.toggle('hidden', !open);
    }

    function openMenu(shouldFocusFirst) {
      setExpanded(true);
      if (shouldFocusFirst) {
        var items = menuItems();
        if (items.length) items[0].focus();
      }
    }

    function closeMenu(returnFocus) {
      if (!isVisible(panel)) return;
      setExpanded(false);
      if (returnFocus) trigger.focus();
    }

    function toggleMenu() {
      if (isVisible(panel)) {
        closeMenu(false);
      } else {
        openMenu(false);
      }
    }

    function focusByOffset(offset) {
      var items = menuItems();
      if (!items.length) return;
      var currentIndex = items.indexOf(document.activeElement);
      var nextIndex = currentIndex + offset;
      if (currentIndex === -1) {
        nextIndex = offset > 0 ? 0 : items.length - 1;
      } else if (nextIndex < 0) {
        nextIndex = items.length - 1;
      } else if (nextIndex >= items.length) {
        nextIndex = 0;
      }
      items[nextIndex].focus();
    }

    trigger.addEventListener('click', function (event) {
      event.preventDefault();
      toggleMenu();
    });

    trigger.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openMenu(true);
      }
      if (event.key === 'ArrowUp') {
        event.preventDefault();
        openMenu(false);
        focusByOffset(-1);
      }
      if (event.key === 'Escape') {
        closeMenu(false);
      }
    });

    panel.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeMenu(true);
      }
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        focusByOffset(1);
      }
      if (event.key === 'ArrowUp') {
        event.preventDefault();
        focusByOffset(-1);
      }
      if (event.key === 'Home') {
        event.preventDefault();
        var first = menuItems()[0];
        if (first) first.focus();
      }
      if (event.key === 'End') {
        event.preventDefault();
        var items = menuItems();
        if (items.length) items[items.length - 1].focus();
      }
      if (event.key === 'Tab') {
        closeMenu(false);
      }
    });

    panel.addEventListener('click', function (event) {
      var item = event.target.closest('[role="menuitem"]');
      if (item) closeMenu(false);
    });

    document.addEventListener('click', function (event) {
      if (!menuRoot.contains(event.target)) {
        closeMenu(false);
      }
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        closeMenu(true);
      }
    });
  }

  // Collapse sidebar (desktop)
  var collapseBtn = qs('[data-sidebar-collapse]');
  var sidebar = qs('[data-sidebar]');
  if (collapseBtn && sidebar) {
    collapseBtn.addEventListener('click', function () {
      sidebar.classList.toggle('is-collapsed');
      document.documentElement.classList.toggle('sidebar-collapsed');
    });
  }

  // Mobile drawer
  var openBtn = qs('[data-sidebar-open]');
  var closeBtn = qs('[data-sidebar-close]');
  var backdrop = qs('[data-sidebar-backdrop]');
  var mobileDrawer = qs('[data-sidebar-drawer]');
  var desktopSidebar = qs('[data-sidebar]');
  var agentDrawer = qs('[data-agent-drawer]');
  var agentDrawerBackdrop = qs('[data-agent-drawer-backdrop]');
  var mobileMedia = window.matchMedia ? window.matchMedia('(max-width: 1023px)') : null;
  function isMobileViewport() {
    return mobileMedia ? mobileMedia.matches : window.innerWidth < 1024;
  }
  function closeAgentDrawer() {
    if (agentDrawer) agentDrawer.classList.remove('is-open');
    if (agentDrawerBackdrop) agentDrawerBackdrop.classList.remove('is-visible');
    document.documentElement.classList.remove('agent-drawer-open');
  }
  function openDrawer(){
    if (!isMobileViewport()) {
      closeDrawer();
      return;
    }
    closeAgentDrawer();
    document.documentElement.classList.add('sidebar-drawer-open');
  }
  function closeDrawer(){
    document.documentElement.classList.remove('sidebar-drawer-open');
  }
  function syncDrawerByViewport() {
    if (!isMobileViewport()) closeDrawer();
  }
  function closeDrawerOnNavigate(event) {
    var link = event.target.closest('a[href]');
    if (!link) return;
    var href = link.getAttribute('href') || '';
    if (!href || href === '#' || href.indexOf('javascript:') === 0) return;
    if (isMobileViewport()) closeDrawer();
  }
  closeDrawer();
  closeAgentDrawer();
  syncDrawerByViewport();
  if (openBtn) openBtn.addEventListener('click', openDrawer);
  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
  if (backdrop) backdrop.addEventListener('click', closeDrawer);
  if (mobileDrawer) mobileDrawer.addEventListener('click', closeDrawerOnNavigate);
  if (desktopSidebar) desktopSidebar.addEventListener('click', closeDrawerOnNavigate);
  window.addEventListener('resize', syncDrawerByViewport);
  if (mobileMedia && typeof mobileMedia.addEventListener === 'function') {
    mobileMedia.addEventListener('change', syncDrawerByViewport);
  } else if (mobileMedia && typeof mobileMedia.addListener === 'function') {
    mobileMedia.addListener(syncDrawerByViewport);
  }
  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Escape') return;
    closeDrawer();
    closeAgentDrawer();
  });

  // Sidebar system dropdown
  qsa('[data-menu-dropdown]').forEach(function (dropdown) {
    var trigger = qs('[data-menu-dropdown-toggle]', dropdown);
    if (!trigger) return;
    var hasActiveRoute = !!qs('.menu-subitem--active, .menu-item--active', dropdown);

    function setOpen(open) {
      var nextOpen = hasActiveRoute ? true : open;
      dropdown.setAttribute('data-open', nextOpen ? 'true' : 'false');
      trigger.setAttribute('aria-expanded', nextOpen ? 'true' : 'false');
    }

    setOpen(dropdown.getAttribute('data-open') === 'true' || hasActiveRoute);

    trigger.addEventListener('click', function () {
      var currentlyOpen = dropdown.getAttribute('data-open') === 'true';
      if (hasActiveRoute) {
        setOpen(true);
        return;
      }
      setOpen(!currentlyOpen);
    });
  });

  // Toggle groups
  qsa('[data-nav-group-toggle]').forEach(function(btn){
    btn.addEventListener('click', function(){
      var id = btn.getAttribute('data-nav-group-toggle');
      var panel = qs('[data-nav-group="'+id+'"]');
      if (!panel) return;
      panel.classList.toggle('hidden');
      btn.setAttribute('aria-expanded', panel.classList.contains('hidden') ? 'false' : 'true');
    });
  });

  initProfileMenu();
  initTheme();
  initMicroInteractions();
  initIcons();
})();
