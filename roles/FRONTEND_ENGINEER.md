# Frontend Engineer — HAKI FMCG 2.0

> Role perspective documentation for the **Frontend Engineer** covering what was built, how it was built, why each decision was made, and the methods and protocols used.

---

## 1. What Has Been Built

### 1.1 Single-Page Application (SPA)

A full-featured **React 19** single-page procurement intelligence platform (haki-fmcg-frontend/) serving as the user-facing layer for the HAKI FMCG 2.0 backend. The SPA includes **70+ pages** across 12 functional modules:

**Dashboard** — DashboardPage: KPI cards, live agent activity, pipeline health, quick actions.

**RFP Management** — 7 pages: RFPListPage, RFPDetailPage, RFPUploadPage, RFPComparePage, RFPAnalyticsPage, RFPPDFPreviewPage, RFPTermsDatabasePage. Full lifecycle — upload, process, compare, analyze RFPs.

**Bid Management** — 11 pages: BidsPage, BidBuilderPage, BidApprovalPage, BidAnalyticsPage, BidDocumentPreviewPage, BidCalendarPage, BidPricingEditorPage, BidTemplatesPage, BidFinancialSummaryPage, BidNotificationsPage, BidRevisionHistoryPage. Create, price, approve, track bids.

**Product Catalog** — 8 pages: ProductsPage, ProductDetailPage, ProductComparisonPage, ProductAdvancedSearchPage, EngineeringCalculatorPage, CategoryNavigatorPage, PriceTrackerPage, ProductRecommendationPage. Browse, search, compare, recommend products.

**Vendor Management** — 11 pages: VendorsPage, VendorProfilePage, VendorRankingsPage, VendorAnalyticsPage, VendorCommunicationPage, VendorComparisonPage, VendorRegistrationPage, VendorActivityFeedPage, VendorComplianceStatusPage, VendorBlacklistPage, VendorAuditTrailPage. Full vendor lifecycle and due diligence.

**AI Agents** — 9 pages: AgentsPage, AgentDetailPage, AgentChatPage, AgentConfigPage, AgentIntercomPage, AgentWorkflowTemplatesPage, AgentErrorHandlingPage, AgentHealthCheckPage, AgentAnalyticsPage. Monitor, configure, chat with AI agents.

**Pipeline** — 3 pages: PipelinePage, PipelineHistoryPage, PipelineConfigPage. RFP processing pipeline status and configuration.

**Analytics & Intelligence** — 8 pages: AnalyticsPage, PredictiveAnalyticsPage, CostAnalysisPage, TrendAnalysisPage, ABTestingDashboardPage, TenderPricingIntelPage, AlertConfigurationPage, ReportTemplateDesignerPage. Business intelligence dashboards.

**Compliance & Audit** — 5 pages: CompliancePage, ComplianceReportPage, ComplianceRuleViewerPage, AuditTrailPage, AuditTrailDetailPage. Regulatory compliance and audit trail.

**Settings & Admin** — 5 pages: SettingsPage, SystemPerformancePage, PerformanceTuningPage, UserManagementPage, WebhookManagementPage. System administration.

**User Portal** — 8 pages: UserDashboardPage, UserRFPProcessingPage, UserRFPAnalyzerPage, UserProductsPage, UserAnalyticsPage, UserHistoryPage, CompanyProfilesPage, BidGeneratorPage. Simplified end-user portal (separate AppShell).

**Auth** — 2 pages: LoginPage, RegisterPage. JWT-based authentication.

### 1.2 Reusable Component Library

A custom component system in src/components/:

