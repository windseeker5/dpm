# Phase 3: Image Handling Implementation Plan

**Created:** January 9, 2025  
**Purpose:** Convert inline base64 images to hosted URLs for better deliverability  
**Expected Impact:** 20% spam reduction  
**Status:** Ready for implementation  

---

## Current System Analysis

### How Images Currently Work:
1. **Compiled Templates**: Store images as base64 in `inline_images.json`
2. **Email Sending**: Loads base64 data and embeds as `MIMEImage` attachments
3. **Template References**: Use `cid:image_name` references in HTML
4. **QR Codes**: Generated dynamically per email using `qrcode.make()`
5. **Hero Images**: Loaded from `static/uploads/{activity_id}_hero.png`
6. **Logos**: Loaded from `static/uploads/{activity_id}_owner_logo.png` or defaults

### Problems with Current System:
- ❌ **Large email size**: Base64 encoding increases size by ~30%
- ❌ **Spam signals**: Email providers flag emails with many embedded images
- ❌ **Poor caching**: Images re-sent with every email
- ❌ **Memory usage**: Large images loaded into memory for each email
- ❌ **QR codes unoptimized**: Default qrcode library creates large images

---

## Implementation Plan

### 3.1 Create Hosted Image URL System

#### A. Directory Structure
Create subdirectories in `static/uploads/`:
```bash
static/uploads/
├── qr/              # QR codes by pass_code
├── heroes/          # Hero images by activity_id  
├── logos/           # Logo images by activity_id or org
└── email_assets/    # Template default images
```

#### B. Image URL Generation Functions
```python
def generate_image_urls(context, base_url):
    """Generate URLs for email images based on context"""
    urls = {}
    
    # QR code URL
    if 'pass_code' in context:
        urls['qr_code'] = f"{base_url}/static/uploads/qr/{context['pass_code']}.png"
    
    # Hero image URL
    if 'activity_id' in context:
        urls['hero_image'] = f"{base_url}/static/uploads/heroes/{context['activity_id']}.jpg"
    
    # Logo URL
    if 'organization_id' in context:
        urls['logo'] = f"{base_url}/static/uploads/logos/org_{context['organization_id']}.png"
    elif 'activity_id' in context:
        urls['logo'] = f"{base_url}/static/uploads/logos/{context['activity_id']}_owner_logo.png"
    
    return urls
```

#### C. Image Storage Functions
```python
def save_qr_code_to_static(pass_code, qr_data, base_url):
    """Save QR code to static directory and return URL"""
    os.makedirs('static/uploads/qr', exist_ok=True)
    file_path = f'static/uploads/qr/{pass_code}.png'
    
    with open(file_path, 'wb') as f:
        f.write(qr_data)
    
    return f"{base_url}/static/uploads/qr/{pass_code}.png"

def ensure_hero_image_accessible(activity_id, base_url):
    """Ensure hero image is accessible via URL"""
    source_path = f'static/uploads/{activity_id}_hero.png'
    dest_path = f'static/uploads/heroes/{activity_id}.jpg'
    
    os.makedirs('static/uploads/heroes', exist_ok=True)
    
    if os.path.exists(source_path):
        # Copy/convert if needed
        shutil.copy2(source_path, dest_path)
        return f"{base_url}/static/uploads/heroes/{activity_id}.jpg"
    
    return None
```

### 3.2 Optimize QR Code Generation

#### A. Size Optimization
```python
def generate_optimized_qr_code(pass_code):
    """Generate QR code optimized for email (200x200px)"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,  # Smaller box size for 200x200
        border=2,
    )
    qr.add_data(pass_code)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize to exactly 200x200
    img = img.resize((200, 200), Image.Resampling.LANCZOS)
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG", optimize=True)
    img_bytes.seek(0)
    
    return img_bytes
```

#### B. QR Code Caching
```python
def get_or_create_qr_code_url(pass_code, base_url):
    """Get existing QR code URL or create new one"""
    qr_path = f'static/uploads/qr/{pass_code}.png'
    
    if os.path.exists(qr_path):
        return f"{base_url}/static/uploads/qr/{pass_code}.png"
    
    # Generate new QR code
    qr_data = generate_optimized_qr_code(pass_code).read()
    return save_qr_code_to_static(pass_code, qr_data, base_url)
```

### 3.3 Update Email System

#### A. Modify send_email() Function
```python
def send_email(subject, to_email, template_name=None, context=None, use_hosted_images=True, **kwargs):
    # ... existing organization detection code ...
    
    if use_hosted_images:
        # Generate image URLs instead of inline data
        image_urls = generate_image_urls(context, base_url)
        context.update(image_urls)
        
        # Save QR code if needed
        if 'pass_code' in context:
            context['qr_code_url'] = get_or_create_qr_code_url(context['pass_code'], base_url)
        
        # No inline_images needed
        inline_images = {}
    else:
        # Fallback to current inline system
        inline_images = load_inline_images_from_compiled_template(template_name)
    
    # ... rest of function unchanged ...
```

