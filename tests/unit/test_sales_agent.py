"""
Unit Tests for Sales Agent
Comprehensive tests for all 30 features
"""

import pytest
import hashlib
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import json
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.sales_agent.sales_agent import (
    # Enums
    AgentState,
    RFPPriority,
    RFPSource,
    AlertLevel,
    
    # Data Classes
    URLMonitorConfig,
    ScrapedRFP,
    Alert,
    ScrapeResult,
    ScrapingStats,
    
    # Classes
    SalesAgentLogger,
    URLMonitorManager,
    RateLimiter,
    ProxyRotator,
    WebScraper,
    RFPDetector,
    KeywordFilter,
    PriorityScorer,
    AlertManager,
    RFPMetadataExtractor,
    DuplicateDetector,
    StatisticsTracker,
    RFPSummaryGenerator,
    RFPSelector,
    OrchestratorHandoff,
    Scheduler,
    AgentStateManager,
    HealthChecker,
    StatusReporter,
    ConfigManager,
    SalesAgent,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_rfp():
    """Sample scraped RFP"""
    return ScrapedRFP(
        id="RFP_TEST_001",
        title="Supply of PVC Insulated Copper Wires",
        description="RFP for supply of electrical wires and cables",
        source_url="https://example.com/rfp/001",
        source_type=RFPSource.WEB_SCRAPE,
        issuing_authority="State Electricity Board",
        published_date=datetime.now(),
        due_date=datetime.now() + timedelta(days=30),
        estimated_value=5000000.0,
        category="power_cables",
        keywords=["wire", "cable", "copper", "pvc"],
        raw_content="Full RFP content here...",
        metadata={"categories": ["power_cables"]},
        content_hash="abc123",
        scraped_at=datetime.now(),
        relevance_score=0.8,
        priority=RFPPriority.HIGH
    )


@pytest.fixture
def sample_rfp_low_priority():
    """Low priority RFP for testing"""
    return ScrapedRFP(
        id="RFP_TEST_002",
        title="Supply of Office Supplies",
        description="RFP for office supplies",
        source_url="https://example.com/rfp/002",
        source_type=RFPSource.WEB_SCRAPE,
        issuing_authority="Local Municipality",
        published_date=datetime.now(),
        due_date=datetime.now() + timedelta(days=90),
        estimated_value=50000.0,
        category="general",
        keywords=["office"],
        raw_content="Content...",
        metadata={},
        content_hash="def456",
        scraped_at=datetime.now(),
        relevance_score=0.3,
        priority=RFPPriority.LOW
    )


@pytest.fixture
def url_config():
    """Sample URL monitor config"""
    return URLMonitorConfig(
        url="https://eprocure.gov.in/tenders",
        name="Government Tenders",
        enabled=True,
        check_interval_hours=6.0,
        requires_javascript=False,
        keywords=["wire", "cable"],
        exclude_keywords=["optical"]
    )


@pytest.fixture
def temp_config_file(tmp_path):
    """Create temporary config file"""
    config = {
        "scan_interval_hours": 6.0,
        "rate_limit_per_minute": 10,
        "keywords": {
            "include": ["wire", "cable"],
            "exclude": ["optical"]
        }
    }
    config_path = tmp_path / "config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f)
    return str(config_path)


@pytest.fixture
def sales_agent(tmp_path):
    """Create Sales Agent for testing"""
    agent = SalesAgent(
        agent_id="TEST_AGENT",
        log_dir=str(tmp_path / "logs")
    )
    yield agent
    # Cleanup
    if agent.state_manager.get_state() not in [AgentState.STOPPED, AgentState.IDLE]:
        agent.stop()


# ============================================================================
# Test 1: SalesAgent Class Structure
# ============================================================================

class TestSalesAgentStructure:
    """Test Sales Agent class structure"""
    
    def test_agent_initialization(self, sales_agent):
        """Agent should initialize with all components"""
        assert sales_agent.agent_id == "TEST_AGENT"
        assert sales_agent.state_manager is not None
        assert sales_agent.url_manager is not None
        assert sales_agent.scraper is not None
        assert sales_agent.rfp_detector is not None
        assert sales_agent.keyword_filter is not None
        assert sales_agent.alert_manager is not None
        assert sales_agent.statistics is not None
        assert sales_agent.scheduler is not None
    
    def test_agent_has_required_methods(self, sales_agent):
        """Agent should have all required methods"""
        required_methods = [
            'start', 'stop', 'pause', 'resume',
            'add_url', 'remove_url', 'scan_url', 'scan_all_urls',
            'get_rfps', 'get_rfp_summary', 'select_rfp',
            'get_dashboard_data', 'get_status', 'health_check'
        ]
        for method in required_methods:
            assert hasattr(sales_agent, method), f"Missing method: {method}"
    
    def test_agent_initial_state(self, sales_agent):
        """Agent should start in IDLE state"""
        assert sales_agent.state_manager.get_state() == AgentState.IDLE


# ============================================================================
# Test 2: URL Monitoring Configuration
# ============================================================================

class TestURLMonitorManager:
    """Test URL monitoring configuration"""
    
    def test_add_url(self):
        """Should add URL to monitor"""
        manager = URLMonitorManager()
        config = URLMonitorConfig(
            url="https://example.com",
            name="Example Site"
        )
        result = manager.add_url(config)
        assert result is True
        assert len(manager.configs) == 1
    
    def test_remove_url(self):
        """Should remove URL from monitoring"""
        manager = URLMonitorManager()
        config = URLMonitorConfig(url="https://example.com", name="Example")
        manager.add_url(config)
        
        result = manager.remove_url("https://example.com")
        assert result is True
        assert len(manager.configs) == 0
    
    def test_get_due_urls(self):
        """Should return URLs due for checking"""
        manager = URLMonitorManager()
        config = URLMonitorConfig(
            url="https://example.com",
            name="Example",
            last_checked=None  # Never checked
        )
        manager.add_url(config)
        
        due = manager.get_due_urls()
        assert len(due) == 1
    
    def test_get_due_urls_filters_disabled(self):
        """Should not return disabled URLs"""
        manager = URLMonitorManager()
        config = URLMonitorConfig(
            url="https://example.com",
            name="Example",
            enabled=False
        )
        manager.add_url(config)
        
        due = manager.get_due_urls()
        assert len(due) == 0
    
    def test_update_checked(self):
        """Should update last checked time"""
        manager = URLMonitorManager()
        config = URLMonitorConfig(url="https://example.com", name="Example")
        manager.add_url(config)
        
        manager.update_checked("https://example.com", "hash123")
        
        updated = manager.get_config("https://example.com")
        assert updated.last_checked is not None
        assert updated.last_hash == "hash123"


# ============================================================================
# Test 3 & 4: Web Scraping (BeautifulSoup & Selenium)
# ============================================================================

class TestRateLimiter:
    """Test rate limiter"""
    
    def test_can_proceed_initially(self):
        """Should allow requests initially"""
        limiter = RateLimiter(requests_per_minute=10)
        assert limiter.can_proceed() is True
    
    def test_rate_limit_tracking(self):
        """Should track requests"""
        limiter = RateLimiter(requests_per_minute=3)
        
        for _ in range(3):
            limiter.wait()
        
        # After 3 requests, should be at limit
        assert len(limiter.request_times) == 3


class TestProxyRotator:
    """Test proxy rotation"""
    
    def test_add_proxy(self):
        """Should add proxy"""
        rotator = ProxyRotator()
        rotator.add_proxy("http://proxy1:8080")
        assert len(rotator.proxies) == 1
    
    def test_get_proxy_rotation(self):
        """Should rotate through proxies"""
        rotator = ProxyRotator(["http://proxy1:8080", "http://proxy2:8080"])
        
        p1 = rotator.get_proxy()
        p2 = rotator.get_proxy()
        
        assert p1 != p2 or len(rotator.proxies) == 1
    
    def test_proxy_failure_tracking(self):
        """Should track proxy failures"""
        rotator = ProxyRotator(["http://proxy1:8080"])
        
        rotator.report_failure("http://proxy1:8080")
        rotator.report_failure("http://proxy1:8080")
        rotator.report_failure("http://proxy1:8080")
        
        # Should be blocked after 3 failures
        assert rotator.proxy_stats["http://proxy1:8080"]["blocked"] is True


class TestWebScraper:
    """Test web scraper"""
    
    def test_scraper_initialization(self):
        """Scraper should initialize"""
        scraper = WebScraper()
        assert scraper.rate_limiter is not None
        assert scraper.timeout == 30
    
    def test_parse_html_extracts_text(self):
        """Should parse HTML and extract text"""
        scraper = WebScraper()
        
        # Only test if BeautifulSoup available
        try:
            from bs4 import BeautifulSoup
            html = "<html><body><h1>Test Title</h1><p>Content here</p></body></html>"
            result = scraper.parse_html(html)
            assert 'full_text' in result
            assert 'Test Title' in result['full_text']
        except ImportError:
            pytest.skip("BeautifulSoup not available")


# ============================================================================
# Test 5 & 6: RFP Detection & Relevance Filter
# ============================================================================

class TestRFPDetector:
    """Test RFP announcement detector"""
    
    def test_detect_rfp_indicators(self):
        """Should detect RFP indicators in content"""
        detector = RFPDetector()
        content = """
        Notice Inviting Tender (NIT)
        Request for Proposal for Supply of Electrical Cables
        Due Date: 15-03-2026
        Estimated Value: Rs. 50,00,000
        """
        
        detected = detector.detect_rfps(content)
        assert len(detected) >= 1
        assert detected[0]['confidence'] > 0
    
    def test_detect_no_rfp_in_generic_content(self):
        """Should not detect RFP in generic content"""
        detector = RFPDetector()
        content = "This is a generic webpage about cooking recipes."
        
        detected = detector.detect_rfps(content)
        assert len(detected) == 0
    
    def test_extract_due_date(self):
        """Should extract due date from content"""
        detector = RFPDetector()
        content = "Due Date: 15-03-2026"
        
        date = detector._extract_date(content)
        assert date is not None
        assert date.day == 15
        assert date.month == 3
    
    def test_extract_value(self):
        """Should extract estimated value"""
        detector = RFPDetector()
        content = "Estimated Value: Rs. 50,00,000"
        
        value = detector._extract_value(content)
        assert value == 5000000.0


# ============================================================================
# Test 7: Keyword-based Filtering
# ============================================================================

class TestKeywordFilter:
    """Test keyword filtering"""
    
    def test_filter_relevant_content(self):
        """Should identify relevant content"""
        filter = KeywordFilter(include_keywords=["wire", "cable", "copper"])
        
        is_relevant, score, matched = filter.filter(
            "Supply of copper wire and cable for power distribution"
        )
        
        assert is_relevant is True
        assert score > 0
        assert "wire" in matched
        assert "cable" in matched
    
    def test_filter_excludes_irrelevant(self):
        """Should exclude irrelevant content"""
        filter = KeywordFilter(
            include_keywords=["wire", "cable"],
            exclude_keywords=["optical", "fibre"]
        )
        
        is_relevant, score, matched = filter.filter(
            "Supply of fibre optic cables"
        )
        
        assert is_relevant is False
    
    def test_minimum_keyword_matches(self):
        """Should require minimum matches"""
        filter = KeywordFilter(
            include_keywords=["wire", "cable", "copper"],
            min_keyword_matches=2
        )
        
        # Only one match
        is_relevant, _, _ = filter.filter("Supply of wire")
        assert is_relevant is False
        
        # Two matches
        is_relevant, _, _ = filter.filter("Supply of wire and cable")
        assert is_relevant is True
    
    def test_add_keyword(self):
        """Should add keywords"""
        filter = KeywordFilter()
        filter.add_keyword("aluminium")
        assert "aluminium" in filter.include_keywords
    
    def test_add_exclude_keyword(self):
        """Should add exclude keywords"""
        filter = KeywordFilter()
        filter.add_keyword("telephone", exclude=True)
        assert "telephone" in filter.exclude_keywords


# ============================================================================
# Test 8 & 9: Deadline Extraction & Priority Scoring
# ============================================================================

class TestPriorityScorer:
    """Test priority scoring algorithm"""
    
    def test_critical_priority_for_urgent_rfp(self, sample_rfp):
        """Should assign CRITICAL priority for urgent high-value RFP"""
        scorer = PriorityScorer()
        
        # Modify to be very urgent
        sample_rfp.due_date = datetime.now() + timedelta(days=5)
        sample_rfp.estimated_value = 20000000  # 2 Crores
        sample_rfp.relevance_score = 0.9
        
        score, priority = scorer.calculate_priority(sample_rfp)
        
        assert score > 0.7
        assert priority in [RFPPriority.CRITICAL, RFPPriority.HIGH]
    
    def test_low_priority_for_distant_deadline(self, sample_rfp):
        """Should assign lower priority for distant deadlines"""
        scorer = PriorityScorer()
        
        sample_rfp.due_date = datetime.now() + timedelta(days=120)
        sample_rfp.estimated_value = 100000
        sample_rfp.relevance_score = 0.3
        
        score, priority = scorer.calculate_priority(sample_rfp)
        
        assert priority in [RFPPriority.LOW, RFPPriority.MEDIUM]
    
    def test_authority_bonus(self, sample_rfp):
        """Should apply authority bonus"""
        scorer = PriorityScorer()
        
        sample_rfp.issuing_authority = "Central Government Ministry"
        score1, _ = scorer.calculate_priority(sample_rfp)
        
        sample_rfp.issuing_authority = "Local Office"
        score2, _ = scorer.calculate_priority(sample_rfp)
        
        assert score1 > score2


# ============================================================================
# Test 10: Alert/Notification System
# ============================================================================

class TestAlertManager:
    """Test alert management"""
    
    def test_create_alert(self):
        """Should create alert"""
        manager = AlertManager()
        
        alert = manager.create_alert(
            AlertLevel.WARNING,
            "Test Alert",
            "This is a test alert message",
            "RFP_001"
        )
        
        assert alert is not None
        assert alert.level == AlertLevel.WARNING
        assert len(manager.alerts) == 1
    
    def test_acknowledge_alert(self):
        """Should acknowledge alert"""
        manager = AlertManager()
        alert = manager.create_alert(AlertLevel.INFO, "Test", "Message")
        
        result = manager.acknowledge(alert.id)
        
        assert result is True
        assert manager.alerts[alert.id].acknowledged is True
    
    def test_get_active_alerts(self):
        """Should return unacknowledged alerts"""
        manager = AlertManager()
        
        alert1 = manager.create_alert(AlertLevel.INFO, "Alert 1", "Message 1")
        alert2 = manager.create_alert(AlertLevel.WARNING, "Alert 2", "Message 2")
        manager.acknowledge(alert1.id)
        
        active = manager.get_active_alerts()
        
        assert len(active) == 1
        assert active[0].id == alert2.id
    
    def test_filter_alerts_by_level(self):
        """Should filter alerts by level"""
        manager = AlertManager()
        
        manager.create_alert(AlertLevel.INFO, "Info", "Message")
        manager.create_alert(AlertLevel.CRITICAL, "Critical", "Message")
        
        critical = manager.get_active_alerts(AlertLevel.CRITICAL)
        
        assert len(critical) == 1
        assert critical[0].level == AlertLevel.CRITICAL
    
    def test_subscriber_notification(self):
        """Should notify subscribers"""
        manager = AlertManager()
        received = []
        
        def callback(alert):
            received.append(alert)
        
        manager.subscribe(callback)
        manager.create_alert(AlertLevel.INFO, "Test", "Message")
        
        assert len(received) == 1


# ============================================================================
# Test 11 & 12: Metadata Extraction & Duplicate Detection
# ============================================================================

class TestRFPMetadataExtractor:
    """Test metadata extraction"""
    
    def test_detect_categories(self):
        """Should detect product categories"""
        extractor = RFPMetadataExtractor()
        
        categories = extractor._detect_categories(
            "supply of xlpe power cable and control cables"
        )
        
        assert "power_cables" in categories or "control_cables" in categories
    
    def test_extract_quantities(self):
        """Should extract quantities"""
        extractor = RFPMetadataExtractor()
        
        quantities = extractor._extract_quantities(
            "Supply of 5000 meters of cable and 100 coils"
        )
        
        assert len(quantities) >= 1
    
    def test_extract_certifications(self):
        """Should extract certification requirements"""
        extractor = RFPMetadataExtractor()
        
        certs = extractor._extract_certifications(
            "BIS certification mandatory. ISO 9001 required."
        )
        
        assert len(certs) >= 1


class TestDuplicateDetector:
    """Test duplicate detection"""
    
    def test_register_and_detect(self, sample_rfp):
        """Should detect duplicates"""
        detector = DuplicateDetector()
        
        # Register first RFP
        detector.register(sample_rfp)
        
        # Check same RFP again
        is_dup, existing_id = detector.is_duplicate(sample_rfp)
        
        assert is_dup is True
        assert existing_id == sample_rfp.id
    
    def test_no_false_positive(self, sample_rfp, sample_rfp_low_priority):
        """Should not mark different RFPs as duplicates"""
        detector = DuplicateDetector()
        
        detector.register(sample_rfp)
        
        is_dup, _ = detector.is_duplicate(sample_rfp_low_priority)
        
        assert is_dup is False
    
    def test_clear(self, sample_rfp):
        """Should clear detection history"""
        detector = DuplicateDetector()
        detector.register(sample_rfp)
        
        detector.clear()
        
        is_dup, _ = detector.is_duplicate(sample_rfp)
        assert is_dup is False


# ============================================================================
# Test 13: Scheduling Mechanism
# ============================================================================

class TestScheduler:
    """Test scheduling mechanism"""
    
    def test_add_task(self):
        """Should add scheduled task"""
        scheduler = Scheduler()
        
        scheduler.add_task("test_task", lambda: None, interval_hours=1.0)
        
        assert "test_task" in scheduler.tasks
    
    def test_remove_task(self):
        """Should remove task"""
        scheduler = Scheduler()
        scheduler.add_task("test_task", lambda: None)
        
        scheduler.remove_task("test_task")
        
        assert "test_task" not in scheduler.tasks
    
    def test_get_status(self):
        """Should return scheduler status"""
        scheduler = Scheduler()
        scheduler.add_task("task1", lambda: None)
        
        status = scheduler.get_status()
        
        assert 'running' in status
        assert 'tasks' in status
        assert 'task1' in status['tasks']


# ============================================================================
# Test 14 & 15: Rate Limiter & Error Recovery
# ============================================================================

class TestScrapingErrorRecovery:
    """Test error recovery for failed scrapes"""
    
    def test_error_count_tracking(self):
        """Should track error counts"""
        manager = URLMonitorManager()
        config = URLMonitorConfig(url="https://example.com", name="Example")
        manager.add_url(config)
        
        # Simulate errors
        manager.update_checked("https://example.com", error=True)
        manager.update_checked("https://example.com", error=True)
        
        updated = manager.get_config("https://example.com")
        assert updated.error_count == 2
    
    def test_skip_urls_with_max_errors(self):
        """Should skip URLs with max errors"""
        manager = URLMonitorManager()
        config = URLMonitorConfig(
            url="https://example.com",
            name="Example",
            error_count=5,
            max_errors=5
        )
        manager.add_url(config)
        
        due = manager.get_due_urls()
        assert len(due) == 0


# ============================================================================
# Test 17-23: Statistics & Performance Tracking
# ============================================================================

class TestStatisticsTracker:
    """Test statistics tracking"""
    
    def test_record_scrape(self):
        """Should record scrape results"""
        tracker = StatisticsTracker()
        
        result = ScrapeResult(
            url="https://example.com",
            success=True,
            rfps_found=3,
            error_message="",
            duration_ms=500,
            timestamp=datetime.now()
        )
        
        tracker.record_scrape(result)
        
        stats = tracker.get_stats()
        assert stats['total_scrapes'] == 1
        assert stats['successful_scrapes'] == 1
        assert stats['total_rfps_found'] == 3
    
    def test_record_failed_scrape(self):
        """Should track failed scrapes"""
        tracker = StatisticsTracker()
        
        result = ScrapeResult(
            url="https://example.com",
            success=False,
            rfps_found=0,
            error_message="Connection error",
            duration_ms=100,
            timestamp=datetime.now()
        )
        
        tracker.record_scrape(result)
        
        stats = tracker.get_stats()
        assert stats['failed_scrapes'] == 1
    
    def test_get_dashboard_data(self):
        """Should return dashboard data"""
        tracker = StatisticsTracker()
        
        data = tracker.get_dashboard_data()
        
        assert 'summary' in data
        assert 'recent_scrapes' in data
        assert 'recent_rfps' in data
    
    def test_reset(self):
        """Should reset statistics"""
        tracker = StatisticsTracker()
        tracker.record_scrape(ScrapeResult(
            url="test", success=True, rfps_found=1,
            error_message="", duration_ms=100, timestamp=datetime.now()
        ))
        
        tracker.reset()
        
        stats = tracker.get_stats()
        assert stats['total_scrapes'] == 0


# ============================================================================
# Test 18 & 19: RFP Summary & Selection
# ============================================================================

class TestRFPSummaryGenerator:
    """Test RFP summary generation"""
    
    def test_generate_summary(self, sample_rfp):
        """Should generate comprehensive summary"""
        generator = RFPSummaryGenerator()
        
        summary = generator.generate_summary(sample_rfp)
        
        assert summary['id'] == sample_rfp.id
        assert summary['title'] == sample_rfp.title
        assert 'estimated_value_formatted' in summary
        assert 'urgency' in summary
    
    def test_generate_brief(self, sample_rfp):
        """Should generate brief summary"""
        generator = RFPSummaryGenerator()
        
        brief = generator.generate_brief(sample_rfp)
        
        assert sample_rfp.title in brief
        assert sample_rfp.issuing_authority in brief
    
    def test_format_currency(self):
        """Should format currency values"""
        generator = RFPSummaryGenerator()
        
        assert "Cr" in generator._format_currency(20000000)
        assert "L" in generator._format_currency(500000)


class TestRFPSelector:
    """Test RFP selection logic"""
    
    def test_select_top_rfps(self, sample_rfp, sample_rfp_low_priority):
        """Should select top priority RFPs"""
        selector = RFPSelector()
        
        rfps = [sample_rfp_low_priority, sample_rfp]
        top = selector.select_top_rfps(rfps, count=1)
        
        assert len(top) == 1
        assert top[0].id == sample_rfp.id  # Higher priority
    
    def test_select_best_rfp(self, sample_rfp, sample_rfp_low_priority):
        """Should select single best RFP"""
        selector = RFPSelector()
        
        rfps = [sample_rfp_low_priority, sample_rfp]
        best = selector.select_best_rfp(rfps)
        
        assert best is not None
        assert best.id == sample_rfp.id


# ============================================================================
# Test 20: Handoff to Orchestrator
# ============================================================================

class TestOrchestratorHandoff:
    """Test orchestrator handoff"""
    
    def test_prepare_handoff(self, sample_rfp):
        """Should prepare handoff data"""
        handoff = OrchestratorHandoff()
        
        data = handoff.prepare_handoff(sample_rfp)
        
        assert data['rfp_id'] == sample_rfp.id
        assert data['title'] == sample_rfp.title
        assert 'handoff_time' in data
    
    def test_queue_handoff(self, sample_rfp):
        """Should queue RFP for handoff"""
        handoff = OrchestratorHandoff()
        
        handoff.queue_handoff(sample_rfp)
        
        assert handoff.get_pending_count() == 1
    
    def test_process_handoffs_with_callback(self, sample_rfp):
        """Should process handoffs with callback"""
        received = []
        
        def callback(data):
            received.append(data)
        
        handoff = OrchestratorHandoff(orchestrator_callback=callback)
        handoff.queue_handoff(sample_rfp)
        
        processed = handoff.process_handoffs()
        
        assert processed == 1
        assert len(received) == 1
        assert received[0]['rfp_id'] == sample_rfp.id


# ============================================================================
# Test 24-29: Agent State Management & Health
# ============================================================================

class TestAgentStateManager:
    """Test agent state management"""
    
    def test_initial_state(self):
        """Should start in IDLE state"""
        manager = AgentStateManager()
        assert manager.get_state() == AgentState.IDLE
    
    def test_valid_transition(self):
        """Should allow valid state transitions"""
        manager = AgentStateManager()
        
        result = manager.transition(AgentState.STARTING)
        
        assert result is True
        assert manager.get_state() == AgentState.STARTING
    
    def test_invalid_transition(self):
        """Should reject invalid state transitions"""
        manager = AgentStateManager()
        
        # Can't go from IDLE to RUNNING directly
        result = manager.transition(AgentState.RUNNING)
        
        assert result is False
        assert manager.get_state() == AgentState.IDLE
    
    def test_state_history(self):
        """Should track state history"""
        manager = AgentStateManager()
        
        manager.transition(AgentState.STARTING)
        manager.transition(AgentState.RUNNING)
        
        assert len(manager.state_history) == 2


class TestHealthChecker:
    """Test health check functionality"""
    
    def test_run_checks(self, sales_agent):
        """Should run health checks"""
        result = sales_agent.health_checker.run_checks()
        
        assert 'healthy' in result
        assert 'checks' in result
        assert 'state' in result['checks']
    
    def test_register_custom_check(self, sales_agent):
        """Should allow custom health checks"""
        sales_agent.health_checker.register_check(
            'custom',
            lambda: True
        )
        
        result = sales_agent.health_checker.run_checks()
        
        assert 'custom' in result['checks']


class TestStatusReporter:
    """Test status reporter"""
    
    def test_get_full_report(self, sales_agent):
        """Should generate full status report"""
        report = sales_agent.status_reporter.get_full_report()
        
        assert 'agent_id' in report
        assert 'state' in report
        assert 'health' in report
        assert 'statistics' in report
    
    def test_get_brief_status(self, sales_agent):
        """Should generate brief status"""
        status = sales_agent.status_reporter.get_brief_status()
        
        assert "SalesAgent" in status
        assert "idle" in status or "running" in status


# ============================================================================
# Test 27: Configuration Hot Reload
# ============================================================================

class TestConfigManager:
    """Test configuration management"""
    
    def test_default_config(self):
        """Should have default configuration"""
        config = ConfigManager()
        
        assert config.get('scan_interval_hours') == 6.0
        assert config.get('rate_limit_per_minute') == 10
    
    def test_load_config(self, temp_config_file):
        """Should load config from file"""
        config = ConfigManager(temp_config_file)
        
        assert config.get('scan_interval_hours') == 6.0
        assert 'wire' in config.get('keywords', {}).get('include', [])
    
    def test_set_and_get(self):
        """Should set and get values"""
        config = ConfigManager()
        
        config.set('custom_key', 'custom_value')
        
        assert config.get('custom_key') == 'custom_value'


# ============================================================================
# Test 30: Integration Tests
# ============================================================================

class TestSalesAgentIntegration:
    """Integration tests for Sales Agent"""
    
    def test_add_and_list_urls(self, sales_agent):
        """Should add and list URLs"""
        sales_agent.add_url(
            "https://example.com/tenders",
            name="Example Tenders",
            keywords=["wire", "cable"]
        )
        
        urls = sales_agent.get_monitored_urls()
        
        assert len(urls) == 1
        assert urls[0]['name'] == "Example Tenders"
    
    def test_get_dashboard_data(self, sales_agent):
        """Should return dashboard data"""
        dashboard = sales_agent.get_dashboard_data()
        
        assert 'agent' in dashboard
        assert 'statistics' in dashboard
        assert 'urls' in dashboard
        assert 'rfps' in dashboard
        assert 'alerts' in dashboard
        assert 'health' in dashboard
    
    def test_lifecycle_start_stop(self, sales_agent):
        """Should handle start/stop lifecycle"""
        # Start
        result = sales_agent.start()
        assert result is True
        assert sales_agent.state_manager.get_state() == AgentState.RUNNING
        
        # Stop
        result = sales_agent.stop()
        assert result is True
        assert sales_agent.state_manager.get_state() == AgentState.STOPPED
    
    def test_pause_resume(self, sales_agent):
        """Should handle pause/resume"""
        sales_agent.start()
        
        # Pause
        result = sales_agent.pause()
        assert result is True
        assert sales_agent.state_manager.get_state() == AgentState.PAUSED
        
        # Resume
        result = sales_agent.resume()
        assert result is True
        assert sales_agent.state_manager.get_state() == AgentState.RUNNING
        
        sales_agent.stop()


# ============================================================================
# Test Data Classes
# ============================================================================

class TestDataClasses:
    """Test data class creation"""
    
    def test_url_monitor_config(self):
        """Should create URLMonitorConfig"""
        config = URLMonitorConfig(
            url="https://example.com",
            name="Example"
        )
        assert config.enabled is True
        assert config.check_interval_hours == 6.0
    
    def test_scraped_rfp(self, sample_rfp):
        """Should create ScrapedRFP"""
        assert sample_rfp.id == "RFP_TEST_001"
        assert sample_rfp.priority == RFPPriority.HIGH
    
    def test_alert(self):
        """Should create Alert"""
        alert = Alert(
            id="alert_001",
            level=AlertLevel.WARNING,
            title="Test",
            message="Test message",
            rfp_id=None,
            created_at=datetime.now()
        )
        assert alert.acknowledged is False
    
    def test_scrape_result(self):
        """Should create ScrapeResult"""
        result = ScrapeResult(
            url="https://example.com",
            success=True,
            rfps_found=5,
            error_message="",
            duration_ms=250.5,
            timestamp=datetime.now()
        )
        assert result.success is True
        assert result.rfps_found == 5


class TestEnums:
    """Test enum values"""
    
    def test_agent_states(self):
        """Should have all agent states"""
        states = [s.value for s in AgentState]
        assert "idle" in states
        assert "running" in states
        assert "stopped" in states
    
    def test_rfp_priorities(self):
        """Should have all priorities"""
        priorities = [p.value for p in RFPPriority]
        assert "critical" in priorities
        assert "high" in priorities
        assert "medium" in priorities
        assert "low" in priorities
    
    def test_alert_levels(self):
        """Should have all alert levels"""
        levels = [l.value for l in AlertLevel]
        assert "info" in levels
        assert "warning" in levels
        assert "critical" in levels


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
