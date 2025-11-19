# Implementation Plan: Custom Payment Instructions Toggle

**Created:** 2025-11-18
**Status:** Ready for Implementation
**Estimated Complexity:** Medium
**Files to Modify:** 5 files

---

## 🚨 CRITICAL CONSTRAINTS - READ FIRST

### ⚠️ CONSTRAINT #1: Use Existing Design System Components ONLY
- **DO NOT improvise UI components**
- Use the SAME toggle pattern from `activity_form.html` (lines 164-173):
  ```html
  <label class="form-check form-switch">
    <input class="form-check-input" type="checkbox" id="toggleCustomPaymentInstructions">
    <span class="form-check-label">Use custom payment instructions</span>
  </label>
  ```
- Maintain standardization across all pages
- Reference: `docs/DESIGN_SYSTEM.md` for all UI patterns

### ⚠️ CONSTRAINT #2: PRESERVE SIGNUP PAGE DESIGN (5 HOURS OF WORK)

**ABSOLUTELY NO CHANGES TO SIGNUP PAGE VISUAL DESIGN**

#### When Toggle is OFF (Default - 95% of users):
- ✅ ZERO changes to signup_form.html appearance
- ✅ Gray card displays exactly as it does now
- ✅ Structured format: Amount, Sessions, Location, Payment Interac
- ✅ All spacing, padding, colors, borders remain identical

