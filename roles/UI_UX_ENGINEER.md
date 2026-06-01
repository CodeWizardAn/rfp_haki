# UI/UX Engineer — HAKI FMCG 2.0

> Role perspective documentation for the **UI/UX Engineer** covering the design system, user experience patterns, visual language, interaction design, accessibility, and the methods and protocols used.

---

## 1. What Has Been Designed & Built

### 1.1 Design System — "Electric Procurement"

A **dark-mode-first glassmorphism + neo-brutalism** design system built as a cohesive visual language for an enterprise procurement intelligence platform. The system is implemented directly in code via Tailwind CSS 4's @theme directive and custom @utility classes in src/index.css.

#### Color Palette

| Token | Hex | Role |
|---|---|---|
| deep-navy | #0A0E27 | Page background |
| midnight-blue | #121833 | Card / surface background |
| steel-slate | #1E2642 | Borders, muted surfaces |
| ghost-white | #E8ECF4 | Primary text |
| muted-silver | #8892B0 | Secondary text |
| electric-cyan | #00D4FF | Primary accent (CTAs) |
| neon-emerald | #00E68A | Success |
| amber-glow | #FFB224 | Warning |
| coral-flame | #FF4757 | Danger / Error |
| violet-pulse | #7C3AED | Secondary accent |
| rose-pink | #F472B6 | Tertiary accent |
| teal-depth | #14B8A6 | Technical agent accent |

Each accent has a **dim variant** (rgba at 0.15 opacity) for subtle backgrounds, hover states, and badge fills.

#### Typography Scale

| Class | Size | Weight |
|---|---|---|
| text-display | 64px | 700 (Bold) |
| text-h1 | 36px | 700 (Bold) |
| text-h2 | 28px | 600 (Semi-bold) |
| text-h3 | 20px | 600 (Semi-bold) |
| text-body | 14px | 400 (Regular) |
| text-caption | 12px | 500 (Medium) |
| text-mono-data | 13px | 500 (Medium) |

Font usage:

- text-display — Hero sections, splash numbers (Inter Variable)
- text-h1 — Page titles (Inter Variable)
- text-h2 — Section headings (Inter Variable)
- text-h3 — Card titles, sub-sections (Inter Variable)
- text-body — Body copy, descriptions (Inter Variable)
- text-caption — Labels, timestamps, metadata (Inter Variable)
- text-mono-data — Data values, code, IDs, prices (JetBrains Mono / Fira Code)

**Font stack**: Inter Variable → SF Pro Display → system sans → fallback. Monospace: JetBrains Mono → Fira Code → system mono.

### 1.2 Glassmorphism System

Five glass surface tiers with increasing visual prominence:

**glass-card** — Standard cards

- Blur: 20px, Background: rgba(18,24,51,0.6)
- Border: cyan/10, Shadow: 0 8px 32px black/30

**glass-card-elevated** — Featured/hover cards

- Blur: 24px, Background: rgba(30,38,66,0.7)
- Border: cyan/15, Shadow: 0 16px 48px + inset white/5

**glass-sidebar** — Navigation sidebar

- Blur: 24px, Background: rgba(10,14,39,0.85)
- Border: right cyan/8

**glass-input** — Form inputs

- Blur: 12px, Background: rgba(18,24,51,0.4)
- Border: steel-slate

**glass-modal** — Overlay modals

- Blur: 32px, Background: rgba(18,24,51,0.8)
- Border: cyan/12, Shadow: 0 24px 64px black/50

### 1.3 Gradient System

| Gradient | Usage |
|---|---|
| gradient-hero | Hero sections, primary CTAs |
| gradient-card | Card backgrounds |
| gradient-pipeline | Pipeline-related accents |
| gradient-success | Success states |
| gradient-danger | Error/danger states |
| gradient-gold | Premium/gold tier |
| text-gradient-cyan | Gradient text for headings |
| text-gradient-pipeline | Pipeline heading text |

Color compositions:

