/*
  MiniPass Filter Tabs — positions the sliding active-pill indicator
  (.mp-filter-tabs__indicator, macros/filter_tabs.html) under whichever
  .mp-filter-btn currently has .active, and re-measures on resize so it
  stays correct if the container's width (and therefore each button's
  offsetLeft) changes.

  Self-contained, no dependency on window.mpBasecoat — this isn't a
  popover-based component (see mp-action-menu.js's registry), just a
  measure-and-position helper.

  A real filtered page (macros/data_table.html's table_toolbar(), or any
  other filter_tabs() caller) reaches this only through a normal <a href>
  navigation — the browser loads a fresh page with a different tab already
  marked .active server-side, so this only ever "lands" the indicator
  silently on load; there's no prior state within that page load to
  animate from. The slide is visible when something toggles .active on an
  existing DOM without a navigation — e.g. style_guide.html's demo, which
  fakes filtering with a plain click handler since its tabs point at "#".
*/
(() => {
  const position = (root, animate) => {
    const indicator = root.querySelector('.mp-filter-tabs__indicator');
    if (!indicator) return;
    const active = root.querySelector('.mp-filter-btn.active');
    if (!active) {
      indicator.style.opacity = '0';
      indicator.style.width = '0';
      return;
    }
    if (!animate) indicator.style.transition = 'none';
    indicator.style.transform = `translateX(${active.offsetLeft}px)`;
    indicator.style.width = `${active.offsetWidth}px`;
    indicator.classList.add('is-ready');
    if (!animate) {
      // Force layout so the transition:none above actually applies to this
      // frame before restoring it, instead of the browser coalescing both
      // style writes into one paint (which would animate the very first
      // placement in from width:0 — the "flash of sliding in" this avoids).
      void indicator.offsetWidth;
      indicator.style.transition = '';
    }
  };

  const positionAll = (animate) => {
    document.querySelectorAll('.mp-filter-tabs').forEach((root) => position(root, animate));
  };

  document.addEventListener('DOMContentLoaded', () => positionAll(false));
  window.addEventListener('resize', () => positionAll(false));

  window.mpFilterTabs = {
    reposition: (root, animate = true) => position(root, animate),
  };
})();
