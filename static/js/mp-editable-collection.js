/* Shared runtime helpers for macros/editable_collection.html. */
(() => {
  const esc = (value) => String(value ?? '')
    .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;').replaceAll("'", '&#039;');

  const attrs = (values = {}) => Object.entries(values)
    .filter(([, value]) => value !== null && value !== undefined && value !== false)
    .map(([key, value]) => ` ${esc(key)}="${esc(value === true ? '' : value)}"`).join('');

  const button = ({ label = '', variant = 'outline', size = 'default', icon = null, attributes = {} } = {}) =>
    `<button type="button" class="mp-btn" data-variant="${esc(variant)}"${size !== 'default' ? ` data-size="${esc(size)}"` : ''}${attrs(attributes)}>` +
      `${icon ? `<i class="ti ${esc(icon)}" aria-hidden="true"></i>` : ''}${esc(label)}</button>`;

  const actionMenu = (id, items = []) => {
    const menuItems = items.map((item, index) => {
      if (item.type === 'separator') return '<div role="separator"></div>';
      return `<button type="button" role="menuitem" id="${esc(id)}-item-${index}"` +
        `${item.variant ? ` data-variant="${esc(item.variant)}"` : ''}${attrs(item.attributes)}>` +
        `${item.icon ? `<i class="ti ${esc(item.icon)}" aria-hidden="true"></i>` : ''}${esc(item.label)}</button>`;
    }).join('');
    return `<div class="mp-action-menu">` +
      `<button type="button" class="mp-btn" data-variant="ghost" data-size="icon-sm" aria-haspopup="menu" aria-expanded="false" aria-controls="${esc(id)}-menu" aria-label="Actions">` +
      `<i class="ti ti-dots" aria-hidden="true"></i></button>` +
      `<div data-popover aria-hidden="true" data-align="end"><div role="menu" id="${esc(id)}-menu" aria-orientation="vertical">${menuItems}</div></div></div>`;
  };

  const sync = (id) => {
    const root = typeof id === 'string' ? document.getElementById(id) : id;
    if (!root) return;
    const rows = document.getElementById(root.dataset.rowsId);
    const table = root.querySelector('[data-collection-table]');
    const empty = document.getElementById(root.dataset.emptyId);
    const hasRows = Boolean(rows?.children.length);
    if (table) table.hidden = !hasRows;
    if (empty) empty.hidden = hasRows;
  };

  const init = () => document.querySelectorAll('.mp-editable-collection').forEach(sync);
  window.mpEditableCollection = { escape: esc, button, actionMenu, sync };
  document.addEventListener('DOMContentLoaded', init);
})();
