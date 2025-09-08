# Email Template System - Complete Flow Analysis & Fix Plan

## Current Flow Understanding

### 1. Template Creation & Compilation
- **Source Templates**: Located in `templates/email_templates/{type}/` (e.g., newPass/)
- **Compilation Process**: `compileEmailTemplate.py` converts images to base64 and creates `{type}_compiled/`
- **Compiled Output**: `index.html` with `cid:` references + `inline_images.json` with base64 data

### 2. Template Customization Flow
- **Storage**: Customizations saved in `activity.email_templates[template_type]` JSON
- **Custom Heroes**: Saved as `{activity_id}_{template_type}_hero.png` in uploads
- **Priority System**: Custom upload → Compiled default → Activity image (fallback)

### 3. Key Issues Identified

**Issue #1: Hero Image Recompilation Problem**
When user uploads custom hero, the system cannot properly reset to original compiled default because:
- Custom hero file persists even after "reset"
- No separation between "original compiled" vs "user customized compiled"

**Issue #2: Preview vs Edit Modal Inconsistency**
- Preview correctly shows compiled templates with customizations
- Edit modal might show different images due to priority logic

**Issue #3: Reset Function Limitations**
- Deletes custom hero file but doesn't preserve original compiled state
- No way to differentiate between "compiled default" and "recompiled with custom"

## Comprehensive Fix Plan

### Phase 1: Template Version Management
1. **Create Template Versioning System**
   - Add `original_compiled/` folders to preserve pristine compiled versions
   - Never modify original_compiled - it's the permanent source of truth
   - Keep `{type}_compiled/` for current active version

2. **Backup Original Compiled Templates**
   ```
   templates/email_templates/
   ├── newPass/                  # Source files
   ├── newPass_original/         # NEW: Backup of original compiled
   └── newPass_compiled/         # Active compiled (may be customized)
   ```

### Phase 2: Fix Hero Image Management
1. **Update `get_activity_hero_image()` Priority**:
   - Check custom upload first (`{activity_id}_{template_type}_hero.png`)
   - Load from `original_compiled` for defaults (not current compiled)
   - Activity image only as last resort

2. **Add Hero Image Tracking**:
   - Store flag in `activity.email_templates[type]['uses_custom_hero']`
   - Track original hero key for proper reset

### Phase 3: Improve Reset Functionality
1. **Enhanced Reset Process**:
   - Delete custom hero file
   - Copy `original_compiled` back to `compiled`
   - Clear customization flags in database
   - Ensure preview and edit show same default

2. **Add "Reset All Templates" Option**:
   - Batch reset for all template types
   - Restore all original compiled versions

### Phase 4: Fix Compilation Process
1. **Preserve Original Compilation**:
   - First compilation creates both `compiled` and `original_compiled`
   - Re-compilation only updates `compiled`
   - Add compilation timestamp tracking

2. **Smart Recompilation**:
   - Detect if template has customizations
   - Preserve custom uploads during recompilation
   - Merge custom data with new compilation

### Phase 5: Improve UI Consistency
1. **Unified Image Resolution**:
   - Use same `get_activity_hero_image()` for both edit modal and preview
   - Ensure consistent display across all views

2. **Add Visual Indicators**:
   - Show "Customized" badge when using custom hero
   - Display "Default" when using compiled template
   - Add tooltip showing image source

## Implementation Steps

1. **Backup current compiled templates** to `_original` folders
2. **Update `utils.py`**:
   - Fix `get_activity_hero_image()` to use original_compiled
   - Add version tracking functions
3. **Update `app.py`**:
   - Enhance reset function to restore from original
   - Fix edit modal to use correct image source
4. **Update compilation script**:
   - Create both compiled and original on first run
   - Add smart recompilation logic
5. **Test all scenarios**:
   - Fresh template → shows compiled default
   - Upload custom → shows custom
   - Reset → returns to original compiled
   - Recompile → preserves customizations

## Testing Checklist
- [ ] Edit modal shows correct default hero (person with certificate)
- [ ] Preview matches edit modal display
- [ ] Custom upload works and persists
- [ ] Reset returns to original compiled (not activity image)
- [ ] Email sending uses correct images
- [ ] All template types work consistently

## Technical Details

### File Structure After Implementation
```
templates/email_templates/
├── newPass/                      # Source template files
│   ├── index.html
│   ├── hero_new_pass.png
│   └── other_assets.png
├── newPass_original/             # Pristine compiled version (never modified)
│   ├── index.html
│   └── inline_images.json
├── newPass_compiled/             # Active compiled version
│   ├── index.html
│   └── inline_images.json
└── compileEmailTemplate.py       # Compilation script

static/uploads/
├── {activity_id}_{template}_hero.png  # Custom uploaded heroes
└── {activity_id}_owner_logo.png       # Custom logos
```

### Database Structure
```json
activity.email_templates = {
  "newPass": {
    "subject": "Custom subject",
    "title": "Custom title",
    "intro_text": "Custom intro",
    "conclusion_text": "Custom conclusion",
    "uses_custom_hero": true,
    "original_hero_key": "hero_new_pass",
    "last_customized": "2025-01-09T10:00:00Z"
  }
}
```

### Priority Resolution Logic
```python
def get_activity_hero_image(activity, template_type):
    # 1. Custom upload (highest priority)
    if exists(f"{activity.id}_{template_type}_hero.png"):
        return custom_hero
    
    # 2. Original compiled default
    if exists(f"{template_type}_original/inline_images.json"):
        return original_compiled_hero
    
    # 3. Current compiled (might be modified)
    if exists(f"{template_type}_compiled/inline_images.json"):
        return compiled_hero
    
    # 4. Activity image (last resort)
    if activity.image_filename:
        return activity_image
    
    return None
```

## Expected Outcomes

### Before Fix
- Edit modal shows wrong image (activity image instead of template default)
- Reset doesn't fully restore original template
- Preview and edit modal show different images
- Confusion about what is "default"

### After Fix
- Edit modal shows correct template default
- Reset fully restores original compiled template
- Preview and edit modal always match
- Clear distinction between original, customized, and activity images
- User can always return to pristine state

## Notes
- This plan maintains backward compatibility
- Existing customizations will be preserved
- Migration script needed for existing installations
- Consider adding audit log for template changes