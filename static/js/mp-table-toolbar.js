/*
  MiniPass Table Toolbar — search icon that expands into an inline input
  next to the filter tabs (macros/data_table.html's table_toolbar()).

  Self-contained: no dependency on window.mpBasecoat (that registry backs
  popover-based components — see mp-action-menu.js — this toolbar has no
  popover, just a toggled [data-search-open] attribute that mp-components.css
  reads to decide layout per breakpoint).
*/
(() => {
  const init = (toolbar) => {
    if (toolbar.dataset.mpTableToolbarInitialized) return;
    toolbar.dataset.mpTableToolbarInitialized = 'true';

    const btn = toolbar.querySelector('.mp-table-toolbar__search-btn');
    const input = toolbar.querySelector('.mp-table-toolbar__search-input');
    if (!btn || !input) return;

    const open = () => {
      toolbar.setAttribute('data-search-open', '');
      btn.setAttribute('aria-expanded', 'true');
      input.focus();
    };

    const close = (clear) => {
      if (clear) input.value = '';
      toolbar.removeAttribute('data-search-open');
      btn.setAttribute('aria-expanded', 'false');
    };

    btn.addEventListener('click', () => {
      if (toolbar.hasAttribute('data-search-open')) {
        close(true);
        btn.focus();
      } else {
        open();
      }
    });

    input.addEventListener('blur', () => {
      if (!input.value) close(false);
    });

    input.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') {
        close(true);
        btn.focus();
      }
    });
  };

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.mp-table-toolbar').forEach(init);
  });
})();
