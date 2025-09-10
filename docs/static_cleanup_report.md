# Static Folder Cleanup Report
Generated: 2025-01-10

## Executive Summary
Current static folder size: ~133MB  
Potential reduction: ~69MB (52%)  
Target size after cleanup: ~64MB

---

## Files and Folders to Delete - By Risk Level

### 🟢 **NO RISK - Safe to Delete (64MB+)**
These files are 100% unused and can be deleted immediately without any impact.

#### Backup Directories (59MB)
| Path | Size | Reason | Risk |
|------|------|--------|------|
| `/static/backups/` | 40MB | Old zip backups and database copies, not referenced anywhere | NO RISK |
| `/static/uploads_bk_ken/` | 19MB | Duplicate backup of uploads directory | NO RISK |

#### Unused Tabler CSS Files (2MB+)
| Path | Size | Reason | Risk |
|------|------|--------|------|
| `/static/tabler/css/tabler-marketing.css` | ~200KB | Marketing components not used | NO RISK |
| `/static/tabler/css/tabler-marketing.min.css` | ~150KB | Marketing components not used | NO RISK |
| `/static/tabler/css/tabler-marketing.rtl.css` | ~200KB | RTL marketing not used | NO RISK |
| `/static/tabler/css/tabler-marketing.rtl.min.css` | ~150KB | RTL marketing not used | NO RISK |
| `/static/tabler/css/tabler-flags.css` | ~100KB | Flag components not referenced | NO RISK |
| `/static/tabler/css/tabler-flags.min.css` | ~80KB | Flag components not referenced | NO RISK |
| `/static/tabler/css/tabler-flags.rtl.css` | ~100KB | RTL flags not used | NO RISK |
| `/static/tabler/css/tabler-flags.rtl.min.css` | ~80KB | RTL flags not used | NO RISK |
| `/static/tabler/css/tabler-payments.css` | ~50KB | Payment icons not used | NO RISK |
| `/static/tabler/css/tabler-payments.min.css` | ~40KB | Payment icons not used | NO RISK |
| `/static/tabler/css/tabler-payments.rtl.css` | ~50KB | RTL payments not used | NO RISK |
| `/static/tabler/css/tabler-payments.rtl.min.css` | ~40KB | RTL payments not used | NO RISK |
| `/static/tabler/css/tabler-socials.css` | ~30KB | Social icons not used | NO RISK |
| `/static/tabler/css/tabler-socials.min.css` | ~25KB | Social icons not used | NO RISK |
| `/static/tabler/css/tabler-socials.rtl.css` | ~30KB | RTL socials not used | NO RISK |
| `/static/tabler/css/tabler-socials.rtl.min.css` | ~25KB | RTL socials not used | NO RISK |
| `/static/tabler/css/tabler-vendors.css` | ~150KB | Vendor styles not used | NO RISK |
| `/static/tabler/css/tabler-vendors.min.css` | ~120KB | Vendor styles not used | NO RISK |
| `/static/tabler/css/tabler-vendors.rtl.css` | ~150KB | RTL vendors not used | NO RISK |
| `/static/tabler/css/tabler-vendors.rtl.min.css` | ~120KB | RTL vendors not used | NO RISK |
| `/static/tabler/css/demo.css` | ~50KB | Demo styles not needed | NO RISK |
| `/static/tabler/css/demo.min.css` | ~40KB | Demo styles not needed | NO RISK |
| `/static/tabler/css/demo.rtl.css` | ~50KB | RTL demo not used | NO RISK |
| `/static/tabler/css/demo.rtl.min.css` | ~40KB | RTL demo not used | NO RISK |
| All `.css.map` files in `/static/tabler/css/` | ~1MB | Source maps not needed in production | NO RISK |

#### Unused Tabler Image Directories (3MB+)
| Path | Size | Reason | Risk |
|------|------|--------|------|
| `/static/tabler/img/flags/` | ~1MB | Flag images not used anywhere | NO RISK |
| `/static/tabler/img/payments/` | ~500KB | Payment method icons not used | NO RISK |
| `/static/tabler/img/social/` | ~300KB | Social media icons not used | NO RISK |

#### Orphaned Files
| Path | Size | Reason | Risk |
|------|------|--------|------|
| `/static/minipass.css.backup` | 8.4KB | Old backup file | NO RISK |
| `/static/beep.wav` | 339KB | Audio file never referenced in code | NO RISK |
| `/static/qr-scanner.js` | 1KB | JavaScript file not referenced anywhere | NO RISK |

---

### 🟡 **LOW RISK - Probably Safe to Delete (5MB+)**
These files appear unused but might have indirect references. Recommend testing after deletion.

#### TinyMCE Unused Plugins (4MB+)
Currently only using: `link`, `lists`, `code`, `preview` (from base.html line 643)

