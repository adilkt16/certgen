---
name: CertGen
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#d0c5af'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#99907c'
  outline-variant: '#4d4635'
  surface-tint: '#e9c349'
  primary: '#f2ca50'
  on-primary: '#3c2f00'
  primary-container: '#d4af37'
  on-primary-container: '#554300'
  inverse-primary: '#735c00'
  secondary: '#c8c6c2'
  on-secondary: '#30312e'
  secondary-container: '#494946'
  on-secondary-container: '#b9b8b4'
  tertiary: '#d0cdcd'
  on-tertiary: '#313030'
  tertiary-container: '#b4b2b2'
  on-tertiary-container: '#454544'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffe088'
  primary-fixed-dim: '#e9c349'
  on-primary-fixed: '#241a00'
  on-primary-fixed-variant: '#574500'
  secondary-fixed: '#e4e2dd'
  secondary-fixed-dim: '#c8c6c2'
  on-secondary-fixed: '#1b1c19'
  on-secondary-fixed-variant: '#474744'
  tertiary-fixed: '#e5e2e1'
  tertiary-fixed-dim: '#c8c6c5'
  on-tertiary-fixed: '#1c1b1b'
  on-tertiary-fixed-variant: '#474746'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Bodoni Moda
    fontSize: 64px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Bodoni Moda
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-lg:
    fontFamily: Bodoni Moda
    fontSize: 48px
    fontWeight: '500'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Bodoni Moda
    fontSize: 32px
    fontWeight: '500'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.1em
  button:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.02em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1280px
  gutter-desktop: 32px
  gutter-mobile: 16px
  margin-desktop: 64px
  margin-mobile: 24px
---

## Brand & Style

This design system embodies the prestige of a traditional institution through a modern, editorial lens. The visual language balances the authority of classic typography with the sleek efficiency of a high-end digital tool. It is designed to evoke confidence and exclusivity, ensuring that every certificate generated feels like a high-value asset.

The aesthetic follows a **High-Contrast Editorial** movement. It utilizes dark, cinematic backgrounds to frame light, tactile "paper" surfaces. Layouts are governed by generous whitespace and a rigorous hierarchy, prioritizing legibility and a sense of "breathe-ability" often found in luxury fashion or architectural journals.

## Colors

The palette is rooted in a "Dark Mode Luxury" foundation. The background utilizes **Midnight Black (#1A1A1A)** and **Deep Charcoal (#121212)** to create a sophisticated, immersive environment. 

Primary interaction surfaces and certificate previews use **Warm Parchment (#F9F7F2)** and **Cream Neutral (#E8E4D9)** to mimic physical high-grade paper stock. This creates a stark, intentional contrast against the dark interface. **Rich Gold (#D4AF37)** and **Amber (#C5A028)** are used sparingly as "jewel" accents for critical actions, status indicators, and branding flourishes, ensuring they command attention without overwhelming the editorial balance.

## Typography

Typography is the cornerstone of the system's identity. **Bodoni Moda** serves as the display typeface, providing high-contrast serifs that suggest heritage and craftsmanship. It should be used for headings and branding elements where visual impact is paramount.

**Inter** provides a functional, neutral counterpoint for the interface. It handles all utility-driven content—form fields, data tables, and navigation—ensuring the app remains highly usable despite its stylistic flourishes. Use uppercase labels with generous letter spacing for categorization to maintain an editorial "spec-sheet" feel.

## Layout & Spacing

The layout philosophy follows a **Fixed Grid** for content-heavy views and a **Fluid Editor** for the certificate workspace. On desktop, a 12-column grid is used with wide 32px gutters to prevent information density from feeling cluttered.

Margins are intentionally large (64px on desktop) to frame the content as if it were a plate in a book. The vertical rhythm is strictly based on an 8px baseline grid. On mobile devices, gutters compress to 16px and margins to 24px, with the 12-column grid collapsing into a single-column stack for data entry, while keeping the live preview persistent or easily accessible via a floating toggle.

## Elevation & Depth

Depth is achieved through **Tonal Layering** rather than aggressive shadows. 
- **Level 0:** The base background (#121212).
- **Level 1:** Floating panels or sidebar containers (#1A1A1A) with a subtle 1px border (#2A2A2A).
- **Level 2:** Primary workspace "Paper" (Parchment #F9F7F2). This layer uses a soft, diffused ambient shadow with a hint of gold-tinted color (`rgba(212, 175, 55, 0.08)`) to make the certificate appear as if it is resting on a dark velvet surface.

Avoid heavy blurs; instead, use sharp, 1px lines in low-opacity gold or grey to define boundaries between dark elements.

## Shapes

The shape language is primarily **Soft (0.25rem)** to maintain a structured, professional appearance. 
- Standard components like buttons and input fields use a 4px radius. 
- Card containers and larger parchment surfaces use `rounded-lg` (8px). 
- Avoid fully pill-shaped or circular elements unless used for avatars or status dots, as they break the sophisticated, architectural tone of the system.

## Components

### Buttons & Controls
Primary buttons use the Gold accent with dark text, featuring a 4px corner radius. Hover states should involve a subtle shift to the Amber tint or a slight lift shadow. Secondary buttons are "Ghost" style with a 1px Gold border and text.

### Stepper Indicator
A minimalist, vertical or horizontal line-based stepper. Completed steps are indicated by a gold checkmark; current steps are a small gold ring; upcoming steps are muted grey. No heavy backgrounds for steps—keep the focus on the text labels.

### Drag-and-Drop Zones
Dashed borders in #E8E4D9 (Cream) over the #1A1A1A background. On hover, the dashed line turns solid Gold with a very faint gold wash (5% opacity) over the drop area.

### Live Preview Cards
The most prominent component. The certificate preview must be framed in a parchment-colored container with a 1px border. It should use a "scale-to-fit" logic within its parent container to ensure the user always sees the full composition.

### Data Tables
Tables are designed with high-end editorial lists in mind: no vertical grid lines, only thin horizontal separators (#2A2A2A). Header rows use the `label-caps` typography style. Cell padding is generous (16px vertical) to ensure each row feels like a distinct record.

### Input Fields
Dark-themed inputs (#1A1A1A) with a subtle 1px border. Focus states use a solid Gold 1px border. Labels should sit above the field in `label-caps` style for maximum clarity.