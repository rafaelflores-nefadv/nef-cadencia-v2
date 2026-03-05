(function () {
  function qs(sel, root){ return (root||document).querySelector(sel); }
  function qsa(sel, root){ return Array.prototype.slice.call((root||document).querySelectorAll(sel)); }
  function isVisible(el){ return !!el && !el.classList.contains('hidden'); }

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
  function openDrawer(){
    document.documentElement.classList.add('sidebar-drawer-open');
  }
  function closeDrawer(){
    document.documentElement.classList.remove('sidebar-drawer-open');
  }
  if (openBtn) openBtn.addEventListener('click', openDrawer);
  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
  if (backdrop) backdrop.addEventListener('click', closeDrawer);

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
  initIcons();
})();
