# Design System: Tallybook

## 1. Visual Theme & Atmosphere
A calm, editorial research desk. Warm off-white canvas, near-black ink, one emerald accent. Variance 8 (asymmetric splits, left-aligned heroes), motion 6 (spring-feel CSS rise, one looping hero demo), density 6 (data pages use rules and whitespace, not boxes).

## 2. Color Palette & Roles
- **Canvas** (#F7F7F5) page background
- **Charcoal Ink** (#18181B) text, primary buttons
- **Muted Steel** (#71717A) secondary text
- **Whisper Line** (#E4E4E7) 1px dividers
- **Emerald** (#059669) the single accent: bullish scores, focus rings, active states
- **Rose** (#BE123C) semantic only: bearish scores and errors
- No purple, no neon, no pure black.

## 3. Typography Rules
- **Display and body:** Geist, tight tracking on headlines, weight and colour for hierarchy.
- **Numbers and labels:** Geist Mono, tabular figures for every score.
- **Banned:** Inter, serif fonts (this is a software UI).

## 4. Component Stylings
- **Buttons:** flat, no glow, 1px push on `:active`, 44px minimum height.
- **Cards:** used once (hero panel), 2rem radius, tinted diffusion shadow. Everything else is divided by `divide-y`.
- **Inputs:** label above, helper below, errors inline in a left-ruled banner.
- **Loaders:** shimmer skeletons that match the final layout. Empty states say how to fill them.

## 5. Layout Principles
CSS Grid only. `max-w-7xl`, 16px mobile gutters, `min-h-[100dvh]` heroes. Two-column asymmetric hero, ruled lists instead of a 3-up card row. Single column below 768px.

## 6. Motion & Interaction
CSS keyframes on transform and opacity only. Hero panel loops the four agents lighting up. `prefers-reduced-motion` turns all of it off.

## 7. Anti-Patterns (Banned)
Emojis, Inter, pure black, neon glows, gradient headline text, 3 equal feature cards, centered hero, filler copy ("seamless", "elevate"), round fake numbers, stock-photo placeholders.