- gradient-hero — electric-cyan → violet-pulse → rose-pink
- gradient-card — midnight-blue → steel-slate
- gradient-pipeline — electric-cyan → teal-depth
- gradient-success — neon-emerald → teal-depth
- gradient-danger — coral-flame → rose-pink
- gradient-gold — amber-glow → coral-flame
- text-gradient-cyan — electric-cyan → ghost-white
- text-gradient-pipeline — electric-cyan → teal-depth

### 1.4 Glow Effects

Color-coded soft box-shadows for visual emphasis and status indication:

| Glow | Purpose |
|---|---|
| glow-cyan | Primary emphasis (two-layer) |
| glow-emerald | Success/healthy glow |
| glow-amber | Warning glow |
| glow-coral | Error/danger glow |
| glow-violet | AI/agent glow |

All glows use a two-layer box-shadow pattern: 0 0 20px + 0 0 40px for diffuse effect.

### 1.5 Component Variant Design

#### Card Variants (6)

| Variant | Treatment |
|---|---|
| default | glass-card surface |
| glass | Elevated with stronger blur |
| elevated | Stronger shadow + inset |
| outlined | Border-emphasized, minimal |
| gradient | gradient-card background |
| interactive | Hover: translate, glow, border |

Cards support a **glowColor prop** with 5 color options (cyan, emerald, amber, coral, violet) that renders a colored accent bar at the top.

#### Button Variants (6 × 5 Sizes)

| Variant | Treatment |
|---|---|
| primary | gradient-hero, white text |
| secondary | steel-slate, ghost-white text |
| ghost | Transparent, hover: subtle bg |
| danger | coral-flame background |
| outline | Border only, transparent fill |
| link | Text-only, underline on hover |

**Sizes**: xs (28px), sm (32px), md (38px), lg (44px), xl (52px)

#### Modal Sizes (5)

sm (max-w-md), md (max-w-lg), lg (max-w-2xl), xl (max-w-4xl), full (95vw × 95vh)

---

## 2. User Experience Patterns

### 2.1 Navigation Architecture

**Two-tier navigation model:**

1. **Admin Portal** (AppShell):
   - **Collapsible sidebar** (240px ↔ 64px) with 5 grouped sections:
     - **Core**: Dashboard
     - **Procurement**: RFPs, Pipeline, Bids
     - **Management**: Products, Vendors
     - **Intelligence**: Analytics, Agents
     - **System**: Compliance, Settings
   - **Top bar** with: breadcrumbs, search trigger, pipeline health indicator, theme toggle, notifications, user avatar

2. **User Portal** (UserAppShell):
   - Simplified sidebar with 8 focused pages
   - Streamlined top bar

### 2.2 Information Architecture

| Level | Pattern |
|---|---|
| Overview | Dashboard KPI cards + charts |
| List | Filterable + searchable tables |
| Detail | Full-page deep dive |
| Compare | Side-by-side views |
| Action | Task-focused flows |
| Analytics | Charts + trends |

Examples:

- Overview — Dashboard: 6 KPI cards, agent activity chart, pipeline status
- List — RFP List: filters panel, search autocomplete, batch operations, stats bar
- Detail — RFP Detail: metadata, requirements, compliance score, timeline
- Compare — RFP Compare, Product Comparison, Vendor Comparison
- Action — Bid Builder, RFP Upload, Vendor Registration
- Analytics — Analytics pages with bar/donut/trend charts

### 2.3 Page Load Experience

**Choreographed loading sequence:**
1. PageLoader (centered spinner) shown during route chunk download
2. Skeleton shimmer placeholders shown during data fetch
3. KPICardSkeleton for specific dashboard card placeholders
4. **Stagger animation**: Cards fade up (opacity: 0 → 1, y: 8 → 0) with staggerChildren: 0.06 delay — creating a cascading reveal effect
5. **Mock data fallback**: Dashboard renders with realistic mock data when backend is offline — zero blank-page experience

### 2.4 Empty States

