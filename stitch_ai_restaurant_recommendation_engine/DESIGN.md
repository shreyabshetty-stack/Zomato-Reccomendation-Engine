---
name: Crimson Ether
colors:
  surface: '#121414'
  surface-dim: '#121414'
  surface-bright: '#38393a'
  surface-container-lowest: '#0d0e0f'
  surface-container-low: '#1a1c1c'
  surface-container: '#1e2020'
  surface-container-high: '#292a2a'
  surface-container-highest: '#343535'
  on-surface: '#e3e2e2'
  on-surface-variant: '#e4bebc'
  inverse-surface: '#e3e2e2'
  inverse-on-surface: '#2f3131'
  outline: '#ab8987'
  outline-variant: '#5b403f'
  surface-tint: '#ffb3b1'
  primary: '#ffb3b1'
  on-primary: '#680011'
  primary-container: '#ff535a'
  on-primary-container: '#5b000e'
  inverse-primary: '#bb162c'
  secondary: '#c3c6d0'
  on-secondary: '#2d3138'
  secondary-container: '#43474f'
  on-secondary-container: '#b2b5be'
  tertiary: '#c2c6d2'
  on-tertiary: '#2c313a'
  tertiary-container: '#8c919c'
  on-tertiary-container: '#252a33'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#dfe2ec'
  secondary-fixed-dim: '#c3c6d0'
  on-secondary-fixed: '#181c23'
  on-secondary-fixed-variant: '#43474f'
  tertiary-fixed: '#dee2ee'
  tertiary-fixed-dim: '#c2c6d2'
  on-tertiary-fixed: '#171c24'
  on-tertiary-fixed-variant: '#424750'
  background: '#121414'
  on-background: '#e3e2e2'
  surface-variant: '#343535'
typography:
  display:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 16px
  md: 24px
  lg: 32px
  xl: 48px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style

The design system embodies a "Premium AI-first" aesthetic, merging the precision of high-end developer tools with the vibrant energy of food and hospitality. It targets a sophisticated audience that expects speed, intelligence, and a tactile sense of luxury. 

The visual style is a fusion of **Minimalism** and **Glassmorphism**. It utilizes deep obsidian surfaces to let content and AI-generated imagery pop, while employing subtle translucent layers for navigation to maintain a sense of depth and spatial awareness. The emotional response should be one of "effortless intelligence"—where the UI feels secondary to the service, yet rewards interaction with smooth, glowing transitions and meticulous attention to detail.

## Colors

The palette is anchored in a deep charcoal-black (`#0F1115`) to provide a high-contrast foundation for the "Zomato Red" primary accent (`#E23744`). 

- **Primary:** Used for key actions, brand moments, and AI "sparkle" highlights.
- **Surface & Elevated:** Layers are defined by hex steps rather than shadows alone, creating a "stacked" physical feel inspired by modern SaaS interfaces.
- **Borders:** A critical component for the AI aesthetic. Use `#2A2F38` for standard states, shifting to subtle gradients or white-opacity overlays on hover.
- **Text:** High-contrast white for headers and soft, legible grays for metadata to ensure a clear information hierarchy.

## Typography

The design system utilizes **Inter** for its systematic, utilitarian, and modern qualities. The typographic scale emphasizes high contrast between large, bold display text and clean, functional body copy.

To maintain the premium AI feel:
- **Tracking:** Tighten tracking slightly for headlines (`-0.01em` to `-0.02em`) to give a "machined" look.
- **Hierarchy:** Use font weight to differentiate. Labels should be medium or semi-bold even at small sizes to ensure legibility against dark backgrounds.
- **Responsiveness:** Large display types scale down aggressively on mobile to prevent awkward line breaks while maintaining their weight.

## Layout & Spacing

This design system follows a **Fluid Grid** model with generous internal breathing room. 

- **Grid:** A 12-column grid for desktop with 24px gutters. On mobile, transition to a single column with 16px side margins.
- **Padding:** High-end AI tools use "spacious" layouts to reduce cognitive load. Cards and containers should default to `32px` padding on desktop and `20px` on mobile.
- **Rhythm:** All spacing must be a multiple of 4px. Use `24px` (md) as the standard gap between related elements and `48px` (xl) between major sections.

## Elevation & Depth

Depth is conveyed through a combination of **Tonal Layering** and **Glassmorphism**.

1.  **Background (`#0F1115`):** The canvas.
2.  **Surface Cards (`#181B20`):** Primary content containers. Use a 1px border of `#2A2F38`.
3.  **Elevated Surfaces (`#1D2128`):** Hover states or floating modals.
4.  **Glass Layers:** Navigation bars and sticky headers use a `20px` backdrop blur with a `10%` white-tinted fill.

**Shadows:** Avoid heavy black shadows. Instead, use soft, diffused "glow" shadows for active AI elements. For example, a focused input might have a `0 0 15px rgba(226, 55, 68, 0.15)` glow.

## Shapes

The shape language is modern and approachable. 
- **Standard Corners:** `16px` (rounded-lg) is the default for cards, modals, and major containers.
- **Interactive Elements:** Buttons and tags use `8px` (rounded-md) to provide a slightly sharper, more "functional" feel compared to the softer containers.
- **Pills:** Used exclusively for status indicators, "AI-powered" tags, and category chips.

## Components

- **Buttons:** Primary buttons use a solid `#E23744` fill with white text. Hover states should trigger a subtle internal glow or a slight scale increase (1.02x). Secondary buttons use a transparent background with a `#2A2F38` border.
- **AI Input Fields:** Text areas should have a "shimmer" border effect when focused. The cursor or focus ring should use the primary accent color. Use "Sparkle" icons to denote AI-assisted features.
- **Glass Navigation:** Top and bottom bars use `backdrop-filter: blur(12px)` and a thin `bottom-border: 1px solid rgba(255, 255, 255, 0.05)`.
- **Cards:** Content cards must have a 1px border. On hover, the border color should transition from `#2A2F38` to a semi-transparent white or primary red to signal interactivity.
- **Chips:** Small, pill-shaped elements for filters. Use the elevated surface color (`#1D2128`) for the background to keep them distinct from the main card surface.
- **AI Micro-interactions:** Use subtle gradients (Primary Red to a deep Purple/Blue) for progress bars or "thinking" states to distinguish AI processing from standard loading.