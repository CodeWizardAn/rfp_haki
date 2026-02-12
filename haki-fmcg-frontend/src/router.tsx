import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppShell } from '@/components/layout';
import { UserAppShell } from '@/components/layout';
import { PageLoader } from '@/components/ui';
import { AuthGuard, GuestGuard } from '@/components/auth/AuthGuard';

// Lazy-loaded pages
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const RFPListPage = lazy(() => import('@/pages/RFPListPage'));
const RFPDetailPage = lazy(() => import('@/pages/RFPDetailPage'));
const RFPUploadPage = lazy(() => import('@/pages/RFPUploadPage'));
const PipelinePage = lazy(() => import('@/pages/PipelinePage'));
const AgentsPage = lazy(() => import('@/pages/AgentsPage'));
const ProductsPage = lazy(() => import('@/pages/ProductsPage'));
const BidsPage = lazy(() => import('@/pages/BidsPage'));
const VendorsPage = lazy(() => import('@/pages/VendorsPage'));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'));
const CompliancePage = lazy(() => import('@/pages/CompliancePage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage'));
const RFPComparePage = lazy(() => import('@/pages/RFPComparePage'));
const BidApprovalPage = lazy(() => import('@/pages/BidApprovalPage'));
const VendorProfilePage = lazy(() => import('@/pages/VendorProfilePage'));
const AuditTrailPage = lazy(() => import('@/pages/AuditTrailPage'));
const ProductDetailPage = lazy(() => import('@/pages/ProductDetailPage'));
const VendorRankingsPage = lazy(() => import('@/pages/VendorRankingsPage'));
const ProductComparisonPage = lazy(() => import('@/pages/ProductComparisonPage'));
const BidBuilderPage = lazy(() => import('@/pages/BidBuilderPage'));
const RFPAnalyticsPage = lazy(() => import('@/pages/RFPAnalyticsPage'));
const SystemPerformancePage = lazy(() => import('@/pages/SystemPerformancePage'));
const BidAnalyticsPage = lazy(() => import('@/pages/BidAnalyticsPage'));
const VendorAnalyticsPage = lazy(() => import('@/pages/VendorAnalyticsPage'));
const AgentAnalyticsPage = lazy(() => import('@/pages/AgentAnalyticsPage'));
const WebhookManagementPage = lazy(() => import('@/pages/WebhookManagementPage'));
const UserManagementPage = lazy(() => import('@/pages/UserManagementPage'));
const BidDocumentPreviewPage = lazy(() => import('@/pages/BidDocumentPreviewPage'));
const BidCalendarPage = lazy(() => import('@/pages/BidCalendarPage'));
const VendorCommunicationPage = lazy(() => import('@/pages/VendorCommunicationPage'));
const VendorComparisonPage = lazy(() => import('@/pages/VendorComparisonPage'));
const TrendAnalysisPage = lazy(() => import('@/pages/TrendAnalysisPage'));
const BidRevisionHistoryPage = lazy(() => import('@/pages/BidRevisionHistoryPage'));
const VendorRegistrationPage = lazy(() => import('@/pages/VendorRegistrationPage'));
const ComplianceReportPage = lazy(() => import('@/pages/ComplianceReportPage'));
const PerformanceTuningPage = lazy(() => import('@/pages/PerformanceTuningPage'));
const AgentConfigPage = lazy(() => import('@/pages/AgentConfigPage'));

// Pipeline sub-pages
const PipelineHistoryPage = lazy(() => import('@/pages/PipelineHistoryPage'));
const PipelineConfigPage = lazy(() => import('@/pages/PipelineConfigPage'));

// Agent sub-pages
const AgentDetailPage = lazy(() => import('@/pages/AgentDetailPage'));
const AgentIntercomPage = lazy(() => import('@/pages/AgentIntercomPage'));
const AgentWorkflowTemplatesPage = lazy(() => import('@/pages/AgentWorkflowTemplatesPage'));
const AgentErrorHandlingPage = lazy(() => import('@/pages/AgentErrorHandlingPage'));
const AgentChatPage = lazy(() => import('@/pages/AgentChatPage'));
const AgentHealthCheckPage = lazy(() => import('@/pages/AgentHealthCheckPage'));

// Product sub-pages
const ProductAdvancedSearchPage = lazy(() => import('@/pages/ProductAdvancedSearchPage'));
const EngineeringCalculatorPage = lazy(() => import('@/pages/EngineeringCalculatorPage'));
const CategoryNavigatorPage = lazy(() => import('@/pages/CategoryNavigatorPage'));
const PriceTrackerPage = lazy(() => import('@/pages/PriceTrackerPage'));
const ProductRecommendationPage = lazy(() => import('@/pages/ProductRecommendationPage'));

