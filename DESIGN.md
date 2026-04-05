# Design System: Sentry Dashboard (Selected)

## 1. Visual Theme & Atmosphere
Dark-mode-first dashboard UI inspired by Sentry's data-dense product surface.
Use warm purple-black backgrounds (not pure black), vivid but controlled accents, and strong card separation for analytics readability.

## 2. Color Palette & Roles
- `--bg`: `#1f1633` (page background)
- `--bg2`: `#19112b` (panel background)
- `--bg3`: `#261c3d` (interactive surface)
- `--bg4`: `#2f2450` (raised/hover surface)
- `--text`: `#f4f1ff` (primary text)
- `--muted`: `#b0a8c9` (secondary text)
- `--accent`: `#c2ef4e` (primary highlight / CTA)
- `--accent3`: `#6a5fc1` (interactive secondary accent)
- `--accent4`: `#ffb287` (warning / attention)
- `--plus`: `#9fe870` (positive)
- `--minus`: `#ff8fb3` (negative)
- `--border`: `rgba(121, 98, 140, 0.45)`

## 3. Typography Rules
- Base UI font: `Rubik`, fallback `Zen Kaku Gothic New`, sans-serif
- Monospace data font: `Share Tech Mono`, fallback `Monaco`, monospace
- Body text: 14px-15px, line-height 1.55
- Labels and tabs: 11px-13px, medium/bold
- Numeric KPI: monospace + semibold/bold

## 4. Spacing & Radius
- Base spacing unit: 4px
- Scale: 4 / 8 / 12 / 16 / 20 / 24
- Radius scale: 8 / 12 / 16 / 999
- Touch target min height: 44px

## 5. Component Stylings
### Buttons
- Rounded 12px, border 1px, subtle inset/ambient shadow
- Primary: accent fill (`#c2ef4e`) with dark text
- Secondary/filter: `--bg3` surface with muted text
- Active state: `--accent3` fill

### Cards
- Background `--bg2` or `--bg3`
- Border `--border`
- Radius 12px
- Soft elevation shadow for separation

### Badges
- Pill radius (999px), 10px-12px text
- Semantic colors for info/success/warning/error
- Keep contrast high against dark surfaces

### Tables
- Sticky visual hierarchy with darker header surface
- Reduced border noise and better row separators
- Mobile uses horizontal scroll container and tighter type scale

## 6. Layout Principles
- Mobile-first single-column default
- Increase density gradually on tablet/desktop
- Keep card/panel rhythm consistent (`12px-16px` interior padding)
- Prioritize glanceability for status, trend, and ranking views

## 7. Responsive Behavior
- `<640px`: larger tap targets, condensed labels, table readability tuning
- `>=640px`: preserve compact dashboard density
- Avoid tiny fonts below 11px for critical data labels

## 8. Do / Don't
### Do
- Use dark purple surfaces consistently
- Keep status colors semantic and reusable
- Use shared button/card/badge primitives

### Don't
- Mix unrelated accent colors in one component
- Use low-contrast gray text on data-heavy panels
- Introduce one-off inline styles for repeated components

## 9. Agent Prompt Guide
When generating or editing UI:
- "Use Sentry-style dark purple dashboard surfaces with high-contrast text."
- "Unify buttons/cards/badges with shared CSS variables and consistent spacing/radius."
- "Optimize mobile readability while preserving desktop data density."
