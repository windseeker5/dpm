# Minipass UI/UX Guide

## Strategy

Minipass keeps its existing **Flask + Jinja + Tabler.io** foundation. We are not migrating the application to another UI framework.

UI improvements happen **one explicitly selected page at a time**. Use the available UI/UX skills to improve hierarchy, usability, accessibility, responsiveness, and visual quality while preserving working product behavior.

## Page-by-page workflow

1. **Audit the current page first.** Inspect its template, route, real data, desktop layout, and mobile layout.
2. **Confirm the goal.** Understand what the user dislikes, what must remain, and what success looks like before editing.
3. **Design for the page's real task.** Do not apply a generic dashboard template or copy another framework's starter component.
4. **Preserve behavior.** Keep routes, form fields, CSRF, permissions, payments, emails, and business rules working.
5. **Implement narrowly.** Change only the selected page and truly shared code required by it. Do not start an application-wide redesign accidentally.
6. **Test the real flow.** Use pi's `browser-tools` against `localhost:5000` with the real local database and credentials.
7. **Review desktop and mobile together.** Inspect the DOM, verify keyboard/touch behavior, and capture screenshots for visual confirmation.
8. **Run an accessibility/UX quality pass** before considering the page complete.

## Implementation rules

- Prefer existing Tabler components and utility classes when they fit the design.
- Custom CSS is allowed when Tabler cannot express the intended result, but keep it purposeful, small, and in a stylesheet—not scattered inline.
- Use Tabler or another consistent SVG icon set already present in the application. Do not use emoji as interface icons.
- Keep JavaScript minimal and vanilla. Search, filtering, sorting, pagination, and validation should remain server-side where practical.
- Do not introduce React, Vue, Angular, another SPA framework, or a second UI framework.
- Do not copy another framework's starter page wholesale. Starter components may be references, not finished Minipass designs.
- Reuse an existing Minipass pattern only when it is already good enough for the task. A bad pattern should not spread merely for consistency.

## UX quality floor

### Hierarchy
- One clear page title and one obvious primary action.
- Group related controls; separate unrelated decisions.
- Avoid excessive cards, borders, badges, and competing accents.
- Put the most frequent user task first.

### Forms
- Every control has a visible label.
- Errors explain the problem and recovery.
- Preserve entered values after validation errors when safe.
- Use the correct input type and autocomplete value.
- Touch targets are at least 44 × 44px.

### Mobile
- Design and test at 375px width.
- No horizontal overflow.
- Do not simply hide essential desktop information.
- Keep primary actions reachable and readable.
- Long names, dates, addresses, and translated text must wrap safely.

### Accessibility
- Use semantic headings, landmarks, labels, and buttons.
- Preserve visible keyboard focus.
- Body text contrast must meet WCAG AA.
- Do not disable zoom.
- Do not use color as the only status indicator.
- Images need useful alternative text and explicit dimensions where practical.

### Performance
- Avoid unnecessary web fonts, icon fonts, JavaScript, and duplicate assets.
- Prefer committed local assets over runtime frontend build dependencies.
- Node.js must not be required in production containers.
- Keep animations rare, purposeful, and respectful of reduced-motion preferences.

## Visual direction

Minipass should feel:

- Clear and operational rather than decorative.
- Professional without looking generic or sterile.
- Calm, compact, and efficient on mobile.
- Branded through typography, spacing, imagery, and deliberate color—not visual effects added everywhere.

Each page can have its own composition, but the application should retain consistent controls, typography, spacing, and feedback patterns.

## Definition of done

A UI change is complete only when:

- The real user flow works.
- Desktop and mobile have been inspected.
- Keyboard and touch interactions work.
- Loading, empty, error, and success states relevant to the page are handled.
- No unrelated page was unintentionally changed.
- Browser console and Flask logs show no new errors.