// Bid sub-pages
const BidPricingEditorPage = lazy(() => import('@/pages/BidPricingEditorPage'));
const BidTemplatesPage = lazy(() => import('@/pages/BidTemplatesPage'));
const BidFinancialSummaryPage = lazy(() => import('@/pages/BidFinancialSummaryPage'));
const BidNotificationsPage = lazy(() => import('@/pages/BidNotificationsPage'));

// Vendor sub-pages
const VendorActivityFeedPage = lazy(() => import('@/pages/VendorActivityFeedPage'));
const VendorComplianceStatusPage = lazy(() => import('@/pages/VendorComplianceStatusPage'));
const VendorBlacklistPage = lazy(() => import('@/pages/VendorBlacklistPage'));
const VendorAuditTrailPage = lazy(() => import('@/pages/VendorAuditTrailPage'));

// Analytics sub-pages
const PredictiveAnalyticsPage = lazy(() => import('@/pages/PredictiveAnalyticsPage'));
const CostAnalysisPage = lazy(() => import('@/pages/CostAnalysisPage'));
const AlertConfigurationPage = lazy(() => import('@/pages/AlertConfigurationPage'));
const ReportTemplateDesignerPage = lazy(() => import('@/pages/ReportTemplateDesignerPage'));
const ABTestingDashboardPage = lazy(() => import('@/pages/ABTestingDashboardPage'));
const TenderPricingIntelPage = lazy(() => import('@/pages/TenderPricingIntelPage'));

// RFP sub-pages
const RFPPDFPreviewPage = lazy(() => import('@/pages/RFPPDFPreviewPage'));
const RFPTermsDatabasePage = lazy(() => import('@/pages/RFPTermsDatabasePage'));

// Compliance sub-pages
const ComplianceRuleViewerPage = lazy(() => import('@/pages/ComplianceRuleViewerPage'));
const AuditTrailDetailPage = lazy(() => import('@/pages/AuditTrailDetailPage'));

// ── User Portal Pages (6 main pages) ──
const UserDashboardPage = lazy(() => import('@/pages/user/UserDashboardPage'));
const UserRFPProcessingPage = lazy(() => import('@/pages/user/UserRFPProcessingPage'));
const UserRFPAnalyzerPage = lazy(() => import('@/pages/user/UserRFPAnalyzerPage'));
const UserProductsPage = lazy(() => import('@/pages/user/UserProductsPage'));
const UserAnalyticsPage = lazy(() => import('@/pages/user/UserAnalyticsPage'));
const UserHistoryPage = lazy(() => import('@/pages/user/UserHistoryPage'));
const CompanyProfilesPage = lazy(() => import('@/pages/user/CompanyProfilesPage'));
const BidGeneratorPage = lazy(() => import('@/pages/user/BidGeneratorPage'));

