(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  var STORAGE_KEY = "admin_menu_state_groups_v1";

  function readState() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return {};
      var parsed = JSON.parse(raw);
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (error) {
      return {};
    }
  }

  function saveState(state) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      // Ignore storage write failures (private mode, full quota, etc).
    }
  }

  function setGroupState(group, isOpen) {
    var toggle = qs("[data-admin-group-toggle]", group);
    var panel = qs(".admin-menu-group__panel", group);
    if (!toggle || !panel) return;

    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    panel.classList.toggle("hidden", !isOpen);
    group.classList.toggle("is-open", !!isOpen);
  }

  function syncGroupStateById(groupId, isOpen) {
    qsa("[data-admin-group]").forEach(function (group) {
      if (group.getAttribute("data-admin-group-id") === groupId) {
        setGroupState(group, isOpen);
        group.setAttribute("data-user-open", isOpen ? "true" : "false");
      }
    });
  }

  function initGroups() {
    var groups = qsa("[data-admin-group]");
    if (!groups.length) return;

    var persistedState = readState();

    groups.forEach(function (group) {
      var groupId = group.getAttribute("data-admin-group-id");
      if (!groupId) return;

      var isAppActive = group.getAttribute("data-app-active") === "true";
      var hasPersisted = Object.prototype.hasOwnProperty.call(persistedState, groupId);
      var startOpen = hasPersisted ? !!persistedState[groupId] : isAppActive;

      setGroupState(group, startOpen);
      group.setAttribute("data-user-open", startOpen ? "true" : "false");

      var toggle = qs("[data-admin-group-toggle]", group);
      if (!toggle) return;

      toggle.addEventListener("click", function () {
        var currentlyOpen = toggle.getAttribute("aria-expanded") === "true";
        var nextOpen = !currentlyOpen;
        syncGroupStateById(groupId, nextOpen);

        var nextState = readState();
        nextState[groupId] = nextOpen;
        saveState(nextState);
      });
    });
  }

  function applySidebarFilter(sidebar, query) {
    var normalized = (query || "").trim().toLowerCase();
    var groups = qsa("[data-admin-group]", sidebar);
    var standaloneLinks = qsa("[data-admin-menu-link]", sidebar).filter(function (link) {
      return !link.closest("[data-admin-group]");
    });

    standaloneLinks.forEach(function (link) {
      var text = (link.getAttribute("data-search-text") || link.textContent || "").toLowerCase();
      var visible = !normalized || text.indexOf(normalized) !== -1;
      link.classList.toggle("hidden", !visible);
    });

    groups.forEach(function (group) {
      var groupText = (group.getAttribute("data-search-text") || "").toLowerCase();
      var groupMatches = !normalized || groupText.indexOf(normalized) !== -1;
      var items = qsa("[data-search-text]", group).filter(function (node) {
        return node !== group;
      });

      var visibleChildren = 0;
      items.forEach(function (item) {
        var text = (item.getAttribute("data-search-text") || item.textContent || "").toLowerCase();
        var itemMatches = !normalized || groupMatches || text.indexOf(normalized) !== -1;
        item.classList.toggle("hidden", !itemMatches);
        if (itemMatches) visibleChildren += 1;
      });

      var shouldShowGroup = !normalized || groupMatches || visibleChildren > 0;
      group.classList.toggle("hidden", !shouldShowGroup);

      if (normalized && shouldShowGroup) {
        setGroupState(group, true);
      } else if (!normalized) {
        var preferredOpen = group.getAttribute("data-user-open") === "true";
        setGroupState(group, preferredOpen);
      }
    });
  }

  function initMenuSearch() {
    qsa("[data-admin-sidebar]").forEach(function (sidebar) {
      var input = qs("[data-admin-menu-search]", sidebar);
      if (!input) return;

      var handleFilter = function () {
        applySidebarFilter(sidebar, input.value);
      };

      input.addEventListener("input", handleFilter);
      input.addEventListener("search", handleFilter);
      input.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && input.value) {
          input.value = "";
          handleFilter();
        }
      });
    });
  }

  initGroups();
  initMenuSearch();
})();
