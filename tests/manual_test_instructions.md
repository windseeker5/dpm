# Dropdown Fix Validation Instructions

## Quick Test Steps

1. **Open the signups page**: http://127.0.0.1:8890/signups
2. **Login** with: `kdresdell@gmail.com` / `admin123`
3. **Open browser console** (F12 → Console tab)
4. **Look for these console messages**:
   - `📋 Signups page loaded`
   - `🔧 Global dropdown fix available: true`
   - `📊 Bootstrap available: true`
   - `🔍 Dropdown toggles found: [number]`

## Manual Testing

### Test 1: Single Dropdown Behavior
1. Click on any "Actions" dropdown in the table
2. **Expected**: Dropdown opens
3. Click on another "Actions" dropdown
4. **Expected**: First dropdown closes, second dropdown opens
5. **Success criteria**: Only one dropdown is open at a time

### Test 2: Click Outside to Close
1. Open any dropdown
2. Click somewhere else on the page (not on a dropdown)
3. **Expected**: Dropdown closes
4. **Success criteria**: All dropdowns are closed

### Test 3: Escape Key
1. Open any dropdown
2. Press the Escape key
3. **Expected**: Dropdown closes
4. **Success criteria**: All dropdowns are closed

### Test 4: Bulk Actions Dropdown
1. Select one or more checkboxes to show the bulk actions bar
2. Click the "Actions" dropdown in the bulk actions bar
3. **Expected**: Dropdown opens properly
4. Click elsewhere or press Escape
5. **Expected**: Dropdown closes

## Advanced Console Testing

Copy and paste this into the browser console for automated testing:

```javascript
// Quick dropdown validation
function testDropdowns() {
    console.log('🧪 Testing dropdown behavior...');
    
    // Check if global fix is loaded
    if (typeof window.dropdownFix === 'undefined') {
        console.error('❌ Global dropdown fix not loaded!');
        return;
    }
    
    // Find dropdowns
    const dropdowns = document.querySelectorAll('[data-bs-toggle="dropdown"]');
    console.log(`Found ${dropdowns.length} dropdowns`);
    
    if (dropdowns.length >= 2) {
        // Test opening first dropdown
        dropdowns[0].click();
        setTimeout(() => {
            const openCount = document.querySelectorAll('.dropdown.show').length;
            console.log(`After opening first: ${openCount} dropdowns open`);
            
            // Test opening second dropdown
            dropdowns[1].click();
            setTimeout(() => {
                const newOpenCount = document.querySelectorAll('.dropdown.show').length;
                console.log(`After opening second: ${newOpenCount} dropdowns open`);
                
                if (newOpenCount === 1) {
                    console.log('✅ SUCCESS: Only one dropdown open at a time');
                } else {
                    console.log('❌ FAILURE: Multiple dropdowns open');
                }
                
                // Test clicking outside
                document.body.click();
                setTimeout(() => {
                    const finalCount = document.querySelectorAll('.dropdown.show').length;
                    console.log(`After clicking outside: ${finalCount} dropdowns open`);
                    
                    if (finalCount === 0) {
                        console.log('✅ SUCCESS: Click outside closes dropdowns');
                    } else {
                        console.log('❌ FAILURE: Click outside did not close dropdowns');
                    }
                }, 300);
            }, 300);
        }, 300);
    } else {
        console.log('⚠️ Not enough dropdowns to test');
    }
}

testDropdowns();
```

## Troubleshooting

### If dropdowns don't close properly:
- Check browser console for JavaScript errors
- Verify that `window.dropdownFix` is available
- Verify that `bootstrap` is available
- Check if there are any conflicting JavaScript event listeners

### If dropdowns don't open:
- Check if Bootstrap JS is loaded properly
- Verify dropdown HTML structure is correct
- Check for CSS issues preventing visibility

### If positioning is wrong:
- Check if the global dropdown-fix.css is loaded
- Verify table-responsive containers aren't overriding styles
- Look for conflicting CSS rules

## Expected Console Output

When everything is working correctly, you should see:
```
📋 Signups page loaded
🔧 Global dropdown fix available: true
📊 Bootstrap available: true
🔍 Dropdown toggles found: [number > 0]
```

And the automated test should show:
```
✅ SUCCESS: Only one dropdown open at a time
✅ SUCCESS: Click outside closes dropdowns
```