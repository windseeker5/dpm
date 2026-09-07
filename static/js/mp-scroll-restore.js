/*
  MiniPass Scroll Restore — keeps the page's scroll position across a
  filter-tab click, pagination-link click, or table-toolbar search submit
  (macros/filter_tabs.html, macros/pagination.html, macros/data_table.html's
  table_toolbar()). All three are real full-page navigations (server-side
  filtering/paging, not AJAX) by design, so the browser resets scroll to
  the top on every one — this saves the scroll position just before the
  navigation and restores it once the new page loads.

  Self-contained, no window.mpBasecoat dependency — same convention as
  mp-table-toolbar.js / mp-filter-tabs.js.

  Reuses the sessionStorage + retry/staleness-check technique already
  proven in static/js/filter-component.js's preserveScrollPosition option,
  rather than that module itself — this one targets the newer .mp-filter-btn/
  .mp-table-toolbar markup (that module is hardcoded to the legacy
  .github-filter-btn class) and additionally covers the search-form submit
  case, which that module doesn't handle at all.

  Scrolling happens on #main-content (static/minipass.css's
  `.minipass-content { overflow-y: auto }`), not the window/document — this
  app's layout shell (templates/base.html) puts the sidebar and header
  outside the scrollable area, so window.scrollY is always 0 here.
*/
(() => {
  const STORAGE_KEY = 'mpScrollRestore';
  const STALE_MS = 8000;
  const TOLERANCE_PX = 20;
  const MAX_ATTEMPTS = 10;

  // Falls back to window/document scrolling if #main-content isn't present
  // (a page not built on templates/base.html's layout shell) rather than
  // silently doing nothing.
  const getScrollEl = () => document.getElementById('main-content');
  const getScrollY = () => {
    const el = getScrollEl();
    return el ? el.scrollTop : window.scrollY;
  };
  const scrollTo = (top) => {
    const el = getScrollEl();
    if (el) el.scrollTo({ top, left: 0, behavior: 'instant' });
    else window.scrollTo({ top, left: 0, behavior: 'instant' });
  };

  const saveScroll = (path) => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
        y: getScrollY(),
        ts: Date.now(),
        path,
      }));
    } catch (error) {
      // Private-browsing / storage-full edge cases — worst case is just no
      // scroll restore, never a broken click or submit.
    }
  };

  const resolvePath = (url) => {
    try {
      return new URL(url, location.href).pathname;
    } catch (error) {
      return location.pathname;
    }
  };

  const onLinkClick = (event) => {
    const a = event.currentTarget;
    const href = a.getAttribute('href') || '';
    // style_guide.html's fake demo links: filter_tabs() uses a bare "#",
    // pagination_desktop()/pagination_mobile() use base_path="#" with a
    // query string appended ("#?page=2&...") — neither is a real
    // navigation (in-page fragment only), so skip anything starting with #.
    if (href.startsWith('#')) return;
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (a.target === '_blank') return;
    saveScroll(resolvePath(a.href));
  };

  const onToolbarSubmit = (event) => {
    const form = event.currentTarget;
    saveScroll(resolvePath(form.action || location.pathname));
  };

  const attemptRestore = (targetY) => {
    let settled = false;
    let attempt = 0;

    const tryOnce = () => {
      if (settled) return;
      scrollTo(targetY);
      if (Math.abs(getScrollY() - targetY) <= TOLERANCE_PX) {
        settled = true;
        return;
      }
      attempt += 1;
      if (attempt < MAX_ATTEMPTS) {
        requestAnimationFrame(() => setTimeout(tryOnce, 60));
      }
    };

    tryOnce();
    // Final safety net for slow-loading pages (charts/images still
    // reflowing after the retry loop above has already given up).
    window.addEventListener('load', () => tryOnce(), { once: true });
  };

  const restoreOnLoad = () => {
    try {
      const navEntries = performance.getEntriesByType && performance.getEntriesByType('navigation');
      const navType = navEntries && navEntries[0] && navEntries[0].type;
      if (navType === 'back_forward' || navType === 'reload') return;
    } catch (error) {
      // Navigation Timing API unavailable — fall through and still attempt
      // restore rather than silently doing nothing.
    }

    let raw;
    try {
      raw = sessionStorage.getItem(STORAGE_KEY);
      sessionStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      return;
    }
    if (!raw) return;

    let data;
    try {
      data = JSON.parse(raw);
    } catch (error) {
      return;
    }

    if (!data || typeof data.y !== 'number') return;
    if (Date.now() - data.ts > STALE_MS) return;
    if (data.path !== location.pathname) return;

    attemptRestore(data.y);
  };

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('a.mp-filter-btn, a.mp-page-btn').forEach((a) => {
      a.addEventListener('click', onLinkClick);
    });
    document.querySelectorAll('form').forEach((form) => {
      if (form.querySelector('.mp-table-toolbar, .mp-filter-tabs')) {
        form.addEventListener('submit', onToolbarSubmit);
      }
    });
    restoreOnLoad();
  });
})();