Every list/data view has an EmptyState component with:
- Relevant icon (from Lucide React)
- Descriptive title ("No RFPs found")
- Helpful description ("Upload your first RFP to get started")
- Action CTA button (e.g., "Upload RFP")

### 2.5 Feedback & Notifications

**Toast notifications** — react-hot-toast at bottom-right, triggered on mutation success/error.

**Confirmation dialogs** — ConfirmDialog modal for destructive actions (delete, blacklist).

**Loading spinners** — Button loading prop → Loader2 spinner replacing icon during form submission.

**Pipeline health pulse** — Green animated dot in TopBar, always visible, indicates system status.

**Notification badge** — Animated count badge on bell icon, 9+ truncation for unread notifications.

Toast styling matches the design system: dark glass background (rgba(18,24,51,0.9)), cyan border, 12px border-radius, backdrop-filter blur(12px).

### 2.6 Command Palette (Cmd+K)

A **spotlight-style** search overlay for power users:
- Triggered with Cmd+K or Ctrl+K
- Renders in a Modal with search input
- Fuzzy filters over navigation destinations and action commands
- Keyboard navigable (arrow keys + Enter)
- Categories: Pages, Actions, Quick Navigation

### 2.7 Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| Cmd+K / Ctrl+K | Open command palette |
| ? | Show keyboard shortcuts |
| Cmd+N / Ctrl+N | Upload new RFP |
| Cmd+B / Ctrl+B | Create new bid |
| Cmd+P / Ctrl+P | Go to pipeline |
| 1 – 9 | Quick navigate by position |

### 2.8 Micro-Interactions

**Button press** — Scale to 0.97 via whileTap (Framer Motion).

**Card hover (interactive)** — Translate up 1px + glow via hover classes.

**Sidebar active indicator** — Slides to active item with spring physics (layoutId, stiffness: 400, damping: 30).

**Sidebar collapse** — Width animates 240px ↔ 64px, text fades via AnimatePresence.

**Modal open** — Backdrop fade + content scale 0.95 → 1 via Framer Motion.

**Modal close** — Reverse animation + exit (opacity: 0, scale: 0.95).

**Notification badge** — Pulse animation via CSS animate-pulse.

### 2.9 Theme Support

- **Dark mode** (default): Deep navy backgrounds, light text
- **Light mode toggle**: Available via TopBar (Sun/Moon icon), managed in uiStore
- Theme preference persisted in Zustand store

---

## 3. Why These Design Decisions Were Made

### 3.1 Dark-Mode-First Glassmorphism

- **Enterprise context**: Procurement platforms are used during long working sessions. Dark backgrounds reduce eye strain and screen glare.
- **Information density**: Dark surfaces allow data-rich dashboards (charts, tables, KPIs) to feel less overwhelming than light backgrounds.
- **Visual hierarchy**: Glass surfaces with varying blur and opacity levels create natural depth ordering — elevated content draws attention without harsh borders.
- **Modern aesthetic**: Glassmorphism signals a modern, intelligent platform — appropriate for an AI-powered procurement tool.

### 3.2 Electric Cyan as Primary Accent

- **Visibility**: Cyan provides maximum contrast against dark navy backgrounds — critical for CTAs, focus rings, and actionable elements.
- **Tech/AI connotation**: Electric blue/cyan is synonymous with technology and intelligence in design language — aligns with the platform's AI agent nature.
- **Accessibility**: Cyan on dark navy meets WCAG AA contrast ratios for interactive elements.

### 3.3 Color-Coded Status System

- **Instant comprehension**: Users scanning 50+ RFPs or bids need status at a glance. Semantic colors (green = good, amber = warning, red = error) require zero learning.
- **Consistency**: The same 5 status colors are used across all modules — RFPs, bids, vendors, pipeline stages, compliance checks.

### 3.4 Command Palette

- **Power user productivity**: Procurement professionals work with 70+ pages. A Cmd+K spotlight eliminates deep sidebar navigation.
- **Reduced clicks**: Common actions (upload RFP, create bid, check pipeline) are accessible from any page without navigating first.
- **Industry expectation**: Products like Linear, Notion, and Vercel Dashboard have normalized the command palette pattern — users expect it.

