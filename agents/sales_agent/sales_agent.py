"""
Sales Agent - Comprehensive RFP Monitoring and Scraping System

Features:
1. SalesAgent class structure
2. URL monitoring configuration
3. Web scraping logic (BeautifulSoup)
4. Dynamic page scraping (Selenium)
5. RFP announcement detector
6. Relevance filter
7. Keyword-based filtering
8. Deadline extraction
9. Priority scoring algorithm
10. Alert/notification system
11. RFP metadata extractor
12. Duplicate detection
13. Scheduling mechanism (every 6 hours)
14. Scraping rate limiter
15. Error recovery for failed scrapes
16. Proxy rotation support
17. Scraping statistics tracker
18. RFP summary generator
19. RFP selection logic
20. Handoff to orchestrator
21. Sales agent dashboard data
22. Historical tracking
23. Performance metrics
24. Agent state management
25. Graceful shutdown
26. Sales agent logging
27. Configuration hot reload
28. Health check endpoint
29. Agent status reporter
30. Unit tests support
"""

import os
import sys
import json
import re
import time
import hashlib
import threading
import signal
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from enum import Enum
from collections import deque
from urllib.parse import urlparse, urljoin
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# Add parent paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Optional imports with fallbacks
BEAUTIFULSOUP_AVAILABLE = False
SELENIUM_AVAILABLE = False
REQUESTS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    pass

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    pass

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    pass


# ============================================================================
# Logging Configuration
# ============================================================================

