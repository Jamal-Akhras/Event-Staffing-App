# Event Staffing Platform UI Restructure Plan

## Overview
Restructure web and mobile UIs to create an Uber/Deliveroo-style experience while maintaining current color scheme. Web UI becomes venue-focused dashboard with sidebar navigation. Mobile app becomes worker-focused with map-based discovery and earnings tracking.

---

## Design Decisions

### Mobile App
- **Map View**: YES - Add map view with location pins for shift discovery
- **Navigation**: 4 tabs (Browse/Map | My Shifts | Earnings | Profile) - most professional approach
- **Earnings**: Full earnings tab with payment tracking and statistics
- **Library**: Will add `react-native-maps`, `@react-navigation/native`, `@gorhom/bottom-sheet`
- **Worker Match Feed**: Future direction documented in `docs/40-future/worker_match_feed.md`. Keep it on hold for now; when revisited, use a vertical feed as the primary browse surface and swipe gestures only as quick apply/pass shortcuts.

### Worker Match Feed Future
- The worker browse experience may later combine Instagram-style vertical scrolling with Tinder-style swipe shortcuts.
- This can be good UX if the feed remains comparison-friendly and detail-rich.
- It becomes bad UX if swiping replaces normal browsing, hides key shift details, or makes irreversible decisions too easy.
- Future ranking can use date preference, weekend vs weekday behavior, location, role/work type, pay, availability, and reliability fit.
- Keep manual search, filters, detail pages, and undo controls even after ranking is added.

### Web Dashboard
- **Layout**: Sidebar navigation with dedicated pages (not single-page panels)
- **Terminology**: Change "Operator" → "Venue Manager" throughout
- **Tone**: Hospitality-focused, not operations jargon
- **Structure**: Dashboard → Shifts → Applications → Workers → Schedule → Analytics

---

## Phase 1: Mobile App Restructure

### 1.1 Install Dependencies
**File**: `apps/mobile/package.json`

Add libraries:
- `react-native-maps` - Map view for shift discovery
- `@react-navigation/native` + `@react-navigation/bottom-tabs` - Better tab navigation
- `@gorhom/bottom-sheet` - Native bottom sheets for shift details
- `react-native-gesture-handler` + `react-native-reanimated` - Smooth animations
- `react-native-safe-area-context` (already installed ✓)

### 1.2 Create New Navigation Structure
**New File**: `apps/mobile/src/navigation/BottomTabNavigator.tsx`

4-tab structure:
```
[🗺️ Browse] [📅 Shifts] [💰 Earnings] [👤 Profile]
```

**Rationale**: Most professional = clear separation of concerns, industry-standard pattern from Uber/Lyft/Deliveroo

### 1.3 Refactor into Screen Components
**Current**: Single `App.tsx` (771 lines) with all logic
**New**: Split into screens:

- `apps/mobile/src/screens/BrowseScreen.tsx` - Map + list toggle for shifts
- `apps/mobile/src/screens/ShiftsScreen.tsx` - Upcoming/Completed/Applications tabs (keep current logic)
- `apps/mobile/src/screens/EarningsScreen.tsx` - NEW - Payment tracking and stats
- `apps/mobile/src/screens/ProfileScreen.tsx` - Worker profile + settings

### 1.4 Create Reusable Components
**New Directory**: `apps/mobile/src/components/`

Components to extract:
- `ShiftCard.tsx` - Reusable shift display card
- `BookingCard.tsx` - Reusable booking display card
- `ApplicationCard.tsx` - Application status card
- `BottomSheet.tsx` - Wrapper for @gorhom/bottom-sheet with app styling
- `StatusBadge.tsx` - Colored status indicators (open, confirmed, completed)
- `MetricCard.tsx` - For earnings dashboard (total, weekly, monthly)

### 1.5 Implement Map View for Shift Discovery
**New File**: `apps/mobile/src/screens/BrowseScreen.tsx`

Features:
- Map with pins showing shift locations
- List/Map toggle button (top-right)
- Cluster pins when zoomed out
- Tap pin → Show bottom sheet with shift details
- Filter chips above map (Near Me, Tonight, High Pay)
- Search bar at top

**Map Pin Colors**:
- Green: High pay ($30+)
- Blue: Standard shifts
- Yellow: Ending soon (< 24hrs to apply)
- Gray: Filled shifts

### 1.6 Implement Bottom Sheet for Shift Details
Replace current modal with native bottom sheet:

**Interaction**:
- Swipe up from collapsed state (shows venue name + pay)
- Expands to 70% screen height
- Grab handle at top + X button for accessibility
- Swipe down to dismiss
- Background dimmed 40%

**Content**:
```
[Grab Handle]                    [X]

The Pearl Bar
$25/hr · 6hrs · Bartender

[APPLY NOW - Full width button]

--- Scrollable ---
📍 Map Preview (small, tap for full map)
⏰ Friday 6PM - 12AM
👤 Requirements: 2+ years experience
⭐ Reliability: 4.0+ required
📝 Notes: Black attire, arrive 15min early
```

### 1.7 Implement Earnings Screen (NEW)
**New File**: `apps/mobile/src/screens/EarningsScreen.tsx`

**Layout**:
```
[Large Total Card]
This Week
$450.00
+$150 from last week

[Tab Selector: Week | Month | Year]

[Bar Chart - Weekly Earnings]

[Payment List]
✓ Paid  Friday, Jan 12
       The Library • Bartender • 6hrs
       $150.00

⏳ Pending Thursday, Jan 11
          Pearl Bar • Server • 4hrs
          $100.00
```

**Data Source**:
- Calculate from completed bookings (state = PAID)
- Group by date ranges
- Show pending (APPROVED, CHECKED_OUT but not PAID)

### 1.8 Polish Existing Shift/Profile Screens
**File**: `apps/mobile/src/screens/ShiftsScreen.tsx` (moved from App.tsx)

Keep current functionality, enhance UI:
- Add empty states with illustrations
- Add pull-to-refresh
- Add skeleton loaders while fetching
- Improve check-in flow with location indicator
- Add persistent "CHECK IN NOW" banner when within window

**File**: `apps/mobile/src/screens/ProfileScreen.tsx`

Keep current form, add:
- Avatar upload (future)
- Reliability score explanation modal
- App settings section (notifications, location permissions)

### 1.9 Update Color Scheme (Minimal Changes)
**File**: `apps/mobile/src/theme/colors.ts` (NEW)

Keep existing palette, add:
```typescript
export const COLORS = {
  // Existing (from App.tsx lines 99-111)
  ink: "#0f1720",
  inkMuted: "#6b7785",
  surface: "#ffffff",
  canvas: "#f4f0ea",
  border: "#e1e6ec",
  primary: "#0e5a3a",
  primaryDeep: "#123a2a",
  primarySoft: "#2f8f5f",
  warning: "#d97706",
  error: "#b83b32",
  onPrimary: "#f7efe8",

  // Add these
  success: "#10B981",      // For completed states
  info: "#3B82F6",         // For informational badges
  mapPinHigh: "#10B981",   // High pay shifts
  mapPinStandard: "#3B82F6", // Standard shifts
  mapPinUrgent: "#F59E0B",  // Ending soon
  mapPinFilled: "#9CA3AF",  // Filled/closed
}
```

---

## Phase 2: Web Dashboard Restructure

### 2.1 Install React Router
**File**: `apps/web/package.json`

Add:
- `react-router-dom` - Client-side routing for multi-page dashboard

### 2.2 Create New Layout Structure
**New File**: `apps/web/src/layouts/DashboardLayout.tsx`

```
┌─────────────────────────────────────┐
│ [Header: Brand + Health Status]    │
├──────┬──────────────────────────────┤
│      │                              │
│ Side │     Page Content             │
│ bar  │                              │
│      │                              │
│ Nav  │                              │
│      │                              │
└──────┴──────────────────────────────┘
```

**Sidebar Items**:
- 🏠 Dashboard
- 📅 Shifts
- 📋 Applications
- 👥 Workers
- 📆 Schedule
- 📊 Analytics
- ⚙️ Settings

### 2.3 Create Page Components
**New Directory**: `apps/web/src/pages/`

Extract from current single-page App.tsx:

**Dashboard Page** (`DashboardPage.tsx`):
- Key metrics cards (shifts this week, fill rate, avg response time)
- Urgent alerts (shifts needing workers, pending applications)
- Upcoming shifts calendar preview
- Recent activity feed

**Shifts Page** (`ShiftsPage.tsx`):
- Create shift form (current panel 1)
- Open shifts table with filters
- Shift history/past shifts
- Bulk actions (cancel, duplicate)

**Applications Page** (`ApplicationsPage.tsx`):
- Pending applications table (current panel 6)
- Filter by shift, status, reliability score
- Batch approve/reject
- Worker profile modal

**Workers Page** (`WorkersPage.tsx` - NEW):
- Worker directory with search
- Reliability score sorting
- Favorite workers list
- Blocked workers list