| Plugin Folder | Size | Reason | Risk |
|--------------|------|--------|------|
| `/static/tinymce/plugins/accordion/` | ~150KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/advlist/` | ~100KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/anchor/` | ~80KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/autolink/` | ~90KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/autoresize/` | ~85KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/autosave/` | ~120KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/charmap/` | ~200KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/codesample/` | ~180KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/directionality/` | ~70KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/emoticons/` | ~250KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/fullscreen/` | ~90KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/help/` | ~300KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/image/` | ~200KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/importcss/` | ~100KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/insertdatetime/` | ~110KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/media/` | ~220KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/nonbreaking/` | ~70KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/pagebreak/` | ~75KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/quickbars/` | ~150KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/save/` | ~80KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/searchreplace/` | ~140KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/table/` | ~300KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/visualblocks/` | ~85KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/visualchars/` | ~90KB | Not in plugin list | LOW RISK |
| `/static/tinymce/plugins/wordcount/` | ~95KB | Not in plugin list | LOW RISK |

#### TinyMCE Unused Skins/Themes (1MB+)
Currently using: oxide UI skin, default content skin (from base.html)

| Path | Size | Reason | Risk |
|------|------|--------|------|
| `/static/tinymce/skins/content/dark/` | ~50KB | Dark theme not used | LOW RISK |
| `/static/tinymce/skins/content/document/` | ~50KB | Document theme not used | LOW RISK |
| `/static/tinymce/skins/content/tinymce-5/` | ~50KB | Legacy theme not used | LOW RISK |
| `/static/tinymce/skins/content/tinymce-5-dark/` | ~50KB | Legacy dark theme not used | LOW RISK |
| `/static/tinymce/skins/content/writer/` | ~50KB | Writer theme not used | LOW RISK |
| `/static/tinymce/skins/ui/oxide-dark/` | ~200KB | Dark UI not used | LOW RISK |
| `/static/tinymce/skins/ui/tinymce-5/` | ~200KB | Legacy UI not used | LOW RISK |
| `/static/tinymce/skins/ui/tinymce-5-dark/` | ~200KB | Legacy dark UI not used | LOW RISK |

#### Duplicate Image Files
Keep SVG versions, delete PNG versions for these:

| File | Size | Reason | Risk |
|------|------|--------|------|
| `/static/currency-dollar.png` | 386B | SVG version exists | LOW RISK |
| `/static/default_signup.jpg` | 3.4KB | SVG version exists | LOW RISK |
| `/static/facebook.png` | 487B | SVG version exists | LOW RISK |
| `/static/good-news.png` | 386B | SVG version exists | LOW RISK |
| `/static/hand-rock.png` | 386B | SVG version exists | LOW RISK |
| `/static/instagram.png` | 386B | SVG version exists | LOW RISK |
| `/static/thumb-down.png` | 386B | SVG version exists | LOW RISK |
| `/static/ticket.png` | 386B | SVG version exists | LOW RISK |

---

### 🔴 **HIGH RISK - Do Not Delete**
These files are actively used by the application.

| Path | Reason |
|------|--------|
| `/static/tabler/css/tabler.min.css` | Core Tabler framework CSS |
| `/static/tabler/css/tabler-icons.min.css` | Icon font used throughout app |
| `/static/tabler/js/tabler.min.js` | Core Tabler JavaScript |
| `/static/tinymce/tinymce.min.js` | Core TinyMCE editor |
| `/static/tinymce/themes/silver/` | Active TinyMCE theme |
| `/static/tinymce/skins/ui/oxide/` | Active TinyMCE UI skin |
| `/static/tinymce/skins/content/default/` | Active TinyMCE content skin |
| `/static/tinymce/plugins/link/` | Used plugin |
| `/static/tinymce/plugins/lists/` | Used plugin |
| `/static/tinymce/plugins/code/` | Used plugin |
| `/static/tinymce/plugins/preview/` | Used plugin |
| `/static/css/` (all files) | Custom application styles |
| `/static/js/` (all files) | Custom application JavaScript |
| `/static/minipass.css` | Main application stylesheet |
| `/static/uploads/` | User-generated content |
| `/static/email_templates/` | Email template assets |
| `/static/assets/` | Brand and logo assets |
| `/static/images/` | Application images |
| Favicon files | Browser icons |

---

## Recommended Cleanup Approach

### Phase 1: No-Risk Deletions (Immediate)
1. Delete backup directories (`/static/backups/`, `/static/uploads_bk_ken/`)
2. Delete unused Tabler components and image directories
3. Delete orphaned files (beep.wav, qr-scanner.js, minipass.css.backup)
4. Delete all .css.map files

**Expected savings: 64MB**

### Phase 2: Low-Risk Deletions (After Testing)
1. Backup TinyMCE directory first
2. Delete unused TinyMCE plugins (keeping only link, lists, code, preview)
3. Delete unused TinyMCE skins and themes
4. Test email template editor functionality
5. Delete duplicate PNG images (keep SVG versions)

**Expected savings: 5MB+**

### Phase 3: Verification
1. Clear browser cache
2. Test all major application features
3. Verify email template editor works
4. Check for any 404 errors in browser console

---

## Total Impact Summary

- **Current Size**: ~133MB
- **After Phase 1**: ~69MB (48% reduction)
- **After Phase 2**: ~64MB (52% reduction)
- **No functionality loss expected**
- **Improved deployment speed**
- **Reduced container size**

## Backup Recommendation
Before deletion, create a full backup:
```bash
tar -czf static_backup_$(date +%Y%m%d).tar.gz static/
```

Then proceed with deletions using:
```bash
# For directories
rm -rf /path/to/directory

# For individual files
rm /path/to/file
```