#### When Toggle is ON (Custom - 5% of users):
- ✅ Gray card structure STAYS THE SAME
- ✅ Card shape, size, borders, shadows UNCHANGED
- ✅ ONLY the inner text content is replaced
- ✅ Add appropriate padding around custom text (maintain gray card's internal spacing)
- ✅ Gray card container itself does NOT change

**Visual Guarantee:**
```
DEFAULT MODE:          CUSTOM MODE:
┌─────────────┐       ┌─────────────┐
│ Montant     │       │             │
│ $200.00     │       │  Custom     │
│             │       │  payment    │
│ Sessions    │  -->  │  text here  │
│ 10 sessions │       │  with       │
│             │       │  padding    │
│ Location... │       │             │
│ Payment...  │       └─────────────┘
└─────────────┘       Same gray card!
```

The gray card is sacred. We only swap the content inside.

---

## Problem Statement

The "Payment Instructions" field in the Edit Passport Type modal is currently disconnected. In the previous signup version, this field was displayed, but the new beautiful signup page with the gray card doesn't use it.

**Current State:**
- Edit Passport Modal has a "Payment Instructions" textarea
- Signup page shows structured gray card (hardcoded format)
- payment_instructions field in database is not being used

**Desired State:**
- Default: Show beautiful structured gray card (no change)
- Optional: Allow users to replace gray card content with custom text
- Preserve both flexibility and beauty

---

## User Research Findings

From user clarification questions:

1. **Replacement Scope:** Replace ENTIRE gray card content (not just payment section)
2. **Preview Requirement:** Always show live preview of what users will see
3. **Migration Strategy:** All toggles default to OFF (clean migration, existing data ignored)

---

## Implementation Plan

### 1. Database Schema Changes

**File:** `models.py`

**Action:** Add new boolean field to PassportType model

```python
# Around line 103-118 in PassportType class
use_custom_payment_instructions = db.Column(db.Boolean, default=False, nullable=False)
```

**Migration Command:**
```bash
flask db migrate -m "Add use_custom_payment_instructions to PassportType"
flask db upgrade
```

---

### 2. Edit Passport Modal UI (activity_form.html)

**File:** `templates/activity_form.html`

**Location:** Edit Passport Type Modal (around lines 486-542)

**Changes to Add:**

#### A. Live Preview Section (Always Visible)
Add BEFORE the toggle section:

```html
<div class="col-12 mb-3">
  <label class="form-label">Current Signup Page Preview</label>
  <div id="paymentInstructionsPreview" class="border rounded p-3" style="background-color: #f8f9fa;">
    <!-- This will be dynamically populated with either structured or custom content -->
    <div id="previewStructured">
      <div class="row g-2">
        <div class="col-6">
          <div class="d-flex align-items-start gap-2">
            <i class="ti ti-currency-dollar text-muted"></i>
            <div>
              <div class="text-muted" style="font-size: 0.75rem;">Montant</div>
              <div style="font-size: 0.85rem;"><strong id="previewPrice">$200.00</strong></div>
            </div>
          </div>
        </div>
        <div class="col-6">
          <div class="d-flex align-items-start gap-2">
            <i class="ti ti-ticket text-muted"></i>
            <div>
              <div class="text-muted" style="font-size: 0.75rem;">Sessions incluses</div>
              <div style="font-size: 0.85rem;"><strong id="previewSessions">10 sessions</strong></div>
            </div>
          </div>
        </div>
        <div class="col-6">
          <div class="d-flex align-items-start gap-2">
            <i class="ti ti-map-pin text-muted"></i>
            <div>
              <div class="text-muted" style="font-size: 0.75rem;">Lieu</div>
              <div style="font-size: 0.85rem;">Activity Location</div>
            </div>
          </div>
        </div>
        <div class="col-6">
          <div class="d-flex align-items-start gap-2">
            <i class="ti ti-credit-card text-muted"></i>
            <div>
              <div class="text-muted" style="font-size: 0.75rem;">Paiement Interac</div>
              <div style="font-size: 0.85rem;"><strong>lhgi@minipass.me</strong></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div id="previewCustom" style="display: none;">
      <!-- Custom text preview will be shown here -->
      <div class="p-3" id="customTextPreview" style="white-space: pre-wrap;"></div>
    </div>
  </div>
  <small class="form-text text-muted">This is exactly what users will see on the signup page</small>
</div>
```

#### B. Toggle Switch Section
Add AFTER preview section:

```html
<div class="col-12 mb-3">
  <label class="form-check form-switch">
    <input class="form-check-input" type="checkbox" id="useCustomPaymentInstructions" onchange="togglePaymentInstructionsMode()">
    <span class="form-check-label">Use custom payment instructions instead of default structured display</span>
  </label>
  <small class="form-text text-muted">Enable this to replace the entire gray card content with your own custom message</small>
</div>
```

#### C. Payment Instructions Textarea (Modified)
Update existing textarea to show/hide based on toggle:

```html
<div class="col-12" id="customPaymentInstructionsSection" style="display: none;">
  <label class="form-label">Custom Payment Instructions</label>
  <textarea class="form-control"
            id="editPassportTypeInstructions"
            rows="5"
            placeholder="Enter your custom payment instructions. This will replace the entire gray card content on the signup page."
            oninput="updateCustomPreview()"></textarea>
  <div class="form-text">This text will replace all structured information in the gray card</div>
</div>
```

#### D. JavaScript Functions
Add to activity_form.html script section:

```javascript
function togglePaymentInstructionsMode() {
  const useCustom = document.getElementById('useCustomPaymentInstructions').checked;
  const customSection = document.getElementById('customPaymentInstructionsSection');
  const previewStructured = document.getElementById('previewStructured');
  const previewCustom = document.getElementById('previewCustom');

  if (useCustom) {
    customSection.style.display = 'block';
    previewStructured.style.display = 'none';
    previewCustom.style.display = 'block';
    updateCustomPreview();
  } else {
    customSection.style.display = 'none';
    previewStructured.style.display = 'block';
    previewCustom.style.display = 'none';
  }
}

function updateCustomPreview() {
  const customText = document.getElementById('editPassportTypeInstructions').value;
  const preview = document.getElementById('customTextPreview');

  if (customText.trim()) {
    preview.textContent = customText;
  } else {
    preview.innerHTML = '<em class="text-muted">Your custom instructions will appear here...</em>';
  }
}

function updateStructuredPreview() {
  // Update preview based on current form values
  const price = document.getElementById('editPassportTypePrice').value || '0.00';
  const sessions = document.getElementById('editPassportTypeSessions').value || '1';

  document.getElementById('previewPrice').textContent = '$' + parseFloat(price).toFixed(2);
  document.getElementById('previewSessions').textContent = sessions + ' session' + (sessions == 1 ? '' : 's');
}

// Update editPassportType() function to populate toggle state
function editPassportType(id) {
  const passportType = passportTypes.find(pt => pt.id == id) || getPassportTypeFromRow(id);
  if (!passportType) return;

  currentEditingId = id;

  // Existing field population...
  document.getElementById('editPassportTypeName').value = passportType.name || '';
  document.getElementById('editPassportTypeType').value = passportType.type || 'permanent';
  document.getElementById('editPassportTypePrice').value = passportType.price_per_user || '0.00';
  document.getElementById('editPassportTypeSessions').value = passportType.sessions_included || '1';
  document.getElementById('editPassportTypeRevenue').value = passportType.target_revenue || '0.00';
  document.getElementById('editPassportTypeInstructions').value = passportType.payment_instructions || '';

  // NEW: Populate toggle state
  const useCustom = passportType.use_custom_payment_instructions || false;
  document.getElementById('useCustomPaymentInstructions').checked = useCustom;
  togglePaymentInstructionsMode();

  // Update previews
  updateStructuredPreview();
  if (useCustom) {
    updateCustomPreview();
  }

  editPassportTypeModal.show();
}

// Update saveEditPassportType() function to save toggle state
function saveEditPassportType() {
  if (!currentEditingId) return;

  // Get all values...
  const name = document.getElementById('editPassportTypeName').value.trim();
  const type = document.getElementById('editPassportTypeType').value;
  const price = document.getElementById('editPassportTypePrice').value;
  const sessions = document.getElementById('editPassportTypeSessions').value;
  const revenue = document.getElementById('editPassportTypeRevenue').value;
  const instructions = document.getElementById('editPassportTypeInstructions').value.trim();

  // NEW: Get toggle state
  const useCustom = document.getElementById('useCustomPaymentInstructions').checked;

  // Validation...
  if (!name) {
    alert('Please enter a passport type name');
    return;
  }

  // Update passport type object
  const updatedPassportType = {
    id: currentEditingId,
    name: name,
    type: type,
    price_per_user: price,
    sessions_included: sessions,
    target_revenue: revenue,
    payment_instructions: instructions,
    use_custom_payment_instructions: useCustom  // NEW field
  };

  // Update in array and re-render...
  const index = passportTypes.findIndex(pt => pt.id == currentEditingId);
  if (index !== -1) {
    passportTypes[index] = updatedPassportType;
  }

  // Rest of save logic...
}

// Add input listeners to update preview in real-time
document.addEventListener('DOMContentLoaded', function() {
  const priceInput = document.getElementById('editPassportTypePrice');
  const sessionsInput = document.getElementById('editPassportTypeSessions');

  if (priceInput) priceInput.addEventListener('input', updateStructuredPreview);
  if (sessionsInput) sessionsInput.addEventListener('input', updateStructuredPreview);
});
```

---

### 3. Signup Page Display Logic (signup_form.html)

**File:** `templates/signup_form.html`

**Location:** Payment information gray card (lines 482-605)

**Current Code (lines 552-562):**
```html
<div class="{% if activity.location_address_formatted %}col-6{% else %}col-12{% endif %}">
  <div class="d-flex align-items-start gap-2">
    <i class="ti ti-credit-card text-muted"></i>
    <div>
      <div class="text-muted" style="font-size: 0.75rem;">Paiement Interac</div>
      <div style="font-size: 0.85rem;">
        <strong>{{ settings.get("PAYMENT_EMAIL_ADDRESS", "lhgi@minipass.me") }}</strong>
      </div>
    </div>
  </div>
</div>
```

**Replace Entire Gray Card Content Section (lines 482-605) with:**

```html
<div class="card mb-4" id="pricing-info" style="background-color: #f6f8fa; border: 1px solid #d1d9e0; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
  <div class="card-body p-4">
    {% if selected_passport_type and selected_passport_type.use_custom_payment_instructions and selected_passport_type.payment_instructions %}
      <!-- CUSTOM MODE: Show custom text with padding (maintains gray card structure) -->
      <div class="p-3" style="white-space: pre-wrap;">
        {{ selected_passport_type.payment_instructions }}
      </div>
    {% else %}
      <!-- DEFAULT MODE: Show structured format (UNCHANGED from current design) -->
      <div class="row g-3">
        <div class="{% if activity.location_address_formatted %}col-6{% else %}col-12{% endif %}">
          <div class="d-flex align-items-start gap-2">
            <i class="ti ti-currency-dollar text-muted"></i>
            <div>
              <div class="text-muted" style="font-size: 0.75rem;">Montant</div>
              <div style="font-size: 0.85rem;">
                <strong>${{ selected_passport_type.price_per_user if selected_passport_type else passport_types[0].price_per_user }}</strong>
              </div>
            </div>
          </div>
        </div>

        <div class="{% if activity.location_address_formatted %}col-6{% else %}col-12{% endif %}">
          <div class="d-flex align-items-start gap-2">
            <i class="ti ti-ticket text-muted"></i>
            <div>
              <div class="text-muted" style="font-size: 0.75rem;">Sessions incluses</div>
              <div style="font-size: 0.85rem;">
                <strong>{{ selected_passport_type.sessions_included if selected_passport_type else passport_types[0].sessions_included }} session{{ 's' if (selected_passport_type.sessions_included if selected_passport_type else passport_types[0].sessions_included) > 1 else '' }}</strong>
              </div>
            </div>
          </div>
        </div>

        {% if activity.location_address_formatted %}
        <div class="col-6">
          <div class="d-flex align-items-start gap-2">
            <i class="ti ti-map-pin text-muted"></i>
            <div>
              <div class="text-muted" style="font-size: 0.75rem;">Lieu</div>
              <div style="font-size: 0.85rem;">{{ activity.location_address_formatted }}</div>
            </div>
          </div>
        </div>
        {% endif %}

        <div class="{% if activity.location_address_formatted %}col-6{% else %}col-12{% endif %}">
          <div class="d-flex align-items-start gap-2">
            <i class="ti ti-credit-card text-muted"></i>
            <div>
              <div class="text-muted" style="font-size: 0.75rem;">Paiement Interac</div>
              <div style="font-size: 0.85rem;">
                <strong>{{ settings.get("PAYMENT_EMAIL_ADDRESS", "lhgi@minipass.me") }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    {% endif %}
  </div>
</div>
```

**Key Points:**
- ✅ Gray card structure (`<div class="card mb-4" ...>`) UNCHANGED
- ✅ Card styling (background, border, shadow) PRESERVED EXACTLY
- ✅ Default mode: Shows existing structured layout (ZERO visual changes)
- ✅ Custom mode: Replaces content with `<div class="p-3">` for proper padding
- ✅ `white-space: pre-wrap` preserves line breaks in custom text

---

### 4. Backend Logic Updates (app.py)

**File:** `app.py`

#### A. Update Save Passport Type Functions

**Location 1:** `save_passport_types()` function (around line 1662)

```python
# Add to passport type data extraction
use_custom = passport_data.get('use_custom_payment_instructions', False)

# Add to PassportType creation/update
new_passport_type = PassportType(
    activity_id=activity_id,
    name=passport_data.get('name', '').strip(),
    type=passport_data.get('type', 'permanent'),
    price_per_user=passport_data.get('price_per_user', 0.0),
    sessions_included=passport_data.get('sessions_included', 1),
    target_revenue=passport_data.get('target_revenue', 0.0),
    payment_instructions=passport_data.get('payment_instructions', '').strip(),
    use_custom_payment_instructions=use_custom  # NEW
)
```

**Location 2:** `create_or_edit_activity()` POST handler (around lines 1813, 1832)

```python
# When creating new passport types
payment_instructions=pt_data.get('payment_instructions', '').strip(),
use_custom_payment_instructions=pt_data.get('use_custom_payment_instructions', False)  # NEW

# When updating existing passport types
pt.payment_instructions = pt_data.get('payment_instructions', '').strip()
pt.use_custom_payment_instructions = pt_data.get('use_custom_payment_instructions', False)  # NEW
```

#### B. Update Load Passport Type Functions

**Location:** `create_or_edit_activity()` GET handler (around line 1897)

```python
# Add to passport type dict
'payment_instructions': pt.payment_instructions or '',
'use_custom_payment_instructions': pt.use_custom_payment_instructions or False  # NEW
```

**Location:** Signup route (around line 1922) - Already loads full PassportType object, no changes needed

---

### 5. Database Migration

**Create migration file:**

```bash
flask db migrate -m "Add use_custom_payment_instructions toggle to PassportType"
```

**Expected migration content:**
```python
def upgrade():
    with op.batch_alter_table('passport_type', schema=None) as batch_op:
        batch_op.add_column(sa.Column('use_custom_payment_instructions', sa.Boolean(), nullable=False, server_default='0'))

def downgrade():
    with op.batch_alter_table('passport_type', schema=None) as batch_op:
        batch_op.drop_column('use_custom_payment_instructions')
```

**Run migration:**
```bash
flask db upgrade
```

---

## Testing Plan

### 1. Database Migration Testing
- [ ] Run migration successfully
- [ ] Verify all existing passport types have `use_custom_payment_instructions = False`
- [ ] Check database schema with `sqlite3 instance/minipass.db ".schema passport_type"`

### 2. Edit Passport Modal Testing (Desktop)
- [ ] Open edit passport modal
- [ ] Verify preview shows structured format by default
- [ ] Update price → Preview updates in real-time
- [ ] Update sessions → Preview updates in real-time
- [ ] Toggle ON custom mode → Textarea appears, preview switches
- [ ] Type in textarea → Custom preview updates in real-time
- [ ] Toggle OFF → Textarea hides, structured preview returns
- [ ] Save changes → Modal closes, data persists

### 3. Edit Passport Modal Testing (Mobile 375px)
- [ ] All above tests on mobile viewport
- [ ] Preview section is responsive
- [ ] Toggle switch works on touch
- [ ] Textarea is properly sized

### 4. Signup Page Testing - Default Mode (Toggle OFF)
- [ ] Load signup page for passport with toggle OFF
- [ ] **CRITICAL:** Verify gray card looks EXACTLY as it does now
- [ ] Check padding, spacing, colors, borders are UNCHANGED
- [ ] Verify structured format: Amount, Sessions, Location, Payment
- [ ] Test on desktop (1920x1080)
- [ ] Test on mobile (375x667)
- [ ] **Compare side-by-side with current production to confirm ZERO visual changes**

### 5. Signup Page Testing - Custom Mode (Toggle ON)
- [ ] Enable toggle in edit modal, add custom text, save
- [ ] Load signup page
- [ ] **CRITICAL:** Verify gray card structure is IDENTICAL (same card, border, shadow)
- [ ] Verify custom text appears with proper padding (p-3)
- [ ] Check line breaks are preserved (white-space: pre-wrap)
- [ ] Test on desktop (1920x1080)
- [ ] Test on mobile (375x667)
- [ ] **Confirm gray card container itself has NOT changed**

### 6. Edge Cases
- [ ] Empty custom text with toggle ON → Should show empty card with padding
- [ ] Very long custom text → Should wrap properly within card
- [ ] Special characters in custom text → Should display correctly
- [ ] Multiple passport types → Each maintains its own toggle state
- [ ] Toggle ON then back OFF → Returns to structured format

### 7. Backward Compatibility
- [ ] Existing passport types with old payment_instructions data
- [ ] Verify toggle defaults to OFF (structured display shown)
- [ ] Old data is preserved in database but not displayed unless toggle is enabled

---

## Rollback Plan

If anything breaks:

1. **Revert signup_form.html:**
   ```bash
   git checkout HEAD -- templates/signup_form.html
   ```

2. **Revert database migration:**
   ```bash
   flask db downgrade
   ```

3. **Revert other files:**
   ```bash
   git checkout HEAD -- templates/activity_form.html models.py app.py
   ```

---

## Success Criteria

✅ **Primary Goal:** Toggle system works without breaking 5 hours of signup page design work

✅ **Visual Guarantee:**
- Default mode (toggle OFF): Signup page looks EXACTLY as it does now
- Custom mode (toggle ON): Gray card structure unchanged, only inner content replaced

✅ **Functionality:**
- Toggle switches correctly in edit modal
- Preview updates in real-time
- Data saves and loads correctly
- Signup page displays correct content based on toggle state

✅ **Code Quality:**
- Uses existing design system components (form-check form-switch)
- No improvised UI components
- Follows established patterns
- Properly tested on desktop and mobile

---

## Files Modified Summary

1. **models.py** - Add `use_custom_payment_instructions` field
2. **templates/activity_form.html** - Add toggle, preview, and update JavaScript
3. **templates/signup_form.html** - Add conditional logic for gray card content
4. **app.py** - Update save/load functions for new field
5. **Database migration** - Add new column

**Total Lines Changed:** ~150 lines
**Risk Level:** Medium (touching signup page that took 5 hours to perfect)
**Mitigation:** Extensive testing, clear rollback plan, preserving exact gray card structure

---

## Post-Implementation Checklist

After implementation is complete:

- [ ] Take screenshots of default mode (toggle OFF) - compare to current production
- [ ] Take screenshots of custom mode (toggle ON) - verify card structure unchanged
- [ ] Document any issues encountered
- [ ] Update user documentation if needed
- [ ] Monitor for bug reports from users

---

**END OF PLAN**
