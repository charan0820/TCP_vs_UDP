---
name: Transport Lab
description: A signal archive for configuring networks and inspecting real NS-3 transport experiments.
colors:
  ink: "#05060a"
  panel: "#0d101a"
  line: "#2a3044"
  text: "#f4f6ff"
  muted: "#b5bed0"
  violet: "#a78bfa"
  cyan: "#5ee7f7"
  pink: "#fb8fb8"
  mint: "#75e3ba"
  selected: "#211b35"
typography:
  display:
    fontFamily: "Sora, sans-serif"
    fontSize: "clamp(64px, 8vw, 96px)"
    fontWeight: 600
    lineHeight: 1.03
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Sora, sans-serif"
    fontSize: "2.7rem"
    fontWeight: 600
    letterSpacing: "-0.035em"
  section:
    fontFamily: "Sora, sans-serif"
    fontSize: "1.65rem"
    letterSpacing: "-0.035em"
  title:
    fontFamily: "Sora, sans-serif"
    fontSize: "1.12rem"
    letterSpacing: "-0.035em"
  body:
    fontFamily: "Sora, sans-serif"
    lineHeight: 1.65
  feature-body:
    fontFamily: "Sora, sans-serif"
    fontSize: "13px"
    lineHeight: 1.8
  button:
    fontFamily: "Sora, sans-serif"
    fontSize: "0.86rem"
  label:
    fontFamily: "'IBM Plex Mono', monospace"
    fontSize: "9px"
    letterSpacing: "0.16em"
  metric:
    fontFamily: "'IBM Plex Mono', monospace"
    fontSize: "1.65rem"
  player-body:
    fontFamily: "system-ui, sans-serif"
    fontSize: "13px"
  player-clock:
    fontFamily: "ui-monospace, monospace"
    fontSize: "14px"
rounded:
  control: "8px"
  panel: "12px"
  status: "999px"
spacing:
  unit: "4px"
  control-gap: "8px"
  small: "12px"
  medium: "16px"
  feature-gap: "18px"
  panel: "24px"
  feature: "32px"
  section: "60px"
components:
  button-primary:
    textColor: "#ffffff"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    height: "44px"
  button-secondary:
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    height: "44px"
  button-secondary-hover:
    backgroundColor: "{colors.selected}"
  navigation:
    rounded: "{rounded.control}"
    padding: "8px 12px"
  navigation-selected:
    backgroundColor: "{colors.selected}"
  hero-status:
    rounded: "{rounded.status}"
    padding: "10px 17px"
  panel:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.panel}"
  feature:
    rounded: "{rounded.panel}"
    padding: "{spacing.feature}"
  player-field:
    textColor: "{colors.text}"
    typography: "{typography.player-body}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
    height: "40px"
  packet-canvas:
    rounded: "{rounded.panel}"
    width: "100%"
    height: "300px"
---

# Design System: Transport Lab

## Overview

**Creative North Star: "Signal archive"**

The Signal archive turns a network experiment into a readable trail of evidence. A near-black field gives white typography room to lead; a cyan-to-violet signal column establishes the identity. Colored gradient panels explain the mechanism, while the working lab uses compact native controls and clear borders.

Sora supplies the large, direct voice; IBM Plex Mono marks technical labels and measured values. The atmosphere is expressive, but every status and recording claim must describe the local simulator honestly. Decorative motion arrives once, then settles so users can inspect the experiment.

**Key Characteristics:**

- Near-black surfaces with cyan and violet signal light.
- Large editorial type paired with precise technical labels.
- Colorful explanatory panels and compact operational controls.
- Bounded motion, visible focus and honest recording states.

The normative values above are extracted from `dashboard/theme.css`, `.streamlit/config.toml` and `visualization/packet_player.html`. `dashboard/theme.py` supplies local fonts and the landing markup. Component height tokens describe implemented minimum control heights. Extensions, motion, breakpoints and isolated component examples live in `.impeccable/design.json`.

## Colors

Primary: **Signal Violet** marks primary actions, selected navigation and ACK/control traffic. **Signal Cyan** marks links, focus, prominent metrics, sender nodes and data packets. These colors carry the identity across the shell and player.

Secondary: **Drop Pink** identifies recorded drops; the player also draws an ×. **Status Mint** marks the local-workspace status. Colored landing panels use cyan, violet and pink-tinted gradients to distinguish explanation groups.

Neutral: **Ink** is the page ground, **Panel** the resting container, **Line** the structural separator, **Text** the principal reading color and **Muted** supporting copy. **Selected** is the darker violet surface shared by selected navigation and secondary-button hover.

The sidecar's tonal ramps are synthesized palette-exploration strips; they are not additional implemented product colors.

**The Recorded Signal Rule.** Packet color always has a text label; animation represents captured events, and a topology preview is identified as a preview.

## Typography

Sora is the display and body family with a sans-serif fallback. IBM Plex Mono is the technical voice with a monospace fallback. Both font files ship locally and are embedded by the theme; no external font request is required.

The display role belongs to the landing title. Headline, section and title roles step down through working-page headings. Body text stays open and readable; feature copy uses the smaller feature-body role with generous leading. Narrative landing copy is capped at 44 characters per line, feature copy at 54, and the wider measurement panel at 68.

Labels are small and tracked; they annotate rather than carry essential instructions. Metrics use the mono role and cyan. Numeric text and number inputs use tabular figures. The self-contained player deliberately uses its player-body and player-clock system stacks rather than importing the shell's embedded font payload.