### 3.5 Stagger Animations

- **Perceived performance**: Staggered card reveals make page loads feel faster than showing everything at once — the eye tracks the cascade and assumes content is loading progressively.
- **Visual polish**: Choreographed motion communicates craftsmanship and attention to detail — important for enterprise SaaS trust.
- **Not overdone**: 0.06s delay between cards is subtle enough to not slow down the experience.

### 3.6 Collapsible Sidebar

- **Screen real estate**: 240px sidebar is informative but consumes ~15% of a 1920px screen. Collapsing to 64px (icons only) gives full width back for data-heavy pages like tables and comparisons.
- **Familiar pattern**: Most modern dashboards (Stripe, Vercel, Linear) use collapsible sidebars — minimal learning curve.
- **Animated transition**: Smooth width animation (vs. instant toggle) maintains spatial context — users understand where the sidebar went.

### 3.7 Compound Component Pattern (Cards)

- **Composition flexibility**: Not all cards need titles, footers, or descriptions. Compound components let each page compose exactly the card structure it needs.
- **Consistent spacing**: Internal components handle their own padding and borders — no manual spacing tweaks per page.
- **Variant system**: 6 visual variants cover all use cases from basic containers to interactive click-targets.

### 3.8 Skeleton Loading (Not Spinners)

- **Layout stability**: Skeletons reserve space for incoming content, preventing layout jumps when data arrives.
- **Perceived speed**: Studies show skeleton screens feel 30-40% faster than spinner-only loading states.
- **Context preservation**: Users see the shape of what's coming — KPI cards, table rows, charts — maintaining mental model of the page.

### 3.9 Mock Data Fallback

- **Zero broken-state UX**: If the backend is down, the dashboard still renders meaningful data. Users (and demo audiences) never see a blank page.
- **Development velocity**: Frontend engineers can build and iterate on UI without waiting for backend endpoints to be ready.

---

## 4. Methods Used

### 4.1 Design Methods

**Design Tokens** — All visual properties (colors, type sizes, shadows, animations) are defined as tokens in @theme — enabling systematic updates.

**Atomic Design (adapted)** — Atoms (Button, Badge, Input) → Molecules (Card, KPICard) → Organisms (Sidebar, TopBar, RFPFiltersPanel) → Templates (AppShell) → Pages.

**Variant-Based Design** — Every component supports multiple visual variants via props (e.g., variant="glass", size="lg", glowColor="cyan").

**Compound Component Pattern** — Card family allows flexible composition without prop drilling.

**Consistent Spacing Scale** — Tailwind's spacing scale (4px base) used throughout: p-3, p-4, p-6, gap-4, gap-6.

**4px Grid** — All spacing, padding, margins align to a 4px grid for visual consistency.

### 4.2 UX Methods

**Progressive Disclosure** — Overview → List → Detail → Compare flow. Complexity is revealed in layers.

**Graceful Degradation** — Mock data fallbacks, empty states with CTAs, skeleton loading during data fetch.

**Keyboard-First Power Features** — Command palette, shortcut overlay, number-key navigation for power users.

**Consistent Feedback** — Every user action produces visible feedback: toasts, spinners, confirmations, state changes.

**Recognition Over Recall** — Lucide icons paired with text labels in sidebar; breadcrumbs show current location; active state highlighting.

**Error Prevention** — Confirmation dialogs before destructive actions; form validation with Zod schemas; disabled states on invalid forms.

### 4.3 Visual Design Methods

**Depth Through Blur** — 5-tier glassmorphism system creates z-axis hierarchy without explicit elevation numbers.

**Color-as-Status** — Semantic color mapping: cyan=primary, green=success, amber=warning, red=danger, violet=AI.

**Glow for Emphasis** — Color-matched glow effects draw attention to active/important elements.

**Gradient as CTA Marker** — Primary gradient (cyan→violet→pink) reserved for hero CTAs and primary buttons.

