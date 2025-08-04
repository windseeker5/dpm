# Navigation System Wireframes

## Current vs. Proposed Navigation

### CURRENT: Dual Navigation (Problems)
```
┌─────────────────────────────────────────────────────────────────┐
│ [DARK HEADER: Heavy bg-gray-800]                               │
│ 🌈 GRADIENT LOGO    "ORG NAME"           [👤 Admin Dropdown]   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ [LIGHT SECONDARY: bg-white border-bottom]                      │
│ 🏠 Home  📊 Activities  🎫 Passports  ✅ Signups  📋 Surveys  │
│                                                  [Scan Button] │
└─────────────────────────────────────────────────────────────────┘
```

**Issues:**
- Visual hierarchy conflict between dark/light navs
- Heavy dark header dominates interface
- Bright gradient text lacks professionalism
- Mobile navigation complexity

### PROPOSED: Unified Navigation System

#### Option A: Single Header Navigation (Recommended)
```
┌─────────────────────────────────────────────────────────────────┐
│ [GRADIENT HEADER: Blue→Purple Professional]                    │
│                                                                 │
│ 📱 minipass          🏠 Dashboard  📊 Activities  🎫 Passports │
│                      ✅ Signups   📋 Surveys   🤖 AI Analytics │
│                                                                 │
│                      [🔍 Scan Passport]    [👤 Admin Dropdown] │
└─────────────────────────────────────────────────────────────────┘
```

#### Option B: Sidebar Navigation (Alternative)
```
┌──────────┬──────────────────────────────────────────────────────┐
│          │ [MINIMAL HEADER: White with org name]               │
│          │ Organization Name                    [👤 Dropdown]  │
│          ├──────────────────────────────────────────────────────┤
│ 📱       │                                                      │
│ minipass │ MAIN CONTENT AREA                                   │
│          │                                                      │
│ 🏠 Dash  │ [Dashboard KPI cards and content here]             │
│ 📊 Act   │                                                      │
│ 🎫 Pass  │                                                      │
│ ✅ Sign  │                                                      │
│ 📋 Surv  │                                                      │
│ 🤖 AI    │                                                      │
│          │                                                      │
│ [🔍 Scan]│                                                      │
└──────────┴──────────────────────────────────────────────────────┘
```

## Detailed Wireframe: Option A (Recommended)

### Desktop Layout (1200px+)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          UNIFIED NAVIGATION HEADER                          │
│  Background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)            │
│  Height: 64px, White text, Professional spacing                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ [LOGO]                    [NAVIGATION ITEMS]              [USER ACTIONS]   │
│                                                                             │
│ 📱 minipass              🏠 Dashboard     📊 Activities                    │
│ Font: Inter 600          ✅ Signups       🎫 Passports     [🔍 Scan Pass] │
│ Size: 24px               📋 Surveys       🤖 AI Analytics   [👤 Profile]   │
│ Color: White             Font: Inter 500, 16px, White                      │
│                          Spacing: 32px between items                       │
└─────────────────────────────────────────────────────────────────────────────┘

Hover States:
- Navigation items: White → rgba(255,255,255,0.8) + subtle underline
- Buttons: Maintain solid background with slight opacity change
- Logo: No hover state (not clickable on app pages)
```

### Tablet Layout (768px - 1199px)
```
┌─────────────────────────────────────────────────────────────────┐
│                     RESPONSIVE NAVIGATION                       │
│  Same gradient background, adjusted spacing                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📱 minipass      🏠 📊 🎫 ✅ 📋 🤖     [🔍] [👤]              │
│                                                                 │
│ Font: 20px       Icons + abbreviated labels                     │
│                  Spacing: 24px between items                    │
└─────────────────────────────────────────────────────────────────┘
```

### Mobile Layout (< 768px)
```
┌─────────────────────────────────────────────────────────────────┐
│                    MOBILE NAVIGATION                            │
│  Collapsible menu system                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 📱 minipass                    [☰] [🔍] [👤]                  │
│                                                                 │
│ [Hamburger Menu Overlay when opened:]                           │
│ ┌─ SLIDE-OUT MENU ─┐                                           │
│ │ 🏠 Dashboard      │                                           │
│ │ 📊 Activities     │                                           │
│ │ 🎫 Passports      │                                           │
│ │ ✅ Signups        │                                           │
│ │ 📋 Surveys        │                                           │
│ │ 🤖 AI Analytics   │                                           │
│ │ ─────────────     │                                           │
│ │ 🔍 Scan Passport  │                                           │
│ │ ⚙️ Settings       │                                           │
│ │ 🚪 Logout         │                                           │
│ └───────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Navigation Component Specifications

### Logo Treatment
```css
.navbar-brand {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 1.5rem;
  color: white;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.navbar-brand-icon {
  width: 32px;
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}
```

### Navigation Items
```css
.navbar-nav {
  display: flex;
  gap: 2rem;
  align-items: center;
}

.nav-link {
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 1rem;
  color: white;
  padding: 0.5rem 0;
  position: relative;
  text-decoration: none;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: rgba(255, 255, 255, 0.8);
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: white;
  border-radius: 1px;
}
```

### Action Buttons
```css
.navbar-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.btn-scan {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-scan:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}
```

## Mobile Menu Details

### Slide-out Menu Specifications
```css
.mobile-menu {
  position: fixed;
  top: 64px;
  left: -280px;
  width: 280px;
  height: calc(100vh - 64px);
  background: white;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.15);
  transition: left 0.3s ease;
  z-index: 1050;
}

.mobile-menu.open {
  left: 0;
}

.mobile-menu-overlay {
  position: fixed;
  top: 64px;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 1049;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
}

.mobile-menu-overlay.open {
  opacity: 1;
  visibility: visible;
}
```

## Implementation Priority

### Phase 1: Basic Structure
1. Replace dual navigation with single header
2. Implement gradient background
3. Update logo treatment
4. Basic responsive behavior

### Phase 2: Interaction States
1. Hover effects
2. Active states
3. Mobile menu functionality
4. Smooth transitions

### Phase 3: Accessibility & Polish
1. Keyboard navigation
2. Screen reader support
3. Focus indicators
4. Animation refinements

## Benefits of New Navigation

### User Experience
- **Reduced cognitive load**: Single navigation reduces decision complexity
- **Better visual hierarchy**: Content gets appropriate focus
- **Improved mobile experience**: Dedicated mobile menu patterns
- **Professional appearance**: Clean, modern aesthetic

### Development Benefits
- **Simplified HTML structure**: Fewer navigation components to maintain
- **Consistent styling**: Single theme across navigation
- **Better responsive patterns**: Clear breakpoint behaviors
- **Easier customization**: Centralized navigation styling