- **UI Primitives** (ui/): Card (compound pattern, 6 variants), Button (6 variants × 5 sizes), Modal (5 sizes + ConfirmDialog), Loading (Skeleton, PageLoader, Spinner, EmptyState, KPICardSkeleton), Badge, Input
- **Layout** (layout/): AppShell, UserAppShell, Sidebar, UserSidebar, TopBar, UserTopBar
- **Charts** (charts/): BarChart, DonutChart, TrendChart — Recharts wrappers
- **Feature Components**: rfp/ (RFPCard, RFPFiltersPanel, RFPSearchAutocomplete, RFPBatchOperations, RFPStatsBar), bids/ (BidAnalyticsWidget), agents/ (AgentPerformancePanel), analytics/ (KPICard), pipeline/ (PipelineStatsPanel, PipelineErrorRecovery)
- **Common** (common/): CommandPalette, ShortcutOverlay
- **Auth** (auth/): AuthGuard, GuestGuard

### 1.3 Services Layer

Typed API service modules in src/services/:

| Service | Domain |
|---|---|
| api.ts | Axios + JWT interceptors + token refresh |
| auth.service.ts | Login, logout, register, profile |
| rfp.service.ts | CRUD + upload + compare + analyze |
| bid.service.ts | Bid lifecycle, approvals, templates |
| product.service.ts | Catalog, search, comparison |
| vendor.service.ts | Management, rankings, comms |
| agent.service.ts | Status, configuration, chat |
| pipeline.service.ts | Runs, configuration, history |
| analytics.service.ts | KPIs, trends, predictions |
| tender-pricing.service.ts | Pricing intelligence |

### 1.4 State Management Layer

Zustand stores in src/stores/:

| Store | Responsibility |
|---|---|
| authStore.ts | User session, login/logout, persisted |
| uiStore.ts | Sidebar, theme, command palette |
| notificationStore.ts | Unread notification count |
| rfpStore.ts | RFP-specific client state |
| pipelineStore.ts | Pipeline state |
| agentStore.ts | Agent state |

### 1.5 Custom Hooks

| Hook | Purpose |
|---|---|
| useApi.ts | 30+ React Query hooks for all APIs |
| useEventStream.ts | SSE with exponential backoff |
| useKeyboardShortcuts.ts | Global shortcut registration |

### 1.6 Type System

Comprehensive TypeScript types in src/types/models.ts (~511 lines):
- Union type enums: RFPStatus (9 states), BidStatus (7), PipelineStage (8), AgentType (4), VendorTier (5), ComplianceStatus (4), Priority (4)
- Full interfaces: RFP, Product, Vendor, Bid, PipelineRun, User, RFPRequirement, etc.
- Generic API wrappers: ApiResponse\<T\>, PaginatedResponse\<T\>

---

## 2. How It Was Built

### 2.1 Build Toolchain

| Tool | Role |
|---|---|
| Vite 7.x | Dev server, HMR, production bundling |
| TypeScript 5.9 | Static type checking |
| ESLint 9.x | Code linting with React hooks rules |
| Tailwind CSS 4.x | Utility-first styling via plugin |

**Vite configuration** (vite.config.ts):
- @ path alias pointing to ./src for clean imports
- Dev server on port 3000 with proxy /api → localhost:8000 (FastAPI backend)
- Plugins: @vitejs/plugin-react (SWC transform) + @tailwindcss/vite

### 2.2 Component Architecture Patterns

**Compound Components** — The Card component exports Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter as separately importable sub-components, allowing flexible composition:
```tsx
<Card variant="glass" glowColor="cyan">
  <CardHeader>
    <CardTitle>Title</CardTitle>
    <CardDescription>Subtitle</CardDescription>
  </CardHeader>
  <CardContent>...</CardContent>
</Card>
```

**forwardRef Pattern** — Button uses React.forwardRef for DOM ref forwarding, enabling integration with form libraries and animation wrappers.

**Functional Hooks** — All stateful logic is encapsulated in hooks (useApi, useEventStream, useKeyboardShortcuts), keeping components declarative.

**Lazy Loading** — Every page component is wrapped with lazy() + \<Suspense fallback=\{PageLoader\}\> in the router, code-splitting each route into its own chunk.

### 2.3 API Integration Architecture