function SuspenseWrap({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

export const router = createBrowserRouter([
  // Default route — redirect to login
  {
    path: '/login',
    element: (
      <GuestGuard>
        <SuspenseWrap>
          <LoginPage />
        </SuspenseWrap>
      </GuestGuard>
    ),
  },
  {
    path: '/register',
    element: (
      <GuestGuard>
        <SuspenseWrap>
          <RegisterPage />
        </SuspenseWrap>
      </GuestGuard>
    ),
  },
  {
    path: '/',
    element: (
      <AuthGuard>
        <AppShell />
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        element: (
          <SuspenseWrap>
            <DashboardPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'rfps',
        element: (
          <SuspenseWrap>
            <RFPListPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'rfps/:id',
        element: (
          <SuspenseWrap>
            <RFPDetailPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'rfps/upload',
        element: (
          <SuspenseWrap>
            <RFPUploadPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'rfps/compare',
        element: (
          <SuspenseWrap>
            <RFPComparePage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'pipeline',
        element: (
          <SuspenseWrap>
            <PipelinePage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'pipeline/:id',
        element: (
          <SuspenseWrap>
            <PipelinePage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'agents',
        element: (
          <SuspenseWrap>
            <AgentsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'agents/workflow/:id',
        element: (
          <SuspenseWrap>
            <AgentsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'products',
        element: (
          <SuspenseWrap>
            <ProductsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'products/:sku',
        element: (
          <SuspenseWrap>
            <ProductDetailPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'products/compare',
        element: (
          <SuspenseWrap>
            <ProductComparisonPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'bids',
        element: (
          <SuspenseWrap>
            <BidsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'bids/create',
        element: (
          <SuspenseWrap>
            <BidBuilderPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'bids/:id',
        element: (
          <SuspenseWrap>
            <BidsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'bids/:bidId/approval',
        element: (
          <SuspenseWrap>
            <BidApprovalPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'bids/:id/preview',
        element: (
          <SuspenseWrap>
            <BidDocumentPreviewPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'bids/calendar',
        element: (
          <SuspenseWrap>
            <BidCalendarPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'vendors',
        element: (
          <SuspenseWrap>
            <VendorsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'vendors/:vendorId',
        element: (
          <SuspenseWrap>
            <VendorProfilePage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'vendors/rankings',
        element: (
          <SuspenseWrap>
            <VendorRankingsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'vendors/compare',
        element: (
          <SuspenseWrap>
            <VendorComparisonPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'bids/:id/revisions',
        element: (
          <SuspenseWrap>
            <BidRevisionHistoryPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'vendors/communications',
        element: (
          <SuspenseWrap>
            <VendorCommunicationPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'vendors/communications/:vendorId',
        element: (
          <SuspenseWrap>
            <VendorCommunicationPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'vendors/register',
        element: (
          <SuspenseWrap>
            <VendorRegistrationPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'agents/config',
        element: (
          <SuspenseWrap>
            <AgentConfigPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'analytics',
        element: (
          <SuspenseWrap>
            <AnalyticsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'analytics/rfp',
        element: (
          <SuspenseWrap>
            <RFPAnalyticsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'analytics/system',
        element: (
          <SuspenseWrap>
            <SystemPerformancePage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'analytics/bids',
        element: (
          <SuspenseWrap>
            <BidAnalyticsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'analytics/vendors',
        element: (
          <SuspenseWrap>
            <VendorAnalyticsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'analytics/agents',
        element: (
          <SuspenseWrap>
            <AgentAnalyticsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'analytics/trends',
        element: (
          <SuspenseWrap>
            <TrendAnalysisPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'analytics/tender-pricing',
        element: (
          <SuspenseWrap>
            <TenderPricingIntelPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'analytics/:section',
        element: (
          <SuspenseWrap>
            <AnalyticsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'compliance',
        element: (
          <SuspenseWrap>
            <CompliancePage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'compliance/report',
        element: (
          <SuspenseWrap>
            <ComplianceReportPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'compliance/audit',
        element: (
          <SuspenseWrap>
            <CompliancePage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'audit',
        element: (
          <SuspenseWrap>
            <AuditTrailPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'settings',
        element: (
          <SuspenseWrap>
            <SettingsPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'settings/webhooks',
        element: (
          <SuspenseWrap>
            <WebhookManagementPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'settings/users',
        element: (
          <SuspenseWrap>
            <UserManagementPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'settings/performance',
        element: (
          <SuspenseWrap>
            <PerformanceTuningPage />
          </SuspenseWrap>
        ),
      },
      {
        path: 'settings/:section',
        element: (
          <SuspenseWrap>
            <SettingsPage />
          </SuspenseWrap>
        ),
      },
      // Pipeline sub-routes
      {
        path: 'pipeline/history',
        element: (<SuspenseWrap><PipelineHistoryPage /></SuspenseWrap>),
      },
      {
        path: 'pipeline/config',
        element: (<SuspenseWrap><PipelineConfigPage /></SuspenseWrap>),
      },
      // Agent sub-routes
      {
        path: 'agents/:agentId',
        element: (<SuspenseWrap><AgentDetailPage /></SuspenseWrap>),
      },
      {
        path: 'agents/intercom',
        element: (<SuspenseWrap><AgentIntercomPage /></SuspenseWrap>),
      },
      {
        path: 'agents/templates',
        element: (<SuspenseWrap><AgentWorkflowTemplatesPage /></SuspenseWrap>),
      },
      {
        path: 'agents/errors',
        element: (<SuspenseWrap><AgentErrorHandlingPage /></SuspenseWrap>),
      },
      {
        path: 'agents/chat',
        element: (<SuspenseWrap><AgentChatPage /></SuspenseWrap>),
      },
      {
        path: 'agents/health',
        element: (<SuspenseWrap><AgentHealthCheckPage /></SuspenseWrap>),
      },
      // Product sub-routes
      {
        path: 'products/search',
        element: (<SuspenseWrap><ProductAdvancedSearchPage /></SuspenseWrap>),
      },
      {
        path: 'products/calculator',
        element: (<SuspenseWrap><EngineeringCalculatorPage /></SuspenseWrap>),
      },
      {
        path: 'products/categories',
        element: (<SuspenseWrap><CategoryNavigatorPage /></SuspenseWrap>),
      },
      {
        path: 'products/prices',
        element: (<SuspenseWrap><PriceTrackerPage /></SuspenseWrap>),
      },
      {
        path: 'products/recommendations',
        element: (<SuspenseWrap><ProductRecommendationPage /></SuspenseWrap>),
      },
      // Bid sub-routes
      {
        path: 'bids/:id/pricing',
        element: (<SuspenseWrap><BidPricingEditorPage /></SuspenseWrap>),
      },
      {
        path: 'bids/templates',
        element: (<SuspenseWrap><BidTemplatesPage /></SuspenseWrap>),
      },
      {
        path: 'bids/:id/financial',
        element: (<SuspenseWrap><BidFinancialSummaryPage /></SuspenseWrap>),
      },
      {
        path: 'bids/notifications',
        element: (<SuspenseWrap><BidNotificationsPage /></SuspenseWrap>),
      },
      // Vendor sub-routes
      {
        path: 'vendors/activity',
        element: (<SuspenseWrap><VendorActivityFeedPage /></SuspenseWrap>),
      },
      {
        path: 'vendors/compliance',
        element: (<SuspenseWrap><VendorComplianceStatusPage /></SuspenseWrap>),
      },
      {
        path: 'vendors/blacklist',
        element: (<SuspenseWrap><VendorBlacklistPage /></SuspenseWrap>),
      },
      {
        path: 'vendors/audit',
        element: (<SuspenseWrap><VendorAuditTrailPage /></SuspenseWrap>),
      },
      // Analytics sub-routes
      {
        path: 'analytics/predictive',
        element: (<SuspenseWrap><PredictiveAnalyticsPage /></SuspenseWrap>),
      },
      {
        path: 'analytics/costs',
        element: (<SuspenseWrap><CostAnalysisPage /></SuspenseWrap>),
      },
      {
        path: 'analytics/alerts',
        element: (<SuspenseWrap><AlertConfigurationPage /></SuspenseWrap>),
      },
      {
        path: 'analytics/reports',
        element: (<SuspenseWrap><ReportTemplateDesignerPage /></SuspenseWrap>),
      },
      {
        path: 'analytics/ab-testing',
        element: (<SuspenseWrap><ABTestingDashboardPage /></SuspenseWrap>),
      },
      // RFP sub-routes
      {
        path: 'rfps/:id/preview',
        element: (<SuspenseWrap><RFPPDFPreviewPage /></SuspenseWrap>),
      },
      {
        path: 'rfps/terms',
        element: (<SuspenseWrap><RFPTermsDatabasePage /></SuspenseWrap>),
      },
      // Compliance sub-routes
      {
        path: 'compliance/rules',
        element: (<SuspenseWrap><ComplianceRuleViewerPage /></SuspenseWrap>),
      },
      {
        path: 'audit/:id',
        element: (<SuspenseWrap><AuditTrailDetailPage /></SuspenseWrap>),
      },
      {
        path: '*',
        element: <Navigate to="/" replace />,
      },
    ],
  },
  // ══════════════════════════════════════════
  //  USER PORTAL ROUTES
  // ══════════════════════════════════════════
  {
    path: '/user',
    element: (
      <AuthGuard>
        <UserAppShell />
      </AuthGuard>
    ),
    children: [
      {
        index: true,
        element: (<SuspenseWrap><UserDashboardPage /></SuspenseWrap>),
      },
      {
        path: 'rfps',
        element: (<SuspenseWrap><UserRFPProcessingPage /></SuspenseWrap>),
      },
      {
        path: 'rfp-analyzer',
        element: (<SuspenseWrap><UserRFPAnalyzerPage /></SuspenseWrap>),
      },
      {
        path: 'products',
        element: (<SuspenseWrap><UserProductsPage /></SuspenseWrap>),
      },
      {
        path: 'analytics',
        element: (<SuspenseWrap><UserAnalyticsPage /></SuspenseWrap>),
      },
      {
        path: 'history',
        element: (<SuspenseWrap><UserHistoryPage /></SuspenseWrap>),
      },
      {
        path: 'profiles',
        element: (<SuspenseWrap><CompanyProfilesPage /></SuspenseWrap>),
      },
      {
        path: 'bid-generator',
        element: (<SuspenseWrap><BidGeneratorPage /></SuspenseWrap>),
      },
      {
        path: '*',
        element: <Navigate to="/user" replace />,
      },
    ],
  },
  // Catch-all — send to login
  {
    path: '*',
    element: <Navigate to="/login" replace />,
  },
]);
