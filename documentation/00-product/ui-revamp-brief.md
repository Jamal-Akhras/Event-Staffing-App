# UI Revamp — Visual Design Brief (brainstorm feed)

Design-intent companion to `ui-revamp-plan.md` (which fixes the IA). This brief is the input to the
visual brainstorm: it sets the aesthetic direction and constraints, not the tabs.

## What we're designing
A full visual revamp of a hospitality **workforce-management** platform (working name **Venue OS**;
worker-app brand may differ). Two clients, one identity:
1. **Worker app** — Expo / React Native (mobile-first, flexible-work audience).
2. **Operator console** — React / Vite (venue managers on desktop).

The backend is feature-complete; the IA (tabs/destinations) is already fixed in `ui-revamp-plan.md`.
This brief is about the **visual identity and design system**, not the IA.

## Design intent (Anthropic frontend-aesthetics guidance)
- **Typography — be distinctive.** Do NOT use Inter, Roboto, Arial, or system fonts. Also
  deliberately move OFF **Space Grotesk** (the guidance flags it as a convergence trap; it is our
  current default). Consider high-contrast pairings (display + mono, serif + geometric sans) and
  weight extremes (100/200 vs 800/900). Editorial faces (Fraunces, Crimson Pro), distinctive sans
  (Clash Display, Satoshi, Cabinet Grotesk), or a characterful mono are all on the table.
- **Color — commit.** One cohesive aesthetic via design tokens; a dominant color with sharp accents
  beats a timid, evenly-distributed palette. Draw the palette from a real-world reference in the
  subject's world (hospitality / service craft / nightlife / the materiality of a working venue),
  not from generic SaaS.
- **Motion — one orchestrated moment.** On web, a single well-staggered page-load reveal per key
  screen beats scattered micro-interactions. Mobile gets subtle, native-feeling transitions.
- **Background — atmosphere over flat fills** on web (layered gradients, geometric texture,
  contextual depth). Mobile stays cleaner.
- **Reject AI-slop:** no purple-on-white gradients, no cookie-cutter card-with-accent-rail, no emoji
  section markers, no centered-everything, no rounded-lg-everywhere.

## Hard constraints
- **Two platforms, one system.** The identity must translate to BOTH React (web) and React Native
  (mobile). RN limits: no CSS gradients/animation as-is (use RN equivalents / Reanimated / SVG), web
  fonts must be bundled, no arbitrary CSS. Decide what's shared (palette, type roles, spacing scale,
  component language) vs platform-specific (motion, background, density).
- **Light AND dark**, both designed (not an auto-invert). **Money in tabular figures.**
- **Accessibility:** legible contrast, visible focus, reduced-motion respected.

## Established rules to KEEP (they already work)
- Accent appears **once per screen**, on the primary action only.
- **Status = a word + a small mark**, never a loud filled pill.
- **Positive-first** (screens double as sales material shown to prospective venues; empty states read
  as achievements — "every shift covered this month", not a blank chart).
- Worker settings are a **drilled list** with the current value shown on each row (not tabs).

## Audience + tone
- **Operators (venues):** professional, confident, "capable, not audited." They may show these
  screens to prospective clients — it must look like software a serious business runs on.
- **Workers:** fast, clear, mobile-native; warmth without being childish or gamified.

## What the brainstorm should produce (a design plan)
- A named **palette** (hexes, light + dark) with the real-world reference it's drawn from.
- A specific **type pairing** (named faces + roles + weights), distinct from Inter/Roboto/Space Grotesk.
- A **spatial system** (scale, radii, density — likely denser on console, roomier on mobile).
- A **component language** (cards, lists, tables, forms, status, money, the feed card, the week board).
- **Motion principles** per platform.
- How the identity **differs across web vs mobile** while staying one brand.

## Open questions the brainstorm should resolve (or surface)
1. How far to push editorial/distinctive vs. how much operator-trust conservatism to keep.
2. One brand for both clients, or a worker sub-brand that shares the system.
3. The signature element — what one thing makes a Venue OS screen recognizable at a glance.
4. Dark-first or light-first as the primary canvas.