```
Component → useApi hook → TanStack React Query → Service → Axios → Backend
                                                                ↕
                                        Interceptors (JWT inject, 401 refresh, 429 retry)
```

- **Axios instance** (src/services/api.ts) is the single HTTP client with:
  - Request interceptor: Injects Bearer token from localStorage
  - Response interceptor: On 401 → attempts silent token refresh via a separate refreshClient (no interceptors to avoid loops); queues concurrent requests during refresh
  - On 429: Respects Retry-After header
- **Service layer**: Thin typed wrappers (e.g., rfpService.getAll(params) calls api.get)
- **React Query hooks**: Compose services + cache policies:
  - STALE_TIME_SHORT / STALE_TIME_LONG control refetch behavior
  - Mutations call queryClient.invalidateQueries() on success for cache coherence
  - No retry on 401/403 (via retry callback in QueryClient defaults)
  - Global onError on mutations fires toast.error()

### 2.4 Routing Architecture

**React Router v7** with createBrowserRouter:
- Two layout shells: AppShell (admin) and UserAppShell (user portal)
- AuthGuard wrapper requires authentication; GuestGuard redirects authenticated users away from login/register
- Nested Outlet pattern for shared layout (sidebar + topbar)
- 80+ route definitions with lazy-loaded page components

### 2.5 State Management Architecture

**Zustand** (v5) with a minimalist pattern:
- Each domain gets its own store created via create\<State\>()
- Actions are co-located with state in the same store definition
- authStore uses zustand/persist middleware for session persistence across browser refreshes
- Stores are consumed via selector hooks: useAuthStore(s => s.user) for granular re-renders

### 2.6 Real-Time Data

**Server-Sent Events (SSE)** via custom useEventStream hook:
- Creates EventSource connection to backend endpoint
- Exponential backoff reconnection: retryBaseMs × 2^retryCount, capped at retryMaxMs
- Exposes { connected, retryCount } for UI status indicators (e.g., green pulse dot in TopBar)
- Used for live dashboard updates (agent activity, pipeline progress)

---

## 3. Why It Was Built This Way

### 3.1 React 19 + Vite

- **React 19**: Latest stable with concurrent features, improved Suspense, and the compiler for automatic memoization — future-proofing the codebase
- **Vite over CRA/Webpack**: Native ESM dev server provides sub-second HMR; Rollup-based production builds produce optimized chunks. Startup time on large codebases stays fast.

### 3.2 TypeScript Throughout

- **Type safety**: With 70+ pages and 10+ services, TypeScript prevents entire classes of runtime errors (wrong prop types, missing fields, incorrect API response shapes)
- **Developer experience**: IDE autocompletion, refactoring support, and self-documenting code via interfaces
- **Union type enums** (e.g., type RFPStatus = 'draft' | 'uploaded' | ...) are used instead of TypeScript enum for tree-shaking friendliness

### 3.3 Tailwind CSS 4

- **Utility-first**: Eliminates CSS naming conventions debate, reduces stylesheet bloat, and makes responsive design trivial
- **@theme directive**: First-class design tokens (colors, animations) that work as Tailwind classes — the design system is enforceable via Tailwind
- **cn() helper**: clsx + tailwind-merge ensures conflicting utilities are resolved correctly when composing conditional classes

### 3.4 Zustand over Redux

- **Minimal boilerplate**: No action types, reducers, or middleware configs — just a create() call
- **Bundle size**: Zustand is ~1KB vs Redux Toolkit's ~11KB
- **Sufficient for this app**: Most server state lives in React Query; Zustand handles only UI state and auth — no need for Redux's middleware ecosystem

### 3.5 TanStack React Query

- **Server state ≠ client state**: RFPs, bids, vendors are server-owned data. React Query manages caching, deduplication, background refetching, and optimistic updates — none of which Zustand naturally handles
- **Declarative data fetching**: Components declare what data they need; React Query handles when/how to fetch, retry, and invalidate
- **Query key factory**: Structured keys (keys.rfps(filters)) enable surgical cache invalidation after mutations

