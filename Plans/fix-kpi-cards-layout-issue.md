# Fix Plan for KPI Cards Layout Issue

## Problem Summary
- **Desktop**: KPI cards are stacking vertically instead of showing 4 across in a grid
- **Mobile**: Carousel/slider functionality is not working
- **Root Cause**: CSS specificity conflicts where mobile styles are overriding desktop styles

## The Issues Identified

### 1. CSS Specificity Problem
- Desktop CSS uses `.kpi-section .kpi-cards-wrapper` selector
- Mobile CSS uses `div.kpi-cards-wrapper` which has HIGHER specificity
- Mobile styles are bleeding into desktop view

### 2. JavaScript Errors
- Carousel initialization lacks null checks
- `offsetWidth` calls on potentially null elements causing errors
- No error handling in `initializeCarouselIndicators()` function

### 3. Media Query Scope Issue
- Mobile media query at line 1082 isn't properly constraining styles to mobile only
- The `!important` flags in mobile CSS are overriding desktop

## The Fix - 6 Specific Changes

### 1. Fix CSS Specificity (lines 1075-1109 in dashboard.html)
```css
/* Desktop - Higher specificity */
.kpi-section .kpi-cards-wrapper {
  display: grid !important;
  grid-template-columns: repeat(4, 1fr) !important;
  gap: 1rem !important;
}

/* Mobile - Properly scoped */
@media screen and (max-width: 767.98px) {
  .kpi-section .kpi-cards-wrapper {
    display: flex !important;
    flex-direction: row !important;
    overflow-x: auto !important;
    grid-template-columns: none !important;
    /* rest of mobile styles */
  }
}
```

### 2. Fix Mobile Media Query Scope
- Ensure mobile CSS at line 1082-1109 is INSIDE the media query block
- Remove `div.kpi-cards-wrapper` selector that has too high specificity
- Use consistent `.kpi-section .kpi-cards-wrapper` selector for both

### 3. Add JavaScript Error Handling (lines 2306-2343)
```javascript
function initializeCarouselIndicators() {
  const carousel = document.querySelector('.kpi-cards-wrapper');
  const indicators = document.querySelectorAll('.indicator');
  
  if (!carousel || indicators.length === 0) return;
  
  function updateActiveIndicator() {
    try {
      const scrollLeft = carousel.scrollLeft;
      const cardElement = carousel.querySelector('.kpi-card-mobile');
      
      // Add null check
      if (!cardElement) {
        console.warn('No .kpi-card-mobile element found');
        return;
      }
      
      const cardWidth = cardElement.offsetWidth + 16;
      const activeIndex = Math.round(scrollLeft / cardWidth);
      
      indicators.forEach((indicator, index) => {
        if (index === activeIndex) {
          indicator.classList.add('active');
        } else {
          indicator.classList.remove('active');
        }
      });
    } catch (error) {
      console.error('Error updating carousel indicators:', error);
    }
  }
  
  // Rest of function with similar error handling
}
```

### 4. HTML Structure (No Changes Needed)
- Keep `.kpi-card-mobile` wrapper divs
- Keep `.kpi-cards-wrapper` container
- Keep indicators div with `.kpi-scroll-indicators`

### 5. Testing Requirements
**Desktop (1200px width):**
- 4 KPI cards displayed horizontally in a grid
- Equal width cards with proper spacing
- No scrolling needed

**Mobile (375px width):**
- Horizontal scrollable carousel
- Each card 280px wide
- Smooth scroll-snap behavior
- Working scroll indicators

### 6. Testing with MCP Playwright
```
URL: http://localhost:5000
Username: kdresdell@gmail.com
Password: admin123

Tests to run:
1. Login to dashboard
2. Resize to 1200px width - verify 4 cards horizontal
3. Resize to 375px width - verify carousel works
4. Test scroll indicators on mobile
5. Check browser console for JavaScript errors
```

## Expected Result
- **Desktop**: 4 KPI cards in a horizontal grid layout
- **Mobile**: Swipeable carousel with working dot indicators
- **No JavaScript errors** in console
- **Clean, responsive** dashboard

## Files to Modify
1. `/home/kdresdell/Documents/DEV/minipass_env/app/templates/dashboard.html`
   - Lines 1075-1109: CSS fixes
   - Lines 2306-2343: JavaScript error handling

## Implementation Order
1. Fix CSS specificity issues first
2. Add JavaScript error handling
3. Test desktop view
4. Test mobile view
5. Verify scroll indicators
6. Check for console errors