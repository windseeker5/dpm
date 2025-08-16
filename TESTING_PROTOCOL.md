# Testing Protocol for UI Development

## MANDATORY TESTING REQUIREMENTS

### Every UI Change MUST Be Tested
1. **After ANY template/UI modification**: ALWAYS use Playwright MCP to take screenshots
2. **Validate changes visually**: Ensure the changes match user requirements exactly
3. **Test interaction**: Click buttons, test responsive behavior, check all states
4. **Iterate until perfect**: If not working as expected, fix and test again

### Testing Workflow
1. Make changes to templates/UI
2. Navigate to the page using Playwright (http://127.0.0.1:8890)
3. Login if required (kdresdell@gmail.com / admin123)
4. Take screenshots to validate changes
5. Test interactive elements
6. If issues found, fix and repeat from step 2
7. Only mark task as complete when visually confirmed working

### Playwright MCP Commands to Remember
- `mcp__playwright__browser_navigate` - Navigate to pages
- `mcp__playwright__browser_snapshot` - Get page structure
- `mcp__playwright__browser_take_screenshot` - Visual validation
- `mcp__playwright__browser_type` - Fill in forms
- `mcp__playwright__browser_click` - Interact with elements

### Test Checklist
- [ ] Visual appearance matches requirements
- [ ] All removed elements are gone
- [ ] All added elements are present
- [ ] Colors and styling are correct
- [ ] Icons display properly (no encoding issues)
- [ ] Responsive behavior works
- [ ] No console errors
- [ ] Page loads without issues

## REMEMBER: TEST, TEST, TEST!
**Never assume changes work - ALWAYS verify with screenshots!**