### 3.6 Axios over Fetch

- **Interceptors**: Critical for JWT injection and silent token refresh — native fetch requires manual wrapper functions
- **Request/response transformation**: Automatic JSON parsing, timeout support, upload progress tracking
- **Separate refresh client**: Prevents infinite loops when the refresh endpoint itself returns 401

### 3.7 Lazy Loading All Pages

- **Initial bundle size**: With 70+ pages, eager loading would produce a massive initial bundle. Lazy loading ensures users only download code for routes they visit.
- **Perceived performance**: PageLoader skeleton is shown during chunk loading, maintaining a responsive feel.

### 3.8 SSE over WebSockets

- **Simplicity**: SSE is unidirectional (server → client), matching our use case (live updates from backend). No socket lifecycle management.
- **HTTP/2 compatible**: Works through standard HTTP — no special proxy configuration
- **Auto-reconnect**: Built into the EventSource API (supplemented with custom exponential backoff)

---

## 4. Methods Used

### 4.1 Development Methodology

- **Component-Driven Development**: UI primitives → feature components → pages. Each layer only depends on layers below it.
- **Separation of Concerns**: Views (pages) → Hooks (data) → Services (API) → Types (contracts). No business logic in components.
- **Code Splitting**: One chunk per route via React.lazy(). Shared dependencies stay in the vendor chunk.
- **Mock Data Fallback**: Dashboard provides hardcoded mock data when backend is offline — graceful degradation during development.

### 4.2 Styling Methods

- **Utility-First CSS**: Tailwind classes directly in JSX — no separate .css or .module.css files per component
- **Design Tokens via @theme**: All colors, animations, and typography defined once in index.css, consumed as Tailwind utilities everywhere
- **Custom @utility Classes**: ~30 reusable utilities for glassmorphism, gradients, glows, focus rings, and typography scales
- **Conditional Class Composition**: cn() (clsx + tailwind-merge) used in every component for variant-based styling

### 4.3 State Management Methods

- **Co-located Actions**: Each Zustand store defines state + actions together — no separate action files
- **Selector-Based Consumption**: useAuthStore(s => s.user) prevents unnecessary re-renders
- **Persistence**: zustand/persist middleware for auth store — survives page refresh
- **Query Key Factory**: Centralized key definitions for React Query enable precise cache invalidation

### 4.4 Animation Methods

- **Framer Motion** for component-level animations:
  - initial / animate / exit for mount/unmount transitions
  - whileTap for micro-interactions (button press)
  - AnimatePresence for conditional rendering with exit animations
  - layoutId for shared layout animations (sidebar active indicator uses spring physics: stiffness 400, damping 30)
  - Stagger containers (staggerChildren: 0.06) for choreographed page loads
- **CSS Keyframes** for ambient effects: pulse-glow, shimmer, ripple, glow-border

### 4.5 Error Handling Methods

- **Global mutation error toasts**: QueryClient's onMutate default fires toast.error(message) on any failed mutation
- **Token refresh queue**: Concurrent 401 responses are queued; all re-sent after a single refresh succeeds
- **Graceful degradation**: Dashboard works with mock data when backend is unreachable
- **Empty states**: EmptyState component provides user-friendly messaging with action CTAs when data is absent

---

## 5. Protocols Used

### 5.1 Communication Protocols

| Protocol | Usage |
|---|---|
| HTTP/HTTPS | All API calls via Axios, proxied in dev |
| SSE | Real-time server-to-client streaming |
| OAuth 2.0 / JWT | Bearer token auth with refresh |

### 5.2 Authentication Protocol