class SalesAgentLogger:
    """Custom logger for Sales Agent with structured logging"""
    
    def __init__(self, name: str = "SalesAgent", log_dir: str = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_dir:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                log_path / f"sales_agent_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s | %(levelname)8s | %(funcName)20s | %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def info(self, msg: str): self.logger.info(msg)
    def debug(self, msg: str): self.logger.debug(msg)
    def warning(self, msg: str): self.logger.warning(msg)
    def error(self, msg: str): self.logger.error(msg)
    def critical(self, msg: str): self.logger.critical(msg)


logger = SalesAgentLogger("SalesAgent")


# ============================================================================
# Enums and Data Classes
# ============================================================================

class AgentState(Enum):
    """Sales Agent states"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    SCANNING = "scanning"
    PROCESSING = "processing"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class RFPPriority(Enum):
    """Priority levels for RFPs"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RFPSource(Enum):
    """Source types for RFPs"""
    WEB_SCRAPE = "web_scrape"
    DYNAMIC_PAGE = "dynamic_page"
    RSS_FEED = "rss_feed"
    EMAIL = "email"
    MANUAL = "manual"
    API = "api"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    CRITICAL = "critical"


@dataclass
class URLMonitorConfig:
    """Configuration for monitoring a URL"""
    url: str
    name: str
    enabled: bool = True
    check_interval_hours: float = 6.0
    requires_javascript: bool = False
    selectors: Dict[str, str] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    last_checked: Optional[datetime] = None
    last_hash: str = ""
    error_count: int = 0
    max_errors: int = 5


@dataclass
class ScrapedRFP:
    """RFP data scraped from web"""
    id: str
    title: str
    description: str
    source_url: str
    source_type: RFPSource
    issuing_authority: str
    published_date: Optional[datetime]
    due_date: Optional[datetime]
    estimated_value: float
    category: str
    keywords: List[str]
    raw_content: str
    metadata: Dict[str, Any]
    content_hash: str
    scraped_at: datetime
    relevance_score: float = 0.0
    priority: RFPPriority = RFPPriority.MEDIUM


@dataclass
class Alert:
    """Alert notification"""
    id: str
    level: AlertLevel
    title: str
    message: str
    rfp_id: Optional[str]
    created_at: datetime
    acknowledged: bool = False
    sent: bool = False


@dataclass
class ScrapeResult:
    """Result of a scraping operation"""
    url: str
    success: bool
    rfps_found: int
    error_message: str
    duration_ms: float
    timestamp: datetime


@dataclass 
class ScrapingStats:
    """Statistics for scraping operations"""
    total_scrapes: int = 0
    successful_scrapes: int = 0
    failed_scrapes: int = 0
    total_rfps_found: int = 0
    total_relevant_rfps: int = 0
    total_duplicates_filtered: int = 0
    average_scrape_time_ms: float = 0.0
    last_scrape_time: Optional[datetime] = None
    urls_monitored: int = 0
    active_alerts: int = 0


# ============================================================================
# 2. URL Monitoring Configuration
# ============================================================================

class URLMonitorManager:
    """Manages URL monitoring configurations"""
    
    DEFAULT_SELECTORS = {
        'title': ['h1', 'h2', '.title', '.rfp-title', '[class*="title"]'],
        'description': ['.description', '.content', '.rfp-content', 'article', '.body'],
        'date': ['.date', '.due-date', '.deadline', '[class*="date"]'],
        'value': ['.value', '.amount', '.budget', '[class*="value"]'],
        'authority': ['.issuer', '.organization', '.authority', '[class*="org"]']
    }
    
    def __init__(self, config_path: str = None):
        self.configs: Dict[str, URLMonitorConfig] = {}
        self.config_path = config_path
        self._lock = threading.Lock()
        
        if config_path and Path(config_path).exists():
            self.load_config(config_path)
    
    def add_url(self, config: URLMonitorConfig) -> bool:
        """Add URL to monitor"""
        with self._lock:
            url_id = self._url_to_id(config.url)
            self.configs[url_id] = config
            logger.info(f"Added URL monitor: {config.name} ({config.url})")
            return True
    
    def remove_url(self, url: str) -> bool:
        """Remove URL from monitoring"""
        with self._lock:
            url_id = self._url_to_id(url)
            if url_id in self.configs:
                del self.configs[url_id]
                logger.info(f"Removed URL monitor: {url}")
                return True
            return False
    
    def get_config(self, url: str) -> Optional[URLMonitorConfig]:
        """Get config for URL"""
        url_id = self._url_to_id(url)
        return self.configs.get(url_id)
    
    def get_due_urls(self) -> List[URLMonitorConfig]:
        """Get URLs that need to be checked"""
        now = datetime.now()
        due = []
        for config in self.configs.values():
            if not config.enabled:
                continue
            if config.error_count >= config.max_errors:
                continue
            if config.last_checked is None:
                due.append(config)
            else:
                hours_since = (now - config.last_checked).total_seconds() / 3600
                if hours_since >= config.check_interval_hours:
                    due.append(config)
        return due
    
    def update_checked(self, url: str, content_hash: str = "", error: bool = False):
        """Update last checked time for URL"""
        with self._lock:
            url_id = self._url_to_id(url)
            if url_id in self.configs:
                config = self.configs[url_id]
                config.last_checked = datetime.now()
                if error:
                    config.error_count += 1
                else:
                    config.error_count = 0
                    config.last_hash = content_hash
    
    def load_config(self, path: str):
        """Load configuration from JSON file"""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            for item in data.get('urls', []):
                config = URLMonitorConfig(
                    url=item['url'],
                    name=item.get('name', item['url']),
                    enabled=item.get('enabled', True),
                    check_interval_hours=item.get('check_interval_hours', 6.0),
                    requires_javascript=item.get('requires_javascript', False),
                    selectors=item.get('selectors', {}),
                    keywords=item.get('keywords', []),
                    exclude_keywords=item.get('exclude_keywords', [])
                )
                self.add_url(config)
            logger.info(f"Loaded {len(self.configs)} URL configs from {path}")
        except Exception as e:
            logger.error(f"Failed to load URL config: {e}")
    
    def save_config(self, path: str = None):
        """Save configuration to JSON file"""
        path = path or self.config_path
        if not path:
            return
        try:
            data = {'urls': []}
            for config in self.configs.values():
                data['urls'].append({
                    'url': config.url,
                    'name': config.name,
                    'enabled': config.enabled,
                    'check_interval_hours': config.check_interval_hours,
                    'requires_javascript': config.requires_javascript,
                    'selectors': config.selectors,
                    'keywords': config.keywords,
                    'exclude_keywords': config.exclude_keywords
                })
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save URL config: {e}")
    
    def _url_to_id(self, url: str) -> str:
        """Convert URL to unique ID"""
        return hashlib.md5(url.encode()).hexdigest()[:16]


# ============================================================================
# 3 & 4. Web Scraping (BeautifulSoup & Selenium)
# ============================================================================

class RateLimiter:
    """Rate limiter for scraping requests"""
    
    def __init__(self, requests_per_minute: int = 10, burst_limit: int = 3):
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.request_times: deque = deque(maxlen=requests_per_minute)
        self._lock = threading.Lock()
    
    def wait(self):
        """Wait if rate limit exceeded"""
        with self._lock:
            now = time.time()
            
            # Remove old requests
            while self.request_times and now - self.request_times[0] > 60:
                self.request_times.popleft()
            
            # Check rate limit
            if len(self.request_times) >= self.requests_per_minute:
                sleep_time = 60 - (now - self.request_times[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                    time.sleep(sleep_time)
            
            self.request_times.append(time.time())
    
    def can_proceed(self) -> bool:
        """Check if we can proceed without waiting"""
        with self._lock:
            now = time.time()
            while self.request_times and now - self.request_times[0] > 60:
                self.request_times.popleft()
            return len(self.request_times) < self.requests_per_minute


class ProxyRotator:
    """Manages proxy rotation for scraping"""
    
    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []
        self.proxy_stats: Dict[str, Dict] = {}
        self.current_index = 0
        self._lock = threading.Lock()
        
        for proxy in self.proxies:
            self.proxy_stats[proxy] = {
                'success': 0, 'failure': 0, 'last_used': None, 'blocked': False
            }
    
    def add_proxy(self, proxy: str):
        """Add proxy to rotation"""
        with self._lock:
            if proxy not in self.proxies:
                self.proxies.append(proxy)
                self.proxy_stats[proxy] = {
                    'success': 0, 'failure': 0, 'last_used': None, 'blocked': False
                }
    
    def get_proxy(self) -> Optional[str]:
        """Get next available proxy"""
        if not self.proxies:
            return None
        
        with self._lock:
            available = [p for p in self.proxies if not self.proxy_stats[p]['blocked']]
            if not available:
                # Reset blocked proxies
                for proxy in self.proxies:
                    self.proxy_stats[proxy]['blocked'] = False
                available = self.proxies
            
            # Round robin
            proxy = available[self.current_index % len(available)]
            self.current_index += 1
            self.proxy_stats[proxy]['last_used'] = datetime.now()
            return proxy
    
    def report_success(self, proxy: str):
        """Report successful use of proxy"""
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['success'] += 1
    
    def report_failure(self, proxy: str):
        """Report failed use of proxy"""
        if proxy in self.proxy_stats:
            stats = self.proxy_stats[proxy]
            stats['failure'] += 1
            # Block proxy after 3 consecutive failures
            if stats['failure'] >= 3 and stats['failure'] > stats['success']:
                stats['blocked'] = True
                logger.warning(f"Proxy blocked: {proxy}")


class WebScraper:
    """
    Web scraper using BeautifulSoup for static pages
    and Selenium for dynamic JavaScript-rendered pages
    """
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
    ]
    
    def __init__(
        self,
        rate_limiter: RateLimiter = None,
        proxy_rotator: ProxyRotator = None,
        timeout: int = 30
    ):
        self.rate_limiter = rate_limiter or RateLimiter()
        self.proxy_rotator = proxy_rotator
        self.timeout = timeout
        self._selenium_driver = None
    
    def scrape_static(self, url: str, config: URLMonitorConfig = None) -> Tuple[str, str]:
        """
        Scrape static webpage using requests + BeautifulSoup
        
        Returns:
            Tuple of (content, content_hash)
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library not available")
        
        self.rate_limiter.wait()
        
        headers = {'User-Agent': random.choice(self.USER_AGENTS)}
        proxies = None
        proxy = None
        
        if self.proxy_rotator:
            proxy = self.proxy_rotator.get_proxy()
            if proxy:
                proxies = {'http': proxy, 'https': proxy}
        
        try:
            response = requests.get(
                url, 
                headers=headers, 
                proxies=proxies, 
                timeout=self.timeout,
                verify=True
            )
            response.raise_for_status()
            
            if self.proxy_rotator and proxy:
                self.proxy_rotator.report_success(proxy)
            
            content = response.text
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            return content, content_hash
            
        except Exception as e:
            if self.proxy_rotator and proxy:
                self.proxy_rotator.report_failure(proxy)
            raise
    
    def scrape_dynamic(self, url: str, config: URLMonitorConfig = None, wait_selector: str = None) -> Tuple[str, str]:
        """
        Scrape dynamic webpage using Selenium
        
        Returns:
            Tuple of (content, content_hash)
        """
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not available")
        
        self.rate_limiter.wait()
        
        driver = self._get_selenium_driver()
        
        try:
            driver.get(url)
            
            # Wait for content to load
            if wait_selector:
                try:
                    WebDriverWait(driver, self.timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                    )
                except TimeoutException:
                    logger.warning(f"Timeout waiting for selector: {wait_selector}")
            else:
                time.sleep(3)  # Default wait
            
            content = driver.page_source
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            return content, content_hash
            
        except Exception as e:
            logger.error(f"Selenium scrape error for {url}: {e}")
            raise
    
    def _get_selenium_driver(self):
        """Get or create Selenium driver"""
        if self._selenium_driver is None:
            options = ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'--user-agent={random.choice(self.USER_AGENTS)}')
            
            if self.proxy_rotator:
                proxy = self.proxy_rotator.get_proxy()
                if proxy:
                    options.add_argument(f'--proxy-server={proxy}')
            
            self._selenium_driver = webdriver.Chrome(options=options)
        
        return self._selenium_driver
    
    def close(self):
        """Close Selenium driver"""
        if self._selenium_driver:
            self._selenium_driver.quit()
            self._selenium_driver = None
    
    def parse_html(self, html: str, selectors: Dict[str, List[str]] = None) -> Dict[str, Any]:
        """Parse HTML content using BeautifulSoup"""
        if not BEAUTIFULSOUP_AVAILABLE:
            return {'raw': html}
        
        soup = BeautifulSoup(html, 'html.parser')
        selectors = selectors or URLMonitorManager.DEFAULT_SELECTORS
        
        result = {}
        for field, selector_list in selectors.items():
            for selector in selector_list:
                try:
                    element = soup.select_one(selector)
                    if element:
                        result[field] = element.get_text(strip=True)
                        break
                except:
                    continue
        
        # Get all text for keyword matching
        result['full_text'] = soup.get_text(separator=' ', strip=True)
        
        # Find all links
        result['links'] = [
            {'text': a.get_text(strip=True), 'href': a.get('href', '')}
            for a in soup.find_all('a', href=True)
        ]
        
        return result


# ============================================================================
# 5 & 6. RFP Announcement Detector & Relevance Filter
# ============================================================================

class RFPDetector:
    """Detects RFP announcements in scraped content"""
    
    RFP_INDICATORS = [
        r'request\s+for\s+proposal',
        r'request\s+for\s+quotation',
        r'request\s+for\s+tender',
        r'invitation\s+to\s+bid',
        r'invitation\s+for\s+bid',
        r'notice\s+inviting\s+tender',
        r'notice\s+inviting\s+quotation',
        r'procurement\s+notice',
        r'tender\s+notice',
        r'bid\s+invitation',
        r'expression\s+of\s+interest',
        r'eoi\s+notice',
        r'rfp\s+notice',
        r'rfq\s+notice',
        r'nit\s+no',
        r'tender\s+no',
        r'bid\s+reference',
    ]
    
    DATE_PATTERNS = [
        r'(?:due|deadline|last|closing)\s*(?:date)?[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s*(?:is\s+the)?\s*(?:due|deadline|last|closing)',
        r'submit\s+(?:by|before)[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{2,4})',
    ]
    
    VALUE_PATTERNS = [
        r'(?:estimated|approximate|contract)?\s*value[:\s]*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)\s*(?:lakhs?|crores?|million|cr|lac)?',
        r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:lakhs?|crores?|million|cr|lac)?',
        r'budget[:\s]*(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)',
    ]
    
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        self.rfp_patterns = [re.compile(p, re.I) for p in self.RFP_INDICATORS]
        self.date_patterns = [re.compile(p, re.I) for p in self.DATE_PATTERNS]
        self.value_patterns = [re.compile(p, re.I) for p in self.VALUE_PATTERNS]
    
    def detect_rfps(self, content: str, parsed: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Detect RFP announcements in content
        
        Returns:
            List of detected RFPs with extracted metadata
        """
        detected = []
        text = parsed.get('full_text', content) if parsed else content
        
        # Check for RFP indicators
        matches = []
        for pattern in self.rfp_patterns:
            found = pattern.findall(text)
            matches.extend(found)
        
        if not matches:
            return []
        
        # Calculate confidence based on number of indicators
        confidence = min(1.0, len(matches) / 3)
        
        if confidence < self.min_confidence:
            return []
        
        # Extract metadata
        rfp_data = {
            'confidence': confidence,
            'indicators_found': list(set(matches)),
            'due_date': self._extract_date(text),
            'estimated_value': self._extract_value(text),
            'title': parsed.get('title', '') if parsed else self._extract_title(text),
            'description': parsed.get('description', '') if parsed else text[:500]
        }
        
        detected.append(rfp_data)
        return detected
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """Extract due date from text"""
        for pattern in self.date_patterns:
            match = pattern.search(text)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 1:
                        date_str = groups[0]
                        for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y']:
                            try:
                                return datetime.strptime(date_str, fmt)
                            except ValueError:
                                continue
                    elif len(groups) == 3:
                        day, month_str, year = groups
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        month = month_map.get(month_str.lower()[:3], 1)
                        year = int(year) if len(year) == 4 else 2000 + int(year)
                        return datetime(year, month, int(day))
                except:
                    continue
        return None
    
    def _extract_value(self, text: str) -> float:
        """Extract estimated value from text"""
        for pattern in self.value_patterns:
            match = pattern.search(text)
            if match:
                try:
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str)
                    
                    # Check for multipliers
                    context = text[max(0, match.start()-20):match.end()+20].lower()
                    if 'crore' in context or 'cr' in context:
                        value *= 10000000
                    elif 'lakh' in context or 'lac' in context:
                        value *= 100000
                    elif 'million' in context:
                        value *= 1000000
                    
                    return value
                except:
                    continue
        return 0.0
    
    def _extract_title(self, text: str) -> str:
        """Extract title from text"""
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if 20 < len(line) < 200:
                for pattern in self.rfp_patterns:
                    if pattern.search(line):
                        return line
        return lines[0][:200] if lines else "Untitled RFP"


# ============================================================================
# 7. Keyword-based Filtering
# ============================================================================

class KeywordFilter:
    """Filters RFPs based on keywords"""
    
    DEFAULT_INCLUDE_KEYWORDS = [
        'wire', 'cable', 'electrical', 'power', 'copper', 'aluminium',
        'conductor', 'insulated', 'pvc', 'xlpe', 'armoured', 'unarmoured',
        'frls', 'fire retardant', 'low smoke', 'control cable', 'power cable',
        'building wire', 'flexible', 'multicore', 'single core',
        'voltage', 'current', 'ampere', 'sqmm', 'sq mm', 'cross section'
    ]
    
    DEFAULT_EXCLUDE_KEYWORDS = [
        'fibre optic', 'fiber optic', 'optical fiber', 'data cable',
        'network cable', 'ethernet', 'cat5', 'cat6', 'coaxial',
        'telephone', 'communication cable'
    ]
    
    def __init__(
        self,
        include_keywords: List[str] = None,
        exclude_keywords: List[str] = None,
        min_keyword_matches: int = 2
    ):
        self.include_keywords = [k.lower() for k in (include_keywords or self.DEFAULT_INCLUDE_KEYWORDS)]
        self.exclude_keywords = [k.lower() for k in (exclude_keywords or self.DEFAULT_EXCLUDE_KEYWORDS)]
        self.min_keyword_matches = min_keyword_matches
    
    def filter(self, text: str, title: str = "") -> Tuple[bool, float, List[str]]:
        """
        Filter text based on keywords
        
        Returns:
            Tuple of (is_relevant, score, matched_keywords)
        """
        combined = f"{title} {text}".lower()
        
        # Check exclude keywords first
        for keyword in self.exclude_keywords:
            if keyword in combined:
                return False, 0.0, []
        
        # Count include keyword matches
        matched = []
        for keyword in self.include_keywords:
            if keyword in combined:
                matched.append(keyword)
        
        if len(matched) < self.min_keyword_matches:
            return False, 0.0, matched
        
        # Calculate relevance score
        score = min(1.0, len(matched) / (len(self.include_keywords) * 0.3))
        
        return True, score, matched
    
    def add_keyword(self, keyword: str, exclude: bool = False):
        """Add keyword to filter"""
        keyword = keyword.lower()
        if exclude:
            if keyword not in self.exclude_keywords:
                self.exclude_keywords.append(keyword)
        else:
            if keyword not in self.include_keywords:
                self.include_keywords.append(keyword)
    
    def remove_keyword(self, keyword: str, exclude: bool = False):
        """Remove keyword from filter"""
        keyword = keyword.lower()
        target = self.exclude_keywords if exclude else self.include_keywords
        if keyword in target:
            target.remove(keyword)


# ============================================================================
# 8 & 9. Deadline Extraction & Priority Scoring
# ============================================================================

class PriorityScorer:
    """Calculates priority score for RFPs"""
    
    def __init__(
        self,
        urgency_weight: float = 0.35,
        value_weight: float = 0.30,
        relevance_weight: float = 0.25,
        authority_weight: float = 0.10
    ):
        self.weights = {
            'urgency': urgency_weight,
            'value': value_weight,
            'relevance': relevance_weight,
            'authority': authority_weight
        }
        
        # High-value authorities get bonus
        self.authority_bonuses = {
            'central government': 0.2,
            'state government': 0.15,
            'psu': 0.15,
            'municipal': 0.1,
            'railway': 0.15,
            'defense': 0.2,
            'power': 0.15
        }
    
    def calculate_priority(self, rfp: ScrapedRFP) -> Tuple[float, RFPPriority]:
        """
        Calculate priority score and level
        
        Returns:
            Tuple of (score, priority_level)
        """
        scores = {}
        
        # Urgency score (0-1)
        if rfp.due_date:
            days_until_due = (rfp.due_date - datetime.now()).days
            if days_until_due <= 0:
                scores['urgency'] = 0  # Expired
            elif days_until_due <= 7:
                scores['urgency'] = 1.0  # Critical
            elif days_until_due <= 14:
                scores['urgency'] = 0.9
            elif days_until_due <= 30:
                scores['urgency'] = 0.7
            elif days_until_due <= 60:
                scores['urgency'] = 0.5
            else:
                scores['urgency'] = 0.3
        else:
            scores['urgency'] = 0.5  # Unknown deadline
        
        # Value score (0-1)
        if rfp.estimated_value > 0:
            if rfp.estimated_value >= 10000000:  # 1 Crore+
                scores['value'] = 1.0
            elif rfp.estimated_value >= 5000000:  # 50 Lakhs+
                scores['value'] = 0.8
            elif rfp.estimated_value >= 1000000:  # 10 Lakhs+
                scores['value'] = 0.6
            elif rfp.estimated_value >= 100000:  # 1 Lakh+
                scores['value'] = 0.4
            else:
                scores['value'] = 0.2
        else:
            scores['value'] = 0.4  # Unknown value
        
        # Relevance score
        scores['relevance'] = rfp.relevance_score
        
        # Authority score
        authority_bonus = 0
        authority_lower = rfp.issuing_authority.lower()
        for key, bonus in self.authority_bonuses.items():
            if key in authority_lower:
                authority_bonus = max(authority_bonus, bonus)
        scores['authority'] = min(1.0, 0.5 + authority_bonus)
        
        # Calculate weighted score
        total_score = sum(
            scores[k] * self.weights[k]
            for k in self.weights
        )
        
        # Determine priority level
        if total_score >= 0.8:
            priority = RFPPriority.CRITICAL
        elif total_score >= 0.6:
            priority = RFPPriority.HIGH
        elif total_score >= 0.4:
            priority = RFPPriority.MEDIUM
        else:
            priority = RFPPriority.LOW
        
        return total_score, priority


# ============================================================================
# 10. Alert/Notification System
# ============================================================================

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, max_alerts: int = 100):
        self.alerts: Dict[str, Alert] = {}
        self.max_alerts = max_alerts
        self.subscribers: List[Callable[[Alert], None]] = []
        self._lock = threading.Lock()
    
    def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        rfp_id: str = None
    ) -> Alert:
        """Create and store alert"""
        with self._lock:
            alert = Alert(
                id=hashlib.md5(f"{title}{datetime.now()}".encode()).hexdigest()[:16],
                level=level,
                title=title,
                message=message,
                rfp_id=rfp_id,
                created_at=datetime.now()
            )
            
            # Clean old alerts if at limit
            if len(self.alerts) >= self.max_alerts:
                oldest = sorted(self.alerts.values(), key=lambda a: a.created_at)
                for old in oldest[:10]:
                    del self.alerts[old.id]
            
            self.alerts[alert.id] = alert
            
            # Notify subscribers
            for subscriber in self.subscribers:
                try:
                    subscriber(alert)
                except Exception as e:
                    logger.error(f"Alert subscriber error: {e}")
            
            logger.info(f"Alert created: [{alert.level.value}] {title}")
            return alert
    
    def acknowledge(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            return True
        return False
    
    def get_active_alerts(self, level: AlertLevel = None) -> List[Alert]:
        """Get unacknowledged alerts"""
        alerts = [a for a in self.alerts.values() if not a.acknowledged]
        if level:
            alerts = [a for a in alerts if a.level == level]
        return sorted(alerts, key=lambda a: a.created_at, reverse=True)
    
    def subscribe(self, callback: Callable[[Alert], None]):
        """Subscribe to alerts"""
        self.subscribers.append(callback)
    
    def clear_old_alerts(self, days: int = 7):
        """Clear alerts older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        with self._lock:
            to_remove = [
                aid for aid, alert in self.alerts.items()
                if alert.created_at < cutoff
            ]
            for aid in to_remove:
                del self.alerts[aid]


# ============================================================================
# 11 & 12. RFP Metadata Extractor & Duplicate Detection
# ============================================================================

class RFPMetadataExtractor:
    """Extracts metadata from RFP content"""
    
    CATEGORY_KEYWORDS = {
        'power_cables': ['power cable', 'ht cable', 'lt cable', 'mv cable', 'xlpe cable'],
        'control_cables': ['control cable', 'instrumentation cable', 'signal cable'],
        'building_wires': ['building wire', 'house wire', 'domestic wire', 'wiring cable'],
        'flexible_cables': ['flexible cable', 'flex cable', 'submersible cable'],
        'armoured_cables': ['armoured cable', 'swa cable', 'steel wire armoured'],
        'fire_resistant': ['fire resistant', 'frls', 'fire retardant', 'low smoke'],
        'solar_cables': ['solar cable', 'photovoltaic', 'pv cable', 'dc cable']
    }
    
    def extract(self, content: str, parsed: Dict = None) -> Dict[str, Any]:
        """Extract comprehensive metadata from RFP content"""
        text = content.lower()
        
        metadata = {
            'categories': self._detect_categories(text),
            'quantities': self._extract_quantities(text),
            'specifications': self._extract_specifications(text),
            'certifications_required': self._extract_certifications(text),
            'delivery_location': self._extract_location(text),
            'payment_terms': self._extract_payment_terms(text),
            'contact_info': self._extract_contact(content)
        }
        
        return metadata
    
    def _detect_categories(self, text: str) -> List[str]:
        """Detect product categories in RFP"""
        categories = []
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                categories.append(category)
        return categories
    
    def _extract_quantities(self, text: str) -> List[Dict]:
        """Extract quantities from text"""
        quantities = []
        pattern = r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(meters?|km|kilometres?|coils?|drums?|lots?|nos?\.?|numbers?)'
        
        for match in re.finditer(pattern, text, re.I):
            quantities.append({
                'value': float(match.group(1).replace(',', '')),
                'unit': match.group(2).lower()
            })
        
        return quantities
    
    def _extract_specifications(self, text: str) -> Dict:
        """Extract technical specifications"""
        specs = {}
        
        # Conductor size
        size_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:sq\.?\s*mm|sqmm|mm2)', text)
        if size_match:
            specs['conductor_size_sqmm'] = float(size_match.group(1))
        
        # Number of cores
        cores_match = re.search(r'(\d+)\s*(?:core|c)\s*x', text)
        if cores_match:
            specs['number_of_cores'] = int(cores_match.group(1))
        
        # Voltage rating
        voltage_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kv|volt|v)', text, re.I)
        if voltage_match:
            specs['voltage_rating'] = voltage_match.group(0)
        
        return specs
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract required certifications"""
        certs = []
        cert_patterns = [
            r'bis\s+(?:certification|certified|mark|license)',
            r'iso\s*\d+',
            r'iec\s*\d+',
            r'is\s*\d+',
            r'nabl\s+accredit',
            r'type\s+test\s+certificate'
        ]
        
        for pattern in cert_patterns:
            if re.search(pattern, text, re.I):
                certs.append(pattern.replace(r'\s+', ' ').replace(r'\s*', ''))
        
        return list(set(certs))
    
    def _extract_location(self, text: str) -> str:
        """Extract delivery location"""
        location_patterns = [
            r'delivery\s+(?:at|to|location)[:\s]+([^,\n]+)',
            r'(?:site|location)[:\s]+([^,\n]+)',
            r'supply\s+(?:at|to)[:\s]+([^,\n]+)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_payment_terms(self, text: str) -> str:
        """Extract payment terms"""
        payment_patterns = [
            r'payment\s+terms?[:\s]+([^.]+)',
            r'(\d+%?\s+(?:advance|on delivery|after inspection))',
        ]
        
        for pattern in payment_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_contact(self, text: str) -> Dict:
        """Extract contact information"""
        contact = {}
        
        # Email
        email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
        if email_match:
            contact['email'] = email_match.group(0)
        
        # Phone
        phone_match = re.search(r'(?:\+91[-\s]?)?[6-9]\d{9}', text)
        if phone_match:
            contact['phone'] = phone_match.group(0)
        
        return contact


class DuplicateDetector:
    """Detects duplicate RFPs"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.seen_hashes: Dict[str, str] = {}  # content_hash -> rfp_id
        self.rfp_signatures: Dict[str, str] = {}  # rfp_id -> signature
    
    def is_duplicate(self, rfp: ScrapedRFP) -> Tuple[bool, Optional[str]]:
        """
        Check if RFP is duplicate
        
        Returns:
            Tuple of (is_duplicate, existing_rfp_id)
        """
        # Check exact content hash
        if rfp.content_hash in self.seen_hashes:
            return True, self.seen_hashes[rfp.content_hash]
        
        # Create signature for similarity check
        signature = self._create_signature(rfp)
        
        for existing_id, existing_sig in self.rfp_signatures.items():
            similarity = self._calculate_similarity(signature, existing_sig)
            if similarity >= self.similarity_threshold:
                return True, existing_id
        
        return False, None
    
    def register(self, rfp: ScrapedRFP):
        """Register RFP for future duplicate detection"""
        self.seen_hashes[rfp.content_hash] = rfp.id
        self.rfp_signatures[rfp.id] = self._create_signature(rfp)
    
    def _create_signature(self, rfp: ScrapedRFP) -> str:
        """Create signature for RFP"""
        # Combine key fields for signature
        parts = [
            rfp.title.lower(),
            rfp.issuing_authority.lower(),
            str(rfp.estimated_value),
            rfp.due_date.strftime('%Y%m%d') if rfp.due_date else ''
        ]
        return '|'.join(parts)
    
    def _calculate_similarity(self, sig1: str, sig2: str) -> float:
        """Calculate similarity between signatures"""
        parts1 = set(sig1.split('|'))
        parts2 = set(sig2.split('|'))
        
        if not parts1 or not parts2:
            return 0.0
        
        intersection = len(parts1 & parts2)
        union = len(parts1 | parts2)
        
        return intersection / union if union > 0 else 0.0
    
    def clear(self):
        """Clear duplicate detection history"""
        self.seen_hashes.clear()
        self.rfp_signatures.clear()


# ============================================================================
# 17 & 21-23. Statistics & Performance Tracking
# ============================================================================

class StatisticsTracker:
    """Tracks scraping and agent statistics"""
    
    def __init__(self, history_size: int = 1000):
        self.stats = ScrapingStats()
        self.scrape_history: deque = deque(maxlen=history_size)
        self.rfp_history: deque = deque(maxlen=history_size)
        self.performance_history: deque = deque(maxlen=100)
        self._lock = threading.Lock()
    
    def record_scrape(self, result: ScrapeResult):
        """Record a scraping operation"""
        with self._lock:
            self.scrape_history.append(result)
            self.stats.total_scrapes += 1
            
            if result.success:
                self.stats.successful_scrapes += 1
                self.stats.total_rfps_found += result.rfps_found
            else:
                self.stats.failed_scrapes += 1
            
            self.stats.last_scrape_time = result.timestamp
            
            # Update average scrape time
            times = [s.duration_ms for s in self.scrape_history if s.success]
            if times:
                self.stats.average_scrape_time_ms = sum(times) / len(times)
    
    def record_rfp(self, rfp: ScrapedRFP, is_relevant: bool, is_duplicate: bool):
        """Record an RFP detection"""
        with self._lock:
            self.rfp_history.append({
                'rfp_id': rfp.id,
                'timestamp': rfp.scraped_at,
                'relevant': is_relevant,
                'duplicate': is_duplicate
            })
            
            if is_relevant:
                self.stats.total_relevant_rfps += 1
            if is_duplicate:
                self.stats.total_duplicates_filtered += 1
    
    def record_performance(self, metric_name: str, value: float):
        """Record a performance metric"""
        with self._lock:
            self.performance_history.append({
                'metric': metric_name,
                'value': value,
                'timestamp': datetime.now()
            })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return asdict(self.stats)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        with self._lock:
            recent_scrapes = list(self.scrape_history)[-10:]
            recent_rfps = list(self.rfp_history)[-10:]
            
            # Calculate success rate
            success_rate = 0.0
            if self.stats.total_scrapes > 0:
                success_rate = self.stats.successful_scrapes / self.stats.total_scrapes
            
            # Calculate relevance rate
            relevance_rate = 0.0
            if self.stats.total_rfps_found > 0:
                relevance_rate = self.stats.total_relevant_rfps / self.stats.total_rfps_found
            
            return {
                'summary': {
                    'total_scrapes': self.stats.total_scrapes,
                    'success_rate': success_rate,
                    'total_rfps': self.stats.total_rfps_found,
                    'relevant_rfps': self.stats.total_relevant_rfps,
                    'relevance_rate': relevance_rate,
                    'duplicates_filtered': self.stats.total_duplicates_filtered,
                    'avg_scrape_time_ms': self.stats.average_scrape_time_ms,
                    'last_scrape': self.stats.last_scrape_time.isoformat() if self.stats.last_scrape_time else None
                },
                'recent_scrapes': [
                    {
                        'url': s.url,
                        'success': s.success,
                        'rfps_found': s.rfps_found,
                        'duration_ms': s.duration_ms,
                        'timestamp': s.timestamp.isoformat()
                    }
                    for s in recent_scrapes
                ],
                'recent_rfps': recent_rfps
            }
    
    def reset(self):
        """Reset all statistics"""
        with self._lock:
            self.stats = ScrapingStats()
            self.scrape_history.clear()
            self.rfp_history.clear()
            self.performance_history.clear()


# ============================================================================
# 18 & 19. RFP Summary Generator & Selection Logic
# ============================================================================

class RFPSummaryGenerator:
    """Generates summaries for RFPs"""
    
    def generate_summary(self, rfp: ScrapedRFP) -> Dict[str, Any]:
        """Generate comprehensive summary for an RFP"""
        days_until_due = None
        if rfp.due_date:
            days_until_due = (rfp.due_date - datetime.now()).days
        
        return {
            'id': rfp.id,
            'title': rfp.title,
            'issuing_authority': rfp.issuing_authority,
            'estimated_value': rfp.estimated_value,
            'estimated_value_formatted': self._format_currency(rfp.estimated_value),
            'due_date': rfp.due_date.strftime('%Y-%m-%d') if rfp.due_date else 'Not specified',
            'days_until_due': days_until_due,
            'urgency': self._get_urgency_label(days_until_due),
            'category': rfp.category,
            'keywords': rfp.keywords[:10],
            'priority': rfp.priority.value,
            'relevance_score': round(rfp.relevance_score * 100, 1),
            'source': rfp.source_url,
            'scraped_at': rfp.scraped_at.strftime('%Y-%m-%d %H:%M')
        }
    
    def generate_brief(self, rfp: ScrapedRFP) -> str:
        """Generate brief one-line summary"""
        days = (rfp.due_date - datetime.now()).days if rfp.due_date else None
        deadline = f"Due in {days} days" if days else "Deadline TBD"
        return f"{rfp.title} | {rfp.issuing_authority} | {self._format_currency(rfp.estimated_value)} | {deadline}"
    
    def _format_currency(self, value: float) -> str:
        """Format currency value"""
        if value >= 10000000:
            return f"₹{value/10000000:.2f} Cr"
        elif value >= 100000:
            return f"₹{value/100000:.2f} L"
        else:
            return f"₹{value:,.0f}"
    
    def _get_urgency_label(self, days: Optional[int]) -> str:
        """Get urgency label based on days until due"""
        if days is None:
            return "Unknown"
        if days <= 0:
            return "Expired"
        if days <= 7:
            return "Critical"
        if days <= 14:
            return "High"
        if days <= 30:
            return "Medium"
        return "Low"


class RFPSelector:
    """Selects best RFPs for response"""
    
    def __init__(self, priority_scorer: PriorityScorer = None):
        self.scorer = priority_scorer or PriorityScorer()
    
    def select_top_rfps(
        self,
        rfps: List[ScrapedRFP],
        count: int = 5,
        min_priority: RFPPriority = RFPPriority.LOW
    ) -> List[ScrapedRFP]:
        """Select top RFPs for response"""
        # Filter by minimum priority
        priority_order = [RFPPriority.CRITICAL, RFPPriority.HIGH, RFPPriority.MEDIUM, RFPPriority.LOW]
        min_index = priority_order.index(min_priority)
        
        scored_rfps = []
        for rfp in rfps:
            score, priority = self.scorer.calculate_priority(rfp)
            if priority_order.index(priority) <= min_index:
                scored_rfps.append((score, rfp))
        
        # Sort by score descending
        scored_rfps.sort(key=lambda x: x[0], reverse=True)
        
        return [rfp for _, rfp in scored_rfps[:count]]
    
    def select_best_rfp(self, rfps: List[ScrapedRFP]) -> Optional[ScrapedRFP]:
        """Select single best RFP"""
        top = self.select_top_rfps(rfps, count=1)
        return top[0] if top else None


# ============================================================================
# 20. Handoff to Orchestrator
# ============================================================================

class OrchestratorHandoff:
    """Handles handoff of selected RFPs to orchestrator"""
    
    def __init__(self, orchestrator_callback: Callable[[Dict], None] = None):
        self.callback = orchestrator_callback
        self.pending_handoffs: queue.Queue = queue.Queue()
        self.completed_handoffs: List[Dict] = []
        self._lock = threading.Lock()
    
    def prepare_handoff(self, rfp: ScrapedRFP) -> Dict[str, Any]:
        """Prepare RFP data for orchestrator handoff"""
        return {
            'rfp_id': rfp.id,
            'title': rfp.title,
            'description': rfp.description,
            'source_url': rfp.source_url,
            'issuing_authority': rfp.issuing_authority,
            'due_date': rfp.due_date.isoformat() if rfp.due_date else None,
            'estimated_value': rfp.estimated_value,
            'category': rfp.category,
            'keywords': rfp.keywords,
            'priority': rfp.priority.value,
            'relevance_score': rfp.relevance_score,
            'metadata': rfp.metadata,
            'raw_content': rfp.raw_content[:5000],  # Limit content size
            'handoff_time': datetime.now().isoformat()
        }
    
    def queue_handoff(self, rfp: ScrapedRFP):
        """Queue RFP for handoff"""
        handoff_data = self.prepare_handoff(rfp)
        self.pending_handoffs.put(handoff_data)
        logger.info(f"Queued handoff for RFP: {rfp.id}")
    
    def process_handoffs(self) -> int:
        """Process all pending handoffs"""
        processed = 0
        while not self.pending_handoffs.empty():
            try:
                data = self.pending_handoffs.get_nowait()
                if self.callback:
                    self.callback(data)
                
                with self._lock:
                    self.completed_handoffs.append({
                        'rfp_id': data['rfp_id'],
                        'timestamp': datetime.now(),
                        'success': True
                    })
                
                processed += 1
                logger.info(f"Completed handoff for RFP: {data['rfp_id']}")
                
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Handoff error: {e}")
        
        return processed
    
    def get_pending_count(self) -> int:
        """Get count of pending handoffs"""
        return self.pending_handoffs.qsize()


# ============================================================================
# 13. Scheduling Mechanism
# ============================================================================

class Scheduler:
    """Scheduler for periodic tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def add_task(
        self,
        name: str,
        callback: Callable,
        interval_hours: float = 6.0,
        run_immediately: bool = True
    ):
        """Add scheduled task"""
        self.tasks[name] = {
            'callback': callback,
            'interval_seconds': interval_hours * 3600,
            'last_run': None,
            'next_run': datetime.now() if run_immediately else datetime.now() + timedelta(hours=interval_hours),
            'run_count': 0,
            'error_count': 0
        }
        logger.info(f"Scheduled task: {name} (every {interval_hours}h)")
    
    def remove_task(self, name: str):
        """Remove scheduled task"""
        if name in self.tasks:
            del self.tasks[name]
    
    def start(self):
        """Start scheduler"""
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Scheduler started")
    
    def stop(self):
        """Stop scheduler"""
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")
    
    def _run_loop(self):
        """Main scheduler loop"""
        while self._running:
            now = datetime.now()
            
            for name, task in list(self.tasks.items()):
                if task['next_run'] and now >= task['next_run']:
                    try:
                        logger.info(f"Running scheduled task: {name}")
                        task['callback']()
                        task['run_count'] += 1
                        task['last_run'] = now
                    except Exception as e:
                        task['error_count'] += 1
                        logger.error(f"Scheduled task error ({name}): {e}")
                    
                    task['next_run'] = now + timedelta(seconds=task['interval_seconds'])
            
            # Sleep for a minute before checking again
            self._stop_event.wait(60)
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            'running': self._running,
            'tasks': {
                name: {
                    'last_run': task['last_run'].isoformat() if task['last_run'] else None,
                    'next_run': task['next_run'].isoformat() if task['next_run'] else None,
                    'run_count': task['run_count'],
                    'error_count': task['error_count']
                }
                for name, task in self.tasks.items()
            }
        }


# ============================================================================
# 24-29. Agent State Management & Health
# ============================================================================

class AgentStateManager:
    """Manages Sales Agent state"""
    
    def __init__(self):
        self.state = AgentState.IDLE
        self.state_history: deque = deque(maxlen=100)
        self.last_state_change = datetime.now()
        self._lock = threading.Lock()
    
    def transition(self, new_state: AgentState) -> bool:
        """Transition to new state"""
        valid_transitions = {
            AgentState.IDLE: [AgentState.STARTING],
            AgentState.STARTING: [AgentState.RUNNING, AgentState.ERROR],
            AgentState.RUNNING: [AgentState.SCANNING, AgentState.PAUSED, AgentState.STOPPING, AgentState.ERROR],
            AgentState.SCANNING: [AgentState.PROCESSING, AgentState.RUNNING, AgentState.ERROR],
            AgentState.PROCESSING: [AgentState.RUNNING, AgentState.ERROR],
            AgentState.PAUSED: [AgentState.RUNNING, AgentState.STOPPING],
            AgentState.STOPPING: [AgentState.STOPPED],
            AgentState.STOPPED: [AgentState.STARTING],
            AgentState.ERROR: [AgentState.STARTING, AgentState.STOPPED]
        }
        
        with self._lock:
            if new_state in valid_transitions.get(self.state, []):
                old_state = self.state
                self.state = new_state
                self.last_state_change = datetime.now()
                self.state_history.append({
                    'from': old_state.value,
                    'to': new_state.value,
                    'timestamp': self.last_state_change
                })
                logger.info(f"State transition: {old_state.value} -> {new_state.value}")
                return True
            else:
                logger.warning(f"Invalid state transition: {self.state.value} -> {new_state.value}")
                return False
    
    def get_state(self) -> AgentState:
        """Get current state"""
        return self.state
    
    def get_status(self) -> Dict[str, Any]:
        """Get full status"""
        return {
            'current_state': self.state.value,
            'last_change': self.last_state_change.isoformat(),
            'uptime_seconds': (datetime.now() - self.last_state_change).total_seconds()
        }


class HealthChecker:
    """Health check functionality"""
    
    def __init__(self, agent: 'SalesAgent'):
        self.agent = agent
        self.checks: Dict[str, Callable[[], bool]] = {}
        
        # Register default checks
        self.register_check('state', self._check_state)
        self.register_check('scheduler', self._check_scheduler)
        self.register_check('scraper', self._check_scraper)
    
    def register_check(self, name: str, check_func: Callable[[], bool]):
        """Register a health check"""
        self.checks[name] = check_func
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        all_healthy = True
        
        for name, check_func in self.checks.items():
            try:
                healthy = check_func()
                results[name] = {'healthy': healthy, 'error': None}
                if not healthy:
                    all_healthy = False
            except Exception as e:
                results[name] = {'healthy': False, 'error': str(e)}
                all_healthy = False
        
        return {
            'healthy': all_healthy,
            'timestamp': datetime.now().isoformat(),
            'checks': results
        }
    
    def _check_state(self) -> bool:
        """Check if agent state is healthy"""
        return self.agent.state_manager.get_state() not in [AgentState.ERROR, AgentState.STOPPED]
    
    def _check_scheduler(self) -> bool:
        """Check if scheduler is running"""
        return self.agent.scheduler._running
    
    def _check_scraper(self) -> bool:
        """Check if scraper is available"""
        return REQUESTS_AVAILABLE or SELENIUM_AVAILABLE


class StatusReporter:
    """Reports agent status"""
    
    def __init__(self, agent: 'SalesAgent'):
        self.agent = agent
    
    def get_full_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        return {
            'agent_id': self.agent.agent_id,
            'state': self.agent.state_manager.get_status(),
            'health': self.agent.health_checker.run_checks(),
            'statistics': self.agent.statistics.get_stats(),
            'scheduler': self.agent.scheduler.get_status(),
            'alerts': {
                'active': len(self.agent.alert_manager.get_active_alerts()),
                'critical': len(self.agent.alert_manager.get_active_alerts(AlertLevel.CRITICAL))
            },
            'urls_monitored': len(self.agent.url_manager.configs),
            'rfps_tracked': len(self.agent.rfps),
            'generated_at': datetime.now().isoformat()
        }
    
    def get_brief_status(self) -> str:
        """Get brief status string"""
        state = self.agent.state_manager.get_state()
        stats = self.agent.statistics.get_stats()
        return f"SalesAgent [{state.value}] | URLs: {stats['urls_monitored']} | RFPs: {stats['total_relevant_rfps']} | Alerts: {stats['active_alerts']}"


# ============================================================================
# 27. Configuration Hot Reload
# ============================================================================

class ConfigManager:
    """Manages configuration with hot reload support"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config: Dict[str, Any] = self._default_config()
        self._last_modified: float = 0
        self._lock = threading.Lock()
        
        if config_path and Path(config_path).exists():
            self.load()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'scan_interval_hours': 6.0,
            'max_concurrent_scrapes': 5,
            'scrape_timeout_seconds': 30,
            'rate_limit_per_minute': 10,
            'min_relevance_score': 0.3,
            'min_priority': 'low',
            'enable_selenium': True,
            'enable_proxy_rotation': False,
            'keywords': {
                'include': KeywordFilter.DEFAULT_INCLUDE_KEYWORDS,
                'exclude': KeywordFilter.DEFAULT_EXCLUDE_KEYWORDS
            },
            'alerts': {
                'enabled': True,
                'critical_only': False
            }
        }
    
    def load(self) -> bool:
        """Load configuration from file"""
        if not self.config_path:
            return False
        
        try:
            with open(self.config_path, 'r') as f:
                loaded = json.load(f)
            
            with self._lock:
                self.config.update(loaded)
                self._last_modified = Path(self.config_path).stat().st_mtime
            
            logger.info(f"Configuration loaded from {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def save(self) -> bool:
        """Save configuration to file"""
        if not self.config_path:
            return False
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def check_reload(self) -> bool:
        """Check if config file changed and reload if needed"""
        if not self.config_path or not Path(self.config_path).exists():
            return False
        
        current_mtime = Path(self.config_path).stat().st_mtime
        if current_mtime > self._last_modified:
            return self.load()
        return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        with self._lock:
            return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        with self._lock:
            self.config[key] = value


# ============================================================================
# Main Sales Agent Class
# ============================================================================

class SalesAgent:
    """
    Sales Agent - Comprehensive RFP Monitoring System
    
    Monitors URLs, scrapes RFP announcements, filters relevant opportunities,
    and triggers the workflow for response preparation.
    """
    
    def __init__(
        self,
        agent_id: str = "SALES_AGENT_001",
        config_path: str = None,
        url_config_path: str = None,
        log_dir: str = None
    ):
        self.agent_id = agent_id
        self.start_time = datetime.now()
        
        # Initialize logging
        global logger
        logger = SalesAgentLogger("SalesAgent", log_dir)
        
        # Initialize components
        self.config = ConfigManager(config_path)
        self.state_manager = AgentStateManager()
        self.url_manager = URLMonitorManager(url_config_path)
        self.rate_limiter = RateLimiter(
            requests_per_minute=self.config.get('rate_limit_per_minute', 10)
        )
        self.proxy_rotator = ProxyRotator()
        self.scraper = WebScraper(
            rate_limiter=self.rate_limiter,
            proxy_rotator=self.proxy_rotator,
            timeout=self.config.get('scrape_timeout_seconds', 30)
        )
        
        self.rfp_detector = RFPDetector()
        self.keyword_filter = KeywordFilter(
            include_keywords=self.config.get('keywords', {}).get('include'),
            exclude_keywords=self.config.get('keywords', {}).get('exclude')
        )
        self.priority_scorer = PriorityScorer()
        self.metadata_extractor = RFPMetadataExtractor()
        self.duplicate_detector = DuplicateDetector()
        
        self.alert_manager = AlertManager()
        self.statistics = StatisticsTracker()
        self.summary_generator = RFPSummaryGenerator()
        self.rfp_selector = RFPSelector(self.priority_scorer)
        self.handoff = OrchestratorHandoff()
        
        self.scheduler = Scheduler()
        self.health_checker = HealthChecker(self)
        self.status_reporter = StatusReporter(self)
        
        # RFP storage
        self.rfps: Dict[str, ScrapedRFP] = {}
        self.selected_rfps: List[str] = []
        
        # Shutdown handling
        self._shutdown_event = threading.Event()
        self._original_sigint = None
        self._original_sigterm = None
        
        logger.info(f"✅ Sales Agent initialized: {agent_id}")
    
    # ========== Lifecycle Methods ==========
    
    def start(self):
        """Start the Sales Agent"""
        if not self.state_manager.transition(AgentState.STARTING):
            logger.error("Failed to start: invalid state")
            return False
        
        try:
            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            # Schedule periodic scan
            self.scheduler.add_task(
                'scan_urls',
                self._scheduled_scan,
                interval_hours=self.config.get('scan_interval_hours', 6.0),
                run_immediately=True
            )
            
            # Schedule config reload check
            self.scheduler.add_task(
                'config_reload',
                self.config.check_reload,
                interval_hours=0.5,  # Every 30 minutes
                run_immediately=False
            )
            
            # Start scheduler
            self.scheduler.start()
            
            self.state_manager.transition(AgentState.RUNNING)
            logger.info("✅ Sales Agent started")
            return True
            
        except Exception as e:
            logger.error(f"Start error: {e}")
            self.state_manager.transition(AgentState.ERROR)
            return False
    
    def stop(self):
        """Stop the Sales Agent gracefully"""
        if not self.state_manager.transition(AgentState.STOPPING):
            return False
        
        logger.info("Stopping Sales Agent...")
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Close scraper
        self.scraper.close()
        
        # Process pending handoffs
        self.handoff.process_handoffs()
        
        # Save configurations
        self.url_manager.save_config()
        self.config.save()
        
        # Restore signal handlers
        self._restore_signal_handlers()
        
        self._shutdown_event.set()
        self.state_manager.transition(AgentState.STOPPED)
        logger.info("✅ Sales Agent stopped")
        return True
    
    def pause(self):
        """Pause the agent"""
        if self.state_manager.transition(AgentState.PAUSED):
            self.scheduler.stop()
            logger.info("Sales Agent paused")
            return True
        return False
    
    def resume(self):
        """Resume the agent"""
        if self.state_manager.transition(AgentState.RUNNING):
            self.scheduler.start()
            logger.info("Sales Agent resumed")
            return True
        return False
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        self._original_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, 'SIGTERM'):
            self._original_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _restore_signal_handlers(self):
        """Restore original signal handlers"""
        if self._original_sigint:
            signal.signal(signal.SIGINT, self._original_sigint)
        if self._original_sigterm and hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._original_sigterm)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
    
    # ========== URL Management ==========
    
    def add_url(
        self,
        url: str,
        name: str = None,
        keywords: List[str] = None,
        requires_javascript: bool = False,
        check_interval_hours: float = 6.0
    ) -> bool:
        """Add URL to monitor"""
        config = URLMonitorConfig(
            url=url,
            name=name or url,
            requires_javascript=requires_javascript,
            check_interval_hours=check_interval_hours,
            keywords=keywords or []
        )
        return self.url_manager.add_url(config)
    
    def remove_url(self, url: str) -> bool:
        """Remove URL from monitoring"""
        return self.url_manager.remove_url(url)
    
    def get_monitored_urls(self) -> List[Dict]:
        """Get list of monitored URLs"""
        return [
            {
                'url': c.url,
                'name': c.name,
                'enabled': c.enabled,
                'last_checked': c.last_checked.isoformat() if c.last_checked else None,
                'error_count': c.error_count
            }
            for c in self.url_manager.configs.values()
        ]
    
    # ========== Scanning & Scraping ==========
    
    def scan_url(self, url: str, force: bool = False) -> ScrapeResult:
        """Scan a single URL for RFPs"""
        start_time = time.time()
        config = self.url_manager.get_config(url)
        
        if not config:
            config = URLMonitorConfig(url=url, name=url)
        
        try:
            self.state_manager.transition(AgentState.SCANNING)
            
            # Scrape page
            if config.requires_javascript and SELENIUM_AVAILABLE:
                content, content_hash = self.scraper.scrape_dynamic(url, config)
            else:
                content, content_hash = self.scraper.scrape_static(url, config)
            
            # Check if content changed
            if not force and content_hash == config.last_hash:
                logger.debug(f"No changes detected: {url}")
                return ScrapeResult(
                    url=url, success=True, rfps_found=0,
                    error_message="", duration_ms=(time.time() - start_time) * 1000,
                    timestamp=datetime.now()
                )
            
            # Parse content
            parsed = self.scraper.parse_html(content, config.selectors)
            
            # Detect RFPs
            detected = self.rfp_detector.detect_rfps(content, parsed)
            rfps_found = 0
            
            self.state_manager.transition(AgentState.PROCESSING)
            
            for rfp_data in detected:
                rfp = self._process_detected_rfp(rfp_data, url, content, parsed)
                if rfp:
                    rfps_found += 1
            
            # Update URL manager
            self.url_manager.update_checked(url, content_hash)
            
            result = ScrapeResult(
                url=url, success=True, rfps_found=rfps_found,
                error_message="", duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
            
            self.statistics.record_scrape(result)
            self.state_manager.transition(AgentState.RUNNING)
            
            return result
            
        except Exception as e:
            logger.error(f"Scan error for {url}: {e}")
            self.url_manager.update_checked(url, error=True)
            
            result = ScrapeResult(
                url=url, success=False, rfps_found=0,
                error_message=str(e), duration_ms=(time.time() - start_time) * 1000,
                timestamp=datetime.now()
            )
            
            self.statistics.record_scrape(result)
            
            # Create alert for repeated failures
            config = self.url_manager.get_config(url)
            if config and config.error_count >= 3:
                self.alert_manager.create_alert(
                    AlertLevel.WARNING,
                    "Repeated Scrape Failures",
                    f"URL {url} has failed {config.error_count} times",
                    None
                )
            
            self.state_manager.transition(AgentState.RUNNING)
            return result
    
    def scan_all_urls(self) -> List[ScrapeResult]:
        """Scan all monitored URLs"""
        due_urls = self.url_manager.get_due_urls()
        results = []
        
        logger.info(f"Scanning {len(due_urls)} URLs...")
        
        max_concurrent = self.config.get('max_concurrent_scrapes', 5)
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {
                executor.submit(self.scan_url, config.url): config
                for config in due_urls
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Scan execution error: {e}")
        
        return results
    
    def _scheduled_scan(self):
        """Scheduled scan callback"""
        results = self.scan_all_urls()
        
        total_rfps = sum(r.rfps_found for r in results)
        successful = sum(1 for r in results if r.success)
        
        logger.info(f"Scheduled scan complete: {successful}/{len(results)} URLs, {total_rfps} RFPs found")
        
        # Select top RFPs and queue for handoff
        self._process_and_handoff()
    
    def _process_detected_rfp(
        self,
        rfp_data: Dict,
        source_url: str,
        content: str,
        parsed: Dict
    ) -> Optional[ScrapedRFP]:
        """Process a detected RFP"""
        # Apply keyword filter
        is_relevant, relevance_score, matched_keywords = self.keyword_filter.filter(
            content, rfp_data.get('title', '')
        )
        
        if not is_relevant:
            self.statistics.record_rfp(None, False, False)
            return None
        
        # Extract metadata
        metadata = self.metadata_extractor.extract(content, parsed)
        
        # Create RFP object
        rfp = ScrapedRFP(
            id=f"RFP_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(source_url) % 10000:04d}",
            title=rfp_data.get('title', 'Untitled RFP'),
            description=rfp_data.get('description', '')[:1000],
            source_url=source_url,
            source_type=RFPSource.WEB_SCRAPE,
            issuing_authority=parsed.get('authority', 'Unknown'),
            published_date=datetime.now(),
            due_date=rfp_data.get('due_date'),
            estimated_value=rfp_data.get('estimated_value', 0),
            category=metadata.get('categories', ['general'])[0] if metadata.get('categories') else 'general',
            keywords=matched_keywords,
            raw_content=content[:10000],
            metadata=metadata,
            content_hash=hashlib.md5(content.encode()).hexdigest(),
            scraped_at=datetime.now(),
            relevance_score=relevance_score
        )
        
        # Check for duplicates
        is_duplicate, existing_id = self.duplicate_detector.is_duplicate(rfp)
        
        if is_duplicate:
            logger.debug(f"Duplicate RFP detected: {rfp.id} matches {existing_id}")
            self.statistics.record_rfp(rfp, True, True)
            return None
        
        # Calculate priority
        score, priority = self.priority_scorer.calculate_priority(rfp)
        rfp.priority = priority
        
        # Register and store
        self.duplicate_detector.register(rfp)
        self.rfps[rfp.id] = rfp
        
        self.statistics.record_rfp(rfp, True, False)
        
        # Create alert for high-priority RFPs
        if priority in [RFPPriority.CRITICAL, RFPPriority.HIGH]:
            self.alert_manager.create_alert(
                AlertLevel.URGENT if priority == RFPPriority.CRITICAL else AlertLevel.INFO,
                f"New {priority.value.upper()} Priority RFP",
                f"{rfp.title} - Due: {rfp.due_date.strftime('%Y-%m-%d') if rfp.due_date else 'TBD'}",
                rfp.id
            )
        
        logger.info(f"✅ New RFP: {rfp.id} [{priority.value}] - {rfp.title[:50]}")
        return rfp
    
    # ========== RFP Management ==========
    
    def get_rfps(
        self,
        priority: RFPPriority = None,
        min_relevance: float = None,
        due_within_days: int = None
    ) -> List[ScrapedRFP]:
        """Get filtered list of RFPs"""
        rfps = list(self.rfps.values())
        
        if priority:
            rfps = [r for r in rfps if r.priority == priority]
        
        if min_relevance:
            rfps = [r for r in rfps if r.relevance_score >= min_relevance]
        
        if due_within_days:
            cutoff = datetime.now() + timedelta(days=due_within_days)
            rfps = [r for r in rfps if r.due_date and r.due_date <= cutoff]
        
        return sorted(rfps, key=lambda r: r.scraped_at, reverse=True)
    
    def get_rfp_summary(self, rfp_id: str) -> Optional[Dict]:
        """Get summary for specific RFP"""
        rfp = self.rfps.get(rfp_id)
        if rfp:
            return self.summary_generator.generate_summary(rfp)
        return None
    
    def select_rfp(self, rfp_id: str) -> bool:
        """Manually select an RFP for response"""
        if rfp_id in self.rfps:
            if rfp_id not in self.selected_rfps:
                self.selected_rfps.append(rfp_id)
                self.handoff.queue_handoff(self.rfps[rfp_id])
                logger.info(f"Selected RFP: {rfp_id}")
                return True
        return False
    
    def _process_and_handoff(self):
        """Process top RFPs and queue for handoff"""
        min_priority_str = self.config.get('min_priority', 'low')
        min_priority = RFPPriority[min_priority_str.upper()]
        
        top_rfps = self.rfp_selector.select_top_rfps(
            list(self.rfps.values()),
            count=5,
            min_priority=min_priority
        )
        
        for rfp in top_rfps:
            if rfp.id not in self.selected_rfps:
                self.selected_rfps.append(rfp.id)
                self.handoff.queue_handoff(rfp)
        
        self.handoff.process_handoffs()
    
    # ========== Dashboard & Status ==========
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            'agent': {
                'id': self.agent_id,
                'state': self.state_manager.get_state().value,
                'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
            },
            'statistics': self.statistics.get_dashboard_data(),
            'urls': {
                'monitored': len(self.url_manager.configs),
                'enabled': len([c for c in self.url_manager.configs.values() if c.enabled]),
                'with_errors': len([c for c in self.url_manager.configs.values() if c.error_count > 0])
            },
            'rfps': {
                'total': len(self.rfps),
                'by_priority': {
                    p.value: len([r for r in self.rfps.values() if r.priority == p])
                    for p in RFPPriority
                },
                'selected': len(self.selected_rfps),
                'pending_handoff': self.handoff.get_pending_count()
            },
            'alerts': {
                'total_active': len(self.alert_manager.get_active_alerts()),
                'critical': len(self.alert_manager.get_active_alerts(AlertLevel.CRITICAL)),
                'urgent': len(self.alert_manager.get_active_alerts(AlertLevel.URGENT))
            },
            'health': self.health_checker.run_checks()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return self.status_reporter.get_full_report()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return self.health_checker.run_checks()
    
    # ========== Proxy Management ==========
    
    def add_proxy(self, proxy: str):
        """Add proxy for rotation"""
        self.proxy_rotator.add_proxy(proxy)
    
    def get_proxy_stats(self) -> Dict[str, Dict]:
        """Get proxy statistics"""
        return self.proxy_rotator.proxy_stats


# ============================================================================
# Module-level convenience functions
# ============================================================================

_agent: Optional[SalesAgent] = None


def get_sales_agent() -> SalesAgent:
    """Get or create Sales Agent singleton"""
    global _agent
    if _agent is None:
        _agent = SalesAgent()
    return _agent


def start_agent() -> bool:
    """Start the Sales Agent"""
    return get_sales_agent().start()


def stop_agent() -> bool:
    """Stop the Sales Agent"""
    global _agent
    if _agent:
        result = _agent.stop()
        _agent = None
        return result
    return True


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SALES AGENT DEMO")
    print("=" * 60)
    
    # Check dependencies
    print(f"\nDependencies:")
    print(f"  requests: {'✅' if REQUESTS_AVAILABLE else '❌'}")
    print(f"  BeautifulSoup: {'✅' if BEAUTIFULSOUP_AVAILABLE else '❌'}")
    print(f"  Selenium: {'✅' if SELENIUM_AVAILABLE else '❌'}")
    
    # Create agent
    agent = SalesAgent(agent_id="DEMO_AGENT")
    
    # Add sample URLs
    agent.add_url(
        "https://eprocure.gov.in",
        name="Government e-Procurement",
        keywords=['wire', 'cable', 'electrical']
    )
    
    # Get status
    print("\n--- Agent Status ---")
    status = agent.get_status()
    print(f"State: {status['state']['current_state']}")
    print(f"URLs monitored: {status['urls_monitored']}")
    
    # Get dashboard data
    print("\n--- Dashboard ---")
    dashboard = agent.get_dashboard_data()
    print(f"Agent: {dashboard['agent']['id']}")
    print(f"Statistics: {dashboard['statistics']['summary']}")
    
    print("\n✅ Demo complete!")