**Schedule Page** (`SchedulePage.tsx` - NEW):
- Weekly/monthly calendar grid view
- Drag workers to reassign (future)
- Export to PDF/CSV

**Analytics Page** (`AnalyticsPage.tsx` - NEW):
- Fill rate trends
- No-show rate charts
- Popular shift times
- Cost analysis

**Settings Page** (`SettingsPage.tsx` - NEW):
- Venue profile (name, type, locations)
- Notification preferences
- API configuration
- Account management

### 2.4 Modernize Shift Creation Form
**File**: `apps/web/src/components/ShiftForm.tsx`

Current: Simple vertical form
New: Smart form with:
- Role dropdown (prepopulated from past shifts)
- Location autocomplete (if multiple venues)
- Time range picker (visual slider)
- Workers needed counter (+/- buttons)
- Pay rate suggestion based on role/time
- Template selector dropdown ("Friday Night Bar Shift")
- Recurring shift options (future)

**Add workers_needed field** (currently missing from UI, but exists in backend migration 004)

### 2.5 Update All Copy/Terminology
**Files**: All web UI files

Find and replace:
- "Operator" → "Venue Manager" (or just "Venue" in some contexts)
- "operator_id" → "venue_id" (API parameter names)
- "operatorHeaders" → "venueHeaders" (JS variable)
- "X-Actor-Role: operator" → "X-Actor-Role: operator" (keep header value as-is for backend compatibility)
- "Control room" → "Dashboard" or "Staffing Hub"
- "Command staffing" → "Fill shifts faster"
- "Lifecycle" pill → "Status" pill
- "Feed" → "Recent"

### 2.6 Create Reusable Web Components
**New Directory**: `apps/web/src/components/`

Components to create:
- `Sidebar.tsx` - Navigation sidebar
- `MetricCard.tsx` - Dashboard metric display
- `ShiftCard.tsx` - Shift display (reuse pattern from mobile)
- `ApplicationRow.tsx` - Worker application in table
- `WorkerProfile.tsx` - Modal/sheet for worker details
- `Calendar.tsx` - Schedule grid view
- `StatusBadge.tsx` - Consistent status indicators
- `EmptyState.tsx` - Illustrations for empty data

### 2.7 Update Color Scheme (Maintain Existing)
**File**: `apps/web/src/index.css`

Keep existing CSS variables (lines with `--ink-`, `--paper-`, `--ocean-`, `--sun-`, `--rose-`)

Add new variables:
```css
:root {
  /* Existing colors stay */

  /* Add sidebar */
  --sidebar-bg: #ffffff;
  --sidebar-border: var(--border);
  --sidebar-hover: var(--paper-1);
  --sidebar-active: rgba(14, 90, 58, 0.08);

  /* Add data visualization */
  --chart-primary: var(--ocean-500);
  --chart-secondary: var(--sun-500);
  --chart-tertiary: var(--rose-400);
}
```

### 2.8 Implement Dashboard Metrics
**File**: `apps/web/src/pages/DashboardPage.tsx`

Calculate from existing data:
- **Shifts This Week**: Count shifts where `created_at` in last 7 days
- **Fill Rate**: `(shifts with status="filled") / (total shifts)` × 100
- **Avg Response Time**: Average time from shift creation to first application
- **Pending Applications**: Count applications with `status="applied"`

Display as 4 metric cards in top row with trend indicators (↑ 5%, ↓ 2hr)

---

## Phase 3: Shared Improvements

### 3.1 Add Status Badge Component (Both Apps)
**Consistent color coding**:
- Green dot + "OPEN" - Open shifts
- Yellow dot + "APPLIED" - Pending applications
- Blue dot + "CONFIRMED" - Confirmed bookings
- Green check + "COMPLETED" - Finished shifts
- Red X + "CANCELLED" - Cancelled bookings
- Orange ! + "NO SHOW" - No-show events

### 3.2 Implement Empty States
**When no data**:
- Illustration (simple SVG)
- Helpful message
- Call-to-action button

Examples:
- No shifts available → "No shifts match your filters. Clear filters?"
- No applications → "No applications yet. Share this shift to attract workers!"
- No bookings → "You're all caught up! Check upcoming shifts."

### 3.3 Add Loading States
Replace blank screens with skeleton loaders:
- Shimmer effect on cards while fetching
- Spinner for actions (apply, approve, check-in)
- Progress indicator on multi-step flows

