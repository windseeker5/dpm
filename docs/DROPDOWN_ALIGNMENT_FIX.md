# Dropdown Menu Right-Alignment Fix

## Problem
When using Bootstrap/Tabler.io dropdown with `dropdown-menu-end` class, the dropdown menu does NOT align its right edge with the button's right edge. Instead, it aligns LEFT edge to LEFT edge, causing the menu to extend far beyond the button.

## Root Cause
Bootstrap's Popper.js positioning system adds inline styles with the attribute `data-popper-placement` instead of `data-bs-popper`. Tabler's CSS rule `.dropdown-menu-end[data-bs-popper]` doesn't match because it's looking for the wrong attribute name.

## Solution

### HTML Structure (Standard Tabler.io)
```html
<div class="dropdown">
  <button type="button" class="btn btn-outline-secondary dropdown-toggle"
          data-bs-toggle="dropdown" aria-expanded="false">
    Actions
  </button>
  <div class="dropdown-menu dropdown-menu-end">
    <a class="dropdown-item" href="#">Option 1</a>
    <a class="dropdown-item" href="#">Option 2</a>
  </div>
</div>
```

### CSS Fix
Add this CSS to force right-alignment:

```css
/* Fix dropdown-menu-end alignment with Popper.js */
.dropdown-menu-end[data-popper-placement] {
  right: 0 !important;
  left: auto !important;
}
```

Or for specific pages only:
```css
.page-header .dropdown-menu-end[data-popper-placement] {
  right: 0 !important;
  left: auto !important;
}
```

## Key Points
1. **NO JAVASCRIPT NEEDED** - Pure CSS solution
2. **Use `data-popper-placement` NOT `data-bs-popper`** - This is what Bootstrap actually adds
3. **Must use `!important`** - Inline styles from Popper have highest specificity
4. **Standard Tabler structure works** - No need for custom data attributes like `data-bs-display="static"`

## Testing
Verify alignment by checking:
```javascript
const button = document.querySelector('.dropdown button');
const menu = document.querySelector('.dropdown-menu');
const buttonRect = button.getBoundingClientRect();
const menuRect = menu.getBoundingClientRect();
console.log('Right edge diff:', menuRect.right - buttonRect.right); // Should be 0
```

## Files Modified
- `templates/surveys.html` - Lines 20-23 (CSS fix in `<style>` block)
- HTML structure at lines 87-98

## Related Issues
This fix applies to ALL dropdowns using `dropdown-menu-end` in the application, including:
- User avatar dropdown in base.html
- Any page header action buttons
- Table action dropdowns (if using dropdown-menu-end)

## Date
2025-10-26

## References
- Bootstrap Dropdown docs: https://getbootstrap.com/docs/5.0/components/dropdowns/
- Tabler.io Dropdown examples: https://preview.tabler.io/dropdowns.html
- Popper.js positioning: https://popper.js.org/
