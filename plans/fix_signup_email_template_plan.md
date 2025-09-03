# Fix Signup Email Template Plan

## Issue Description
- **Date**: September 3, 2025
- **Reported Issue**: Signup confirmation emails are not rendering correctly
- **Symptoms**:
  1. Hero image missing from email body (showing as attachment)
  2. Email content appears as attached HTML file instead of inline
  3. Only affects signup emails - other templates (create_pass) work correctly

## Root Cause Analysis

### Investigation Results
1. **Template Structure**:
   - Signup template uses CID `good-news` for hero image
   - NewPass template uses CID `ticket` for hero image
   - Both templates compiled with inline_images.json

2. **Code Analysis**:
   - `notify_pass_event` (lines 1717-1862 in utils.py) correctly replaces `ticket` CID with activity-specific hero
   - `notify_signup_event` (lines 1608-1715 in utils.py) does NOT replace `good-news` CID
   - Missing hero image replacement logic causes email client to show image as attachment

3. **Email Rendering**:
   - Signup uses `html_body` parameter which should work but lacks image replacement
   - Compiled template loaded correctly but hero image CID not updated

## Implementation Plan

### Phase 1: Code Modification

#### File: `/home/kdresdell/Documents/DEV/minipass_env/app/utils.py`

**Function to modify**: `notify_signup_event` (line 1608)

**Add after line 1690** (after loading organization logo):
```python
# Check for activity-specific hero image (replaces 'good-news' CID)
activity_id = activity.id if activity else None
if activity_id:
    hero_image_path = os.path.join("static/uploads", f"{activity_id}_hero.png")
    if os.path.exists(hero_image_path):
        hero_data = open(hero_image_path, "rb").read()
        inline_images['good-news'] = hero_data  # Replace compiled 'good-news' image
        print(f"Using activity-specific hero image: {activity_id}_hero.png")
    else:
        print(f"Activity hero image not found: {hero_image_path}")
```

### Phase 2: Testing Strategy

#### A. Unit Testing (Safe, Isolated)
- Location: `/test/test_signup_email_template.py`
- Tests email template rendering without sending actual emails
- Validates inline image handling
- Checks CID replacement logic

#### B. Integration Testing (Safe, Local)
1. Use Flask test client to create signup
2. Mock email sending to capture rendered output
3. Validate HTML structure and CID references

#### C. Manual Browser Testing
1. Login to admin panel
2. Navigate to Activity 4
3. Create test signup
4. Verify email rendering

### Phase 3: Deployment Checklist

#### Pre-deployment
- [ ] Backup current utils.py
- [ ] Verify Activity 4 has hero image at `/static/uploads/4_hero.png`
- [ ] Check Flask server running on port 5000
- [ ] Ensure email configuration is correct

#### Post-deployment
- [ ] Create test signup for Activity 4
- [ ] Verify email received with inline hero image
- [ ] Check no attachments in email client
- [ ] Confirm social media icons display
- [ ] Test other email templates still work (create_pass, payment_received)

## Test Scenarios

### Scenario 1: Activity with Custom Hero Image
- **Input**: Signup for Activity 4 (has custom hero: `4_hero.png`)
- **Expected**: Email displays custom hero inline
- **Validation**: No attachments, hero visible in email body

### Scenario 2: Activity without Custom Hero Image
- **Input**: Signup for new activity without hero image
- **Expected**: Email displays default 'good-news' image
- **Validation**: Fallback to compiled template image

### Scenario 3: Multiple Recipients
- **Input**: Bulk signup creation
- **Expected**: All emails render correctly
- **Validation**: Consistent rendering across recipients

## Rollback Plan

If issues occur:
1. Restore original utils.py from backup
2. Clear any pending email queue
3. Restart Flask application if needed
4. Document issue for further investigation

## Success Criteria

1. ✅ Hero image displays inline (not as attachment)
2. ✅ Email content renders in body (not as attachment)
3. ✅ Social media icons visible
4. ✅ No regression in other email templates
5. ✅ Consistent rendering across email clients

## Agent Assignment

- **Primary Agent**: backend-architect
  - Modify utils.py
  - Implement hero image replacement logic
  
- **Testing Agent**: flask-ui-developer or general-purpose
  - Execute unit tests
  - Perform browser testing
  - Validate email rendering

## Notes

- Pattern follows existing `notify_pass_event` implementation
- Maintains backward compatibility
- No database changes required
- No API changes required
- Email template compilation remains unchanged

## Contact

For issues or questions about this plan:
- Review commit: `bfe299a` (last working version)
- Check `docs/workflow_email_template_modifications.md` for template guidelines