### 3.4 Improve Error Handling
- Toast notifications for success/error
- Inline error messages on forms
- Retry button on failed network requests
- Offline mode indicator

---

## Phase 4: API Schema Updates (If Needed)

### 4.1 Add Earnings Endpoint (NEW)
**File**: `apps/api/src/main.py`

New endpoint:
```python
@app.get("/workers/{worker_id}/earnings")
def get_worker_earnings(
    worker_id: str,
    period: str = "week",  # week, month, year
    actor: ActorRole = Depends(get_actor_role),
):
    """Calculate earnings from completed bookings."""
    # Query bookings with state=PAID, group by period
    # Return: {total, breakdown_by_date, pending_amount}
```

### 4.2 Add Location Field to Shifts (Future)
**Currently**: Location is free text
**Better**: Store lat/lng for map plotting

For now: Use geocoding service on client-side to convert "The Pearl Bar, 123 Main St" → lat/lng

---

## File Changes Summary

### New Files (Mobile)
- `apps/mobile/src/navigation/BottomTabNavigator.tsx`
- `apps/mobile/src/screens/BrowseScreen.tsx`
- `apps/mobile/src/screens/ShiftsScreen.tsx`
- `apps/mobile/src/screens/EarningsScreen.tsx`
- `apps/mobile/src/screens/ProfileScreen.tsx`
- `apps/mobile/src/components/ShiftCard.tsx`
- `apps/mobile/src/components/BookingCard.tsx`
- `apps/mobile/src/components/ApplicationCard.tsx`
- `apps/mobile/src/components/BottomSheet.tsx`
- `apps/mobile/src/components/StatusBadge.tsx`
- `apps/mobile/src/components/MetricCard.tsx`
- `apps/mobile/src/theme/colors.ts`

### Modified Files (Mobile)
- `apps/mobile/App.tsx` - Becomes navigation container only
- `apps/mobile/package.json` - Add dependencies

### New Files (Web)
- `apps/web/src/layouts/DashboardLayout.tsx`
- `apps/web/src/pages/DashboardPage.tsx`
- `apps/web/src/pages/ShiftsPage.tsx`
- `apps/web/src/pages/ApplicationsPage.tsx`
- `apps/web/src/pages/WorkersPage.tsx`
- `apps/web/src/pages/SchedulePage.tsx`
- `apps/web/src/pages/AnalyticsPage.tsx`
- `apps/web/src/pages/SettingsPage.tsx`
- `apps/web/src/components/Sidebar.tsx`
- `apps/web/src/components/MetricCard.tsx`
- `apps/web/src/components/ShiftCard.tsx`
- `apps/web/src/components/ApplicationRow.tsx`
- `apps/web/src/components/WorkerProfile.tsx`
- `apps/web/src/components/Calendar.tsx`
- `apps/web/src/components/StatusBadge.tsx`
- `apps/web/src/components/EmptyState.tsx`
- `apps/web/src/components/ShiftForm.tsx`

### Modified Files (Web)
- `apps/web/src/App.tsx` - Becomes router setup, extract all logic to pages
- `apps/web/src/index.css` - Add sidebar and chart color variables
- `apps/web/package.json` - Add react-router-dom

### New Files (API)
- None initially, earnings endpoint can be added later

### Modified Files (API)
- Potentially `apps/api/src/main.py` - Add GET `/workers/{id}/earnings` endpoint

---

## Implementation Order

### Sprint 1: Mobile Foundation (Week 1)
1. Install dependencies (maps, navigation, bottom-sheet)
2. Create navigation structure with 4 tabs
3. Split App.tsx into screen components
4. Extract reusable components (cards, badges)

### Sprint 2: Mobile Map & Discovery (Week 1-2)
1. Implement map view with shift pins
2. Create bottom sheet for shift details
3. Add list/map toggle
4. Implement filter chips

### Sprint 3: Mobile Earnings (Week 2)
1. Create EarningsScreen with stats
2. Calculate earnings from bookings
3. Add payment history list
4. Add week/month/year tabs

### Sprint 4: Web Sidebar & Routing (Week 2-3)
1. Install react-router-dom
2. Create DashboardLayout with sidebar
3. Set up routing for 7 pages
4. Create empty page shells

### Sprint 5: Web Dashboard Page (Week 3)
1. Implement metric cards
2. Add urgent alerts section
3. Create calendar preview
4. Add recent activity feed

### Sprint 6: Web Shifts & Applications (Week 3-4)
1. Migrate shift creation form to ShiftsPage
2. Create open shifts table
3. Migrate applications to ApplicationsPage
4. Add worker profile modal

