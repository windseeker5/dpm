/*
  MiniPass Action Menu — ported from KDUI (flask-shadcn-starter).
  Source: ~/Documents/DEV/kdui/flask-shadcn-starter/node_modules/basecoat-css/dist/js/{basecoat.js, dropdown-menu.js}

  Logic transcribed as-is (open/close, Escape/Arrow/Home/End keyboard nav,
  outside-click close). Renamed .dropdown-menu -> .mp-action-menu and
  window.basecoat -> window.mpBasecoat because Bootstrap/Tabler already
  owns .dropdown-menu and window.bootstrap.Dropdown in this app — same
  reasoning as the .mp-btn port. No data-bs-toggle attributes are used
  here, so Bootstrap's own dropdown JS never touches this component.
  Trimmed: only the pieces action_menu() actually uses (register/init/
  initAll + the dropdown-menu component + the MutationObserver, so menus
  added later via AJAX-loaded rows still work). Theme toggle, other
  Basecoat components, and menu groups/checkboxes/radios are not ported —
  action_menu.html doesn't expose them.
*/
(() => {
  const componentRegistry = {};
  let observer = null;

  const registerComponent = (name, options) => {
    componentRegistry[name] = { selector: options.selector, init: options.init, refresh: options.refresh };
  };

  const initComponent = (element, componentName) => {
    const component = componentRegistry[componentName];
    if (!component) return;
    try {
      component.init(element);
      if (element.hasAttribute(`data-${componentName}-initialized`)) {
        element.dataset.mpComponent = componentName;
      }
    } catch (error) {
      console.error(`Failed to initialize ${componentName}:`, error);
      element.removeAttribute(`data-${componentName}-initialized`);
      delete element.dataset.mpComponent;
    }
  };

  const destroyComponent = (element) => {
    if (!element || element.nodeType !== Node.ELEMENT_NODE) return;
    const componentName = element.dataset?.mpComponent;
    if (typeof element._destroy === 'function') {
      try { element._destroy(); } catch (error) { console.error('Failed to destroy component:', error); }
    }
    delete element._destroy;
    if (componentName) element.removeAttribute(`data-${componentName}-initialized`);
    delete element.dataset.mpComponent;
  };

  const destroyRemovedComponents = (node) => {
    if (node.nodeType !== Node.ELEMENT_NODE || node.isConnected) return;
    if (node.dataset?.mpComponent) destroyComponent(node);
    node.querySelectorAll?.('[data-mp-component]').forEach(destroyComponent);
  };

  const initAllComponents = () => {
    Object.entries(componentRegistry).forEach(([name, { selector }]) => {
      document.querySelectorAll(selector).forEach((element) => initComponent(element, name));
    });
  };

  const initNewComponents = (node) => {
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    Object.entries(componentRegistry).forEach(([name, { selector }]) => {
      if (node.matches?.(selector)) initComponent(node, name);
      node.querySelectorAll?.(selector).forEach((element) => initComponent(element, name));
    });
  };

  const startObserver = () => {
    if (observer) return;
    observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach(initNewComponents);
        mutation.removedNodes.forEach(destroyRemovedComponents);
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  };

  window.mpBasecoat = { register: registerComponent };

  /* ---- Dropdown Menu (action menu) ---- */
  const states = new WeakMap();

  const isDisabled = (item) => item.hasAttribute('disabled') || item.getAttribute('aria-disabled') === 'true';

  const getElements = (root) => {
    const trigger = root.querySelector(':scope > button');
    const popover = root.querySelector(':scope > [data-popover]');
    const menu = popover ? popover.querySelector('[role="menu"]') : null;
    return { trigger, popover, menu };
  };

  const getItems = (menu) => Array.from(menu.querySelectorAll('[role^="menuitem"]')).filter((item) => !isDisabled(item));

  const setActiveItem = (state, index) => {
    if (state.activeIndex > -1 && state.items[state.activeIndex]) {
      state.items[state.activeIndex].classList.remove('active');
    }
    state.activeIndex = index;
    if (state.activeIndex > -1 && state.items[state.activeIndex]) {
      const activeItem = state.items[state.activeIndex];
      activeItem.classList.add('active');
      if (activeItem.id) state.trigger.setAttribute('aria-activedescendant', activeItem.id);
    } else {
      state.trigger.removeAttribute('aria-activedescendant');
    }
  };

  const refreshDropdownMenu = (root) => {
    const state = states.get(root);
    if (!state) return;
    const elements = getElements(root);
    if (!elements.trigger || !elements.popover || !elements.menu) {
      console.error('mp-action-menu refresh failed: missing trigger/popover/menu', root);
      return;
    }
    Object.assign(state, elements);
    state.items = getItems(state.menu);
    if (state.activeIndex > -1 && !state.items[state.activeIndex]) setActiveItem(state, -1);
  };

  const closePopover = (state, focusOnTrigger = true) => {
    if (state.trigger.getAttribute('aria-expanded') === 'false') return;
    state.trigger.setAttribute('aria-expanded', 'false');
    state.trigger.removeAttribute('aria-activedescendant');
    state.popover.setAttribute('aria-hidden', 'true');
    if (focusOnTrigger) state.trigger.focus();
    setActiveItem(state, -1);
  };

  const openPopover = (root, state, initialSelection = false) => {
    document.dispatchEvent(new CustomEvent('mp:action-menu-open', { detail: { source: root } }));
    root.refresh();
    state.trigger.setAttribute('aria-expanded', 'true');
    state.popover.setAttribute('aria-hidden', 'false');
    if (state.items.length > 0 && initialSelection) {
      setActiveItem(state, initialSelection === 'last' ? state.items.length - 1 : 0);
    }
  };

  const initDropdownMenu = (root) => {
    if (root.dataset.mpActionMenuInitialized) return;

    const state = { activeIndex: -1, items: [] };
    states.set(root, state);
    root.refresh = () => refreshDropdownMenu(root);
    refreshDropdownMenu(root);
    if (!state.trigger || !state.popover || !state.menu) {
      states.delete(root);
      delete root.refresh;
      return;
    }

    root.open = (initialSelection = false) => openPopover(root, state, initialSelection);
    root.close = (focusOnTrigger = true) => closePopover(state, focusOnTrigger);
    root.toggle = () => (state.trigger.getAttribute('aria-expanded') === 'true' ? root.close() : root.open(false));

    const handleTriggerClick = root.toggle;

    const handleKeydown = (event) => {
      const isExpanded = state.trigger.getAttribute('aria-expanded') === 'true';

      if (event.key === 'Escape') {
        if (isExpanded) root.close();
        return;
      }

      if (!isExpanded) {
        if (['Enter', ' '].includes(event.key)) {
          event.preventDefault();
          root.open(false);
        } else if (event.key === 'ArrowDown') {
          event.preventDefault();
          root.open('first');
        } else if (event.key === 'ArrowUp') {
          event.preventDefault();
          root.open('last');
        }
        return;
      }

      if (state.items.length === 0) return;

      let nextIndex = state.activeIndex;
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        nextIndex = state.activeIndex === -1 ? 0 : Math.min(state.activeIndex + 1, state.items.length - 1);
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        nextIndex = state.activeIndex === -1 ? state.items.length - 1 : Math.max(state.activeIndex - 1, 0);
      } else if (event.key === 'Home') {
        event.preventDefault();
        nextIndex = 0;
      } else if (event.key === 'End') {
        event.preventDefault();
        nextIndex = state.items.length - 1;
      } else if (['Enter', ' '].includes(event.key)) {
        event.preventDefault();
        state.items[state.activeIndex]?.click();
        root.close();
        return;
      } else {
        return;
      }

      if (nextIndex !== state.activeIndex) setActiveItem(state, nextIndex);
    };

    const handleMenuMousemove = (event) => {
      const menuItem = event.target.closest('[role^="menuitem"]');
      if (menuItem && !isDisabled(menuItem) && state.items.includes(menuItem)) {
        const index = state.items.indexOf(menuItem);
        if (index !== state.activeIndex) setActiveItem(state, index);
      }
    };

    const handleMenuMouseleave = () => setActiveItem(state, -1);

    const handleMenuClick = (event) => {
      const menuItem = event.target.closest('[role^="menuitem"]');
      if (!menuItem || isDisabled(menuItem)) return;
      root.close();
    };

    const handleDocumentClick = (event) => {
      if (!root.contains(event.target)) root.close(false);
    };

    const handleDocumentPopover = (event) => {
      if (event.detail.source !== root) root.close(false);
    };

    state.trigger.addEventListener('click', handleTriggerClick);
    root.addEventListener('keydown', handleKeydown);
    state.menu.addEventListener('mousemove', handleMenuMousemove);
    state.menu.addEventListener('mouseleave', handleMenuMouseleave);
    state.menu.addEventListener('click', handleMenuClick);
    document.addEventListener('click', handleDocumentClick);
    document.addEventListener('mp:action-menu-open', handleDocumentPopover);

    root._destroy = () => {
      state.trigger.removeEventListener('click', handleTriggerClick);
      root.removeEventListener('keydown', handleKeydown);
      state.menu.removeEventListener('mousemove', handleMenuMousemove);
      state.menu.removeEventListener('mouseleave', handleMenuMouseleave);
      state.menu.removeEventListener('click', handleMenuClick);
      document.removeEventListener('click', handleDocumentClick);
      document.removeEventListener('mp:action-menu-open', handleDocumentPopover);
      states.delete(root);
      delete root.refresh;
      delete root.open;
      delete root.close;
      delete root.toggle;
    };

    state.trigger.setAttribute('aria-expanded', 'false');
    state.popover.setAttribute('aria-hidden', 'true');
    root.dataset.mpActionMenuInitialized = 'true';
  };

  window.mpBasecoat.register('mp-action-menu', {
    selector: '.mp-action-menu:not([data-mp-action-menu-initialized])',
    init: initDropdownMenu,
    refresh: refreshDropdownMenu,
  });

  document.addEventListener('DOMContentLoaded', () => {
    initAllComponents();
    startObserver();
  });
})();
