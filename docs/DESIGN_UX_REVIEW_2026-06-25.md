# Frontend Design & UX Review — Event Staffing Platform

**Date:** 2026-06-25
**Reviewer lens:** Graphic design + product UX specialist
**Surfaces:** Web operator dashboard (React/Vite) and mobile worker app (Expo/React Native)
**Companion:** see `DESIGN_UX_MOCKUPS_2026-06-25.html` for visual before/after of key screens.

---

## Overall impression

This is a genuinely above-average MVP front end. Someone made deliberate, taste-driven choices: a warm "paper" palette instead of default SaaS blue, a display typeface (Space Grotesk/Manrope), tokenized spacing/radius/shadow, and real attention to micro-states — skeleton loaders, toasts, focus rings, status badges, and empty states all exist. Most MVPs ship none of that. The mobile browse card (pay rate, estimated total, capacity bar, "spots left") is a well-considered piece of information design.

The work needed now is not "make it prettier" — it's **consistency and signal discipline**. The product currently presents as three slightly different brands (purple login → green/cream web app → cooler-white mobile app), it over-uses ALL-CAPS micro-labels so everything competes for attention, color is doing decorative and semantic duty at the same time, and several muted text colors fail accessibility contrast. Fixing those would lift it from "nicely styled MVP" to "coherent product."

The findings below are prioritized. Severity reflects user/brand impact, not effort.

---

## High — brand & identity coherence

### D1. The product looks like three different apps
The single biggest issue is identity fracture across the three surfaces a user actually moves through:

- **Login/register** (`LoginPage.css`) deliberately overrides the whole palette to **purple** (`#681d96`/`#9333ea`) with a comment that says so explicitly. This is the *first* screen anyone sees.
- **The web app behind it** is ocean-green (`#0e5a3a`) on warm cream paper.
- **The mobile app** shares the green but sits on pure-white surfaces with cooler grays (`#e1e6ec` borders, `#f4f0ea` canvas) — a visibly different temperature from the web's warm cream.

So a user signs in through a purple door, lands in a green-and-cream room, then opens the phone app and it's a third, cooler shade. None of them share a logo. The web sidebar brands as "Venue OS" with a "V" mark; the auth screen uses a sun-colored brand mark; mobile has no wordmark.

**Recommendation:** Pick one brand system and apply it everywhere. One name (decide between "Venue OS" and "Event Staffing Platform"), one logo/wordmark, one primary (the ocean green is the strongest, most ownable choice — keep it), one surface temperature. Drop the purple auth theme entirely or promote purple to a deliberate secondary used consistently across all three surfaces — not just login. Unify the mobile surface to the same warm paper as web, or move web to the cooler white — but make them match.

### D2. Naming is unsettled
"Venue OS" (web sidebar) vs "Event Staffing Platform" (README) vs no name (mobile). Settle the product name and use it consistently in nav, auth, app stores, and metadata. Small thing, but it's the kind of inconsistency that reads as unfinished.

---

## High — accessibility

### D3. Muted label colors fail WCAG AA contrast
Several of the most-repeated text styles use `--ink-300: #9ca3af` (and sometimes `--ink-500: #4b5563`) on the light paper backgrounds. `#9ca3af` on `#fbf7f1` is roughly **2.3:1** — well below the **4.5:1** AA minimum for the small text it's used on (metric labels at 0.76rem, status labels at 0.65rem, captions). These are not decorative; they're field labels and metric captions users need to read.

**Recommendation:** Darken muted label tokens until they pass AA at their actual size. `--ink-500` should be the floor for any text under ~0.9rem; reserve `--ink-300` for non-essential decoration only (e.g. divider text). Quick check every label token against its background with a contrast tool and bump until ≥4.5:1 (≥3:1 only if ≥18px/bold).

### D4. Status is encoded by color alone in places
Status *badges* do this right — they pair color with an uppercase text label, so they're fine. But the **dashboard metric cards** signal warning/success only through a 6px colored left bar (ocean vs amber vs green), and **coverage seats** rely on color (green vs amber) with no shape/icon differentiator. Color-blind users (~8% of men) can't distinguish "needs attention" from "healthy."

**Recommendation:** Add a non-color cue to every semantic state — a small icon (`alert-triangle`, `check`) or a text qualifier next to the value. This pairs well with D7 (adding icons to the web anyway).

### D5. Mobile touch targets are under the minimum
Browse-card action buttons are `minHeight: 40` (`BrowseFeedCard.tsx`), and the "Pass" button is `flex: 0.7` — narrow. iOS HIG recommends 44pt, Android Material 48dp.

**Recommendation:** Raise action buttons to ≥44px height. Reconsider three side-by-side buttons on small phones (see D9).

---

## Medium — visual hierarchy & signal discipline