### Sprint 7: Polish & Testing (Week 4)
1. Add empty states everywhere
2. Add loading skeletons
3. Improve error handling
4. Update all terminology (operator → venue)
5. Cross-device testing
6. Performance optimization

---

## Design Preservation

### MUST KEEP (Do Not Change)
- Color palette (ink, paper, ocean, sun, rose)
- Typography (Space Grotesk, type scale, letter-spacing)
- Shadow system (soft, lift)
- Border radii (12px buttons, 18px cards)
- Frosted glass effect on cards
- Eyebrow text pattern (uppercase, wide spacing)
- Premium, polished aesthetic
- Warm, professional tone

### CAN EVOLVE
- Layout structure (grid → sidebar + pages)
- Navigation pattern (single-page → multi-page with routing)
- Component hierarchy (monolithic → modular)
- Copy/terminology (operator → venue manager)
- Information density (add metrics, charts, empty states)

---

## Success Criteria

### Mobile App
- ✅ Workers can browse shifts on a map
- ✅ Workers can toggle between map and list view
- ✅ Workers can apply to shifts via bottom sheet
- ✅ Workers can track weekly/monthly earnings
- ✅ Workers can check in/out with clear UI
- ✅ 4-tab navigation feels professional and intuitive
- ✅ Color scheme matches web app

### Web Dashboard
- ✅ Venue managers see key metrics at a glance
- ✅ Shift creation is fast and smart (templates, suggestions)
- ✅ Applications are easy to review (table format, bulk actions)
- ✅ Navigation is clear (sidebar with 7 sections)
- ✅ No "operator" jargon - all copy is venue-focused
- ✅ Schedule/calendar view helps plan coverage
- ✅ Color scheme preserved from original

### Both
- ✅ Feels like Uber/Deliveroo (card-based, scannable, action-oriented)
- ✅ Maintains reliability-first messaging
- ✅ Professional tone (not gig economy casual)
- ✅ Fast performance (lazy loading, optimistic UI)
- ✅ Accessible (proper focus states, keyboard nav, ARIA)

---

## Risks & Mitigations

### Risk 1: Map library adds significant bundle size
**Mitigation**: Lazy load map component, only download when Browse tab is active

### Risk 2: Sidebar navigation breaks existing workflows
**Mitigation**: Keep URL structure simple, add breadcrumbs, allow "Open in new tab"

### Risk 3: Earnings calculation is complex (taxes, deductions)
**Mitigation**: Start simple - just sum PAID bookings, show "before taxes" disclaimer

### Risk 4: Workers expect push notifications for new shifts
**Mitigation**: Implement in Phase 2, start with in-app polling (already exists)

### Risk 5: Map pins cluster unreadably in dense areas
**Mitigation**: Use marker clustering library, adjust zoom levels

---

## Next Steps After Approval

1. Create feature branch: `feature/ui-restructure-uber-style`
2. Start with mobile Sprint 1 (foundation work)
3. Work in parallel: one developer on mobile, one on web
4. Weekly demos to validate direction
5. User testing with real venue managers and workers
6. Iterate based on feedback before final merge

---

## Documentation Integration

This plan should be saved to project documentation for future reference:

1. **Create** `docs/40-future/` directory if it doesn't exist
2. **Save this file** as `docs/40-future/ui_restructure_plan.md`
3. **Update** `docs/30-delivery/STATUS.md` to reference this plan in the "Next" section ✓ (DONE)
4. **Update** `docs/30-delivery/DEVLOG.md` to note UI restructure planning completed
5. **Update** `README.md` to mention planned UI improvements

When ready to implement:
- Read `docs/40-future/ui_restructure_plan.md` for full context
- Review current analysis in sections 1.1-1.9 (Mobile) and 2.1-2.8 (Web)
- Follow implementation order in Sprint 1-7
- Reference design decisions made on 2025-12-27

---

## Notes

- This is a significant restructure (~3-4 weeks of work)
- Consider doing mobile OR web first, not both simultaneously
- Can launch mobile app update independently of web
- Backward compatible with existing API (no breaking changes)
- All existing features preserved, just reorganized and polished
- **Plan created**: 2025-12-27
- **Decision maker**: User selected map view, sidebar navigation, earnings tab, professional 4-tab structure
- **Color scheme**: Must preserve existing palette (ocean greens, warm paper backgrounds)
- **Inspiration**: Uber/Deliveroo UX patterns while maintaining reliability-first messaging