1. **Login**: POST /api/v1/auth/login → receives access_token + refresh_token
2. **Token storage**: Both tokens stored in localStorage
3. **Request auth**: Axios interceptor injects Authorization: Bearer header on every request
4. **Silent refresh**: On 401 → POST /api/v1/auth/refresh → updates stored access token → retries original request
5. **Concurrent request queue**: While refreshing, all parallel 401 requests are queued and replayed after refresh completes
6. **Logout**: Clears both tokens from localStorage, calls backend logout endpoint

### 5.3 API Communication Protocol

- **RESTful API**: Standard CRUD operations via HTTP methods (GET, POST, PUT, PATCH, DELETE)
- **Content negotiation**: application/json for standard requests; multipart/form-data for file uploads (auto-detected by Axios)
- **Pagination**: PaginatedResponse\<T\> envelope with items, total, page, size
- **Error envelope**: ApiResponse\<T\> with status and optional error details
- **Rate limiting**: 429 responses trigger retry with Retry-After header respect
- **Request timeout**: 30s default, 120s for file uploads

### 5.4 Proxy Protocol (Development)

Vite dev server proxies /api requests to localhost:8000 with changeOrigin: true, eliminating CORS issues during local development.

---

## 6. Key Technical Decisions Summary

**React 19** — Latest stable, concurrent features, ecosystem maturity.

**Vite 7** — Fast HMR, native ESM, optimized production builds.

**TypeScript 5.9** — Type safety across 70+ pages, 10+ services.

**Tailwind CSS 4** — Utility-first, design token system via @theme.

**Zustand 5** — Lightweight client state, minimal boilerplate, ~1KB.

**TanStack React Query 5** — Caching, deduplication, background refetch, cache invalidation.

**Axios** — Interceptors for JWT, refresh queue, timeout/retry.

**React Router 7** — Nested layouts, lazy loading, auth guards.

**Framer Motion 12** — Layout animations, spring physics, AnimatePresence.

**Lucide React** — Tree-shakable, consistent 24px icon set.

**Recharts 3** — Declarative, composable chart components.

**React Hook Form + Zod** — Performant form state + schema validation.

**react-hot-toast** — Simple, customizable toast system.

**react-dropzone** — Drag-and-drop upload zones.

**SSE (EventSource)** — Simple server→client streaming with auto-reconnect.

---

## 7. File Structure Overview

```
haki-fmcg-frontend/
├── index.html                 # SPA entry point (Inter font, theme-color meta)
├── package.json               # Dependencies & scripts
├── vite.config.ts             # Vite + Tailwind + proxy configuration
├── tsconfig.json              # TypeScript config
├── public/                    # Static assets
└── src/
    ├── main.tsx               # React DOM root render
    ├── App.tsx                # QueryClientProvider + RouterProvider + Toaster
    ├── index.css              # Tailwind imports + @theme tokens + @utility classes
    ├── router.tsx             # 80+ route definitions with lazy loading
    ├── components/
    │   ├── ui/                # Card, Button, Modal, Loading, Badge, Input
    │   ├── layout/            # AppShell, Sidebar, TopBar, UserAppShell
    │   ├── charts/            # BarChart, DonutChart, TrendChart
    │   ├── common/            # CommandPalette, ShortcutOverlay
    │   ├── auth/              # AuthGuard, GuestGuard
    │   ├── rfp/               # RFPCard, RFPFiltersPanel, etc.
    │   ├── bids/              # BidAnalyticsWidget
    │   ├── agents/            # AgentPerformancePanel
    │   ├── analytics/         # KPICard
    │   └── pipeline/          # PipelineStatsPanel, PipelineErrorRecovery
    ├── pages/                 # 70+ lazy-loaded page components
    │   └── user/              # User portal pages
    ├── services/              # Typed API service modules (10 files)
    ├── stores/                # Zustand stores (6 stores)
    ├── hooks/                 # Custom hooks (useApi, useEventStream, useKeyboardShortcuts)
    ├── types/                 # TypeScript interfaces & union types
    ├── utils/                 # Formatters, constants
    ├── lib/                   # QueryClient config, cn() utility
    └── assets/                # Static images/icons
```