#### B. Update Templates
Replace `cid:` references with URL references:
```html
<!-- OLD (inline) -->
<img src="cid:qr_code" alt="QR Code" width="200" height="200">
<img src="cid:hero_new_pass" alt="Hero Image" width="600">

<!-- NEW (hosted URLs) -->
<img src="{{ qr_code_url }}" alt="QR Code" width="200" height="200">
<img src="{{ hero_image_url }}" alt="Hero Image" width="600">
```

### 3.4 Migration Strategy

#### A. Gradual Rollout
1. **Phase 3a**: Create hosted image functions (backward compatible)
2. **Phase 3b**: Update one template type (newPass) to use hosted URLs
3. **Phase 3c**: Test and validate hosted URLs work properly
4. **Phase 3d**: Convert remaining templates
5. **Phase 3e**: Remove inline image system

#### B. Backward Compatibility
Keep `use_hosted_images` parameter to allow fallback:
```python
# New way (Phase 3)
send_email(subject, email, template, context, use_hosted_images=True)

# Old way (fallback)
send_email(subject, email, template, context, use_hosted_images=False)
```

---

## Implementation Steps

### Step 1: Create Infrastructure (30 mins)
1. Create directory structure in `static/uploads/`
2. Add image URL generation functions
3. Add optimized QR code generation function
4. Add image caching logic

### Step 2: Update Email System (20 mins)
1. Modify `send_email()` function to support hosted images
2. Add `use_hosted_images` parameter with default True
3. Update context to include image URLs

### Step 3: Update Templates (15 mins)
1. Update newPass template to use `{{ image_urls }}` instead of `cid:`
2. Recompile newPass template
3. Test with one email

### Step 4: Test & Validate (15 mins)
1. Send test email with newPass template
2. Verify images load correctly
3. Check email size reduction
4. Test QR code functionality

### Step 5: Complete Migration (30 mins)
1. Update remaining 5 templates
2. Recompile all templates
3. Test each template type
4. Remove inline image fallback (optional)

---

## Expected Results

### Email Size Reduction
- **Before**: ~500KB average (with inline base64 images)
- **After**: ~20KB average (with hosted URLs)
- **Savings**: ~95% size reduction per email

### Deliverability Improvement
- **Fewer spam signals**: No embedded images
- **Better caching**: Images cached by email providers
- **Faster loading**: Images load asynchronously
- **Mobile friendly**: Better rendering on mobile devices

### Performance Benefits
- **Memory usage**: ~80% reduction in email processing memory
- **Send speed**: Faster email generation and sending
- **Storage**: QR codes cached on disk, not regenerated

---

## Testing Strategy

### 1. Automated Tests
```python
def test_hosted_image_urls():
    context = {'pass_code': 'TEST123', 'activity_id': 5, 'organization_id': 1}
    urls = generate_image_urls(context, 'https://test.minipass.me')
    
    assert 'qr_code_url' in urls
    assert 'hero_image_url' in urls
    assert urls['qr_code_url'].startswith('https://test.minipass.me')

def test_qr_code_optimization():
    qr_data = generate_optimized_qr_code('TEST123')
    assert qr_data is not None
    # TODO: Check image size is ~200x200 and file size < 10KB
```

### 2. Integration Tests
1. Send test email with hosted images
2. Verify all images accessible via URLs
3. Test from different subdomains (LHGI, etc.)
4. Validate QR code scanning still works

### 3. Performance Tests
1. Measure email size before/after
2. Measure memory usage during email generation
3. Test email sending speed improvement

---

## Risk Mitigation

### 1. Image Accessibility Issues
- **Risk**: Images not accessible via URL
- **Mitigation**: Keep `use_hosted_images=False` fallback option
- **Test**: Verify URLs work from external browser

### 2. QR Code Functionality
- **Risk**: QR codes don't scan properly after optimization  
- **Mitigation**: Test scanning after size optimization
- **Fallback**: Keep original QR generation as backup

### 3. Template Compatibility
- **Risk**: Templates break when switching to URLs
- **Mitigation**: Test each template individually
- **Rollback**: Keep compiled templates with inline images as backup

### 4. Subdomain Issues
- **Risk**: Images don't load from subdomain URLs
- **Mitigation**: Test with actual subdomain setup
- **Fix**: Ensure proper CORS headers if needed

---

## Success Metrics

| Metric | Current | Target | 
|--------|---------|--------|
| Average email size | ~500KB | <50KB |
| Email generation time | ~2s | <0.5s |
| Memory per email | ~50MB | <10MB |
| QR code file size | ~50KB | <10KB |
| Image load time | N/A (embedded) | <1s |

---

## Notes

- This is a significant architectural change
- Requires careful testing before full rollout
- Benefits compound: smaller emails + better deliverability + faster sending
- QR code optimization alone will save significant bandwidth
- Templates become cleaner and more maintainable