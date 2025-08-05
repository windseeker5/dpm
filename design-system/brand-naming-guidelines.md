# Brand Naming Guidelines - minipass

## Official Brand Name Format

### ✅ CORRECT: "minipass"
- **Always lowercase**
- **Always one word**
- **No spaces, no hyphens, no capitals**

### ❌ INCORRECT Formats:
- ~~MiniPass~~ (incorrect capitalization)
- ~~Mini Pass~~ (incorrect spacing)
- ~~mini-pass~~ (incorrect hyphenation)
- ~~MINIPASS~~ (incorrect all caps)
- ~~Minipass~~ (incorrect first letter capitalization)

## Usage Examples

### In Code/Templates
```html
<h1 class="brand-title">minipass</h1>
<title>Sign In - minipass</title>
<meta property="og:site_name" content="minipass">
```

### In Text Content
- "Welcome to minipass"
- "minipass Digital Passport Management"
- "© 2025 minipass.me"
- "Powered by minipass"

### In URLs and Domains
- ✅ minipass.me
- ✅ app.minipass.me
- ✅ api.minipass.me

## Typography Application

### Headers and Titles
```css
.brand-title {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  text-transform: none; /* Never use text-transform: capitalize */
}
```

### In Navigation
```html
<!-- Header logo text -->
<span class="org-name-responsive">minipass</span>

<!-- Navigation breadcrumbs -->
<nav aria-label="breadcrumb">
  <ol class="breadcrumb">
    <li class="breadcrumb-item"><a href="/">minipass</a></li>
    <li class="breadcrumb-item active">Dashboard</li>
  </ol>
</nav>
```

## Rationale

### Why "minipass" (lowercase)?
1. **Modern SaaS Aesthetic**: Follows contemporary tech naming (stripe, slack, zoom)
2. **Clean Typography**: Lowercase creates visual consistency and reduces visual noise
3. **Brand Personality**: Approachable, modern, and professional without being corporate
4. **Digital Native**: Optimized for digital interfaces and modern design systems

### Why One Word?
1. **Domain Consistency**: Matches the minipass.me domain structure
2. **Easy Recognition**: Single unit creates stronger brand memory
3. **Flexible Usage**: Works in tight spaces and various contexts
4. **Technical Benefits**: Better for database fields, API endpoints, and code

## Implementation Checklist

### Immediate Updates Required:
- [ ] Login page title: "minipass" (✅ DONE)
- [ ] All navigation elements
- [ ] Email templates
- [ ] Footer copyright text
- [ ] Meta tags and SEO

### Files to Update:
- `/templates/base.html` - Header navigation
- `/templates/login.html` - Brand title (✅ DONE)
- All email templates in `/templates/email_templates/`
- Any marketing or documentation files

## Brand Voice Impact

The lowercase "minipass" reinforces our brand personality:
- **Approachable**: Not intimidating or overly corporate
- **Modern**: Aligns with contemporary SaaS design patterns
- **Professional**: Clean and consistent without being sterile
- **Trustworthy**: Consistent application builds user confidence

## Design System Integration

This naming guideline integrates with our existing design system:
- **Color System**: Works with our blue-purple gradient palette
- **Typography**: Complements our Inter font choices
- **Visual Identity**: Supports our shield-based security branding
- **User Experience**: Creates cohesive brand recognition across all touchpoints

---

**Last Updated**: August 4, 2025  
**Status**: Active Brand Guideline  
**Implementation**: Required across all interfaces