### D6. Everything is shouting (ALL-CAPS overload)
Uppercase + bold + letter-spacing is applied to nav labels, eyebrows, metric labels, status labels, pills, badges, panel titles, tags — simultaneously. When everything is emphasized, nothing is. The effect is a busy, heavy UI where the eye has no rest and can't find the one thing that matters.

**Recommendation:** Restrict uppercase micro-caps to **one** role (e.g. section eyebrows only). Make nav labels, metric labels, and list captions sentence case at normal weight. Let the big metric numbers and the primary action carry the emphasis. This single change will make the dashboard feel calmer and more premium immediately.

### D7. The web app has no icons (and ships dead icon CSS)
`DashboardPage.css` literally contains `.metric-icon { display: none; }` — icons were designed for metric cards and then hidden. The result: the web dashboard is walls of text and colored bars, while the mobile app uses a clean Ionicons set. Nav items, metrics, attention queue, and empty states would all scan far faster with a lightweight icon per item.

**Recommendation:** Adopt one icon set on web (Lucide/Tabler pair well with this type) and use it in nav, metric headers, attention rows, and empty states. Remove the dead `display:none` rule. Match the metaphor set to the mobile Ionicons so the two surfaces feel related.

### D8. The dashboard says the same thing three times
On first paint the operator sees, in order: a subtitle ("N items need attention"), then a full-width amber **alert banner** repeating the pending-applications/open-seats count, then an **attention queue** panel listing the same items again. Three echoes of one fact pushes the actually-different content (coverage, open shifts) below the fold.

**Recommendation:** Consolidate into a single "Needs attention" hero block with the count and the primary CTA, then go straight to distinct content (metrics → coverage → open shifts). Remove the duplicated subtitle count or the banner — not both in addition to the queue.

### D9. Mobile browse: dismiss and commit sit side by side
"Pass" (irreversible-feeling dismiss) and "Quick apply" (commit) are adjacent in a cramped 3-button row. You cite Uber/Deliveroo as the reference — those use **swipe** for the dismiss/accept gesture and reserve buttons for the deliberate action. The current layout invites mis-taps. (Mitigated by passes being undoable per the README, which is good — but the interaction still feels risky.)

**Recommendation:** Make "Quick apply" the single prominent full-width button, demote "Pass" to a lighter text/icon affordance or a swipe-left gesture, and keep "Details" as a tap on the card body. Fewer competing buttons, clearer primary action, bigger targets.

### D10. Amber is both decoration and warning
`--sun-500` (amber) is used for decorative pills and the brand accent *and* for the warning semantic (coverage warnings, metric warnings, the attention circles' default background). Users can't tell "this is just a highlight" from "this needs action."

**Recommendation:** Reserve amber strictly for warning/attention. Use a neutral (paper/ink) or the green for purely decorative highlights. One color, one meaning.

---

## Low — polish

- **D11. Auth marketing panel vanishes on mobile web.** The left value-prop/trust panel is `display:none` under 700px, so mobile-web visitors get a bare form with no trust signals on a blank cream field. Consider a compact logo + one-line value prop above the form instead of hiding everything.
- **D12. Metric weight 900 + 2.9rem is very heavy.** Glanceable, but combined with the caps overload it tips into aggressive. Once D6 is addressed, 700–800 will likely read better.
- **D13. Decorative circles + gradients on auth** (`auth-panel-left::before/after`, gradient alert) are the only gradients in an otherwise flat system — slightly off-language. Minor.
- **D14. Surface alpha juggling.** Cards mix `rgba(255,252,247,0.94)`, `rgba(255,255,255,0.7)`, `rgba(255,255,255,0.82)` etc. Lots of near-identical translucent whites. Consolidate to 2–3 named surface tokens for consistency and easier theming.

---

## What to keep (don't lose these in a redesign)

The warm paper palette and display type are a real differentiator — do not regress to generic blue SaaS. The micro-state coverage (skeletons, toasts, focus-visible rings, empty states, status badges) is ahead of most MVPs. The mobile browse card's information design — pay rate, estimated total, duration, capacity bar, "spots left" — is excellent and should be the template for how the rest of the product presents shift data. The responsive breakpoints are thoughtfully placed. Keep all of it; the recommendations above are about coherence and signal, not replacing the aesthetic.

---

## Suggested order of work

1. **D1/D2 brand unification** — one palette, one name, one logo across login + web + mobile. Highest perceived-quality return.
2. **D3 contrast pass** — darken muted tokens to AA. Fast, ships accessibility compliance.
3. **D6 caps discipline + D7 icons on web** — biggest "feels calmer / more premium" change for the effort.
4. **D8 dashboard de-duplication**, **D9 mobile action hierarchy**, **D4/D5 a11y cues + targets**.
5. Low-priority polish (D11–D14).