**The Two Voices Rule.** Use Sora for narrative and controls; reserve the mono face for telemetry, identifiers, code and compact technical labels.

## Layout

The shell is centered in a maximum-width container (1320px), with desktop padding (1.25rem 3rem 4rem). Working controls follow native Streamlit layout and wrap where space requires it. Navigation wraps rather than clipping.

The landing feature grid uses unequal columns (1.2fr / 1fr), the feature-gap token and a full-width measurement panel. Feature cards use the feature padding token. The hero has a minimum height (590px), clipped decorative layers and an independent centered content layer.

At the mobile breakpoint (767px), the shell uses padding (1rem 1rem 3rem), feature cards form one column with panel padding, the footer stacks and navigation spacing tightens. The hero minimum height becomes (530px), its title becomes (66px), and its metadata moves inward. Preserve readable controls before preserving desktop composition.

Inside the player, narrow viewports (480px or less) move link bandwidth and delay labels from the graph into a scrollable text list below the canvas. The list has a bounded height (100px), keeping long topologies from displacing playback controls.

## Elevation & Depth

Depth comes primarily from tonal layering, thin structural borders and translucent signal gradients. The hero's dotted field is masked into a narrow central column; a blurred cyan/violet beam creates atmospheric depth without obscuring its title. Working panels remain quiet.

The primary action has one restrained violet shadow; its exact CSS and the landing gradient recipes are captured in the sidecar examples. Hover changes color and raises buttons slightly (1px). There is no general floating-card shadow system.

**The Quiet Surface Rule.** Use tonal layering and borders for working panels. Reserve the luminous field for the landing expression and the violet shadow for primary actions.

## Shapes

Panels and canvas frames share the panel radius; controls use the smaller control radius. Pills are reserved for compact status labels. Network nodes and packet dots are circular, links are straight, and recorded drops have a crossed marker. Preserve the difference between a bounded interface surface and the precise graph geometry within it.

## Components

### Buttons

Primary actions use a violet gradient, white text and the restrained action shadow. Secondary actions use the native dark theme, a fine border and a selected-tone hover surface. Shell controls use the documented minimum height. Both variants transition background, border and position over (0.2s); keyboard focus uses a cyan outline (2px) with an offset (4px).

### Navigation

The native radio navigation reads as compact bordered tabs. The active choice has a selected-tone surface and violet-tinted border. Its group has a bottom divider, wrap behavior and compact mobile padding. Preserve the underlying accessible radio interaction.

### Status labels

The landing ready-state label is a small outlined translucent pill with mono lettering. Local-workspace status uses mint. Status text must remain explicit; decorative color does not establish simulator readiness or recording availability.

### Cards and containers

Resting expanders and bordered containers use the neutral panel treatment. Landing feature cards carry separate cyan, violet and pink-tinted gradients with high-contrast headings. The archive note is a subdued two-tone informational surface. Use the documented panel and feature spacing roles rather than making every working container a colorful feature card.

### Inputs and player controls

Shell inputs remain native Streamlit controls; the theme adds tabular numbers and the shared focus treatment. The standalone player's buttons and selects use their own dark control surface, fine border, control radius and minimum height. They use a cyan focus outline (2px) with an offset (3px). Preserve visible labels and native input semantics.

### Packet canvas

The canvas frame uses a dark radial background and the panel outline. Recorded traffic exposes play/pause, restart, speed, filters and a simulation-time scrubber. A topology without events uses the shorter preview frame (260px) and hides replay controls. Packet colors have a text legend and raw-event alternatives in the dashboard. Dashed rings identify unobserved outcomes; they do not imply delivery.

Link labels remain inline on wider graphs. The narrow player uses a labelled list with one item per link, including endpoint identifiers, bandwidth and delay, to avoid overlapping graph annotations.

### Motion

The shell enters with a short surface reveal (0.45s). The signal field arrives once (1.8s), and the beam resolves once (2s), using the same easing curve. Reduced-motion disables decorative animation, transitions and smooth scrolling; the player begins paused. Playback motion follows recorded simulation timestamps and runs animation frames only while playing.

## Do's and Don'ts

### Do

- Do keep the cyan/violet signal identity and near-black workspace consistent across the shell and packet player.
- Do provide visible keyboard focus and readable labels alongside packet colors.
- Do respect reduced motion: disable decorative transitions and begin playback paused.
- Do distinguish topology previews, recorded events, missing captures and truncated captures.
- Do use the same selected run for replay and its measured results.

### Don't

- Don't turn the reference image's fictional memory or security telemetry into product claims.
- Don't animate invented packet deliveries or expose Play controls on an empty topology preview.
- Don't use the hero's large display treatment for dense editor labels or measured tables.
- Don't add persistent decorative movement behind the operational workspace.

> **Preserved direction contract and implementation audit.** The approved thesis is: build a network, run it, follow the recorded signal, inspect its cost. The supplied Memory Core reference's luminous column and dotted field establish a networking identity. The first expression is large white PACKET CORE typography, compact navigation, honest local-workspace metadata and a clear entry action. The implementation remains custom CSS inside Streamlit with native controls and a self-contained player.
>
> The former cream/teal interface exposed a static preview with disabled Play controls, separate TCP/replay run selectors, duplicated network defaults, cached player HTML and archive entries without recording status. The redesign unifies the run/recording lifecycle. Legacy root C headers now act as compatibility includes for canonical `common/` headers. This is a historical audit, not an additional visual token source.