**Motion as Communication** — Spring-physics sidebar indicator communicates "you are here"; stagger communicates "content is loading".

### 4.4 Interaction Design Methods

**Spring Physics** — Sidebar active indicator uses stiffness: 400, damping: 30 — feels physical and responsive.

**Micro-Interactions** — Button press scale, card hover translate, badge pulse — reward user actions with tactile feedback.

**AnimatePresence** — Enter/exit transitions on modals and sidebar labels — content doesn't just appear/disappear.

**Stagger Choreography** — staggerChildren: 0.06 on page load — systematic instead of chaotic.

**Layout Animation** — layoutId shared-layout transitions for smooth element movement across renders.

### 4.5 Accessibility Methods

**Focus-visible rings** — Cyan outline with offset for keyboard navigation.

**Keyboard navigation** — All modals close on Escape; command palette is fully keyboard-navigable.

**Semantic HTML** — nav, header, main, button used correctly.

**Screen reader hints** — title attributes on collapsed sidebar items; descriptive aria labels.

**Scroll lock** — Modals set document.body overflow hidden to prevent background scroll.

**Contrast compliance** — Primary text (ghost-white on deep-navy) exceeds WCAG AA; electric-cyan on deep-navy meets interactive element requirements.

**Disabled states** — opacity-50, cursor-not-allowed, pointer-events-none on all interactive elements.

---

## 5. Protocols Used

### 5.1 Design System Protocol

1. **Token-first**: Every visual property must be a design token in @theme — no hardcoded hex values in components
2. **Utility-first**: Use Tailwind utility classes; create @utility only when a pattern is used 3+ times
3. **cn() composition**: All conditional classes go through cn() (clsx + tailwind-merge) to prevent class conflicts
4. **Variant exhaustiveness**: New component variants must cover all existing states before shipping
5. **Glass hierarchy**: Use the correct glass tier for the element's visual importance level

### 5.2 Component Design Protocol

1. **Props-driven variants**: Visual differences are controlled by props (e.g., variant, size, glowColor), never by page-specific CSS overrides
2. **Compound over monolithic**: Complex components (like Card) use the compound pattern with exported sub-components
3. **forwardRef for interactives**: All interactive primitives (Button, Input) use React.forwardRef for ref forwarding
4. **Loading as a first-class prop**: Interactive components support a loading prop that internally handles spinner display
5. **Default to motion.div**: Wrapping components with Framer Motion's motion.div for consistent animation capabilities

### 5.3 Animation Protocol

| Rule | Details |
|---|---|
| Duration budget | Max 0.4s, micro ≤ 0.2s |
| Ease curve | easeInOut for position, spring for indicators |
| Exit animations | Every enter has corresponding exit |
| Stagger limit | Max staggerChildren: 0.08 |
| Reduce motion | Respect prefers-reduced-motion |

### 5.4 Color Usage Protocol

**electric-cyan** — Allowed: CTAs, links, focus rings, primary indicators. Forbidden: Error states, warning content.

**neon-emerald** — Allowed: Success messages, healthy status, positive metrics. Forbidden: Navigation, neutral content.

**amber-glow** — Allowed: Warnings, gold tier, pending items. Forbidden: Success states, primary actions.

**coral-flame** — Allowed: Errors, danger actions, critical alerts. Forbidden: Success states, informational.

**violet-pulse** — Allowed: AI indicators, gradients, secondary emphasis. Forbidden: Status indicators, warnings.

### 5.5 Responsive Design Protocol

| Breakpoint | Behavior |
|---|---|
| < 768px (md) | Sidebar auto-collapses, TopBar minimal |
| < 1024px (lg) | TopBar hides pipeline health |
| ≥ 1024px | Full sidebar with text labels |
| Modal sizing | sm/md bounded; full uses 95vw × 95vh |

### 5.6 Feedback Protocol

