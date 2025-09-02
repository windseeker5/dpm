# Quick Share Links for Passport Types - Implementation Plan

## Overview
Replace "X signups" with passport type count and add a share icon that copies signup URLs to clipboard

## Implementation Steps

### 1. **HTML Modification** (`activity_dashboard.html` line 556-563)
Replace the current share stat with:
```html
<div class="stat share-stat">
  <i class="ti ti-share"></i>
  <span>{{ passport_types|length }} {{ 'type' if passport_types|length == 1 else 'types' }}</span>
  <div class="share-dropdown" style="display: none;">
    {% for pt in passport_types %}
    <a href="#" class="share-link" 
       data-url="{{ url_for('signup', activity_id=activity.id, passport_type_id=pt.id, _external=True) }}"
       onclick="copyToClipboard(event, this)">
      {{ pt.name }}
    </a>
    {% endfor %}
  </div>
</div>
```

### 2. **JavaScript** (Add to activity_dashboard.html, ~15 lines)
```javascript
function copyToClipboard(event, element) {
  event.preventDefault();
  const url = element.dataset.url;
  navigator.clipboard.writeText(url).then(() => {
    // Visual feedback
    element.textContent += ' ✓';
    setTimeout(() => {
      element.textContent = element.textContent.replace(' ✓', '');
    }, 2000);
  });
}

// Show/hide dropdown on hover
document.querySelector('.share-stat').addEventListener('mouseenter', function() {
  const dropdown = this.querySelector('.share-dropdown');
  if (dropdown && dropdown.children.length > 0) {
    dropdown.style.display = 'block';
  }
});

document.querySelector('.share-stat').addEventListener('mouseleave', function() {
  const dropdown = this.querySelector('.share-dropdown');
  if (dropdown) dropdown.style.display = 'none';
});
```

### 3. **CSS Additions** (`activity-header-clean.css`)
```css
.share-stat {
  position: relative;
  cursor: pointer;
}

.share-stat:hover i {
  color: #206bc4;
}

.share-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 8px 0;
  margin-top: 4px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  z-index: 1000;
  min-width: 180px;
}

.share-link {
  display: block;
  padding: 8px 12px;
  color: #374151;
  text-decoration: none;
  font-size: 13px;
}

.share-link:hover {
  background: #f3f4f6;
  color: #206bc4;
}
```

## Key Features
- Shows passport type count (e.g., "1 type" or "2 types")
- Gray share icon turns blue on hover
- For 1 passport type: Single click copies URL
- For 2+ passport types: Dropdown shows passport names, click copies specific URL
- Visual checkmark feedback when copied
- Clean, minimal code (~20 lines total JavaScript)

## Benefits
- Quick access to share signup links
- No more navigating through multiple screens
- Perfect for sharing via messenger or social media
- Maintains clean UI with minimal JavaScript