| User Action | Required Feedback |
|---|---|
| Form submission | Button spinner → Toast |
| Destructive action | Confirm dialog → Toast |
| Data loading | Skeleton placeholder |
| Empty data | EmptyState with CTA |
| Network error | Error toast with retry |
| Real-time update | SSE green pulse dot |

---

## 6. Information Visualization Design

### 6.1 Chart Components

| Chart | Usage |
|---|---|
| BarChart | Comparative metrics |
| DonutChart | Proportional data |
| TrendChart | Time-series data |

All charts follow the design system palette and use glassmorphism-styled containers. Built with Recharts.

### 6.2 KPI Cards

- Display format: **Value** (large, text-h2 or display) + **Label** (caption, muted-silver) + **Trend indicator** (green up / red down arrow with percentage)
- Optional glow accent via glowColor prop for visual status
- Skeleton loading state (KPICardSkeleton) reserves exact layout dimensions

### 6.3 Data Formatting

India-focused formatting utilities for procurement data:

| Function | Output Example |
|---|---|
| formatCurrency(1234567) | ₹12,34,567 |
| formatCompactCurrency(1250000) | ₹12.5L |
| formatCompactCurrency(32000000) | ₹3.2Cr |
| formatPercentage(0.875) | 87.5% |
| timeAgo(date) | "5 minutes ago" |

---

## 7. User Flows Summary

### 7.1 Authentication Flow
```
Landing → Login Page → [Enter credentials] → Dashboard (with stagger animation)
                     → [Register link] → Register Page → Login → Dashboard
```

### 7.2 RFP Processing Flow
```
Dashboard → RFPs → [Upload] → Upload Page (drag-and-drop)
                             → Processing (pipeline stages with status updates via SSE)
                             → Detail Page (extracted data, compliance score)
                             → Compare Page (side-by-side analysis)
```

### 7.3 Bid Management Flow
```
RFP Detail → Create Bid → Bid Builder (product selection, pricing editor)
                        → Financial Summary → Approval → Document Preview → Export
```

### 7.4 Power User Flow
```
Any Page → Cmd+K → Command Palette → [Type action] → Navigate/Execute
Any Page → ? → Shortcut Overlay → Learn keyboard shortcuts
Any Page → 1-9 → Quick navigate to core routes
```

---

## 8. Design-to-Code Implementation

### 8.1 Token Implementation

Design tokens live in src/index.css as @theme declarations, making them directly usable as Tailwind classes:

```css
@theme {
  --color-electric-cyan: #00D4FF;
  --color-deep-navy: #0A0E27;
  /* ... */
}
```
→ Consumed as bg-deep-navy, text-electric-cyan, border-electric-cyan/10

### 8.2 Utility Class Implementation

Reusable design patterns are codified as @utility classes:

```css
@utility glass-card {
  backdrop-filter: blur(20px);
  background: rgba(18, 24, 51, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}
```
→ Consumed as class="glass-card" anywhere in JSX

### 8.3 Variant Implementation

Component variants are implemented via the cn() utility pattern:

```tsx
const variants = {
  primary: 'bg-gradient-to-r from-electric-cyan ...',
  danger:  'bg-coral-flame hover:bg-coral-flame/90 ...',
};

<button className={cn(base, variants[variant], sizes[size], className)} />
```

---

## 9. Key Metrics & Targets

| Metric | Target |
|---|---|
| First Contentful Paint | < 1.5s |
| Time to Interactive | < 3s |
| Layout Shift (CLS) | < 0.1 |
| Animation Frame Rate | 60fps |
| Accessibility Score | WCAG AA |
| Max Click Depth | 3 clicks to any feature |

Methods:

- FCP < 1.5s — Lazy loading, code splitting, Vite optimization
- TTI < 3s — Skeleton loading, progressive hydration
- CLS < 0.1 — Skeleton placeholders reserve space
- 60fps — GPU-accelerated transforms, will-change hints
- WCAG AA — Focus-visible rings, semantic HTML, contrast ratios
- 3 clicks — Cmd+K palette, keyboard shortcuts, flat navigation
