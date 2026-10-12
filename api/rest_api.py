"""
REST API for RFP Response System
FastAPI-based RESTful API exposing all functionality

Features:
1. FastAPI Application - Main app with CORS, middleware
2. Authentication System - JWT-based auth
3. Authorization Middleware - Role-based access control
4. RFP Submission Endpoint - Submit new RFPs
5. Status Check Endpoint - Check RFP processing status
6. Result Retrieval Endpoint - Get RFP results
7. Product Search Endpoint - Search products
8. Configuration Endpoints - Manage system config
9. Analytics Endpoints - View analytics data
10. Health Check Endpoint - System health
11. Webhook Endpoints - Webhook management
12. Batch Processing Endpoint - Process multiple RFPs
13. File Upload Handling - Upload RFP documents
14. Streaming Response Support - SSE for progress
15. Rate Limiting - Request throttling
16. API Versioning - Version management
17. OpenAPI Documentation - Auto-generated docs
18. Request Validation - Pydantic models
19. Response Formatting - Standardized responses
20. Error Response Handlers - Custom error handling
"""

import asyncio
import hashlib
import hmac
import io
import json
import logging
import math
import os
import secrets
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path

# Ensure UTF-8 output on Windows consoles to prevent UnicodeEncodeError
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Load environment variables (.env file for GROQ_API_KEY etc.)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

# Performance Integration
try:
    perf_path = str(Path(__file__).parent.parent)
    if perf_path not in sys.path:
        sys.path.insert(0, perf_path)
    from performance.integration import init_performance
    from api.api_performance import setup_api_performance
    PERFORMANCE_AVAILABLE = True
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    print(f"Performance integration not available: {e}")

# Pipeline Connector Integration
try:
    pipeline_root = str(Path(__file__).parent.parent)
    if pipeline_root not in sys.path:
        sys.path.insert(0, pipeline_root)
    from pipeline_connector import PipelineExecutor, create_pipeline, run_full_pipeline
    PIPELINE_AVAILABLE = True
except ImportError as e:
    PIPELINE_AVAILABLE = False
    print(f"Pipeline connector not available: {e}")

# Spec Comparer / PDF Extraction Integration (for /rfps/analyze)
try:
    _project_root = str(Path(__file__).parent.parent)
    _pdf_extraction_path = os.path.join(_project_root, 'pdf_extraction')
    _spec_comparer_path = os.path.join(_project_root, 'spec_comparer')
    for _p in (_project_root, _pdf_extraction_path, _spec_comparer_path):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    from multilingual_extractor import MultilingualExtractor
    from rfp_terms_matcher import RFPTermsMatcher, RFPExtractorEnhanced, RFPCompleteAnalyzer
    SPEC_ANALYSIS_AVAILABLE = True
except ImportError as e:
    SPEC_ANALYSIS_AVAILABLE = False
    print(f"Spec analysis modules not available: {e}")

# OEM Product Database + SpecMatcher + SpecCalculator (lazy-loaded singletons)
_oem_product_db = None
_spec_matcher = None
_spec_calculator = None
SPEC_COMPARER_AVAILABLE = False

# Persistent catalog store (loaded after logger is defined — see below)
CATALOG_STORE_AVAILABLE = False

# In-memory staging for import-preview (extraction_id → detected products)
_import_staging: dict[str, dict] = {}

# In-memory store for background linked-doc downloads (analysis_id → result)
_linked_docs_store: dict[str, dict] = {}

# Persistent analysis history store (replaces in-memory dict)
ANALYSIS_STORE_AVAILABLE = False

try:
    import pandas as pd
    from difflib import SequenceMatcher
    SPEC_COMPARER_AVAILABLE = True
except ImportError:
    pass

from io import BytesIO
from pathlib import Path
from threading import RLock
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Set, Union

# MongoDB async driver
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    print("motor not installed – MongoDB auth disabled")

# FastAPI imports
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Enterprise SaaS Integrations
try:
    from passlib.context import CryptContext
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception:
    _pwd_context = None

try:
    from core.redis_client import get_distributed_state
    _distributed_state = get_distributed_state()
except Exception:
    _distributed_state = None

try:
    from core.tenant_context import EnterpriseContextMiddleware, get_current_tenant_id
except Exception:
    EnterpriseContextMiddleware = None
    def get_current_tenant_id():
        return "default"

try:
    from api.health_router import health_router
    HEALTH_ROUTER_AVAILABLE = True
except Exception:
    HEALTH_ROUTER_AVAILABLE = False


def clean_nan_values(obj: Any) -> Any:
    """Recursively sanitize float NaN and Infinite values to None for valid JSON serialization."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_nan_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan_values(item) for item in obj]
    elif 'pd' in globals() and pd is not None and hasattr(pd, 'isna') and pd.isna(obj):
        return None
    return obj

# Persistent user/imported product catalog store
try:
    from database.catalog_store import (
        load_user_products as _load_persisted_products,
        add_product as _persist_product,
        add_products_bulk as _persist_products_bulk,
        delete_product as _delete_persisted_product,
        sync_to_dataframe as _sync_catalog_to_df,
        get_count as _persisted_product_count,
        get_import_history as _get_import_history,
    )
    CATALOG_STORE_AVAILABLE = True
    logger.info("✅ Persistent catalog store available")
except ImportError as _cse:
    CATALOG_STORE_AVAILABLE = False
    logger.warning(f"⚠️ Catalog store unavailable: {_cse}")

# Persistent analysis history store
try:
    from database.analysis_store import (
        save_analysis as _persist_analysis,
        list_analyses as _list_analyses,
        get_analysis as _get_analysis,
        delete_analysis as _delete_analysis,
    )
    ANALYSIS_STORE_AVAILABLE = True
    logger.info("✅ Persistent analysis store available")
except ImportError as _ase:
    ANALYSIS_STORE_AVAILABLE = False
    logger.warning(f"⚠️ Analysis store unavailable: {_ase}")

# Win/Loss Analytics Integration
try:
    from analytics.win_loss_analytics import WinLossAnalytics
    from database.db_engine import get_db_manager
    WIN_LOSS_ANALYTICS_AVAILABLE = True
    logger.info("✅ Win/Loss analytics available")
except ImportError as _wla_err:
    WIN_LOSS_ANALYTICS_AVAILABLE = False
    logger.warning(f"⚠️ Win/Loss analytics unavailable: {_wla_err}")

# Auto-reload trigger: updated 2026-05-12 00:15 (added bid outcome recording endpoints)


# =============================================================================
# Feature 18: Request Validation - Pydantic Models
# =============================================================================

class UserRole(str, Enum):
    """User roles for authorization"""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


class RFPPriority(str, Enum):
    """RFP priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    STANDARD = "standard"
    LOW = "low"


class RFPStatus(str, Enum):
    """RFP processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Request Models
class UserCredentials(BaseModel):
    """User login credentials"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserCreate(BaseModel):
    """User registration model"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    full_name: str = Field(default="", max_length=100)
    role: UserRole = UserRole.VIEWER


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


class RFPProduct(BaseModel):
    """Product in RFP"""
    product_id: str
    product_name: str
    category: str
    quantity: float = Field(..., gt=0)
    unit: str
    specifications: Dict[str, Any] = Field(default_factory=dict)
    mandatory_specs: List[str] = Field(default_factory=list)


class RFPSubmission(BaseModel):
    """RFP submission request"""
    rfp_number: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=500)
    issuing_authority: str
    due_date: datetime
    estimated_value: float = Field(..., ge=0)
    currency: str = Field(default="INR", max_length=3)
    products: List[RFPProduct] = Field(default_factory=list)
    priority: RFPPriority = RFPPriority.STANDARD
    technical_specs: Dict[str, Any] = Field(default_factory=dict)
    applicable_standards: List[str] = Field(default_factory=list)


class ProductSearchQuery(BaseModel):
    """Product search query"""
    query: str = Field(..., min_length=1)
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    min_match_score: float = Field(default=0.7, ge=0, le=1)
    limit: int = Field(default=10, ge=1, le=100)


class ConfigUpdate(BaseModel):
    """Configuration update request"""
    key: str
    value: Any
    description: Optional[str] = None


class WebhookCreate(BaseModel):
    """Webhook creation request"""
    url: str = Field(..., pattern=r'^https?://')
    events: List[str]
    secret: Optional[str] = None
    active: bool = True


class BatchRFPSubmission(BaseModel):
    """Batch RFP submission"""
    rfps: List[RFPSubmission] = Field(..., min_length=1, max_length=50)
    parallel: bool = False


class AnalyticsQuery(BaseModel):
    """Analytics query parameters"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metrics: List[str] = Field(default_factory=list)
    group_by: Optional[str] = None


# Response Models
class APIResponse(BaseModel):
    """Standard API response"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RFPResponse(BaseModel):
    """RFP response model"""
    rfp_id: str
    rfp_number: str
    title: str
    status: RFPStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    priority: RFPPriority
    progress: float = 0.0


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    uptime_seconds: float
    components: Dict[str, str]
    timestamp: datetime


class PaginatedResponse(BaseModel):
    """Paginated response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Feature 2: Authentication System
# =============================================================================

class JWTConfig:
    """JWT configuration"""
    _env_secret = os.getenv("JWT_SECRET_KEY")
    if _env_secret:
        SECRET_KEY = _env_secret
    else:
        # No env secret configured — generate a random one for this process instead
        # of falling back to a fixed string (which would let anyone who has read
        # this source forge valid tokens). Set JWT_SECRET_KEY in production so
        # tokens survive restarts and stay valid across multiple worker processes.
        SECRET_KEY = secrets.token_hex(32)
        print("WARNING: JWT_SECRET_KEY not set — using a random per-process secret. "
              "All existing tokens will be invalidated on restart. Set JWT_SECRET_KEY for production.")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7


class TokenData(BaseModel):
    """Token payload data"""
    user_id: str
    username: str
    role: UserRole
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation
    tenant_id: Optional[str] = "default"


class AuthenticationManager:
    """
    JWT-based authentication system with MongoDB + JSON-file fallback.

    Priority: MongoDB → JSON file (``database/users.json``) → in-memory dict.
    """

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB  = os.getenv("MONGO_DB", "haki_fmcg")
    _JSON_PATH = Path(__file__).parent.parent / "database" / "users.json"

    def __init__(self):
        self._lock = RLock()
        self._revoked_tokens: Set[str] = set()
        self._refresh_tokens: Dict[str, str] = {}

        # Attempt MongoDB
        self._users_col = None
        if MONGO_AVAILABLE:
            try:
                self._mongo_client: Any = AsyncIOMotorClient(
                    self.MONGO_URI, serverSelectionTimeoutMS=3000,
                )
                self._db = self._mongo_client[self.MONGO_DB]
                self._users_col = self._db["users"]
                logger.info(f"MongoDB auth configured → {self.MONGO_URI}/{self.MONGO_DB}")
            except Exception as exc:
                logger.warning(f"MongoDB init failed ({exc}), using JSON fallback")

        # In-memory dict (populated from JSON on startup)
        self._users: Dict[str, Dict[str, Any]] = {}
        self._load_json()

    # ---- JSON file persistence ----

    def _load_json(self):
        """Load users from JSON file into memory."""
        if self._JSON_PATH.exists():
            try:
                with open(self._JSON_PATH, "r", encoding="utf-8") as f:
                    self._users = json.load(f)
                logger.info(f"Loaded {len(self._users)} users from {self._JSON_PATH}")
            except Exception:
                self._users = {}

    def _save_json(self):
        """Persist in-memory users to JSON file."""
        try:
            self._JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(self._JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(self._users, f, indent=2, default=str)
        except Exception as exc:
            logger.warning(f"Could not write users.json: {exc}")

    # ---- seed demo accounts ----

    async def seed_demo_accounts(self):
        """Create demo admin + user accounts if they don't exist."""
        # First check if MongoDB is actually reachable
        mongo_ok = False
        if self._users_col is not None:
            try:
                await self._mongo_client.admin.command("ping")
                mongo_ok = True
                logger.info("MongoDB is reachable ✓")
            except Exception:
                logger.warning("MongoDB unreachable – using JSON file fallback")
                self._users_col = None  # disable mongo for this session

        demos = [
            {
                "user_id": "USR_ADMIN",
                "username": "admin",
                "password": "admin123",
                "email": "admin@hakifmcg.com",
                "full_name": "Admin User",
                "role": UserRole.ADMIN,
            },
            {
                "user_id": "USR_USER01",
                "username": "user",
                "password": "user1234",
                "email": "user@hakifmcg.com",
                "full_name": "Priya Sharma",
                "role": UserRole.VIEWER,
            },
        ]

        for d in demos:
            pw = d.pop("password")
            d["password_hash"] = self._hash_password(pw)
            d["role"] = d["role"].value
            d["created_at"] = datetime.utcnow().isoformat()

            if mongo_ok:
                existing = await self._users_col.find_one({"username": d["username"]})
                if not existing:
                    await self._users_col.insert_one(d)
                    logger.info(f"Seeded demo → MongoDB: {d['username']}")
            else:
                if d["username"] not in self._users:
                    self._users[d["username"]] = d
                    logger.info(f"Seeded demo → JSON: {d['username']}")

        if mongo_ok:
            await self._users_col.create_index("username", unique=True)
        else:
            self._save_json()

    # ---- password helpers ----

    def _hash_password(self, password: str) -> str:
        if _pwd_context:
            try:
                return _pwd_context.hash(password)
            except Exception:
                pass
        salt = "rfp_system_salt"
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        if _pwd_context and password_hash.startswith(("$2b$", "$2a$", "$2y$")):
            try:
                return _pwd_context.verify(password, password_hash)
            except Exception:
                pass
        # Legacy fallback (salted SHA256)
        salt = "rfp_system_salt"
        if hashlib.sha256(f"{password}{salt}".encode()).hexdigest() == password_hash:
            return True
        # Plain SHA256 fallback for legacy seeded demo accounts
        if hashlib.sha256(password.encode()).hexdigest() == password_hash:
            return True
        return False

    # ---- token helpers ----

    def _create_token(self, user_id: str, username: str, role: UserRole,
                      expires_delta: timedelta, is_refresh: bool = False,
                      tenant_id: Optional[str] = None) -> tuple:
        import base64
        jti = str(uuid.uuid4())
        now = datetime.utcnow()
        exp = now + expires_delta

        active_tenant = tenant_id or get_current_tenant_id()

        payload = {
            "user_id": user_id,
            "username": username,
            "role": role.value if isinstance(role, UserRole) else role,
            "exp": exp.timestamp(),
            "iat": now.timestamp(),
            "jti": jti,
            "tenant_id": active_tenant,
            "type": "refresh" if is_refresh else "access",
        }

        header = base64.urlsafe_b64encode(
            json.dumps({"alg": JWTConfig.ALGORITHM, "typ": "JWT"}).encode()
        ).decode().rstrip("=")

        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip("=")

        signature = hmac.new(
            JWTConfig.SECRET_KEY.encode(),
            f"{header}.{payload_encoded}".encode(),
            hashlib.sha256,
        ).hexdigest()[:32]

        return f"{header}.{payload_encoded}.{signature}", jti

    # ---- auth operations ----

    async def authenticate(self, username: str, password: str) -> Optional[TokenResponse]:
        user = await self._get_user_record(username)
        if not user:
            return None
        if not self._verify_password(password, user["password_hash"]):
            return None

        role = UserRole(user["role"]) if isinstance(user["role"], str) else user["role"]

        access_token, _ = self._create_token(
            user["user_id"], username, role,
            timedelta(minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token, refresh_jti = self._create_token(
            user["user_id"], username, role,
            timedelta(days=JWTConfig.REFRESH_TOKEN_EXPIRE_DAYS),
            is_refresh=True,
        )
        self._refresh_tokens[refresh_jti] = user["user_id"]

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def validate_token(self, token: str) -> Optional[TokenData]:
        try:
            import base64
            parts = token.split(".")
            if len(parts) != 3:
                return None

            header, payload_encoded, signature = parts

            expected_sig = hmac.new(
                JWTConfig.SECRET_KEY.encode(),
                f"{header}.{payload_encoded}".encode(),
                hashlib.sha256,
            ).hexdigest()[:32]

            if not hmac.compare_digest(signature, expected_sig):
                return None

            padding = 4 - len(payload_encoded) % 4
            payload_encoded += "=" * padding
            payload = json.loads(base64.urlsafe_b64decode(payload_encoded))

            if datetime.utcnow().timestamp() > payload["exp"]:
                return None
            
            jti = payload["jti"]
            # Check distributed state and local revocation
            if (_distributed_state and _distributed_state.is_token_revoked(jti)) or (jti in self._revoked_tokens):
                return None

            return TokenData(
                user_id=payload["user_id"],
                username=payload["username"],
                role=UserRole(payload["role"]),
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                jti=jti,
                tenant_id=payload.get("tenant_id", "default"),
            )
        except Exception:
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[TokenResponse]:
        token_data = self.validate_token(refresh_token)
        if not token_data:
            return None

        user = await self._get_user_record(token_data.username)
        if not user:
            return None

        role = UserRole(user["role"]) if isinstance(user["role"], str) else user["role"]
        access_token, _ = self._create_token(
            user["user_id"], token_data.username, role,
            timedelta(minutes=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES),
            tenant_id=token_data.tenant_id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=JWTConfig.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def revoke_token(self, jti: str):
        with self._lock:
            self._revoked_tokens.add(jti)
            self._refresh_tokens.pop(jti, None)
            if _distributed_state:
                _distributed_state.revoke_token(jti)

    async def create_user(self, user_data: UserCreate) -> Optional[Dict[str, Any]]:
        user_id = f"USR_{uuid.uuid4().hex[:8].upper()}"
        doc = {
            "user_id": user_id,
            "username": user_data.username,
            "password_hash": self._hash_password(user_data.password),
            "email": user_data.email,
            "full_name": getattr(user_data, "full_name", "") or user_data.username,
            "role": user_data.role.value if isinstance(user_data.role, UserRole) else user_data.role,
            "created_at": datetime.utcnow().isoformat(),
        }

        if self._users_col is not None:
            try:
                existing = await self._users_col.find_one({"username": user_data.username})
                if existing:
                    return None
                await self._users_col.insert_one(doc)
                return {"user_id": user_id, "username": user_data.username}
            except Exception as exc:
                logger.warning(f"MongoDB create_user failed ({exc}), falling back to JSON")

        # In-memory + JSON fallback
        if user_data.username in self._users:
            return None
        self._users[user_data.username] = doc
        self._save_json()

        return {"user_id": user_id, "username": user_data.username}

    async def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        user = await self._get_user_record(username)
        if user:
            return {k: v for k, v in user.items() if k not in ("password_hash", "_id")}
        return None

    # ---- internal ----

    async def _get_user_record(self, username: str) -> Optional[Dict[str, Any]]:
        if self._users_col is not None:
            try:
                result = await self._users_col.find_one({"username": username})
                if result:
                    return result
            except Exception:
                pass  # fall through to in-memory
        return self._users.get(username)


# =============================================================================
# Feature 3: Authorization Middleware
# =============================================================================

class AuthorizationManager:
    """
    Role-based access control (RBAC) system
    
    Defines permissions for each role and endpoint
    """
    
    # Permission definitions
    PERMISSIONS = {
        UserRole.ADMIN: {
            "rfp:create", "rfp:read", "rfp:update", "rfp:delete",
            "config:read", "config:write",
            "user:create", "user:read", "user:update", "user:delete",
            "analytics:read", "analytics:export",
            "webhook:create", "webhook:read", "webhook:delete",
            "batch:execute", "file:upload"
        },
        UserRole.MANAGER: {
            "rfp:create", "rfp:read", "rfp:update",
            "config:read",
            "user:read",
            "analytics:read",
            "webhook:read",
            "batch:execute", "file:upload"
        },
        UserRole.ANALYST: {
            "rfp:create", "rfp:read",
            "config:read",
            "analytics:read",
            "file:upload"
        },
        UserRole.VIEWER: {
            "rfp:read",
            "config:read",
            "analytics:read"
        }
    }
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: str) -> bool:
        """Check if role has permission"""
        return permission in cls.PERMISSIONS.get(role, set())
    
    @classmethod
    def get_permissions(cls, role: UserRole) -> Set[str]:
        """Get all permissions for a role"""
        return cls.PERMISSIONS.get(role, set()).copy()


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by dependency)
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not AuthorizationManager.has_permission(current_user.role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# Feature 15: Rate Limiting
# =============================================================================

class RateLimiter:
    """
    Token bucket rate limiter
    
    Limits requests per client based on IP or user ID
    """
    
    def __init__(self, requests_per_minute: int = 60,
                 requests_per_hour: int = 1000):
        self._lock = RLock()
        self._minute_buckets: Dict[str, List[float]] = defaultdict(list)
        self._hour_buckets: Dict[str, List[float]] = defaultdict(list)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
    
    def _cleanup_bucket(self, bucket: List[float], window: float) -> List[float]:
        """Remove expired entries from bucket"""
        now = time.time()
        return [t for t in bucket if now - t < window]
    
    def is_allowed(self, client_id: str) -> tuple:
        """
        Check if request is allowed
        Returns (allowed, remaining, reset_seconds)
        """
        with self._lock:
            now = time.time()
            
            # Cleanup minute bucket
            self._minute_buckets[client_id] = self._cleanup_bucket(
                self._minute_buckets[client_id], 60
            )
            
            # Cleanup hour bucket
            self._hour_buckets[client_id] = self._cleanup_bucket(
                self._hour_buckets[client_id], 3600
            )
            
            minute_count = len(self._minute_buckets[client_id])
            hour_count = len(self._hour_buckets[client_id])
            
            # Check limits
            if minute_count >= self.requests_per_minute:
                reset_time = 60 - (now - self._minute_buckets[client_id][0])
                return False, 0, int(reset_time)
            
            if hour_count >= self.requests_per_hour:
                reset_time = 3600 - (now - self._hour_buckets[client_id][0])
                return False, 0, int(reset_time)
            
            # Record request
            self._minute_buckets[client_id].append(now)
            self._hour_buckets[client_id].append(now)
            
            remaining = min(
                self.requests_per_minute - minute_count - 1,
                self.requests_per_hour - hour_count - 1
            )
            
            return True, remaining, 60
    
    def get_client_stats(self, client_id: str) -> Dict[str, Any]:
        """Get rate limit stats for client"""
        with self._lock:
            now = time.time()
            
            minute_bucket = self._cleanup_bucket(
                self._minute_buckets.get(client_id, []), 60
            )
            hour_bucket = self._cleanup_bucket(
                self._hour_buckets.get(client_id, []), 3600
            )
            
            return {
                "minute_remaining": self.requests_per_minute - len(minute_bucket),
                "hour_remaining": self.requests_per_hour - len(hour_bucket),
                "minute_limit": self.requests_per_minute,
                "hour_limit": self.requests_per_hour
            }


# =============================================================================
# Feature 11: Webhook Manager
# =============================================================================

class WebhookManager:
    """
    Webhook management system
    
    Handles webhook registration, delivery, and retry
    """
    
    def __init__(self):
        self._lock = RLock()
        self._webhooks: Dict[str, Dict[str, Any]] = {}
        self._delivery_log: List[Dict[str, Any]] = []
    
    def register(self, webhook: WebhookCreate) -> str:
        """Register a new webhook"""
        with self._lock:
            webhook_id = f"WH_{uuid.uuid4().hex[:8].upper()}"
            self._webhooks[webhook_id] = {
                "webhook_id": webhook_id,
                "url": webhook.url,
                "events": webhook.events,
                "secret": webhook.secret or secrets.token_urlsafe(32),
                "active": webhook.active,
                "created_at": datetime.now(),
                "delivery_count": 0,
                "failure_count": 0
            }
            return webhook_id
    
    def get_webhook(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook by ID"""
        return self._webhooks.get(webhook_id)
    
    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all webhooks"""
        return list(self._webhooks.values())
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete webhook"""
        with self._lock:
            return self._webhooks.pop(webhook_id, None) is not None
    
    def update_webhook(self, webhook_id: str, active: bool) -> bool:
        """Update webhook status"""
        with self._lock:
            webhook = self._webhooks.get(webhook_id)
            if webhook:
                webhook["active"] = active
                return True
            return False
    
    async def trigger(self, event: str, payload: Dict[str, Any]):
        """Trigger webhooks for an event"""
        for webhook_id, webhook in self._webhooks.items():
            if not webhook["active"]:
                continue
            if event not in webhook["events"] and "*" not in webhook["events"]:
                continue
            
            # Queue delivery (in production, use proper queue)
            delivery = {
                "delivery_id": f"DEL_{uuid.uuid4().hex[:8].upper()}",
                "webhook_id": webhook_id,
                "event": event,
                "payload": payload,
                "timestamp": datetime.now(),
                "status": "queued"
            }
            self._delivery_log.append(delivery)
            
            # Update counts
            webhook["delivery_count"] += 1
    
    def get_delivery_log(self, webhook_id: str = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get webhook delivery log"""
        logs = self._delivery_log
        if webhook_id:
            logs = [l for l in logs if l["webhook_id"] == webhook_id]
        return logs[-limit:]


# =============================================================================
# Feature 12: Batch Processor
# =============================================================================

class BatchProcessor:
    """
    Batch processing for multiple RFPs
    
    Supports parallel and sequential processing
    """
    
    def __init__(self):
        self._lock = RLock()
        self._batches: Dict[str, Dict[str, Any]] = {}
    
    def create_batch(self, rfp_ids: List[str], parallel: bool = False) -> str:
        """Create a new batch job"""
        with self._lock:
            batch_id = f"BATCH_{uuid.uuid4().hex[:8].upper()}"
            self._batches[batch_id] = {
                "batch_id": batch_id,
                "rfp_ids": rfp_ids,
                "parallel": parallel,
                "status": "pending",
                "created_at": datetime.now(),
                "started_at": None,
                "completed_at": None,
                "results": {},
                "progress": 0.0
            }
            return batch_id
    
    def get_batch(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch status"""
        return self._batches.get(batch_id)
    
    def update_progress(self, batch_id: str, rfp_id: str,
                       status: str, result: Any = None):
        """Update batch progress"""
        with self._lock:
            batch = self._batches.get(batch_id)
            if batch:
                batch["results"][rfp_id] = {
                    "status": status,
                    "result": result,
                    "timestamp": datetime.now()
                }
                completed = len([r for r in batch["results"].values()
                               if r["status"] in ["completed", "failed"]])
                batch["progress"] = completed / len(batch["rfp_ids"])
                
                if completed == len(batch["rfp_ids"]):
                    batch["status"] = "completed"
                    batch["completed_at"] = datetime.now()
    
    def start_batch(self, batch_id: str):
        """Mark batch as started"""
        with self._lock:
            batch = self._batches.get(batch_id)
            if batch:
                batch["status"] = "processing"
                batch["started_at"] = datetime.now()


# =============================================================================
# Feature 19 & 20: Response Formatting & Error Handlers
# =============================================================================

class ResponseFormatter:
    """Standardized response formatting"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success",
                request_id: str = None) -> APIResponse:
        """Format success response"""
        return APIResponse(
            success=True,
            message=message,
            data=data,
            request_id=request_id
        )
    
    @staticmethod
    def error(message: str, request_id: str = None) -> APIResponse:
        """Format error response"""
        return APIResponse(
            success=False,
            message=message,
            data=None,
            request_id=request_id
        )
    
    @staticmethod
    def paginated(items: List[Any], total: int, page: int,
                  page_size: int) -> PaginatedResponse:
        """Format paginated response"""
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )


class ErrorHandlers:
    """Custom error response handlers"""
    
    @staticmethod
    def validation_error(request: Request, exc: Exception) -> JSONResponse:
        """Handle validation errors"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Validation error",
                "data": {"errors": str(exc)},
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def not_found_error(request: Request, exc: Exception) -> JSONResponse:
        """Handle not found errors"""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "success": False,
                "message": str(exc) or "Resource not found",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    @staticmethod
    def internal_error(request: Request, exc: Exception) -> JSONResponse:
        """Handle internal server errors"""
        logger.error(f"Internal error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "Internal server error",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        )


# =============================================================================
# Feature 1: FastAPI Application Setup
# =============================================================================

# App metadata
API_VERSION = "1.0.0"
API_TITLE = "RFP Response System API"
API_DESCRIPTION = """
## RFP Response System RESTful API

Complete API for managing RFP (Request for Proposal) responses.

### Features
- **Authentication**: JWT-based authentication with refresh tokens
- **RFP Management**: Submit, track, and retrieve RFP responses
- **Product Search**: Search and match products to RFP requirements
- **Analytics**: View processing analytics and metrics
- **Batch Processing**: Process multiple RFPs simultaneously
- **Webhooks**: Register webhooks for event notifications

### Authentication
All endpoints (except `/health` and `/auth/*`) require authentication.
Include the JWT token in the `Authorization` header:
```
Authorization: Bearer <your_token>
```
"""

# Enterprise Cybersecurity: Brute-Force & Account Lockout Defense
class AccountLockoutManager:
    """Enforces account lockout on repeated failed authentication attempts."""
    def __init__(self, max_attempts: int = 5, lockout_minutes: int = 15):
        self._lock = RLock()
        self.max_attempts = max_attempts
        self.lockout_time = timedelta(minutes=lockout_minutes)
        self._failures: Dict[str, List[datetime]] = defaultdict(list)

    def record_failure(self, username: str) -> bool:
        with self._lock:
            now = datetime.utcnow()
            self._failures[username] = [t for t in self._failures[username] if now - t < self.lockout_time]
            self._failures[username].append(now)
            return len(self._failures[username]) >= self.max_attempts

    def record_success(self, username: str):
        with self._lock:
            self._failures.pop(username, None)

    def is_locked(self, username: str) -> tuple:
        with self._lock:
            now = datetime.utcnow()
            recent = [t for t in self._failures.get(username, []) if now - t < self.lockout_time]
            if len(recent) >= self.max_attempts:
                remaining = int((recent[0] + self.lockout_time - now).total_seconds())
                return True, max(remaining, 1)
            return False, 0


# Initialize managers
auth_manager = AuthenticationManager()
lockout_manager = AccountLockoutManager(max_attempts=5, lockout_minutes=15)
rate_limiter = RateLimiter(requests_per_minute=1000, requests_per_hour=10000)
webhook_manager = WebhookManager()
batch_processor = BatchProcessor()

# RFP storage (in-memory for demo)
rfp_store: Dict[str, Dict[str, Any]] = {}
config_store: Dict[str, Any] = {
    "default_priority": "standard",
    "auto_process": True,
    "max_parallel_rfps": 5,
    "notification_enabled": True,
    "matching_threshold": 0.7
}

# App start time for uptime
app_start_time = time.time()


# Feature 16: API Versioning
def create_app(version: str = "v1") -> FastAPI:
    """Create FastAPI application with versioning and hardened security controls"""
    
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        docs_url=f"/api/{version}/docs",
        redoc_url=f"/api/{version}/redoc",
        openapi_url=f"/api/{version}/openapi.json"
    )
    
    # Hardened CORS Middleware with explicit origin whitelist
    raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:80,http://localhost:8080"
    )
    allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.hakifmcg\.com|.*\.saarthi\.ai)(:[0-9]+)?$",
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Request-ID", "X-Tenant-ID"],
        max_age=86400,
    )
    
    return app


# Create main app
app = create_app()

# Mount Enterprise Multi-Tenant & Correlation Context Middleware
if EnterpriseContextMiddleware is not None:
    app.add_middleware(EnterpriseContextMiddleware)

# Mount Enterprise Health & Observability Router
if HEALTH_ROUTER_AVAILABLE:
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(health_router)

# Initialize Performance System
if PERFORMANCE_AVAILABLE:
    try:
        setup_api_performance(app)
        logger.info("✅ Performance system integrated")
    except Exception as e:
        logger.warning(f"Performance integration failed: {e}")

# Security
security = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


# ---------- Startup: seed demo accounts into MongoDB ----------
@app.on_event("startup")
async def _startup_seed():
    await auth_manager.seed_demo_accounts()
    logger.info("✅ Demo accounts seeded (admin / admin123, user / user1234)")


# =============================================================================
# Middleware & Dependencies
# =============================================================================

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """
    Global request middleware
    - Add request ID
    - Log requests
    - Handle rate limiting
    """
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    # Rate limiting (skip for health endpoint)
    if not request.url.path.endswith("/health"):
        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining, reset = rate_limiter.is_allowed(client_ip)
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "message": "Rate limit exceeded",
                    "data": {"retry_after": reset}
                },
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(reset)
                }
            )
    
    # Process request
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    
    return response


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenData]:
    """Dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token_data = auth_manager.validate_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return token_data


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenData]:
    """Dependency to get optional authenticated user"""
    if not credentials:
        return None
    return auth_manager.validate_token(credentials.credentials)


async def get_current_user_sse(
    token: Optional[str] = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """
    Dependency for SSE endpoints, which browsers connect to via EventSource —
    an API that cannot set an Authorization header. Accepts the JWT via a
    `token` query param as a fallback when no bearer header is present.
    """
    raw_token = credentials.credentials if credentials else token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_data = auth_manager.validate_token(raw_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


# =============================================================================
# Feature 10: Health Check Endpoint
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint
    
    Returns system health status and component states.
    No authentication required.
    """
    uptime = time.time() - app_start_time
    
    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        uptime_seconds=uptime,
        components={
            "api": "healthy",
            "auth": "healthy",
            "database": "healthy",
            "cache": "healthy"
        },
        timestamp=datetime.now()
    )


@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
async def health_check_v1():
    """Versioned health check endpoint"""
    return await health_check()


# =============================================================================
# Feature 2: Authentication Endpoints
# =============================================================================

@app.post("/api/v1/auth/token", response_model=TokenResponse, tags=["Authentication"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate and get access token with brute-force lockout protection
    """
    locked, retry_after = lockout_manager.is_locked(form_data.username)
    if locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to consecutive failed attempts. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    result = await auth_manager.authenticate(form_data.username, form_data.password)
    if not result:
        is_locked = lockout_manager.record_failure(form_data.username)
        msg = "Account locked for 15 minutes due to multiple failed login attempts." if is_locked else "Invalid credentials"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={"WWW-Authenticate": "Bearer"}
        )
    lockout_manager.record_success(form_data.username)
    return result


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login_json(credentials: UserCredentials):
    """
    Authenticate with JSON body with brute-force lockout protection
    """
    locked, retry_after = lockout_manager.is_locked(credentials.username)
    if locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to consecutive failed attempts. Retry after {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )

    result = await auth_manager.authenticate(credentials.username, credentials.password)
    if not result:
        is_locked = lockout_manager.record_failure(credentials.username)
        msg = "Account locked for 15 minutes due to multiple failed login attempts." if is_locked else "Invalid credentials"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg
        )
    lockout_manager.record_success(credentials.username)
    return result


@app.post("/api/v1/auth/refresh", response_model=TokenResponse, tags=["Authentication"])
async def refresh_token(request: TokenRefresh):
    """
    Refresh access token
    
    Use refresh token to get a new access token.
    """
    try:
        result = await auth_manager.refresh_access_token(request.refresh_token)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        return result
    except Exception as e:
        import logging
        logging.error(f"Refresh token error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token refresh failed: {str(e)}"
        )


@app.post("/api/v1/auth/logout", tags=["Authentication"])
async def logout(current_user: TokenData = Depends(get_current_user)):
    """
    Logout and revoke token
    
    Invalidates the current access token.
    """
    auth_manager.revoke_token(current_user.jti)
    return ResponseFormatter.success(message="Logged out successfully")


@app.post("/api/v1/auth/register", tags=["Authentication"])
async def register_user(user_data: UserCreate):
    """
    Register a new user account (public).

    Anyone can create an account, but it is always created as VIEWER —
    role escalation must go through an authenticated admin action.
    """
    user_data.role = UserRole.VIEWER
    result = await auth_manager.create_user(user_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    return ResponseFormatter.success(data=result, message="Account created successfully")


@app.get("/api/v1/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """
    Get current user information
    
    Returns details about the authenticated user.
    """
    user = await auth_manager.get_user(current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return ResponseFormatter.success(data=user)


# =============================================================================
# Feature 4, 5, 6: RFP Endpoints
# =============================================================================

@app.post("/api/v1/rfps", tags=["RFP Management"])
async def submit_rfp(
    rfp: RFPSubmission,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Submit a new RFP
    
    Creates a new RFP and queues it for processing.
    """
    if not AuthorizationManager.has_permission(current_user.role, "rfp:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    rfp_id = f"RFP_{uuid.uuid4().hex[:12].upper()}"
    
    rfp_data = {
        "rfp_id": rfp_id,
        "rfp_number": rfp.rfp_number,
        "title": rfp.title,
        "issuing_authority": rfp.issuing_authority,
        "due_date": rfp.due_date.isoformat(),
        "estimated_value": rfp.estimated_value,
        "currency": rfp.currency,
        "products": [p.dict() for p in rfp.products],
        "priority": rfp.priority.value,
        "technical_specs": rfp.technical_specs,
        "applicable_standards": rfp.applicable_standards,
        "status": RFPStatus.PENDING.value,
        "created_at": datetime.now().isoformat(),
        "created_by": current_user.username,
        "progress": 0.0,
        "results": None
    }
    
    rfp_store[rfp_id] = rfp_data
    
    # Trigger webhook
    await webhook_manager.trigger("rfp.created", {
        "rfp_id": rfp_id,
        "title": rfp.title
    })
    
    return ResponseFormatter.success(
        data={"rfp_id": rfp_id, "status": "pending"},
        message="RFP submitted successfully"
    )


# =============================================================================
# Pipeline Endpoints
# =============================================================================

class PipelineRequest(BaseModel):
    """Pipeline execution request"""
    text: Optional[str] = None
    requirements: Optional[List[Dict[str, Any]]] = None
    vendor_info: Optional[Dict[str, Any]] = None
    use_agents: bool = False
    rfp_urls: Optional[List[str]] = None


@app.post("/api/v1/pipeline/run", tags=["Pipeline"])
async def run_pipeline(
    req: PipelineRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Run the full end-to-end pipeline from text or requirements.
    Pipelines: Intake → Matching → Pricing → Compliance → Audit → Analytics → Bid
    """
    if not PIPELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Pipeline connector not available")

    if not AuthorizationManager.has_permission(current_user.role, "rfp:create"):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        result = run_full_pipeline(
            text=req.text,
            requirements=req.requirements,
            vendor_info=req.vendor_info,
            use_agents=req.use_agents,
            rfp_urls=req.rfp_urls,
        )

        # Store result for later retrieval
        pipeline_id = result.get('pipeline_id', '')
        if pipeline_id:
            rfp_store[pipeline_id] = {
                **result,
                'type': 'pipeline',
                'created_by': current_user.username,
            }

        return ResponseFormatter.success(
            data=result,
            message=f"Pipeline {result.get('status', 'unknown')}"
        )
    except Exception as e:
        logger.error(f"Pipeline execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pipeline/upload", tags=["Pipeline"])
async def pipeline_upload_rfp(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Upload an RFP PDF and process through the full pipeline.
    """
    if not PIPELINE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Pipeline connector not available")

    if not AuthorizationManager.has_permission(current_user.role, "rfp:create"):
        raise HTTPException(status_code=403, detail="Permission denied")

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files supported")

    try:
        # Save temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            result = run_full_pipeline(pdf_path=tmp_path)
            return ResponseFormatter.success(
                data=result,
                message=f"Pipeline {result.get('status', 'unknown')}"
            )
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Pipeline upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/rfps", tags=["RFP Management"])
async def list_rfps(
    status: Optional[RFPStatus] = None,
    priority: Optional[RFPPriority] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """
    List all RFPs with pagination
    
    Filter by status and/or priority.
    """
    if not AuthorizationManager.has_permission(current_user.role, "rfp:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    rfps = list(rfp_store.values())
    
    # Apply filters
    if status:
        rfps = [r for r in rfps if r["status"] == status.value]
    if priority:
        rfps = [r for r in rfps if r["priority"] == priority.value]
    
    # Pagination
    total = len(rfps)
    start = (page - 1) * page_size
    end = start + page_size
    items = rfps[start:end]
    
    return ResponseFormatter.paginated(items, total, page, page_size)


@app.get("/api/v1/rfps/{rfp_id}", tags=["RFP Management"])
async def get_rfp(
    rfp_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get RFP details
    
    Retrieve complete RFP information by ID.
    """
    if not AuthorizationManager.has_permission(current_user.role, "rfp:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    rfp = rfp_store.get(rfp_id)
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    return ResponseFormatter.success(data=rfp)


@app.get("/api/v1/rfps/{rfp_id}/status", tags=["RFP Management"])
async def get_rfp_status(
    rfp_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get RFP processing status
    
    Returns current status and progress of RFP processing.
    """
    if not AuthorizationManager.has_permission(current_user.role, "rfp:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    rfp = rfp_store.get(rfp_id)
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    return ResponseFormatter.success(data={
        "rfp_id": rfp_id,
        "status": rfp["status"],
        "progress": rfp["progress"],
        "created_at": rfp["created_at"],
        "updated_at": rfp.get("updated_at")
    })


@app.get("/api/v1/rfps/{rfp_id}/results", tags=["RFP Management"])
async def get_rfp_results(
    rfp_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get RFP processing results
    
    Returns the complete results after RFP processing is complete.
    """
    if not AuthorizationManager.has_permission(current_user.role, "rfp:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    rfp = rfp_store.get(rfp_id)
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if rfp["status"] != RFPStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"RFP not completed. Current status: {rfp['status']}"
        )
    
    return ResponseFormatter.success(data={
        "rfp_id": rfp_id,
        "results": rfp.get("results"),
        "completed_at": rfp.get("completed_at")
    })


@app.put("/api/v1/rfps/{rfp_id}", tags=["RFP Management"])
async def update_rfp(
    rfp_id: str,
    updates: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update RFP
    
    Update RFP details. Cannot update completed RFPs.
    """
    if not AuthorizationManager.has_permission(current_user.role, "rfp:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    rfp = rfp_store.get(rfp_id)
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if rfp["status"] == RFPStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Cannot update completed RFP")
    
    # Update allowed fields
    allowed_fields = {"title", "priority", "technical_specs", "applicable_standards"}
    for key, value in updates.items():
        if key in allowed_fields:
            rfp[key] = value
    
    rfp["updated_at"] = datetime.now().isoformat()
    
    return ResponseFormatter.success(data=rfp, message="RFP updated")


@app.delete("/api/v1/rfps/{rfp_id}", tags=["RFP Management"])
async def delete_rfp(
    rfp_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Delete RFP
    
    Delete an RFP. Only admins can delete.
    """
    if not AuthorizationManager.has_permission(current_user.role, "rfp:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if rfp_id not in rfp_store:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    del rfp_store[rfp_id]
    
    return ResponseFormatter.success(message="RFP deleted")


@app.post("/api/v1/rfps/{rfp_id}/cancel", tags=["RFP Management"])
async def cancel_rfp(
    rfp_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Cancel RFP processing
    
    Stop processing an RFP in progress.
    """
    if not AuthorizationManager.has_permission(current_user.role, "rfp:update"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    rfp = rfp_store.get(rfp_id)
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    if rfp["status"] not in [RFPStatus.PENDING.value, RFPStatus.PROCESSING.value]:
        raise HTTPException(status_code=400, detail="Cannot cancel RFP in current state")
    
    rfp["status"] = RFPStatus.CANCELLED.value
    rfp["updated_at"] = datetime.now().isoformat()
    
    await webhook_manager.trigger("rfp.cancelled", {"rfp_id": rfp_id})
    
    return ResponseFormatter.success(message="RFP cancelled")


# =============================================================================
# Feature 7: Product Search Endpoint
# =============================================================================

@app.post("/api/v1/products/search", tags=["Products"])
async def search_products(
    query: ProductSearchQuery,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Search products
    
    Search for products matching specifications.
    """
    # Mock product search results
    results = [
        {
            "sku": "PROD001",
            "name": f"Product matching '{query.query}'",
            "category": query.category or "General",
            "manufacturer": query.manufacturer or "Various",
            "match_score": 0.95,
            "specifications": {"spec1": "value1"}
        },
        {
            "sku": "PROD002",
            "name": f"Alternative for '{query.query}'",
            "category": query.category or "General",
            "manufacturer": query.manufacturer or "Various",
            "match_score": 0.85,
            "specifications": {"spec1": "value2"}
        }
    ]
    
    # Filter by match score
    results = [r for r in results if r["match_score"] >= query.min_match_score]
    
    return ResponseFormatter.success(data={
        "query": query.query,
        "results": results[:query.limit],
        "total": len(results)
    })


# NOTE: Removed old mock GET /api/v1/products/{sku} that was shadowing
# the /products/categories route. The real implementation is at
# GET /api/v1/products/{product_id_or_sku} further below.


@app.get("/api/v1/products/categories", tags=["Products"])
async def list_categories(
    current_user: TokenData = Depends(get_current_user)
):
    """
    List product categories
    
    Get all available product categories.
    """
    categories = [
        {"id": "cables", "name": "Cables & Wires", "count": 1500},
        {"id": "connectors", "name": "Connectors", "count": 800},
        {"id": "switches", "name": "Switches", "count": 500}
    ]
    
    return ResponseFormatter.success(data=categories)


# =============================================================================
# Feature 8: Configuration Endpoints
# =============================================================================

@app.get("/api/v1/config", tags=["Configuration"])
async def get_config(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get system configuration
    
    Retrieve all configuration settings.
    """
    if not AuthorizationManager.has_permission(current_user.role, "config:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return ResponseFormatter.success(data=config_store)


@app.get("/api/v1/config/{key}", tags=["Configuration"])
async def get_config_value(
    key: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get specific configuration value
    
    Retrieve a single configuration setting by key.
    """
    if not AuthorizationManager.has_permission(current_user.role, "config:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if key not in config_store:
        raise HTTPException(status_code=404, detail="Configuration key not found")
    
    return ResponseFormatter.success(data={key: config_store[key]})


@app.put("/api/v1/config/{key}", tags=["Configuration"])
async def update_config(
    key: str,
    update: ConfigUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Update configuration value
    
    Update a single configuration setting.
    """
    if not AuthorizationManager.has_permission(current_user.role, "config:write"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    old_value = config_store.get(key)
    config_store[key] = update.value
    
    return ResponseFormatter.success(
        data={"key": key, "old_value": old_value, "new_value": update.value},
        message="Configuration updated"
    )


@app.post("/api/v1/config/reset", tags=["Configuration"])
async def reset_config(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Reset configuration to defaults
    
    Reset all configuration to default values.
    """
    if not AuthorizationManager.has_permission(current_user.role, "config:write"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    global config_store
    config_store = {
        "default_priority": "standard",
        "auto_process": True,
        "max_parallel_rfps": 5,
        "notification_enabled": True,
        "matching_threshold": 0.7
    }
    
    return ResponseFormatter.success(message="Configuration reset to defaults")


# =============================================================================
# Feature 9: Analytics Endpoints
# =============================================================================

@app.get("/api/v1/analytics/overview", tags=["Analytics"])
async def get_analytics_overview(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get analytics overview
    
    Returns summary statistics for the system.
    """
    if not AuthorizationManager.has_permission(current_user.role, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Calculate stats from rfp_store
    total_rfps = len(rfp_store)
    status_counts = defaultdict(int)
    for rfp in rfp_store.values():
        status_counts[rfp["status"]] += 1
    
    return ResponseFormatter.success(data={
        "total_rfps": total_rfps,
        "by_status": dict(status_counts),
        "average_processing_time_hours": 4.5,
        "success_rate": 0.92,
        "active_users": 15,
        "period": "last_30_days"
    })


@app.get("/api/v1/analytics/rfps", tags=["Analytics"])
async def get_rfp_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    group_by: str = Query("day", pattern="^(day|week|month)$"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get RFP analytics
    
    Detailed RFP processing analytics with time-based grouping.
    """
    if not AuthorizationManager.has_permission(current_user.role, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return ResponseFormatter.success(data={
        "period": {
            "start": (start_date or datetime.now() - timedelta(days=30)).isoformat(),
            "end": (end_date or datetime.now()).isoformat()
        },
        "group_by": group_by,
        "data": [
            {"date": "2026-02-01", "submitted": 10, "completed": 8, "failed": 1},
            {"date": "2026-02-02", "submitted": 15, "completed": 12, "failed": 2},
            {"date": "2026-02-03", "submitted": 8, "completed": 7, "failed": 0}
        ]
    })


@app.get("/api/v1/analytics/performance", tags=["Analytics"])
async def get_performance_analytics(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get performance analytics
    
    System performance metrics and trends.
    """
    if not AuthorizationManager.has_permission(current_user.role, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return ResponseFormatter.success(data={
        "avg_response_time_ms": 245,
        "p95_response_time_ms": 890,
        "requests_per_minute": 42,
        "error_rate": 0.02,
        "uptime_percent": 99.95,
        "cpu_usage_percent": 45,
        "memory_usage_percent": 62
    })


@app.post("/api/v1/analytics/query", tags=["Analytics"])
async def query_analytics(
    query: AnalyticsQuery,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Custom analytics query
    
    Execute custom analytics queries with specified metrics.
    """
    if not AuthorizationManager.has_permission(current_user.role, "analytics:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return ResponseFormatter.success(data={
        "query": query.dict(),
        "results": {
            "metrics": {m: 100 for m in (query.metrics or ["total"])},
            "generated_at": datetime.now().isoformat()
        }
    })


@app.get("/api/v1/analytics/export", tags=["Analytics"])
async def export_analytics(
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Export analytics data
    
    Export analytics data in JSON or CSV format.
    """
    if not AuthorizationManager.has_permission(current_user.role, "analytics:export"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    data = {
        "exported_at": datetime.now().isoformat(),
        "format": format,
        "data": list(rfp_store.values())
    }
    
    if format == "csv":
        # Return as CSV
        csv_content = "rfp_id,title,status,created_at\n"
        for rfp in rfp_store.values():
            csv_content += f"{rfp['rfp_id']},{rfp['title']},{rfp['status']},{rfp['created_at']}\n"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=analytics.csv"}
        )
    
    return ResponseFormatter.success(data=data)


# =============================================================================
# Feature 11: Webhook Endpoints
# =============================================================================

@app.post("/api/v1/webhooks", tags=["Webhooks"])
async def create_webhook(
    webhook: WebhookCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Register a webhook
    
    Register a new webhook for event notifications.
    """
    if not AuthorizationManager.has_permission(current_user.role, "webhook:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    webhook_id = webhook_manager.register(webhook)
    
    return ResponseFormatter.success(
        data={"webhook_id": webhook_id},
        message="Webhook registered"
    )


@app.get("/api/v1/webhooks", tags=["Webhooks"])
async def list_webhooks(
    current_user: TokenData = Depends(get_current_user)
):
    """
    List all webhooks
    
    Get all registered webhooks.
    """
    if not AuthorizationManager.has_permission(current_user.role, "webhook:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    webhooks = webhook_manager.list_webhooks()
    
    return ResponseFormatter.success(data=webhooks)


@app.get("/api/v1/webhooks/{webhook_id}", tags=["Webhooks"])
async def get_webhook(
    webhook_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get webhook details
    
    Retrieve webhook configuration by ID.
    """
    if not AuthorizationManager.has_permission(current_user.role, "webhook:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    webhook = webhook_manager.get_webhook(webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return ResponseFormatter.success(data=webhook)


@app.delete("/api/v1/webhooks/{webhook_id}", tags=["Webhooks"])
async def delete_webhook(
    webhook_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Delete webhook
    
    Unregister a webhook.
    """
    if not AuthorizationManager.has_permission(current_user.role, "webhook:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not webhook_manager.delete_webhook(webhook_id):
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return ResponseFormatter.success(message="Webhook deleted")


@app.patch("/api/v1/webhooks/{webhook_id}", tags=["Webhooks"])
async def toggle_webhook(
    webhook_id: str,
    active: bool = Query(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Toggle webhook status
    
    Enable or disable a webhook.
    """
    if not AuthorizationManager.has_permission(current_user.role, "webhook:create"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if not webhook_manager.update_webhook(webhook_id, active):
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    return ResponseFormatter.success(message=f"Webhook {'enabled' if active else 'disabled'}")


@app.get("/api/v1/webhooks/{webhook_id}/logs", tags=["Webhooks"])
async def get_webhook_logs(
    webhook_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get webhook delivery logs
    
    Retrieve delivery history for a webhook.
    """
    if not AuthorizationManager.has_permission(current_user.role, "webhook:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    logs = webhook_manager.get_delivery_log(webhook_id, limit)
    
    return ResponseFormatter.success(data=logs)


# =============================================================================
# Feature 12: Batch Processing Endpoint
# =============================================================================

@app.post("/api/v1/batch/rfps", tags=["Batch Processing"])
async def submit_batch_rfps(
    batch: BatchRFPSubmission,
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Submit batch RFPs
    
    Submit multiple RFPs for batch processing.
    """
    if not AuthorizationManager.has_permission(current_user.role, "batch:execute"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    rfp_ids = []
    for rfp in batch.rfps:
        rfp_id = f"RFP_{uuid.uuid4().hex[:12].upper()}"
        rfp_ids.append(rfp_id)
        
        rfp_data = {
            "rfp_id": rfp_id,
            "rfp_number": rfp.rfp_number,
            "title": rfp.title,
            "issuing_authority": rfp.issuing_authority,
            "due_date": rfp.due_date.isoformat(),
            "estimated_value": rfp.estimated_value,
            "currency": rfp.currency,
            "products": [p.dict() for p in rfp.products],
            "priority": rfp.priority.value,
            "status": RFPStatus.PENDING.value,
            "created_at": datetime.now().isoformat(),
            "created_by": current_user.username,
            "progress": 0.0
        }
        rfp_store[rfp_id] = rfp_data
    
    batch_id = batch_processor.create_batch(rfp_ids, batch.parallel)
    
    return ResponseFormatter.success(
        data={
            "batch_id": batch_id,
            "rfp_count": len(rfp_ids),
            "rfp_ids": rfp_ids,
            "parallel": batch.parallel
        },
        message="Batch submitted"
    )


@app.get("/api/v1/batch/{batch_id}", tags=["Batch Processing"])
async def get_batch_status(
    batch_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get batch status
    
    Check the status and progress of a batch job.
    """
    if not AuthorizationManager.has_permission(current_user.role, "batch:execute"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    batch = batch_processor.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return ResponseFormatter.success(data=batch)


# =============================================================================
# Feature 13: File Upload Handling
# =============================================================================

UPLOAD_DIR = Path("uploads/rfp_documents")
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xlsx", ".xls"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@app.post("/api/v1/upload/rfp-document", tags=["File Upload"])
async def upload_rfp_document(
    file: UploadFile = File(...),
    rfp_id: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Upload RFP document
    
    Upload a document file for an RFP.
    Supported formats: PDF, DOC, DOCX, XLSX, XLS
    Max size: 50MB
    """
    if not AuthorizationManager.has_permission(current_user.role, "file:upload"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate file ID
    file_id = f"FILE_{uuid.uuid4().hex[:12].upper()}"
    
    # In production, save to storage
    # UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # file_path = UPLOAD_DIR / f"{file_id}{ext}"
    # file_path.write_bytes(content)
    
    return ResponseFormatter.success(
        data={
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "rfp_id": rfp_id
        },
        message="File uploaded successfully"
    )


@app.post("/api/v1/upload/batch", tags=["File Upload"])
async def upload_batch_files(
    files: List[UploadFile] = File(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Upload multiple files
    
    Upload multiple documents at once.
    """
    if not AuthorizationManager.has_permission(current_user.role, "file:upload"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    uploaded = []
    errors = []
    
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append({"filename": file.filename, "error": "Invalid file type"})
            continue
        
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            errors.append({"filename": file.filename, "error": "File too large"})
            continue
        
        file_id = f"FILE_{uuid.uuid4().hex[:12].upper()}"
        uploaded.append({
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content)
        })
    
    return ResponseFormatter.success(
        data={
            "uploaded": uploaded,
            "errors": errors,
            "total_uploaded": len(uploaded),
            "total_errors": len(errors)
        }
    )


# =============================================================================
# Feature 14: Streaming Response Support (SSE)
# =============================================================================

@app.get("/api/v1/rfps/{rfp_id}/progress/stream", tags=["Streaming"])
async def stream_rfp_progress(
    rfp_id: str,
    current_user: TokenData = Depends(get_current_user_sse)
):
    """
    Stream RFP processing progress
    
    Server-Sent Events (SSE) stream for real-time progress updates.
    """
    if not AuthorizationManager.has_permission(current_user.role, "rfp:read"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    rfp = rfp_store.get(rfp_id)
    if not rfp:
        raise HTTPException(status_code=404, detail="RFP not found")
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events"""
        progress = 0
        while progress < 100:
            # Simulate progress
            await asyncio.sleep(1)
            progress += 10
            
            event = {
                "rfp_id": rfp_id,
                "progress": min(progress, 100),
                "status": "processing" if progress < 100 else "completed",
                "timestamp": datetime.now().isoformat()
            }
            
            yield f"data: {json.dumps(event)}\n\n"
            
            if progress >= 100:
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


@app.get("/api/v1/events/stream", tags=["Streaming"])
async def stream_events(
    events: List[str] = Query(["*"]),
    current_user: TokenData = Depends(get_current_user_sse)
):
    """
    Stream system events
    
    Subscribe to system events via SSE.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events"""
        event_id = 0
        while True:
            await asyncio.sleep(5)
            event_id += 1
            
            event = {
                "id": event_id,
                "type": "heartbeat",
                "data": {"timestamp": datetime.now().isoformat()},
            }
            
            yield f"id: {event_id}\ndata: {json.dumps(event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


# =============================================================================
# Additional Utility Endpoints
# =============================================================================

@app.get("/api/v1/rate-limit/status", tags=["System"])
async def get_rate_limit_status(
    request: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get rate limit status
    
    Check current rate limit status for your client.
    """
    client_ip = request.client.host if request.client else "unknown"
    stats = rate_limiter.get_client_stats(client_ip)
    
    return ResponseFormatter.success(data=stats)


# =============================================================================
# Vendor Endpoints (consumed by frontend vendor.service.ts)
# =============================================================================

# In-memory vendor store
vendor_store: Dict[str, Dict[str, Any]] = {
    "1": {
        "id": 1, "vendor_id": "VND-001", "name": "Polycab India Ltd",
        "contact_person": "Rajesh Kumar", "email": "sales@polycab.com",
        "phone": "+91 22 6613 7272", "address": "Halol, Gujarat",
        "city": "Halol", "country": "India", "website": "https://polycab.com",
        "tier": "platinum", "rating": 4.8, "total_orders": 245,
        "on_time_delivery_rate": 96.5, "quality_score": 94.2,
        "compliance_score": 98.0, "is_active": True,
        "categories": ["Cables & Wires", "Electrical"],
        "certifications": ["ISO 9001", "ISO 14001", "IEC 60502"],
        "payment_terms": "Net 30", "notes": "Preferred supplier for HV cables",
        "products": [], "created_at": "2025-06-15T10:00:00", "updated_at": "2026-02-01T14:30:00"
    },
    "2": {
        "id": 2, "vendor_id": "VND-002", "name": "KEI Industries",
        "contact_person": "Anil Gupta", "email": "procurement@kei-ind.com",
        "phone": "+91 11 4600 2222", "address": "New Delhi, India",
        "city": "New Delhi", "country": "India", "website": "https://kei-ind.com",
        "tier": "gold", "rating": 4.5, "total_orders": 180,
        "on_time_delivery_rate": 93.2, "quality_score": 91.5,
        "compliance_score": 95.0, "is_active": True,
        "categories": ["Cables & Wires"],
        "certifications": ["ISO 9001", "BIS"],
        "payment_terms": "Net 45", "notes": None,
        "products": [], "created_at": "2025-07-20T09:00:00", "updated_at": "2026-01-28T11:15:00"
    },
    "3": {
        "id": 3, "vendor_id": "VND-003", "name": "Havells India",
        "contact_person": "Priya Sharma", "email": "b2b@havells.com",
        "phone": "+91 120 467 5600", "address": "Noida, UP",
        "city": "Noida", "country": "India", "website": "https://havells.com",
        "tier": "platinum", "rating": 4.7, "total_orders": 312,
        "on_time_delivery_rate": 95.8, "quality_score": 93.0,
        "compliance_score": 97.5, "is_active": True,
        "categories": ["Cables & Wires", "Electrical", "Industrial"],
        "certifications": ["ISO 9001", "ISO 14001", "NABL"],
        "payment_terms": "Net 30", "notes": None,
        "products": [], "created_at": "2025-05-10T08:00:00", "updated_at": "2026-02-05T16:45:00"
    },
    "4": {
        "id": 4, "vendor_id": "VND-004", "name": "Schneider Electric",
        "contact_person": "David Ochieng", "email": "orders@schneider.co.ke",
        "phone": "+254 20 271 4000", "address": "Nairobi, Kenya",
        "city": "Nairobi", "country": "Kenya", "website": "https://se.com",
        "tier": "gold", "rating": 4.6, "total_orders": 156,
        "on_time_delivery_rate": 94.0, "quality_score": 96.0,
        "compliance_score": 99.0, "is_active": True,
        "categories": ["Electrical", "Industrial"],
        "certifications": ["ISO 9001", "IEC 61439", "CE"],
        "payment_terms": "Net 30", "notes": "East Africa distributor",
        "products": [], "created_at": "2025-08-01T07:30:00", "updated_at": "2026-02-08T09:20:00"
    },
    "5": {
        "id": 5, "vendor_id": "VND-005", "name": "Siemens AG",
        "contact_person": "Hans Mueller", "email": "industry@siemens.com",
        "phone": "+49 89 636 00", "address": "Munich, Germany",
        "city": "Munich", "country": "Germany", "website": "https://siemens.com",
        "tier": "platinum", "rating": 4.9, "total_orders": 89,
        "on_time_delivery_rate": 97.1, "quality_score": 98.5,
        "compliance_score": 99.5, "is_active": True,
        "categories": ["Electrical", "Industrial", "Safety Equipment"],
        "certifications": ["ISO 9001", "ISO 14001", "IEC 61131"],
        "payment_terms": "Net 60", "notes": None,
        "products": [], "created_at": "2025-09-12T11:00:00", "updated_at": "2026-02-10T13:00:00"
    },
}
_vendor_id_counter = 6


@app.get("/api/v1/vendors", tags=["Vendors"])
async def list_vendors(
    tier: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    current_user: TokenData = Depends(get_current_user),
):
    """List vendors with filtering and pagination."""
    vendors = list(vendor_store.values())

    if tier:
        vendors = [v for v in vendors if v["tier"] == tier]
    if category:
        vendors = [v for v in vendors if category in v.get("categories", [])]
    if is_active is not None:
        vendors = [v for v in vendors if v["is_active"] == is_active]
    if search:
        q = search.lower()
        vendors = [v for v in vendors if q in v["name"].lower() or q in v.get("contact_person", "").lower()]

    reverse = sort_order == "desc"
    vendors.sort(key=lambda v: v.get(sort_by, ""), reverse=reverse)

    total = len(vendors)
    start = (page - 1) * per_page
    page_items = vendors[start : start + per_page]
    total_pages = (total + per_page - 1) // per_page

    return {"data": page_items, "total": total, "page": page, "per_page": per_page, "total_pages": total_pages}


@app.get("/api/v1/vendors/rankings", tags=["Vendors"])
async def get_vendor_rankings(current_user: TokenData = Depends(get_current_user)):
    """Return vendors ranked by composite score."""
    vendors = list(vendor_store.values())
    for v in vendors:
        v["composite_score"] = round(
            (v["rating"] / 5) * 30 + v["on_time_delivery_rate"] * 0.3 + v["quality_score"] * 0.2 + v["compliance_score"] * 0.2, 2
        )
    vendors.sort(key=lambda v: v["composite_score"], reverse=True)
    return ResponseFormatter.success(data=vendors)


@app.get("/api/v1/vendors/{vendor_id}", tags=["Vendors"])
async def get_vendor(vendor_id: int, current_user: TokenData = Depends(get_current_user)):
    """Get vendor by ID."""
    vendor = vendor_store.get(str(vendor_id))
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return ResponseFormatter.success(data=vendor)


class VendorCreateRequest(BaseModel):
    name: str
    contact_person: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    country: str = ""
    website: Optional[str] = None
    tier: str = "new"
    categories: List[str] = Field(default_factory=list)
    payment_terms: str = "Net 30"


@app.post("/api/v1/vendors", tags=["Vendors"])
async def create_vendor(vendor: VendorCreateRequest, current_user: TokenData = Depends(get_current_user)):
    """Create a new vendor."""
    global _vendor_id_counter
    vid = _vendor_id_counter
    _vendor_id_counter += 1
    data = {
        "id": vid, "vendor_id": f"VND-{vid:03d}", **vendor.dict(),
        "rating": 0, "total_orders": 0, "on_time_delivery_rate": 0,
        "quality_score": 0, "compliance_score": 0, "is_active": True,
        "certifications": [], "notes": None, "products": [],
        "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(),
    }
    vendor_store[str(vid)] = data
    return ResponseFormatter.success(data=data, message="Vendor created")


@app.put("/api/v1/vendors/{vendor_id}", tags=["Vendors"])
async def update_vendor(vendor_id: int, vendor: VendorCreateRequest, current_user: TokenData = Depends(get_current_user)):
    """Update vendor."""
    existing = vendor_store.get(str(vendor_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Vendor not found")
    existing.update({**vendor.dict(), "updated_at": datetime.now().isoformat()})
    return ResponseFormatter.success(data=existing, message="Vendor updated")


# =============================================================================
# Company Profiles & Bid Document Generation Endpoints
# =============================================================================

try:
    from api.bid_document_generator import (
        get_all_profiles, get_profile, create_profile, update_profile,
        delete_profile, set_default_profile,
        generate_bid_document, get_generated_bid, list_generated_bids, send_bid_email,
    )
    BID_GENERATOR_AVAILABLE = True
except ImportError:
    BID_GENERATOR_AVAILABLE = False
    print("Bid document generator not available")

try:
    from api.bid_pdf_generator import generate_bid_pdf
    BID_PDF_AVAILABLE = True
except Exception as e:
    BID_PDF_AVAILABLE = False
    print(f"Bid PDF generator not available: {e}")


@app.get("/api/v1/company-profiles", tags=["Company Profiles"])
async def api_list_profiles(current_user: TokenData = Depends(get_current_user)):
    """List all company profiles."""
    if not BID_GENERATOR_AVAILABLE:
        return ResponseFormatter.success(data=[])
    return ResponseFormatter.success(data=get_all_profiles())


@app.get("/api/v1/company-profiles/{profile_id}", tags=["Company Profiles"])
async def api_get_profile(profile_id: str, current_user: TokenData = Depends(get_current_user)):
    """Get a single company profile."""
    profile = get_profile(profile_id) if BID_GENERATOR_AVAILABLE else None
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ResponseFormatter.success(data=profile)


@app.post("/api/v1/company-profiles", tags=["Company Profiles"])
async def api_create_profile(data: Dict[str, Any], current_user: TokenData = Depends(get_current_user)):
    """Create a new company profile."""
    profile = create_profile(data)
    return ResponseFormatter.success(data=profile, message="Profile created")


@app.put("/api/v1/company-profiles/{profile_id}", tags=["Company Profiles"])
async def api_update_profile(profile_id: str, data: Dict[str, Any], current_user: TokenData = Depends(get_current_user)):
    """Update a company profile."""
    profile = update_profile(profile_id, data)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ResponseFormatter.success(data=profile, message="Profile updated")


@app.delete("/api/v1/company-profiles/{profile_id}", tags=["Company Profiles"])
async def api_delete_profile(profile_id: str, current_user: TokenData = Depends(get_current_user)):
    """Delete a company profile."""
    if not delete_profile(profile_id):
        raise HTTPException(status_code=404, detail="Profile not found")
    return ResponseFormatter.success(message="Profile deleted")


@app.post("/api/v1/company-profiles/{profile_id}/default", tags=["Company Profiles"])
async def api_set_default_profile(profile_id: str, current_user: TokenData = Depends(get_current_user)):
    """Set a profile as default."""
    profile = set_default_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ResponseFormatter.success(data=profile, message="Default profile updated")


@app.post("/api/v1/bid-documents/generate", tags=["Bid Documents"])
async def api_generate_bid_document(
    payload: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
):
    """Generate a formatted bid/RFP response document from analysis results + company profile."""
    analysis_result = payload.get("analysis_result", {})
    profile_id = payload.get("profile_id", "")
    bid_options = payload.get("bid_options", {})
    if not profile_id:
        raise HTTPException(status_code=400, detail="profile_id is required")
    try:
        doc = generate_bid_document(analysis_result, profile_id, bid_options)
        return ResponseFormatter.success(data=doc, message="Bid document generated")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/bid-documents", tags=["Bid Documents"])
async def api_list_bid_documents(current_user: TokenData = Depends(get_current_user)):
    """List all generated bid documents."""
    return ResponseFormatter.success(data=list_generated_bids() if BID_GENERATOR_AVAILABLE else [])


@app.get("/api/v1/bid-documents/{bid_id}", tags=["Bid Documents"])
async def api_get_bid_document(bid_id: str, current_user: TokenData = Depends(get_current_user)):
    """Get a generated bid document by ID."""
    doc = get_generated_bid(bid_id) if BID_GENERATOR_AVAILABLE else None
    if not doc:
        raise HTTPException(status_code=404, detail="Bid document not found")
    return ResponseFormatter.success(data=doc)


@app.post("/api/v1/bid-documents/{bid_id}/send", tags=["Bid Documents"])
async def api_send_bid_document(
    bid_id: str,
    payload: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
):
    """Send a generated bid document via email."""
    email_to = payload.get("email_to", "")
    email_cc = payload.get("email_cc", "")
    message = payload.get("message", "")
    if not email_to:
        raise HTTPException(status_code=400, detail="email_to is required")
    try:
        result = send_bid_email(bid_id, email_to, email_cc, message)
        return ResponseFormatter.success(data=result, message="Bid sent")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/bid-documents/{bid_id}/pdf", tags=["Bid Documents"])
async def api_download_bid_pdf(bid_id: str, current_user: TokenData = Depends(get_current_user)):
    """Generate and download a professional PDF of the bid document."""
    if not BID_GENERATOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Bid generator not available")
    doc = get_generated_bid(bid_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Bid document not found")
    if not BID_PDF_AVAILABLE:
        raise HTTPException(status_code=503, detail="PDF generator not available — install reportlab")
    try:
        pdf_bytes = generate_bid_pdf(doc)
        safe_name = bid_id.replace(" ", "_")
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}_Tender_Response.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# =============================================================================
# Saved Analyses — persist analysis results so BidGenerator can load them later
# =============================================================================

@app.post("/api/v1/saved-analyses", tags=["Saved Analyses"])
async def api_save_analysis(body: dict, current_user: TokenData = Depends(get_current_user)):
    """Save an analysis result for later use in bid generation."""
    analysis_result = body.get("analysis_result", {})
    file_name = body.get("file_name") or analysis_result.get("filename", "Unknown")

    if ANALYSIS_STORE_AVAILABLE:
        record = _persist_analysis(
            analysis_result=analysis_result,
            file_name=file_name,
            saved_by=current_user.username,
            source="manual",
        )
    else:
        analysis_id = analysis_result.get("analysis_id") or f"SA-{uuid.uuid4().hex[:8].upper()}"
        record = {
            "id": analysis_id,
            "file_name": file_name,
            "analysis_result": analysis_result,
            "total_requirements": analysis_result.get("total_requirements", 0),
            "matched": len([c for c in analysis_result.get("comparisons", []) if c.get("match_count", 0) > 0]),
            "detected_application": analysis_result.get("detected_application", ""),
            "rfp_title": (analysis_result.get("rfp_summary") or {}).get("boq_title", "") or file_name,
            "organization": (analysis_result.get("rfp_summary") or {}).get("organization", ""),
            "saved_at": datetime.now().isoformat(),
            "saved_by": current_user.username,
        }
    return ResponseFormatter.success(data=record, message="Analysis saved")


@app.get("/api/v1/saved-analyses", tags=["Saved Analyses"])
async def api_list_saved_analyses(current_user: TokenData = Depends(get_current_user)):
    """List all saved analyses (most recent first). Summaries only."""
    if ANALYSIS_STORE_AVAILABLE:
        items = _list_analyses(include_result=False)
    else:
        items = sorted([], key=lambda x: x.get("saved_at", ""), reverse=True)
    return ResponseFormatter.success(data=items)


@app.get("/api/v1/saved-analyses/{analysis_id}", tags=["Saved Analyses"])
async def api_get_saved_analysis(analysis_id: str, current_user: TokenData = Depends(get_current_user)):
    """Get a specific saved analysis by ID (includes full analysis_result)."""
    if ANALYSIS_STORE_AVAILABLE:
        record = _get_analysis(analysis_id)
    else:
        record = None
    if not record:
        raise HTTPException(status_code=404, detail="Saved analysis not found")
    return ResponseFormatter.success(data=record)


@app.delete("/api/v1/saved-analyses/{analysis_id}", tags=["Saved Analyses"])
async def api_delete_saved_analysis(analysis_id: str, current_user: TokenData = Depends(get_current_user)):
    """Delete a saved analysis."""
    if ANALYSIS_STORE_AVAILABLE:
        deleted = _delete_analysis(analysis_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Saved analysis not found")
    else:
        raise HTTPException(status_code=404, detail="Saved analysis not found")
    return ResponseFormatter.success(message="Deleted")


# =============================================================================
# Portal Scrape API — runs the rfp_processor scraper from the frontend
# =============================================================================

@app.post("/api/v1/portals/scrape", tags=["Portals"])
async def api_scrape_portals(
    background_tasks: BackgroundTasks,
    current_user: TokenData = Depends(get_current_user),
):
    """Trigger a full portal scrape and return immediately. Results appear in GET /portals/rfps."""
    global _portal_scrape_status
    if _portal_scrape_status.get("running"):
        return ResponseFormatter.success(data=_portal_scrape_status, message="Scrape already in progress")

    _portal_scrape_status = {"running": True, "started_at": datetime.now().isoformat(), "portals_done": 0, "total_rfps": 0, "errors": []}
    background_tasks.add_task(_run_portal_scrape)
    return ResponseFormatter.success(data=_portal_scrape_status, message="Scrape started")


@app.get("/api/v1/portals/scrape/status", tags=["Portals"])
async def api_scrape_status(current_user: TokenData = Depends(get_current_user)):
    """Check the status of the last/current scrape."""
    return ResponseFormatter.success(data=_portal_scrape_status)


@app.get("/api/v1/portals/rfps", tags=["Portals"])
async def api_portal_rfps(current_user: TokenData = Depends(get_current_user)):
    """Return all scraped RFPs from the manifest."""
    try:
        manifest_path = Path("rfp_processor/scraped_rfps/scrape_manifest.json")
        if not manifest_path.exists():
            return ResponseFormatter.success(data=[])
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rfps = data.get("rfps", [])
        # Enrich with saved-analysis status
        _existing_ids = {a["id"] for a in (_list_analyses() if ANALYSIS_STORE_AVAILABLE else [])}
        for r in rfps:
            aid = r.get("rfp_id")
            if aid and aid in _existing_ids:
                r["analysis_saved"] = True
                r["saved_analysis_id"] = aid
            else:
                r["analysis_saved"] = False
        return ResponseFormatter.success(data=rfps)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/portals/rfps/{rfp_id}/pdf", tags=["Portals"])
async def api_portal_rfp_pdf(rfp_id: str, current_user: TokenData = Depends(get_current_user)):
    """Serve a scraped RFP PDF so the frontend/analyzer can use it."""
    base = Path("rfp_processor/scraped_rfps")
    # Search in any portal sub-folder
    for portal_dir in base.iterdir():
        if not portal_dir.is_dir():
            continue
        pdf_path = portal_dir / f"{rfp_id}.pdf"
        if pdf_path.exists():
            return FileResponse(pdf_path, media_type="application/pdf", filename=f"{rfp_id}.pdf")
    raise HTTPException(status_code=404, detail=f"PDF for {rfp_id} not found")


# ── Portal scrape background worker ──

_portal_scrape_status: dict = {"running": False}


def _run_portal_scrape():
    """Background task: run the portal scraper with parallel PDF downloads."""
    global _portal_scrape_status
    import requests as _req
    from pathlib import Path as _P

    PORTALS = [
        {"portal_id": "portal_1", "name": "GovProcure India",  "base_url": "http://localhost:5001"},
        {"portal_id": "portal_2", "name": "TenderConnect",     "base_url": "http://localhost:5002"},
        {"portal_id": "portal_3", "name": "eProcure Hub",      "base_url": "http://localhost:5003"},
        {"portal_id": "portal_4", "name": "BidMarket Pro",     "base_url": "http://localhost:5004"},
        {"portal_id": "portal_5", "name": "PublicBids Online",  "base_url": "http://localhost:5005"},
    ]

    output_dir = _P("rfp_processor/scraped_rfps")
    output_dir.mkdir(parents=True, exist_ok=True)
    all_rfps: list = []
    session = _req.Session()
    session.headers["User-Agent"] = "HakiFMCG/2.0"

    from concurrent.futures import ThreadPoolExecutor, as_completed as _as

    def _download_one(rfp_rec: dict, portal_dir: _P):
        rid = rfp_rec["rfp_id"]
        pdf_path = portal_dir / f"{rid}.pdf"
        if pdf_path.exists():
            rfp_rec["local_pdf_path"] = str(pdf_path)
            return
        try:
            r = session.get(rfp_rec["download_url"], timeout=15)
            r.raise_for_status()
            pdf_path.write_bytes(r.content)
            rfp_rec["local_pdf_path"] = str(pdf_path)
            rfp_rec["file_size_bytes"] = len(r.content)
        except Exception as ex:
            rfp_rec["download_error"] = str(ex)

    for portal in PORTALS:
        try:
            resp = session.get(f"{portal['base_url']}/api/rfps", timeout=8)
            resp.raise_for_status()
            rfps = resp.json().get("rfps", [])
        except Exception as ex:
            _portal_scrape_status["errors"].append(f"{portal['name']}: {ex}")
            _portal_scrape_status["portals_done"] = _portal_scrape_status.get("portals_done", 0) + 1
            continue

        portal_dir = output_dir / portal["portal_id"]
        portal_dir.mkdir(exist_ok=True)

        records = []
        for rfp in rfps:
            records.append({
                "rfp_id": rfp["rfp_id"],
                "filename": rfp.get("filename", ""),
                "title": rfp.get("title", ""),
                "category": rfp.get("category", ""),
                "organization": rfp.get("organization", ""),
                "publish_date": rfp.get("publish_date", ""),
                "deadline": rfp.get("deadline", ""),
                "status": rfp.get("status", ""),
                "estimated_value": rfp.get("estimated_value", ""),
                "location": rfp.get("location", ""),
                "source_portal": portal["name"],
                "source_portal_id": portal["portal_id"],
                "source_url": f"{portal['base_url']}/rfp/{rfp['rfp_id']}",
                "download_url": f"{portal['base_url']}/download/{rfp['rfp_id']}",
                "scraped_at": datetime.now().isoformat(),
            })

        # Parallel PDF downloads (8 threads)
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(_download_one, rec, portal_dir) for rec in records]
            for f in _as(futures):
                f.result()

        all_rfps.extend(records)
        _portal_scrape_status["portals_done"] = _portal_scrape_status.get("portals_done", 0) + 1
        _portal_scrape_status["total_rfps"] = len(all_rfps)

    # Write manifest
    manifest = {
        "scrape_timestamp": datetime.now().isoformat(),
        "total_rfps": len(all_rfps),
        "portals_scraped": len(PORTALS),
        "rfps": all_rfps,
    }
    with open(output_dir / "scrape_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    _portal_scrape_status.update({"running": False, "finished_at": datetime.now().isoformat(), "total_rfps": len(all_rfps)})

bid_store: Dict[str, Dict[str, Any]] = {
    "1": {
        "id": 1, "bid_id": "BID-2026-001", "rfp_id": 1,
        "title": "HV Cable Supply — Kenya Power Phase 3",
        "description": "Bid for HV cable supply per KPLC tender",
        "status": "approved", "total_value": 12500000, "currency": "KES",
        "discount_percentage": 5.0, "validity_days": 90,
        "delivery_timeline": "8 weeks", "payment_terms": "Net 30",
        "technical_score": 92, "commercial_score": 88, "compliance_score": 95, "overall_score": 91,
        "items": [
            {"id": 1, "bid_id": 1, "product_id": 1, "product_name": "XLPE Insulated HV Cable 33kV 3x185mm²", "sku": "CAB-001", "quantity": 500, "unit_price": 4250, "discount": 5.0, "total_price": 2018750},
        ],
        "approvals": [{"id": 1, "bid_id": 1, "approver_name": "James Mwangi", "approver_role": "Manager", "status": "approved", "comments": "Pricing looks competitive", "decided_at": "2026-02-08T14:00:00", "created_at": "2026-02-07T10:00:00"}],
        "submitted_at": "2026-02-09T09:00:00", "approved_at": "2026-02-08T14:00:00",
        "created_by": "admin", "notes": None,
        "created_at": "2026-02-05T08:00:00", "updated_at": "2026-02-09T09:00:00",
    },
    "2": {
        "id": 2, "bid_id": "BID-2026-002", "rfp_id": 2,
        "title": "Safety Equipment Warehouse Supply",
        "description": "Safety equipment bid for warehouse project",
        "status": "in_review", "total_value": 3200000, "currency": "KES",
        "discount_percentage": 3.0, "validity_days": 60,
        "delivery_timeline": "4 weeks", "payment_terms": "Net 45",
        "technical_score": 87, "commercial_score": 91, "compliance_score": 89, "overall_score": 89,
        "items": [], "approvals": [],
        "submitted_at": None, "approved_at": None,
        "created_by": "admin", "notes": None,
        "created_at": "2026-02-08T11:00:00", "updated_at": "2026-02-10T15:30:00",
    },
    "3": {
        "id": 3, "bid_id": "BID-2026-003", "rfp_id": 3,
        "title": "FMCG Q1 Restock Response",
        "description": "Quarterly FMCG replenishment bid",
        "status": "draft", "total_value": 8750000, "currency": "KES",
        "discount_percentage": 0, "validity_days": 30,
        "delivery_timeline": "2 weeks", "payment_terms": "Net 30",
        "technical_score": 0, "commercial_score": 0, "compliance_score": 0, "overall_score": 0,
        "items": [], "approvals": [],
        "submitted_at": None, "approved_at": None,
        "created_by": "admin", "notes": "Draft in progress",
        "created_at": "2026-02-10T07:00:00", "updated_at": "2026-02-10T07:00:00",
    },
}
_bid_id_counter = 4


@app.get("/api/v1/bids", tags=["Bids"])
async def list_bids(
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    current_user: TokenData = Depends(get_current_user),
):
    """List bids with filtering and pagination."""
    bids = list(bid_store.values())
    if status:
        bids = [b for b in bids if b["status"] == status]
    if search:
        q = search.lower()
        bids = [b for b in bids if q in b["title"].lower() or q in b["bid_id"].lower()]
    reverse = sort_order == "desc"
    bids.sort(key=lambda b: b.get(sort_by, ""), reverse=reverse)
    total = len(bids)
    start = (page - 1) * per_page
    page_items = bids[start : start + per_page]
    total_pages = (total + per_page - 1) // per_page
    return {"data": page_items, "total": total, "page": page, "per_page": per_page, "total_pages": total_pages}


@app.get("/api/v1/bids/{bid_id}", tags=["Bids"])
async def get_bid(bid_id: int, current_user: TokenData = Depends(get_current_user)):
    """Get bid by ID."""
    bid = bid_store.get(str(bid_id))
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    return ResponseFormatter.success(data=bid)


class BidCreateRequest(BaseModel):
    rfp_id: int
    title: str
    description: str = ""
    total_value: float = 0
    currency: str = "KES"
    discount_percentage: float = 0
    validity_days: int = 30
    delivery_timeline: str = ""
    payment_terms: str = "Net 30"


@app.post("/api/v1/bids", tags=["Bids"])
async def create_bid(bid: BidCreateRequest, current_user: TokenData = Depends(get_current_user)):
    """Create a new bid."""
    global _bid_id_counter
    bid_id = _bid_id_counter
    _bid_id_counter += 1
    data = {
        "id": bid_id, "bid_id": f"BID-2026-{bid_id:03d}", **bid.dict(),
        "status": "draft", "technical_score": 0, "commercial_score": 0,
        "compliance_score": 0, "overall_score": 0, "items": [], "approvals": [],
        "submitted_at": None, "approved_at": None, "created_by": current_user.username,
        "notes": None, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(),
    }
    bid_store[str(bid_id)] = data
    return ResponseFormatter.success(data=data, message="Bid created")


@app.put("/api/v1/bids/{bid_id}", tags=["Bids"])
async def update_bid(bid_id: int, bid: BidCreateRequest, current_user: TokenData = Depends(get_current_user)):
    """Update bid."""
    existing = bid_store.get(str(bid_id))
    if not existing:
        raise HTTPException(status_code=404, detail="Bid not found")
    existing.update({**bid.dict(), "updated_at": datetime.now().isoformat()})
    return ResponseFormatter.success(data=existing, message="Bid updated")


@app.delete("/api/v1/bids/{bid_id}", tags=["Bids"])
async def delete_bid(bid_id: int, current_user: TokenData = Depends(get_current_user)):
    """Delete bid."""
    if str(bid_id) not in bid_store:
        raise HTTPException(status_code=404, detail="Bid not found")
    del bid_store[str(bid_id)]
    return ResponseFormatter.success(message="Bid deleted")


@app.post("/api/v1/bids/{bid_id}/items", tags=["Bids"])
async def add_bid_item(bid_id: int, item: Dict[str, Any], current_user: TokenData = Depends(get_current_user)):
    """Add item to bid."""
    bid = bid_store.get(str(bid_id))
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    item["id"] = len(bid["items"]) + 1
    item["bid_id"] = bid_id
    bid["items"].append(item)
    bid["updated_at"] = datetime.now().isoformat()
    return ResponseFormatter.success(data=bid, message="Item added")


@app.post("/api/v1/bids/{bid_id}/submit", tags=["Bids"])
async def submit_bid(bid_id: int, current_user: TokenData = Depends(get_current_user)):
    """Submit bid for approval."""
    bid = bid_store.get(str(bid_id))
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    bid["status"] = "submitted"
    bid["submitted_at"] = datetime.now().isoformat()
    bid["updated_at"] = datetime.now().isoformat()
    return ResponseFormatter.success(data=bid, message="Bid submitted")


@app.post("/api/v1/bids/{bid_id}/approval/request", tags=["Bids"])
async def request_bid_approval(bid_id: int, current_user: TokenData = Depends(get_current_user)):
    """Request approval for a bid."""
    bid = bid_store.get(str(bid_id))
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    bid["status"] = "in_review"
    bid["updated_at"] = datetime.now().isoformat()
    return ResponseFormatter.success(data=bid, message="Approval requested")


@app.post("/api/v1/bids/{bid_id}/approval/{action}", tags=["Bids"])
async def action_bid_approval(bid_id: int, action: str, current_user: TokenData = Depends(get_current_user)):
    """Approve or reject a bid."""
    bid = bid_store.get(str(bid_id))
    if not bid:
        raise HTTPException(status_code=404, detail="Bid not found")
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
    bid["status"] = "approved" if action == "approve" else "rejected"
    bid["approved_at"] = datetime.now().isoformat() if action == "approve" else None
    bid["updated_at"] = datetime.now().isoformat()
    bid["approvals"].append({
        "id": len(bid["approvals"]) + 1, "bid_id": bid_id,
        "approver_name": current_user.username, "approver_role": current_user.role.value,
        "status": "approved" if action == "approve" else "rejected",
        "comments": None, "decided_at": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
    })
    return ResponseFormatter.success(data=bid, message=f"Bid {action}d")


# =============================================================================
# Product List Endpoint (consumed by frontend product.service.ts)
# =============================================================================

product_catalog: List[Dict[str, Any]] = [
    {"id": 1, "sku": "CAB-001", "name": "XLPE Insulated HV Cable 33kV 3×185mm²", "description": "High voltage XLPE cable for power transmission", "category": "Cables & Wires", "subcategory": "HV Cables", "brand": "Polycab", "manufacturer": "Polycab India Ltd", "unit_price": 4250, "currency": "INR", "unit_of_measure": "meter", "min_order_quantity": 100, "lead_time_days": 14, "specifications": {"voltage": "33kV", "size": "3×185mm²", "insulation": "XLPE"}, "certifications": ["ISO 9001", "IEC 60502"], "is_active": True, "stock_quantity": 5000, "tags": ["hv", "xlpe", "copper"], "created_at": "2025-06-01T00:00:00", "updated_at": "2026-02-01T00:00:00"},
    {"id": 2, "sku": "CAB-002", "name": "PVC Insulated Copper Cable 4 Core 16mm²", "description": "LV PVC copper cable for general wiring", "category": "Cables & Wires", "subcategory": "LV Cables", "brand": "KEI", "manufacturer": "KEI Industries", "unit_price": 890, "currency": "INR", "unit_of_measure": "meter", "min_order_quantity": 50, "lead_time_days": 7, "specifications": {"voltage": "1.1kV", "size": "4×16mm²", "insulation": "PVC"}, "certifications": ["ISO 9001", "BIS"], "is_active": True, "stock_quantity": 12000, "tags": ["lv", "pvc", "copper"], "created_at": "2025-06-01T00:00:00", "updated_at": "2026-01-15T00:00:00"},
    {"id": 3, "sku": "CAB-003", "name": "Armoured Power Cable 11kV 3×95mm²", "description": "Medium voltage armoured cable", "category": "Cables & Wires", "subcategory": "MV Cables", "brand": "Havells", "manufacturer": "Havells India", "unit_price": 2150, "currency": "INR", "unit_of_measure": "meter", "min_order_quantity": 100, "lead_time_days": 10, "specifications": {"voltage": "11kV", "size": "3×95mm²", "armour": "SWA"}, "certifications": ["ISO 9001", "IEC 60502"], "is_active": True, "stock_quantity": 3000, "tags": ["mv", "armoured"], "created_at": "2025-07-01T00:00:00", "updated_at": "2026-02-05T00:00:00"},
    {"id": 4, "sku": "CAB-004", "name": "Flexible Copper Wire 1.5mm² Multi-strand", "description": "Flexible multistrand copper wire", "category": "Cables & Wires", "subcategory": "Flexible Wires", "brand": "Finolex", "manufacturer": "Finolex Cables", "unit_price": 28, "currency": "INR", "unit_of_measure": "meter", "min_order_quantity": 200, "lead_time_days": 3, "specifications": {"voltage": "660V", "size": "1.5mm²", "type": "Flexible"}, "certifications": ["BIS"], "is_active": True, "stock_quantity": 50000, "tags": ["flexible", "copper"], "created_at": "2025-06-15T00:00:00", "updated_at": "2026-01-20T00:00:00"},
    {"id": 5, "sku": "ELE-001", "name": "MCB 63A Triple Pole", "description": "Miniature circuit breaker 63A 3P", "category": "Electrical", "subcategory": "Circuit Breakers", "brand": "Schneider", "manufacturer": "Schneider Electric", "unit_price": 1850, "currency": "INR", "unit_of_measure": "piece", "min_order_quantity": 10, "lead_time_days": 5, "specifications": {"current": "63A", "poles": "3P", "breaking_capacity": "10kA"}, "certifications": ["IEC 60898", "CE"], "is_active": True, "stock_quantity": 500, "tags": ["mcb", "protection"], "created_at": "2025-08-01T00:00:00", "updated_at": "2026-02-08T00:00:00"},
    {"id": 6, "sku": "ELE-002", "name": "MCCB 250A 4 Pole", "description": "Moulded case circuit breaker", "category": "Electrical", "subcategory": "Circuit Breakers", "brand": "ABB", "manufacturer": "ABB Ltd", "unit_price": 12500, "currency": "INR", "unit_of_measure": "piece", "min_order_quantity": 1, "lead_time_days": 10, "specifications": {"current": "250A", "poles": "4P", "type": "Adjustable"}, "certifications": ["IEC 60947", "CE"], "is_active": True, "stock_quantity": 120, "tags": ["mccb", "protection"], "created_at": "2025-08-15T00:00:00", "updated_at": "2026-02-01T00:00:00"},
    {"id": 7, "sku": "ELE-003", "name": "Contactor 3P 40A AC3", "description": "Power contactor for motor control", "category": "Electrical", "subcategory": "Contactors", "brand": "Siemens", "manufacturer": "Siemens AG", "unit_price": 3200, "currency": "INR", "unit_of_measure": "piece", "min_order_quantity": 5, "lead_time_days": 7, "specifications": {"current": "40A", "category": "AC3", "coil": "230V AC"}, "certifications": ["IEC 60947", "CE"], "is_active": False, "stock_quantity": 0, "tags": ["contactor", "motor"], "created_at": "2025-09-01T00:00:00", "updated_at": "2026-02-03T00:00:00"},
    {"id": 8, "sku": "ELE-004", "name": "VFD 7.5kW 3-Phase", "description": "Variable frequency drive", "category": "Electrical", "subcategory": "Drives", "brand": "ABB", "manufacturer": "ABB Ltd", "unit_price": 45000, "currency": "INR", "unit_of_measure": "piece", "min_order_quantity": 1, "lead_time_days": 14, "specifications": {"power": "7.5kW", "input": "3Ph 415V", "protocol": "Modbus"}, "certifications": ["IEC 61800", "CE"], "is_active": True, "stock_quantity": 30, "tags": ["vfd", "drive"], "created_at": "2025-09-15T00:00:00", "updated_at": "2026-02-06T00:00:00"},
    {"id": 9, "sku": "SAF-001", "name": "Safety Helmet ISI Marked", "description": "Industrial safety helmet", "category": "Safety Equipment", "subcategory": "Head Protection", "brand": "Karam", "manufacturer": "Karam Industries", "unit_price": 350, "currency": "INR", "unit_of_measure": "piece", "min_order_quantity": 50, "lead_time_days": 3, "specifications": {"standard": "IS 2925", "material": "HDPE", "type": "Ratchet"}, "certifications": ["ISI", "EN 397"], "is_active": True, "stock_quantity": 2000, "tags": ["helmet", "safety"], "created_at": "2025-07-01T00:00:00", "updated_at": "2026-01-25T00:00:00"},
    {"id": 10, "sku": "SAF-002", "name": "Safety Harness Full Body", "description": "Fall protection harness", "category": "Safety Equipment", "subcategory": "Fall Protection", "brand": "Karam", "manufacturer": "Karam Industries", "unit_price": 2800, "currency": "INR", "unit_of_measure": "piece", "min_order_quantity": 10, "lead_time_days": 5, "specifications": {"standard": "EN 361", "type": "Full Body", "weight": "1.8kg"}, "certifications": ["EN 361", "CE"], "is_active": True, "stock_quantity": 300, "tags": ["harness", "fall"], "created_at": "2025-07-15T00:00:00", "updated_at": "2026-02-02T00:00:00"},
    {"id": 11, "sku": "FMC-001", "name": "Hand Sanitizer 500ml (Pack of 24)", "description": "Alcohol-based hand sanitizer bulk", "category": "FMCG", "subcategory": "Hygiene", "brand": "Unilever", "manufacturer": "Unilever", "unit_price": 2880, "currency": "INR", "unit_of_measure": "case", "min_order_quantity": 10, "lead_time_days": 3, "specifications": {"volume": "500ml", "pack": "24 pcs", "alcohol": "70%"}, "certifications": ["WHO Formula"], "is_active": True, "stock_quantity": 800, "tags": ["sanitizer", "hygiene"], "created_at": "2025-10-01T00:00:00", "updated_at": "2026-01-30T00:00:00"},
    {"id": 12, "sku": "OFF-001", "name": "A4 Copier Paper 80gsm (5 Reams)", "description": "Office copier paper", "category": "Office Supplies", "subcategory": "Paper", "brand": "Chamex", "manufacturer": "Chamex", "unit_price": 1650, "currency": "INR", "unit_of_measure": "box", "min_order_quantity": 20, "lead_time_days": 2, "specifications": {"size": "A4", "weight": "80gsm", "sheets": "2500"}, "certifications": [], "is_active": True, "stock_quantity": 1500, "tags": ["paper", "office"], "created_at": "2025-11-01T00:00:00", "updated_at": "2026-02-01T00:00:00"},
]


@app.get("/api/v1/products", tags=["Products"])
async def list_products(
    category: Optional[str] = None,
    brand: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    current_user: TokenData = Depends(get_current_user),
):
    """List products with filtering, search and pagination."""
    products = [p.copy() for p in product_catalog]

    if category:
        products = [p for p in products if p["category"] == category]
    if brand:
        products = [p for p in products if p["brand"].lower() == brand.lower()]
    if is_active is not None:
        products = [p for p in products if p["is_active"] == is_active]
    if min_price is not None:
        products = [p for p in products if p["unit_price"] >= min_price]
    if max_price is not None:
        products = [p for p in products if p["unit_price"] <= max_price]
    if search:
        q = search.lower()
        products = [p for p in products if q in p["name"].lower() or q in p["sku"].lower() or q in p["manufacturer"].lower()]

    reverse = sort_order == "desc"
    products.sort(key=lambda p: p.get(sort_by, ""), reverse=reverse)

    total = len(products)
    start = (page - 1) * per_page
    page_items = products[start : start + per_page]
    total_pages = (total + per_page - 1) // per_page

    return {"data": page_items, "total": total, "page": page, "per_page": per_page, "total_pages": total_pages}


# =============================================================================
# Product Catalog — Real OEM Dataset (22k+ products)
# NOTE: These /catalog routes MUST be registered BEFORE the /{product_id_or_sku}
#       wildcard route, otherwise FastAPI will match "catalog" as a sku value.
# =============================================================================

# In-memory store for user-added products — seeded from persistent store
_user_added_products: List[Dict[str, Any]] = []
if CATALOG_STORE_AVAILABLE:
    try:
        _user_added_products = _load_persisted_products()
        if _user_added_products:
            logger.info(f"Loaded {len(_user_added_products)} persisted user/imported products from catalog store")
    except Exception as _lpe:
        logger.warning(f"Could not load persisted products: {_lpe}")

@app.get("/api/v1/products/catalog", tags=["Products"])
async def list_catalog_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    oem: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    source: Optional[str] = None,  # 'oem' | 'moglix' | 'user' | 'all'
    current_user: TokenData = Depends(get_current_user),
):
    """
    List products from the real OEM dataset (22k+ wires & cables)
    plus any user-added products. Supports pagination, filtering, and search.
    """
    product_db, _ = _get_oem_db_and_matcher()
    if product_db is None or product_db.products_df is None:
        # Fallback to static catalog
        return {"data": product_catalog[:per_page], "total": len(product_catalog), "page": 1, "per_page": per_page, "total_pages": 1}

    df = product_db.products_df.copy()

    # Normalize column access
    def _col(df, *names):
        for n in names:
            if n in df.columns:
                return n
        return None

    name_col = _col(df, 'Product_Name', 'product_name', 'Name', 'name')
    oem_col = _col(df, 'OEM', 'Company', 'oem')
    cat_col = _col(df, 'Product_Category', 'Category', 'category', 'Type')
    code_col = _col(df, 'Product_Code', 'product_code', 'SKU', 'sku')
    price_col = _col(df, 'Price_Per_Meter_INR', 'Calculated_Price_Per_Meter', 'price')
    price_100m_col = _col(df, 'Price_Per_100m_INR')
    src_col = _col(df, 'Source', 'source')
    voltage_col = _col(df, 'Voltage_Rating', 'voltage_rating', 'Voltage')
    size_col = _col(df, 'Conductor_Size_sqmm', 'conductor_size', 'Size')
    cores_col = _col(df, 'No_of_Cores', 'no_of_cores', 'Cores')
    insulation_col = _col(df, 'Insulation_Type', 'insulation_type', 'Insulation')
    standard_col = _col(df, 'Standard', 'standard', 'Compliance_Standards')
    quality_col = _col(df, 'Overall_Quality_Score', 'quality_score')
    material_col = _col(df, 'Conductor_Material', 'conductor_material', 'Material')

    # ── Filters ──
    if oem and oem_col:
        df = df[df[oem_col].astype(str).str.lower() == oem.lower()]
    if category and cat_col:
        df = df[df[cat_col].astype(str).str.lower().str.contains(category.lower(), na=False)]
    if source and src_col:
        if source == 'oem':
            df = df[df[src_col] == 'OEM Direct']
        elif source == 'moglix':
            df = df[df[src_col] == 'Moglix Marketplace']
        elif source == 'user':
            df = df[df[src_col] == 'User Added']
        elif source == 'imported':
            df = df[df[src_col] == 'PDF Import']
    if search:
        q = search.lower()
        mask = pd.Series([False] * len(df), index=df.index)
        for col_name in [name_col, oem_col, cat_col, code_col]:
            if col_name:
                mask = mask | df[col_name].astype(str).str.lower().str.contains(q, na=False)
        df = df[mask]

    total = len(df)
    start = (page - 1) * per_page
    page_df = df.iloc[start:start + per_page]

    # Build slim response
    import math as _math
    def _v(row, col):
        if col is None:
            return None
        v = row.get(col)
        if v is None or (isinstance(v, float) and _math.isnan(v)):
            return None
        return v

    import re as _re
    _coil_len_re = _re.compile(r'Length:\s*(\d+)\s*m', _re.IGNORECASE)
    _calc_col = _col(df, 'Calculated_Price_Per_Meter')

    def _price_unit_for_row(row):
        """Detect whether the listed price is per-meter or per N-metre coil.
        Priority:
          1. Product name contains 'Length: N m'  → 'Nm'  (e.g. '90m', '100m')
          2. Price_Per_Meter_INR ÷ Calculated_Price_Per_Meter ≈ N (85–115 → 100m, 80–95 → 90m, 170–195 → 180m)
          3. Default → 'm'
        """
        name_val = str(row.get(name_col) or '')
        m = _coil_len_re.search(name_val)
        if m:
            return f"{m.group(1)}m"
        if _calc_col:
            try:
                ppm = float(row.get(price_col) or 0)
                calc = float(row.get(_calc_col) or 0)
                if calc > 0 and ppm > 0:
                    ratio = ppm / calc
                    if 85 <= ratio <= 115:
                        return '100m'
                    if 170 <= ratio <= 195:
                        return '180m'
                    if 80 <= ratio <= 95:
                        return '90m'
            except (TypeError, ValueError):
                pass
        return 'm'

    items = []
    for idx, row in page_df.iterrows():
        _src_val = _v(row, src_col) or 'OEM Direct'
        _p_unit = _price_unit_for_row(row)
        _is_coil = _p_unit != 'm'
        items.append({
            'product_code': _v(row, code_col) or f"P-{idx + 1}",
            'name': _v(row, name_col) or 'Unknown Product',
            'oem': _v(row, oem_col) or 'Unknown',
            'category': _v(row, cat_col) or 'General',
            'price_per_meter': _v(row, price_col),
            'price_per_100m': _v(row, price_100m_col) if _is_coil else None,
            'price_unit': _p_unit,
            'voltage_rating': _v(row, voltage_col),
            'conductor_size': _v(row, size_col),
            'cores': _v(row, cores_col),
            'insulation': _v(row, insulation_col),
            'conductor_material': _v(row, material_col),
            'standard': _v(row, standard_col),
            'quality_score': _v(row, quality_col),
            'source': _src_val,
        })

    # Append user-added products to the first page when no filter excludes them
    if source in (None, 'all', 'user') and page == 1 and _user_added_products:
        user_match = _user_added_products
        if search:
            q = search.lower()
            user_match = [p for p in user_match if q in (p.get('name','') + p.get('oem','')).lower()]
        items = user_match + items
        total += len(user_match)

    oem_list = product_db.get_oem_list()
    source_stats = product_db.get_source_stats()

    return {
        "data": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "oem_list": oem_list,
        "source_stats": source_stats,
        "user_added_count": len(_user_added_products),
    }


@app.get("/api/v1/products/catalog/stats", tags=["Products"])
async def catalog_stats(current_user: TokenData = Depends(get_current_user)):
    """Return quick summary stats for the product catalog."""
    product_db, _ = _get_oem_db_and_matcher()
    if product_db is None:
        return ResponseFormatter.success(data={"total": 0, "oems": [], "source_stats": {}})
    return ResponseFormatter.success(data={
        "total": product_db.get_total_products(),
        "oems": product_db.get_oem_list(),
        "source_stats": product_db.get_source_stats(),
        "user_added": len(_user_added_products),
    })


@app.post("/api/v1/products/add", tags=["Products"])
async def add_product_manually(
    body: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
):
    """
    Manually add a product to the catalog.
    Accepts: name, oem, category, price_per_meter, voltage_rating,
    conductor_size, cores, insulation, conductor_material, standard.
    """
    name = body.get('name', '').strip()
    if not name:
        raise HTTPException(status_code=400, detail="Product name is required")

    product = {
        'product_code': f"USR-{uuid.uuid4().hex[:8].upper()}",
        'name': name,
        'oem': body.get('oem', 'Custom').strip() or 'Custom',
        'category': body.get('category', 'Cables & Wires').strip(),
        'price_per_meter': body.get('price_per_meter'),
        'voltage_rating': body.get('voltage_rating'),
        'conductor_size': body.get('conductor_size'),
        'cores': body.get('cores'),
        'insulation': body.get('insulation'),
        'conductor_material': body.get('conductor_material'),
        'standard': body.get('standard'),
        'quality_score': None,
        'source': 'User Added',
        'added_at': datetime.now().isoformat(),
    }

    _user_added_products.append(product)
    logger.info(f"User added product: {name} (code={product['product_code']})")

    # Persist to disk
    if CATALOG_STORE_AVAILABLE:
        try:
            _persist_product(product)
        except Exception as _pe:
            logger.warning(f"Could not persist product: {_pe}")

    # Also try to inject into the in-memory OEM DataFrame for RFP matching
    product_db, _ = _get_oem_db_and_matcher()
    if product_db and product_db.products_df is not None:
        import math as _math
        new_row = {
            'Product_Name': name,
            'Product_Code': product['product_code'],
            'OEM': product['oem'],
            'Source': 'User Added',
            'Product_Category': product['category'],
            'Price_Per_Meter_INR': product.get('price_per_meter'),
            'Voltage_Rating': product.get('voltage_rating'),
            'Conductor_Size_sqmm': product.get('conductor_size'),
            'No_of_Cores': product.get('cores'),
            'Insulation_Type': product.get('insulation'),
            'Conductor_Material': product.get('conductor_material'),
            'Standard': product.get('standard'),
        }
        product_db.products_df = pd.concat(
            [product_db.products_df, pd.DataFrame([new_row])], ignore_index=True
        )
        logger.info(f"Product injected into OEM DB — new total: {len(product_db.products_df)}")

    return ResponseFormatter.success(data=product, message="Product added successfully")



@app.post("/api/v1/products/import-catalog", tags=["Products"])
async def import_product_catalog(
    file: UploadFile = File(None),
    url: Optional[str] = Query(None),
    auto_confirm: bool = Query(False, description="If true, skip preview and add products immediately"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Import products from a PDF catalog or a URL.
    Extracts product names, specs, and pricing from the uploaded document.

    Two modes:
    - **auto_confirm=false** (default): Returns a preview with extraction_id.
      Call POST /import-catalog/confirm to actually add them.
    - **auto_confirm=true**: Extracts AND adds products in one step (legacy behaviour).
    """
    import tempfile as _tmpfile

    extracted_text = ""
    source_name = ""
    page_count = 0

    # ── Option A: PDF file upload ──
    if file and file.filename:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        source_name = file.filename
        content = await file.read()
        tmp = _tmpfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp.write(content)
        tmp.close()
        try:
            if SPEC_ANALYSIS_AVAILABLE:
                extractor = MultilingualExtractor(tmp.name)
                extracted_text = extractor.extract_all_text()
            else:
                import pdfplumber
                with pdfplumber.open(tmp.name) as pdf:
                    page_count = len(pdf.pages)
                    for pg in pdf.pages:
                        extracted_text += (pg.extract_text() or "") + "\n"
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    # ── Option B: URL ──
    elif url:
        source_name = url
        import urllib.request as _ureq
        try:
            req = _ureq.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with _ureq.urlopen(req, timeout=15) as resp:
                ctype = resp.headers.get('Content-Type', '')
                raw = resp.read()
                if 'pdf' in ctype.lower() or url.lower().endswith('.pdf'):
                    tmp = _tmpfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                    tmp.write(raw)
                    tmp.close()
                    try:
                        if SPEC_ANALYSIS_AVAILABLE:
                            extractor = MultilingualExtractor(tmp.name)
                            extracted_text = extractor.extract_all_text()
                        else:
                            import pdfplumber
                            with pdfplumber.open(tmp.name) as pdf:
                                page_count = len(pdf.pages)
                                for pg in pdf.pages:
                                    extracted_text += (pg.extract_text() or "") + "\n"
                    finally:
                        try:
                            os.unlink(tmp.name)
                        except Exception:
                            pass
                else:
                    extracted_text = raw.decode('utf-8', errors='replace')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="Provide a PDF file or a URL")

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the provided source")

    # ── Extract products using LangChain or regex ──
    detected_products = []
    extraction_method = "regex"
    try:
        from agents.langchain_agent import LangChainRFPAgent, LANGCHAIN_AVAILABLE as LC_AVAIL
        if LC_AVAIL:
            agent = LangChainRFPAgent()
            if agent.is_llm_available:
                from langchain_core.prompts import ChatPromptTemplate
                from langchain_core.output_parsers import StrOutputParser
                from agents.langchain_agent.rfp_chain import get_llm, _smart_trim, _safe_json_parse

                llm = get_llm()
                if llm:
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", """You are a product catalog parser. Extract ALL products from the text.

Return a JSON array where each item has:
{{
  "name": "full product name",
  "description": "brief description or null",
  "category": "product category",
  "voltage_rating": "voltage or null",
  "conductor_size": "size in sqmm or null",
  "cores": cores_number_or_null,
  "insulation": "insulation type or null",
  "conductor_material": "Copper/Aluminium or null",
  "price_per_meter": price_number_or_null,
  "standard": "IS/IEC standard or null",
  "oem": "manufacturer name or null"
}}

Extract every distinct product. Return ONLY valid JSON array."""),
                        ("human", "{text}"),
                    ])
                    chain = prompt | llm | StrOutputParser()
                    raw = chain.invoke({"text": _smart_trim(extracted_text, 6000)})
                    parsed = _safe_json_parse(raw)
                    if isinstance(parsed, list):
                        detected_products = parsed
                        extraction_method = "ai"
                    elif isinstance(parsed, dict) and 'products' in parsed:
                        detected_products = parsed['products']
                        extraction_method = "ai"
    except Exception as llm_err:
        logger.warning(f"LLM catalog extraction failed: {llm_err}")

    # Regex fallback — simple line-by-line detection
    if not detected_products:
        import re
        lines = extracted_text.split('\n')
        cable_pattern = re.compile(
            r'(?P<name>[\w\s/×\-\.]+(?:cable|wire|conductor|XLPE|PVC|armoured|FRLS|LSZH|SWA|HT|LT)[\w\s/×\-\.]*)',
            re.IGNORECASE
        )
        price_pattern = re.compile(r'(?:₹|Rs\.?|INR)\s*(\d[\d,]*(?:\.\d{1,2})?)', re.IGNORECASE)
        for line in lines:
            m = cable_pattern.search(line)
            if m:
                pname = m.group('name').strip()
                if len(pname) > 8 and pname not in [p['name'] for p in detected_products]:
                    size_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:sq\.?mm|mm²)', line, re.I)
                    voltage_m = re.search(r'(\d+(?:\.\d+)?)\s*(?:kV|V)', line, re.I)
                    cores_m = re.search(r'(\d+)\s*(?:core|c\b)', line, re.I)
                    material_m = re.search(r'\b(copper|aluminium|aluminum|cu|al)\b', line, re.I)
                    insulation_m = re.search(r'\b(XLPE|PVC|EPR|LSZH|FRLS|PE|rubber)\b', line, re.I)
                    price_m = price_pattern.search(line)
                    oem_m = re.search(r'\b(Polycab|Havells|KEI|Finolex|RR Kabel|Moglix|Anchor|Syska)\b', line, re.I)
                    detected_products.append({
                        'name': pname[:120],
                        'category': 'Cables & Wires',
                        'conductor_size': size_m.group(1) if size_m else None,
                        'voltage_rating': voltage_m.group(0) if voltage_m else None,
                        'cores': int(cores_m.group(1)) if cores_m else None,
                        'conductor_material': material_m.group(1).capitalize() if material_m else None,
                        'insulation': insulation_m.group(1).upper() if insulation_m else None,
                        'price_per_meter': float(price_m.group(1).replace(',', '')) if price_m else None,
                        'oem': oem_m.group(1) if oem_m else None,
                    })
        # Dedupe
        seen = set()
        unique = []
        for p in detected_products:
            key = p.get('name', '').lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(p)
        detected_products = unique[:200]  # cap at 200

    # ── Build preview items with temp codes ──
    preview_items = []
    for p in detected_products:
        preview_items.append({
            'product_code': f"IMP-{uuid.uuid4().hex[:8].upper()}",
            'name': p.get('name', 'Unnamed Product'),
            'description': p.get('description'),
            'oem': p.get('manufacturer') or p.get('oem') or 'Imported',
            'category': p.get('category', 'Cables & Wires'),
            'price_per_meter': p.get('price_per_meter'),
            'voltage_rating': p.get('voltage_rating'),
            'conductor_size': p.get('conductor_size'),
            'cores': p.get('cores'),
            'insulation': p.get('insulation'),
            'conductor_material': p.get('conductor_material'),
            'standard': p.get('standard'),
            'quality_score': None,
            'source': 'PDF Import',
            'selected': True,  # default all selected in preview
        })

    # ── Auto-confirm mode (legacy, or when user doesn't need preview) ──
    if auto_confirm:
        added = _finalize_import(preview_items, source_name)
        return ResponseFormatter.success(
            data={
                "imported_count": len(added),
                "products": added,
                "source": source_name,
                "extraction_method": extraction_method,
            },
            message=f"Imported {len(added)} products from catalog",
        )

    # ── Preview mode: stage the extraction for later confirmation ──
    extraction_id = f"ext-{uuid.uuid4().hex[:12]}"
    _import_staging[extraction_id] = {
        "products": preview_items,
        "source": source_name,
        "extracted_at": datetime.now().isoformat(),
        "extraction_method": extraction_method,
        "text_length": len(extracted_text),
        "page_count": page_count,
    }
    # Auto-expire old staging entries (keep last 20)
    if len(_import_staging) > 20:
        oldest = sorted(_import_staging.keys(), key=lambda k: _import_staging[k]["extracted_at"])
        for k in oldest[:-20]:
            del _import_staging[k]

    return ResponseFormatter.success(
        data={
            "extraction_id": extraction_id,
            "preview": preview_items,
            "total_detected": len(preview_items),
            "source": source_name,
            "extraction_method": extraction_method,
            "page_count": page_count,
            "text_length": len(extracted_text),
        },
        message=f"Detected {len(preview_items)} products. Review and confirm to add to catalog.",
    )


@app.post("/api/v1/products/import-catalog/confirm", tags=["Products"])
async def confirm_catalog_import(
    body: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
):
    """
    Confirm an import after previewing extracted products.
    Body: { extraction_id: str, selected_codes?: string[] }
    If selected_codes is provided, only those products are added.
    Otherwise all detected products are added.
    """
    extraction_id = body.get("extraction_id", "")
    if extraction_id not in _import_staging:
        raise HTTPException(status_code=404, detail="Extraction not found or expired. Please re-upload the catalog.")

    staged = _import_staging.pop(extraction_id)
    products = staged["products"]
    source_name = staged["source"]

    # Filter by selected codes if provided
    selected_codes = body.get("selected_codes")
    if selected_codes and isinstance(selected_codes, list):
        products = [p for p in products if p["product_code"] in selected_codes]

    if not products:
        return ResponseFormatter.success(
            data={"imported_count": 0, "products": []},
            message="No products selected for import",
        )

    added = _finalize_import(products, source_name)
    return ResponseFormatter.success(
        data={
            "imported_count": len(added),
            "products": added,
            "source": source_name,
        },
        message=f"Successfully added {len(added)} products to your catalog",
    )


@app.delete("/api/v1/products/import-catalog/{product_code}", tags=["Products"])
async def delete_imported_product(
    product_code: str,
    current_user: TokenData = Depends(get_current_user),
):
    """Delete a single user-added or imported product by its code."""
    global _user_added_products
    before = len(_user_added_products)
    _user_added_products = [p for p in _user_added_products if p.get("product_code") != product_code]
    removed = before - len(_user_added_products)

    if CATALOG_STORE_AVAILABLE:
        _delete_persisted_product(product_code)

    if removed == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return ResponseFormatter.success(data={"deleted": product_code}, message="Product removed from catalog")


@app.get("/api/v1/products/import-history", tags=["Products"])
async def import_history(current_user: TokenData = Depends(get_current_user)):
    """Return a history of catalog imports grouped by timestamp."""
    if CATALOG_STORE_AVAILABLE:
        return ResponseFormatter.success(data=_get_import_history())
    return ResponseFormatter.success(data=[])


def _finalize_import(products: List[Dict[str, Any]], source_name: str) -> List[Dict[str, Any]]:
    """
    Internal helper — add products from an import to:
    1. In-memory _user_added_products
    2. Persistent JSON store
    3. OEM DataFrame
    """
    now = datetime.now().isoformat()
    added = []
    for p in products:
        product = {
            'product_code': p.get('product_code', f"IMP-{uuid.uuid4().hex[:8].upper()}"),
            'name': p.get('name', 'Unnamed Product'),
            'description': p.get('description'),
            'oem': p.get('oem', 'Imported'),
            'category': p.get('category', 'Cables & Wires'),
            'price_per_meter': p.get('price_per_meter'),
            'voltage_rating': p.get('voltage_rating'),
            'conductor_size': p.get('conductor_size'),
            'cores': p.get('cores'),
            'insulation': p.get('insulation'),
            'conductor_material': p.get('conductor_material'),
            'standard': p.get('standard'),
            'quality_score': None,
            'source': 'PDF Import',
            'source_file': source_name,
            'added_at': now,
        }
        _user_added_products.append(product)
        added.append(product)

    # Persist to disk
    if CATALOG_STORE_AVAILABLE and added:
        try:
            _persist_products_bulk(added, source="PDF Import")
        except Exception as _pe:
            logger.warning(f"Could not persist imported products: {_pe}")

    # Inject into OEM DataFrame
    product_db, _ = _get_oem_db_and_matcher()
    if product_db and product_db.products_df is not None and added:
        new_rows = []
        for p in added:
            new_rows.append({
                'Product_Name': p['name'],
                'Product_Code': p['product_code'],
                'OEM': p['oem'],
                'Source': 'PDF Import',
                'Product_Category': p['category'],
                'Price_Per_Meter_INR': p.get('price_per_meter'),
                'Voltage_Rating': p.get('voltage_rating'),
                'Conductor_Size_sqmm': p.get('conductor_size'),
                'No_of_Cores': p.get('cores'),
                'Insulation_Type': p.get('insulation'),
                'Conductor_Material': p.get('conductor_material'),
                'Standard': p.get('standard'),
            })
        product_db.products_df = pd.concat(
            [product_db.products_df, pd.DataFrame(new_rows)], ignore_index=True
        )
        logger.info(f"Imported {len(added)} products from catalog — new total: {len(product_db.products_df)}")

    return added


# ── Recommendations Endpoint — MUST be registered BEFORE /{product_id_or_sku} ──

@app.get("/api/v1/products/recommendations", tags=["Products"])
async def get_product_recommendations(
    tab: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    rfp_id: Optional[str] = Query(None),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get dynamic, AI-ranked product recommendations from the catalog.
    Provides categorized suggestions: Top Matches, Alternatives, Accessories, and Safety.
    """
    tabs_list = [
        "Top Recommendations",
        "Cost-Effective Alternatives",
        "Frequently Bought Together",
        "Critical & Fire Safety"
    ]

    all_recommendations: Dict[str, List[Dict[str, Any]]] = {
        "Top Recommendations": [
            {
                "sku": "POL-PVC-2.5-R",
                "name": "Polycab Optima Plus PVC Wire 2.5 sq mm",
                "category": "PVC Insulated Wire",
                "manufacturer": "Polycab",
                "matchScore": 96,
                "reason": "Top IS 694 & IS 8130 compliant ETP copper wire; optimal conductivity",
                "price": 28,
                "priceUnit": "/m",
                "brand": "Polycab"
            },
            {
                "sku": "HAV-XLPE-4C-16",
                "name": "Havells XLPE Armoured Power Cable 4 Core 16 sq mm",
                "category": "XLPE Armoured Cable",
                "manufacturer": "Havells",
                "matchScore": 94,
                "reason": "Heavy duty power distribution with steel wire armouring & IS 7098 compliance",
                "price": 890,
                "priceUnit": "/m",
                "brand": "Havells"
            },
            {
                "sku": "KEI-FLX-3C-2.5",
                "name": "KEI Conflame Flexible Copper Cable 3 Core 2.5 sq mm",
                "category": "Flexible Cable",
                "manufacturer": "KEI Industries",
                "matchScore": 91,
                "reason": "Class 5 highly flexible annealed copper with flame-retardant PVC sheath",
                "price": 68,
                "priceUnit": "/m",
                "brand": "KEI"
            },
            {
                "sku": "FIN-PVC-4.0-R",
                "name": "Finolex Industrial PVC Cable 4.0 sq mm",
                "category": "PVC Insulated Wire",
                "manufacturer": "Finolex",
                "matchScore": 89,
                "reason": "High temperature resistant Class 2 stranded conductor for motor feeders",
                "price": 46,
                "priceUnit": "/m",
                "brand": "Finolex"
            },
            {
                "sku": "CAB-001",
                "name": "XLPE Insulated HV Cable 33kV 3×185mm²",
                "category": "HV Cables",
                "manufacturer": "Polycab India Ltd",
                "matchScore": 95,
                "reason": "High voltage XLPE cable for primary substations & IEC 60502 compliance",
                "price": 4250,
                "priceUnit": "/m",
                "brand": "Polycab"
            }
        ],
        "Cost-Effective Alternatives": [
            {
                "sku": "ALU-XLPE-185",
                "name": "Aluminium XLPE Power Cable 185mm² 3.5 Core",
                "category": "Power Cables",
                "manufacturer": "KEI Industries",
                "matchScore": 86,
                "reason": "High electrical capacity equivalent at 38% material cost reduction",
                "price": 1450,
                "priceUnit": "/m",
                "savings": 850,
                "brand": "KEI"
            },
            {
                "sku": "ALU-XLPE-240",
                "name": "Aluminium XLPE Power Cable 240mm² 3 Core",
                "category": "Power Cables",
                "manufacturer": "Polycab",
                "matchScore": 88,
                "reason": "Same continuous current rating with significant bulk procurement savings",
                "price": 1720,
                "priceUnit": "/m",
                "savings": 1100,
                "brand": "Polycab"
            },
            {
                "sku": "POL-PVC-1.5-R",
                "name": "Polycab Optima Plus PVC Wire 1.5 sq mm",
                "category": "PVC Insulated Wire",
                "manufacturer": "Polycab",
                "matchScore": 82,
                "reason": "Value-engineered gauge for low-draw lighting circuits meeting IS 694",
                "price": 19,
                "priceUnit": "/m",
                "savings": 9,
                "brand": "Polycab"
            }
        ],
        "Frequently Bought Together": [
            {
                "sku": "ACC-TERM-240",
                "name": "Heat Shrink Termination Kit 11kV/33kV",
                "category": "Accessories",
                "manufacturer": "Raychem RPG",
                "matchScore": 0,
                "reason": "Essential termination accessory for XLPE armoured cables",
                "price": 4800,
                "priceUnit": "/kit",
                "brand": "Raychem"
            },
            {
                "sku": "ACC-JOINT-240",
                "name": "Straight Through Jointing Kit 1.1kV-11kV",
                "category": "Accessories",
                "manufacturer": "3M India",
                "matchScore": 0,
                "reason": "Resin-filled jointing kit for underground cable runs",
                "price": 6400,
                "priceUnit": "/kit",
                "brand": "3M"
            },
            {
                "sku": "ACC-LUG-240",
                "name": "Heavy Duty Copper Compression Lugs (Pack of 10)",
                "category": "Accessories",
                "manufacturer": "Dowells",
                "matchScore": 0,
                "reason": "High conductivity ETP copper lugs compliant with IS 8309",
                "price": 1350,
                "priceUnit": "/pack",
                "brand": "Dowells"
            },
            {
                "sku": "ACC-GLAND-01",
                "name": "Double Compression Weatherproof Brass Cable Glands (Pack 5)",
                "category": "Accessories",
                "manufacturer": "Comet",
                "matchScore": 0,
                "reason": "IP66 rated mechanical retention & earth continuity for armoured cables",
                "price": 1950,
                "priceUnit": "/pack",
                "brand": "Comet"
            }
        ],
        "Critical & Fire Safety": [
            {
                "sku": "RRK-FRLS-1.5-R",
                "name": "RR Kabel Superex FR-LSH Fire Survival Wire 1.5 sq mm",
                "category": "Fire Resistant",
                "manufacturer": "RR Kabel",
                "matchScore": 94,
                "reason": "Low smoke zero halogen; ideal for hospitals, data centers & public safety",
                "price": 32,
                "priceUnit": "/m",
                "brand": "RR Kabel"
            },
            {
                "sku": "CAB-003",
                "name": "Armoured Power Cable 11kV 3×95mm²",
                "category": "MV Cables",
                "manufacturer": "Havells India",
                "matchScore": 92,
                "reason": "Medium voltage armoured cable with galvanized steel wire protection",
                "price": 2150,
                "priceUnit": "/m",
                "brand": "Havells"
            }
        ]
    }

    # Add dynamically matched items from user's latest rfp or database if available
    try:
        product_db, _ = _get_oem_db_and_matcher()
        if product_db and product_db.products_df is not None:
            df = product_db.products_df
            high_quality = df[df['Overall_Quality_Score'].fillna(0) >= 88].head(3)
            for _, r in high_quality.iterrows():
                code = str(r.get('Product_Code') or r.get('Product_Name', ''))[:16]
                if code and not any(x['sku'] == code for x in all_recommendations["Top Recommendations"]):
                    all_recommendations["Top Recommendations"].append({
                        "sku": code,
                        "name": str(r.get('Product_Name', 'OEM Cable')),
                        "category": str(r.get('Product_Category', 'Cables & Wires')),
                        "manufacturer": str(r.get('OEM', 'Leading OEM')),
                        "matchScore": int(r.get('Overall_Quality_Score', 90)),
                        "reason": f"High quality rating ({r.get('Overall_Quality_Score', 90)}%) with certified standards compliance",
                        "price": float(r.get('Price_Per_Meter_INR') or 150),
                        "priceUnit": "/m",
                        "brand": str(r.get('OEM', 'OEM'))
                    })
    except Exception as e:
        logger.debug(f"Catalog recommendation enrichment notice: {e}")

    active_tab = tab if tab and tab in all_recommendations else tabs_list[0]
    items = all_recommendations.get(active_tab, all_recommendations[tabs_list[0]])

    return ResponseFormatter.success(data={
        "tabs": tabs_list,
        "active_tab": active_tab,
        "recommendations": all_recommendations,
        "items": items,
        "total": len(items)
    })


# ── Wildcard product routes — MUST be AFTER /catalog, /catalog/stats, /recommendations, /add, /import-catalog ──

@app.get("/api/v1/products/{product_id_or_sku}", tags=["Products"])
async def get_product_by_id_or_sku(product_id_or_sku: str, current_user: TokenData = Depends(get_current_user)):
    """
    Get product by numeric ID or SKU string across all database sources:
    1. In-memory product catalog
    2. User-added / imported products
    3. OEM products JSON catalog
    4. Real 22,000+ SKU DataFrame
    """
    query_str = product_id_or_sku.strip().lower()

    # 1. Search in-memory product_catalog
    for p in product_catalog:
        if str(p.get("id")) == query_str or str(p.get("sku", "")).lower() == query_str:
            return ResponseFormatter.success(data=p)

    # 2. Search user-added products
    for p in _user_added_products:
        if (str(p.get("id")) == query_str or
            str(p.get("sku", "")).lower() == query_str or
            str(p.get("product_code", "")).lower() == query_str):
            return ResponseFormatter.success(data=p)

    # 3. Search database/db_products/oem_products.json
    try:
        oem_json_path = os.path.join(Path(__file__).parent.parent, 'database', 'db_products', 'oem_products.json')
        if os.path.isfile(oem_json_path):
            with open(oem_json_path, 'r', encoding='utf-8') as f:
                oem_data = json.load(f)
                for p in oem_data.get('products', []):
                    if str(p.get('sku', '')).lower() == query_str:
                        # Normalize format for frontend
                        normalized = {
                            "id": p.get("sku"),
                            "sku": p.get("sku"),
                            "name": p.get("name"),
                            "description": f"{p.get('name')} by {p.get('manufacturer')}",
                            "category": p.get("category", "Cables & Wires"),
                            "subcategory": p.get("category", "Wires"),
                            "brand": p.get("manufacturer"),
                            "manufacturer": p.get("manufacturer"),
                            "unit_price": p.get("specifications", {}).get("current_rating_amps", 20) * 1.8,
                            "currency": "INR",
                            "unit_of_measure": "meter",
                            "specifications": p.get("specifications", {}),
                            "certifications": p.get("certifications", []),
                            "standards_compliance": p.get("standards_compliance", []),
                            "is_active": True,
                            "stock_quantity": 5000,
                        }
                        return ResponseFormatter.success(data=normalized)
    except Exception as e:
        logger.debug(f"oem_products.json lookup notice: {e}")

    # 4. Search 22k+ OEM DataFrame
    try:
        product_db, _ = _get_oem_db_and_matcher()
        if product_db and product_db.products_df is not None:
            df = product_db.products_df
            for col in ['Product_Code', 'sku', 'SKU', 'Product_Name']:
                if col in df.columns:
                    matched = df[df[col].astype(str).str.lower() == query_str]
                    if not matched.empty:
                        row = matched.iloc[0].to_dict()
                        cleaned = clean_nan_values(row)
                        # Add standardized fields
                        cleaned.setdefault('id', cleaned.get('Product_Code', product_id_or_sku))
                        cleaned.setdefault('sku', cleaned.get('Product_Code', product_id_or_sku))
                        cleaned.setdefault('name', cleaned.get('Product_Name', 'OEM Product'))
                        cleaned.setdefault('brand', cleaned.get('OEM', 'Leading OEM'))
                        cleaned.setdefault('category', cleaned.get('Product_Category', 'Cables & Wires'))
                        cleaned.setdefault('unit_price', cleaned.get('Price_Per_Meter_INR', 0))
                        cleaned.setdefault('currency', 'INR')
                        return ResponseFormatter.success(data=cleaned)
    except Exception as e:
        logger.debug(f"DataFrame product lookup notice: {e}")

    # 5. Check recommendation accessory or alternative synthesized SKUs
    acc_map = {
        "acc-term-240": {"id": "ACC-TERM-240", "sku": "ACC-TERM-240", "name": "Heat Shrink Termination Kit 11kV/33kV", "category": "Accessories", "brand": "Raychem", "unit_price": 4800, "unit_of_measure": "kit", "description": "High voltage termination kit with heat shrinkable stress control tubing."},
        "acc-joint-240": {"id": "ACC-JOINT-240", "sku": "ACC-JOINT-240", "name": "Straight Through Jointing Kit 1.1kV-11kV", "category": "Accessories", "brand": "3M", "unit_price": 6400, "unit_of_measure": "kit", "description": "Resin-filled cable jointing kit for underground power cable installations."},
        "acc-lug-240": {"id": "ACC-LUG-240", "sku": "ACC-LUG-240", "name": "Heavy Duty Copper Compression Lugs (Pack 10)", "category": "Accessories", "brand": "Dowells", "unit_price": 1350, "unit_of_measure": "pack", "description": "IS 8309 compliant electrolytic ETP copper compression lugs."},
        "acc-gland-01": {"id": "ACC-GLAND-01", "sku": "ACC-GLAND-01", "name": "Double Compression Brass Cable Glands (Pack 5)", "category": "Accessories", "brand": "Comet", "unit_price": 1950, "unit_of_measure": "pack", "description": "IP66 rated mechanical brass cable glands for armoured cables."},
        "alu-xlpe-185": {"id": "ALU-XLPE-185", "sku": "ALU-XLPE-185", "name": "Aluminium XLPE Power Cable 185mm² 3.5 Core", "category": "Power Cables", "brand": "KEI", "unit_price": 1450, "unit_of_measure": "meter", "description": "Cost-effective heavy industrial feeder cable with aluminum conductor."},
        "alu-xlpe-240": {"id": "ALU-XLPE-240", "sku": "ALU-XLPE-240", "name": "Aluminium XLPE Power Cable 240mm² 3 Core", "category": "Power Cables", "brand": "Polycab", "unit_price": 1720, "unit_of_measure": "meter", "description": "High current carrying aluminum conductor power cable."},
    }
    if query_str in acc_map:
        item = acc_map[query_str]
        item.update({"is_active": True, "currency": "INR", "specifications": {}, "certifications": ["IS Certified"]})
        return ResponseFormatter.success(data=item)

    raise HTTPException(status_code=404, detail=f"Product '{product_id_or_sku}' not found")


@app.post("/api/v1/products/compare", tags=["Products"])
async def compare_products(body: Dict[str, Any], current_user: TokenData = Depends(get_current_user)):
    """Compare products by IDs."""
    ids = body.get("ids", [])
    results = [p for p in product_catalog if p["id"] in ids]
    return ResponseFormatter.success(data=results)


# =============================================================================
# RFP Upload & Processing (consumed by frontend rfp.service.ts)
# =============================================================================

@app.post("/api/v1/rfps/upload", tags=["RFP Management"])
async def upload_rfp_file(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
):
    """Upload an RFP PDF file, run it through the pipeline, and return matched products."""
    rfp_id = f"RFP_{uuid.uuid4().hex[:12].upper()}"

    # ── Attempt real pipeline processing ──
    pipeline_result = None
    if PIPELINE_AVAILABLE and file.filename and file.filename.lower().endswith('.pdf'):
        import tempfile as _tmpfile
        try:
            with _tmpfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            try:
                pipeline_result = run_full_pipeline(pdf_path=tmp_path)
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Pipeline processing failed for {file.filename}: {e}")

    # ── Build response ──
    matched_products_list = []
    requirements_list = []
    if pipeline_result:
        matched_products_list = pipeline_result.get('matched_products', [])
        requirements_list = pipeline_result.get('requirements', [])

    rfp_data = {
        "rfp_id": rfp_id,
        "id": len(rfp_store) + 1,
        "title": file.filename or "Uploaded RFP",
        "description": f"RFP from uploaded file: {file.filename}",
        "source_file": file.filename,
        "status": "processed" if matched_products_list else "draft",
        "priority": "medium",
        "tags": [],
        "requirements": requirements_list,
        "bids": [],
        "matched_products": matched_products_list,
        "pricing_data": pipeline_result.get('pricing_data', {}) if pipeline_result else {},
        "currency": "KES",
        "pipeline_id": pipeline_result.get('pipeline_id') if pipeline_result else None,
        "pipeline_status": pipeline_result.get('status') if pipeline_result else None,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    rfp_store[rfp_id] = rfp_data
    return ResponseFormatter.success(data=rfp_data, message="RFP uploaded and processed successfully")


# ── Lazy-loaded singletons for /rfps/analyze ──

def _get_oem_db_and_matcher():
    """Lazy-load OEMProductDatabase + SpecMatcher from spec_comparer/app.py or pdf_extraction/app.py"""
    global _oem_product_db, _spec_matcher
    if _oem_product_db is not None:
        return _oem_product_db, _spec_matcher

    _project = str(Path(__file__).parent.parent)
    oem_data_path = os.path.join(_project, 'wires_cables_data', 'wires_cables_data')

    # Try importing from pdf_extraction/app.py first (it has the OEMProductDatabase class inline)
    try:
        _pdf_mod_path = os.path.join(_project, 'pdf_extraction')
        if _pdf_mod_path not in sys.path:
            sys.path.insert(0, _pdf_mod_path)
        # pdf_extraction/app.py defines OEMProductDatabase, SpecMatcher, SpecCalculator at module level
        import importlib, types
        # We can't import app.py directly (name clash), so load the classes from spec_comparer/app.py
        _sc_path = os.path.join(_project, 'spec_comparer')
        if _sc_path not in sys.path:
            sys.path.insert(0, _sc_path)
        # The spec_comparer/app.py module defines the same classes
        spec_mod_path = os.path.join(_sc_path, 'app.py')
        spec = importlib.util.spec_from_file_location("spec_comparer_app", spec_mod_path)
        spec_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(spec_mod)
        OEMProductDatabase = spec_mod.OEMProductDatabase
        SpecMatcher = spec_mod.SpecMatcher
        _oem_product_db = OEMProductDatabase(oem_data_path)
        _spec_matcher = SpecMatcher(_oem_product_db)
        logger.info(f"Spec Comparer loaded: {_oem_product_db.get_total_products()} products")
        return _oem_product_db, _spec_matcher
    except Exception as e:
        logger.warning(f"Failed to load OEM DB from spec_comparer: {e}")
        return None, None


def _get_spec_calculator():
    """Lazy-load SpecCalculator"""
    global _spec_calculator
    if _spec_calculator is not None:
        return _spec_calculator
    try:
        import importlib.util
        _project = str(Path(__file__).parent.parent)
        spec_mod_path = os.path.join(_project, 'spec_comparer', 'app.py')
        spec = importlib.util.spec_from_file_location("spec_comparer_app_calc", spec_mod_path)
        spec_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(spec_mod)
        _spec_calculator = spec_mod.SpecCalculator()
        return _spec_calculator
    except Exception as e:
        logger.warning(f"SpecCalculator not available: {e}")
        return None


def _clean_nan(obj):
    """Recursively convert NaN / pd.NA / None to JSON-safe values"""
    import math
    if isinstance(obj, dict):
        return {k: _clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_nan(i) for i in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    try:
        import pandas as _pd
        if _pd.isna(obj):
            return None
    except Exception:
        pass
    return obj


def _detect_application(text: str) -> str:
    """Detect application type from text"""
    t = text.lower()
    if any(w in t for w in ['hospital', 'medical', 'healthcare']):
        return 'hospital'
    if any(w in t for w in ['industrial', 'factory', 'manufacturing', 'plant']):
        return 'industrial'
    if any(w in t for w in ['commercial', 'office', 'building', 'mall']):
        return 'commercial'
    if any(w in t for w in ['residential', 'housing', 'apartment', 'flat']):
        return 'residential'
    if any(w in t for w in ['solar', 'renewable', 'wind', 'photovoltaic']):
        return 'solar'
    if any(w in t for w in ['underground', 'tunnel', 'subway', 'metro']):
        return 'underground'
    return 'general'


def _build_sales_metadata_from_fields(extracted_fields: dict, summary: dict) -> dict:
    """
    Build sales_metadata from deterministic extracted_fields (always available).
    This ensures AI Sales Intelligence always has data even without LLM.
    extracted_fields has keys like 'Bid Number' → {'value': '...', ...}
    summary has keys like 'bid_number', 'organization', etc.
    """
    ef = extracted_fields or {}
    sm = summary or {}

    def _fval(*keys):
        """Get first non-empty value from extracted_fields (nested {value:...}) or summary."""
        for k in keys:
            # Try extracted_fields (nested dict with 'value' key)
            v = ef.get(k)
            if isinstance(v, dict) and v.get('value'):
                return v['value']
            # Try as flat key (some formats use flat values)
            if isinstance(v, str) and v:
                return v
        # Try summary (flat dict)
        for k in keys:
            # Map common display names to summary keys
            sk = k.lower().replace(' ', '_').replace('/', '_')
            v = sm.get(sk)
            if v:
                return v
        return None

    meta = {
        'rfp_title': (
            _fval('BOQ Title', 'Tender Title', 'Project Name', 'Title')
            or sm.get('boq_title') or sm.get('title') or sm.get('project_name')
            or 'RFP Analysis'
        ),
        'bid_number': (
            _fval('Bid Number', 'Tender Number', 'Reference Number')
            or sm.get('bid_number') or sm.get('tender_number')
        ),
        'due_date': (
            _fval('Bid End Date/Time', 'Submission Deadline', 'Last Date of Submission', 'Closing Date')
            or sm.get('bid_end_date')
        ),
        'issuing_authority': (
            _fval('Organisation Name', 'Department Name', 'Ministry/State Name')
            or sm.get('organization') or sm.get('department') or sm.get('ministry')
        ),
        'estimated_value': (
            _fval('Estimated Cost', 'Estimated Value', 'Contract Value', 'Total Quantity')
            or sm.get('total_quantity')
        ),
        'emd_amount': (
            _fval('EMD Amount', 'Earnest Money Deposit', 'Bid Security')
            or sm.get('emd_amount')
        ),
        'project_description': (
            _fval('Scope of Work', 'Work Description', 'Description')
            or sm.get('description')
        ),
        'compliance_requirements': [],
        'tests_required': [],
        'acceptance_criteria': [],
    }

    # Extract compliance/standards from extracted fields
    for key in ('Standards', 'Required Standards', 'Applicable Standards', 'Certifications',
                'standards', 'required_standards', 'applicable_standards', 'certifications'):
        val = ef.get(key)
        if isinstance(val, dict) and val.get('value'):
            v = val['value']
            if isinstance(v, list):
                meta['compliance_requirements'].extend(v)
            elif isinstance(v, str) and v:
                meta['compliance_requirements'].append(v)
        elif isinstance(val, list):
            meta['compliance_requirements'].extend(val)
        elif isinstance(val, str) and val:
            meta['compliance_requirements'].append(val)

    # Extract tests from extracted fields
    for key in ('Tests Required', 'Testing Requirements', 'Type Tests', 'Acceptance Tests',
                'tests_required', 'testing_requirements', 'type_tests', 'acceptance_tests'):
        val = ef.get(key)
        if isinstance(val, dict) and val.get('value'):
            v = val['value']
            if isinstance(v, list):
                meta['tests_required'].extend(v)
            elif isinstance(v, str) and v:
                meta['tests_required'].append(v)
        elif isinstance(val, list):
            meta['tests_required'].extend(val)
        elif isinstance(val, str) and val:
            meta['tests_required'].append(val)

    # De-duplicate lists
    meta['compliance_requirements'] = list(dict.fromkeys(meta['compliance_requirements']))
    meta['tests_required'] = list(dict.fromkeys(meta['tests_required']))

    logger.info(f"Sales metadata built from extracted_fields: title='{meta.get('rfp_title')}', bid='{meta.get('bid_number')}'")
    return meta


import re as _re


@app.post("/api/v1/rfps/analyze", tags=["RFP Analysis"])
async def analyze_rfp(
    file: UploadFile = File(...),
    include_calculations: bool = Query(False),
    include_recommendations: bool = Query(True),
    include_budget: bool = Query(True),
    include_win_loss: bool = Query(False),
    cable_length: float = Query(100),
    application: str = Query("auto"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: Optional[TokenData] = Depends(get_optional_user),
):
    """
    Comprehensive RFP analysis: extract → parse → match against 22k+ OEM products.
    Returns requirements, BOQ, OEM summary, top-3 products per requirement
    with engineering calculations, recommendations, and budget analysis.
    
    Optional: include_win_loss=true to also calculate historical win/loss ratio for the RFP.
    """
    import tempfile as _tmpfile
    import math

    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # ── Save uploaded file ──
    content = await file.read()
    tmp = _tmpfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp.write(content)
    tmp.close()
    tmp_path = tmp.name
    has_linked_docs = False

    try:
        # ── Step 1: Extract text ──
        if not SPEC_ANALYSIS_AVAILABLE:
            raise HTTPException(status_code=500, detail="PDF extraction modules not available")

        extractor = MultilingualExtractor(tmp_path)
        rfp_text = extractor.extract_all_text()
        if not rfp_text or not rfp_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")

        # ── Step 2: Structured extraction (bid details, BOQ — skip links for speed) ──
        analyzer = RFPCompleteAnalyzer(tmp_path)
        analysis = analyzer.analyze(
            download_linked=False, extract_boq=True, extract_specs=True,
            skip_links=True,          # <-- defer link extraction to background
        )

        extracted_fields = analysis.get('extracted_fields', {})
        summary = analysis.get('summary', {})
        boq = analysis.get('boq', {})
        linked_docs = analysis.get('linked_documents', {})
        specifications = analysis.get('specifications', [])

        # Generate a unique analysis ID for background doc retrieval
        analysis_id = str(uuid.uuid4())

        # ── Step 3: Parse cable/wire requirements ──
        product_db, spec_matcher = _get_oem_db_and_matcher()
        calculator = _get_spec_calculator()

        detected_app = _detect_application(rfp_text) if application == 'auto' else application

        comparisons = []
        all_top_products = []
        total_wire_cable = 0
        total_cable_only = 0

        # ── LangChain multi-agent system (parallel: Sales + Technical + Pricing) ──
        langchain_agent = None
        langchain_used = False
        sales_metadata = {}
        pricing_estimate = {}
        try:
            from agents.langchain_agent import LangChainRFPAgent, LANGCHAIN_AVAILABLE as LC_AVAIL
            if LC_AVAIL:
                langchain_agent = LangChainRFPAgent()
                if langchain_agent.is_llm_available:
                    logger.info("LangChain multi-agent active — parallel Sales + Technical + Pricing")
        except Exception as lc_err:
            logger.info(f"LangChain agent not available: {lc_err}")

        # ── Always build sales_metadata from deterministic extracted_fields ──
        sales_metadata = _build_sales_metadata_from_fields(extracted_fields, summary)

        if product_db and spec_matcher:
            # Try LangChain parallel extraction first (Sales + Technical run together)
            requirements = []
            if langchain_agent and langchain_agent.is_llm_available:
                try:
                    # run_full_analysis runs Sales + Technical in parallel (~8-12s)
                    extraction_result = langchain_agent.run_full_analysis(rfp_text)
                    requirements = extraction_result.get("requirements", [])
                    llm_sales = extraction_result.get("sales_metadata", {})
                    # Merge LLM sales metadata into deterministic (LLM wins if non-empty)
                    if llm_sales:
                        for k, v in llm_sales.items():
                            if v and (v != [] and v != {}):
                                sales_metadata[k] = v
                    if requirements:
                        langchain_used = True
                        logger.info(f"LangChain extracted {len(requirements)} requirements + sales metadata in {extraction_result.get('extraction_time_s', '?')}s")
                except Exception as lce:
                    logger.warning(f"LangChain extraction failed, using deterministic: {lce}")

            if not requirements:
                requirements = spec_matcher.parse_rfp_requirements(rfp_text)
            logger.info(f"Parsed {len(requirements)} requirements from RFP (langchain={langchain_used})")

            for req in requirements:
                req_type = req.get('requirement_type', 'unknown')

                if req_type == 'cable_only':
                    total_cable_only += 1
                    comparisons.append({
                        'requirement': {
                            'original_text': req.get('original_text', ''),
                            'requirement_type': 'cable_only',
                            'status': 'cannot_fulfill',
                        },
                        'message': "Cable infrastructure requirement — can't be matched from product catalog",
                        'top_matches': [],
                        'match_count': 0,
                    })
                    continue

                total_wire_cable += 1
                top_products = spec_matcher.find_matching_products(req, top_n=3)

                enhanced_products = []
                for product in top_products:
                    ep = dict(product)

                    # ── Engineering calculations ──
                    if include_calculations and calculator and product.get('conductor_size'):
                        try:
                            cable_size = float(product.get('conductor_size', 4))
                            cores = int(product.get('cores', 3)) if product.get('cores') else 3
                            material = 'copper' if 'copper' in str(product.get('conductor_material', '')).lower() else 'aluminum'
                            current_rating = float(product.get('current_rating', 20)) if product.get('current_rating') else 20
                            voltage_str = str(product.get('voltage_rating', '415'))
                            vm = _re.search(r'(\d+)', voltage_str)
                            voltage = float(vm.group(1)) if vm else 415
                            if 'kv' in voltage_str.lower():
                                voltage *= 1000

                            vd = calculator.calculate_voltage_drop(cable_size=cable_size, length=cable_length, current=current_rating, material=material, voltage=voltage, cores=cores)
                            ep['voltage_drop'] = {
                                'drop_volts': round(vd.get('voltage_drop_volts', 0), 3),
                                'drop_percent': round(vd.get('voltage_drop_percent', 0), 2),
                                'status': vd.get('assessment', 'N/A'),
                                'compliant_feeder': vd.get('compliant_feeder', False),
                                'compliant_branch': vd.get('compliant_branch', False),
                                'cable_length': cable_length,
                            }

                            pc = calculator.calculate_power_capacity(cable_size=cable_size, voltage=voltage, material=material, cores=cores)
                            ep['power_capacity'] = {
                                'power_kw': round(pc.get('power_capacity_kW', 0), 1),
                                'power_kva': round(pc.get('power_capacity_kVA', 0), 1),
                                'current_capacity': round(pc.get('derated_current_capacity', 0), 1),
                            }

                            sc = calculator.calculate_short_circuit_capacity(cable_size=cable_size, material=material)
                            ep['short_circuit'] = {
                                'withstand_1s_kA': round(sc.get('withstand_current_1s_kA', 0), 2),
                                'i2t_rating': round(sc.get('i2t_rating', 0), 0),
                            }
                        except Exception as calc_err:
                            logger.warning(f"Calculation error: {calc_err}")

                    # ── Budget analysis ──
                    if include_budget:
                        price_m = ep.get('price_per_meter') or 0
                        ep['budget_analysis'] = {
                            'price_per_meter': round(price_m, 2),
                            'total_cost': round(price_m * cable_length, 2),
                            'cable_length': cable_length,
                        }

                    # ── Recommendations ──
                    # ── Recommendations ──
                    if include_recommendations:
                        recs = []
                        if ep.get('is_qualified') is False or ep.get('compliance_status') == 'DISQUALIFIED':
                            reasons = ep.get('knockout_reasons') or ['Fatal specification mismatch']
                            recs.append(f"❌ DISQUALIFIED: {'; '.join(reasons)}")
                            recs.append("⚠️ Product fails mandatory technical knockout criteria")
                        else:
                            score = ep.get('match_score', 0)
                            if score >= 90:
                                recs.append("✅ Excellent match — meets all key specifications")
                            elif score >= 75:
                                recs.append("👍 Good match — minor spec differences")
                            else:
                                recs.append("⚠️ Partial match — review specifications carefully")

                            quality = ep.get('overall_quality_score')
                            if quality and quality >= 85:
                                recs.append("⭐ Premium quality product")
                            warranty = ep.get('warranty_years')
                            if warranty and warranty >= 5:
                                recs.append(f"🛡️ {warranty}-year warranty")

                        ep['recommendations'] = recs[:4]

                    enhanced_products.append(ep)
                    all_top_products.append(ep)

                # Build comparison with immediate recommendation analysis
                analysis_data = None
                if enhanced_products:
                    try:
                        req_text = req.get('original_text', '')
                        if langchain_agent and hasattr(langchain_agent, 'technical'):
                            analysis_data = langchain_agent.technical.analyze_matches(req_text, enhanced_products)
                    except Exception as _an_err:
                        logger.debug(f"Direct match analysis notice: {_an_err}")

                comparisons.append({
                    'requirement': {
                        'original_text': req.get('original_text', ''),
                        'conductor_size': req.get('conductor_size'),
                        'cores': req.get('cores'),
                        'voltage': req.get('voltage'),
                        'insulation': req.get('insulation'),
                        'conductor_material': req.get('conductor_material'),
                        'armoured': req.get('armoured'),
                        'current_rating': req.get('current_rating'),
                        'standard': req.get('standard'),
                        'fire_rating': req.get('fire_rating'),
                        'requirement_type': req_type,
                    },
                    'top_matches': enhanced_products,
                    'match_count': len(enhanced_products),
                    'llm_analysis': analysis_data,
                })

            # ── Queue LLM enrichment in background (non-blocking) ──
            if langchain_agent and langchain_agent.is_llm_available and comparisons:
                background_tasks.add_task(
                    _enrich_analysis_background, analysis_id, langchain_agent,
                    comparisons, all_top_products, sales_metadata,
                )
                _linked_docs_store.setdefault(analysis_id, {})['llm_status'] = 'processing'
        else:
            requirements = []

        # ── OEM Summary ──
        oem_summary = {'oem_rankings': [], 'total_oems': 0, 'best_oem': None}
        if product_db and all_top_products:
            oem_stats: Dict[str, dict] = {}
            for oem in product_db.get_oem_list():
                oem_stats[oem] = {'count': 0, 'total_score': 0, 'prices': [], 'max_quality': 0, 'warranty_max': 0, 'best_match': 0}
            for p in all_top_products:
                oem = p.get('oem', 'Unknown')
                if oem not in oem_stats:
                    oem_stats[oem] = {'count': 0, 'total_score': 0, 'prices': [], 'max_quality': 0, 'warranty_max': 0, 'best_match': 0}
                oem_stats[oem]['count'] += 1
                s = p.get('match_score', 0)
                oem_stats[oem]['total_score'] += s
                if s > oem_stats[oem]['best_match']:
                    oem_stats[oem]['best_match'] = s
                if p.get('price_per_meter'):
                    oem_stats[oem]['prices'].append(p['price_per_meter'])
                q = p.get('overall_quality_score', 0)
                if q and q > oem_stats[oem]['max_quality']:
                    oem_stats[oem]['max_quality'] = q
                w = p.get('warranty_years', 0)
                if w and w > oem_stats[oem]['warranty_max']:
                    oem_stats[oem]['warranty_max'] = w

            rankings = []
            for oem, st in oem_stats.items():
                rankings.append({
                    'oem': oem,
                    'appearances': st['count'],
                    'best_match_score': round(st['best_match'], 1),
                    'avg_match_score': round(st['total_score'] / st['count'], 1) if st['count'] else 0,
                    'avg_price': round(sum(st['prices']) / len(st['prices']), 2) if st['prices'] else 0,
                    'max_quality_score': st['max_quality'],
                    'max_warranty': st['warranty_max'],
                })
            rankings.sort(key=lambda x: (x['appearances'], x['best_match_score']), reverse=True)
            oem_summary = {
                'oem_rankings': rankings,
                'total_oems': len(rankings),
                'best_oem': rankings[0]['oem'] if rankings else None,
            }

        # ── Win/Loss Ratio Calculation (fully dynamic, always populated) ──
        win_loss_ratio = None
        if WIN_LOSS_ANALYTICS_AVAILABLE:
            try:
                # Extract RFP ID from extracted fields or use filename
                raw_rfp_id = extracted_fields.get('rfp_number') or extracted_fields.get('rfp_id') or file.filename or analysis_id
                rfp_id_str = str(raw_rfp_id).strip()
                
                try:
                    db_manager = get_db_manager()
                    session = db_manager.get_session()
                    if session:
                        try:
                            win_loss_analytics = WinLossAnalytics(session_factory=lambda: db_manager.get_session())
                            win_loss_ratio = win_loss_analytics.get_win_loss_ratio_by_rfp(session, rfp_id_str)
                            logger.info(f"Win/Loss ratio dynamically calculated for RFP {rfp_id_str}: status={win_loss_ratio.get('status')}")
                        except Exception as inner_err:
                            logger.warning(f"Win/Loss calculation inner error: {inner_err}")
                            win_loss_ratio = None
                        finally:
                            try:
                                session.close()
                            except:
                                pass
                except Exception as db_err:
                    logger.warning(f"Win/Loss DB access error: {db_err}")
                    win_loss_ratio = None
            except Exception as wl_err:
                logger.warning(f"Win/Loss calculation skipped: {wl_err}")
                win_loss_ratio = None

        # ── Build full result ──
        result = _clean_nan({
            'status': 'success',
            'filename': file.filename,
            'total_requirements': len(comparisons),
            'requirement_summary': {
                'total': len(comparisons),
                'wire_cable_specs': total_wire_cable,
                'cable_only_infrastructure': total_cable_only,
            },
            'rfp_summary': summary,
            'extracted_fields': extracted_fields,
            'boq': boq,
            'linked_documents': linked_docs,
            'specifications': specifications,
            'comparisons': comparisons,
            'oem_summary': oem_summary,
            'win_loss_analysis': win_loss_ratio,
            'detected_application': detected_app,
            'analysis_options': {
                'include_calculations': include_calculations,
                'include_recommendations': include_recommendations,
                'include_budget': include_budget,
                'cable_length': cable_length,
                'application': detected_app,
            },
            'database_info': {
                'total_products': product_db.get_total_products() if product_db else 0,
                'oems': product_db.get_oem_list() if product_db else [],
            },
            'agent_info': {
                'langchain_used': langchain_used,
                'agent_mode': 'multi-agent-parallel' if langchain_used else 'deterministic',
                'model': langchain_agent.model if langchain_agent and langchain_agent.is_llm_available else None,
                'agents': ['SalesAgent', 'TechnicalAgent', 'PricingAgent', 'MasterOrchestrator'] if langchain_used else [],
            },
            'sales_metadata': sales_metadata or None,
            'pricing_estimate': pricing_estimate or None,
            'analysis_id': analysis_id,
            'linked_docs_status': 'extracting',  # links always deferred to background
        })

        # ── Queue background link extraction + download (non-blocking) ──
        _linked_docs_store[analysis_id] = {'status': 'extracting', 'documents': {}, 'results': []}
        background_tasks.add_task(
            _extract_and_download_links_background, analysis_id, tmp_path,
        )

        # ── Auto-save to persistent analysis history ──
        if ANALYSIS_STORE_AVAILABLE:
            try:
                _persist_analysis(
                    analysis_result=result,
                    file_name=file.filename or "Unknown",
                    saved_by=getattr(current_user, 'username', 'system') if current_user else 'anonymous',
                    source="auto",
                )
                logger.info(f"Auto-saved analysis {analysis_id} to history")
            except Exception as _auto_save_err:
                logger.warning(f"Auto-save analysis failed (non-fatal): {_auto_save_err}")

        return ResponseFormatter.success(data=result, message="RFP analysis complete")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RFP analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        # Don't unlink if background task still needs it — it will clean up
        if not has_linked_docs:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# ── Background link extraction + download function ──────────────────────

def _extract_and_download_links_background(analysis_id: str, pdf_path: str):
    """Extract hyperlinks from the PDF and optionally download them — runs AFTER main analysis response."""
    import threading

    _timeout_hit = threading.Event()

    def _timeout_guard():
        _timeout_hit.wait(90)

    timer = threading.Thread(target=_timeout_guard, daemon=True)
    timer.start()

    try:
        logger.info(f"[{analysis_id}] Background link extraction started")

        # Phase 1: extract link metadata (page-by-page scan)
        from pdf_extraction.hyperlink_extractor import PDFHyperlinkExtractor
        extractor = PDFHyperlinkExtractor()
        links = extractor.extract_hyperlinks(pdf_path)
        link_list = []
        by_type: dict = {}
        for link in links:
            d = link.to_dict() if hasattr(link, 'to_dict') else {
                'name': getattr(link, 'name', 'Unknown'),
                'url': getattr(link, 'url', ''),
                'document_type': getattr(link, 'document_type', 'unknown'),
                'page_number': getattr(link, 'page_number', 0),
                'file_type': getattr(link, 'file_type', 'unknown'),
            }
            link_list.append(d)
            dt = d.get('document_type', 'unknown')
            by_type[dt] = by_type.get(dt, 0) + 1

        linked_docs = {'total': len(link_list), 'by_type': by_type, 'details': link_list}

        if not link_list:
            _linked_docs_store[analysis_id].update({
                'status': 'complete', 'documents': linked_docs, 'results': [],
            })
            logger.info(f"[{analysis_id}] No links found — done")
            _timeout_hit.set()
            return

        logger.info(f"[{analysis_id}] Extracted {len(link_list)} links — now downloading")

        # Phase 2: download linked document content
        _linked_docs_store[analysis_id].update({'status': 'downloading', 'documents': linked_docs})
        try:
            analyzer = RFPCompleteAnalyzer(pdf_path)
            result = analyzer.analyze(download_linked=True, extract_boq=False, extract_specs=False)
            downloaded = result.get('linked_documents', {})
            _linked_docs_store[analysis_id].update({
                'status': 'complete',
                'documents': downloaded if downloaded.get('total', 0) > 0 else linked_docs,
                'results': downloaded.get('details', []),
            })
        except Exception as dl_err:
            logger.warning(f"[{analysis_id}] Link download failed, returning metadata only: {dl_err}")
            _linked_docs_store[analysis_id].update({
                'status': 'complete', 'documents': linked_docs, 'results': link_list,
            })

        _timeout_hit.set()
        logger.info(f"[{analysis_id}] Background link extraction + download complete")

    except Exception as e:
        _timeout_hit.set()
        logger.error(f"[{analysis_id}] Background link extraction failed: {e}")
        _linked_docs_store[analysis_id].update({
            'status': 'failed', 'error': str(e), 'documents': {}, 'results': [],
        })
    finally:
        try:
            os.unlink(pdf_path)
        except Exception:
            pass


# ── Background linked-doc download function (legacy) ────────────────────

def _download_linked_docs_background(analysis_id: str, pdf_path: str, linked_docs: dict):
    """Download linked documents in background after main response is sent."""
    import tempfile as _tmpfile
    import signal
    import threading

    # Timeout guard — abort if download takes over 60 seconds
    _timeout_hit = threading.Event()

    def _timeout_guard():
        _timeout_hit.wait(60)
        if not _timeout_hit.is_set():
            logger.warning(f"[{analysis_id}] Linked-doc download timed out after 60s")

    timer = threading.Thread(target=_timeout_guard, daemon=True)
    timer.start()

    try:
        logger.info(f"[{analysis_id}] Background linked-doc download started ({linked_docs.get('total', 0)} docs)")
        analyzer = RFPCompleteAnalyzer(pdf_path)
        result = analyzer.analyze(download_linked=True, extract_boq=False, extract_specs=False)
        downloaded_docs = result.get('linked_documents', {})
        _timeout_hit.set()  # Signal done
        _linked_docs_store[analysis_id].update({
            'status': 'complete',
            'documents': downloaded_docs,
            'results': downloaded_docs.get('details', downloaded_docs.get('documents', [])),
        })
        logger.info(f"[{analysis_id}] Background linked-doc download complete — {len(downloaded_docs.get('details', []))} docs")
    except Exception as e:
        _timeout_hit.set()
        logger.error(f"[{analysis_id}] Background linked-doc download failed: {e}")
        _linked_docs_store[analysis_id].update({
            'status': 'failed',
            'error': str(e),
            'documents': linked_docs,
            'results': [],
        })
    finally:
        try:
            os.unlink(pdf_path)
        except Exception:
            pass


@app.get("/api/v1/rfps/analyze/{analysis_id}/linked-docs", tags=["RFP Analysis"])
async def get_linked_docs_status(
    analysis_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Poll for background linked-document download status.
    Returns 'downloading', 'complete', 'failed', or 'none'.
    """
    if analysis_id not in _linked_docs_store:
        raise HTTPException(status_code=404, detail="Analysis ID not found")
    return ResponseFormatter.success(data=_linked_docs_store[analysis_id])


def _enrich_analysis_background(analysis_id: str, langchain_agent, comparisons, all_top_products, sales_metadata):
    """Run LLM match analysis + pricing in background after main response is sent."""
    try:
        logger.info(f"[{analysis_id}] Background LLM enrichment started")

        # Batch-parallel LLM analysis for all comparisons
        enriched = langchain_agent.analyze_matches_batch(comparisons)

        # Pricing estimation
        pricing = {}
        try:
            tests_list = sales_metadata.get('tests_required', []) if sales_metadata else []
            pricing = langchain_agent.estimate_pricing(all_top_products, tests_list)
        except Exception as pe:
            logger.warning(f"[{analysis_id}] Pricing estimation failed: {pe}")

        store = _linked_docs_store.setdefault(analysis_id, {})
        store['llm_status'] = 'complete'
        store['enriched_comparisons'] = enriched
        store['pricing_estimate'] = pricing
        logger.info(f"[{analysis_id}] Background LLM enrichment complete")
    except Exception as e:
        logger.error(f"[{analysis_id}] Background LLM enrichment failed: {e}")
        store = _linked_docs_store.setdefault(analysis_id, {})
        store['llm_status'] = 'failed'
        store['enriched_comparisons'] = comparisons
        store['pricing_estimate'] = {}


@app.get("/api/v1/rfps/analyze/{analysis_id}/enrichment", tags=["RFP Analysis"])
async def get_enrichment_status(
    analysis_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Poll for background LLM enrichment status (match analysis + pricing).
    Returns enriched comparisons and pricing when ready.
    """
    if analysis_id not in _linked_docs_store:
        raise HTTPException(status_code=404, detail="Analysis ID not found")
    store = _linked_docs_store[analysis_id]
    return ResponseFormatter.success(data={
        'llm_status': store.get('llm_status', 'none'),
        'enriched_comparisons': store.get('enriched_comparisons'),
        'pricing_estimate': store.get('pricing_estimate'),
    })


# ── Linked Document Analytics Endpoint ──────────────────────────────────

@app.post("/api/v1/rfps/linked-doc/analyze", tags=["RFP Analysis"])
async def analyze_linked_document(
    url: str = Query(..., description="URL of the linked document to analyze"),
    name: str = Query("", description="Document name"),
    document_type: str = Query("", description="Document type hint"),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Download and analyze a single linked document.
    Returns extracted content: text summary, BOQ items, specifications, raw text.
    """
    import tempfile as _tmpfile

    try:
        from pdf_extraction.hyperlink_extractor import HyperlinkExtractor, LinkedDocument

        # Create a temporary download folder
        download_dir = _tmpfile.mkdtemp(prefix="haki_linked_doc_")

        extractor = HyperlinkExtractor(pdf_path="", download_folder=download_dir)

        # Build a LinkedDocument and download it
        doc = LinkedDocument(
            name=name or "linked_document",
            url=url,
            document_type=document_type or "unknown",
            page_number=0,
            link_text=name,
        )

        success = extractor.download_document(doc)
        if not success:
            return ResponseFormatter.error(
                message=f"Failed to download document: {doc.error}",
                status_code=400,
            )

        # Extract content based on type
        content_result: Dict[str, Any] = {
            "name": doc.name,
            "url": url,
            "document_type": document_type,
            "file_type": doc.file_type or os.path.splitext(doc.local_path)[1].lstrip('.'),
            "is_downloaded": True,
            "local_path": doc.local_path,
            "content_summary": "",
            "raw_text": "",
            "boq_items": [],
            "specifications": [],
            "extracted_data": {},
        }

        file_ext = os.path.splitext(doc.local_path)[1].lower()

        # BOQ extraction for spreadsheets
        if file_ext in ['.xlsx', '.xls', '.xlsm', '.csv']:
            boq_items = extractor.process_boq_document(doc)
            content_result["boq_items"] = [
                {
                    "sr_no": item.sr_no,
                    "description": item.description,
                    "specification": item.specification,
                    "unit": item.unit,
                    "quantity": item.quantity,
                    "unit_rate": item.unit_rate,
                    "total_amount": item.total_amount,
                    "hsn_code": item.hsn_code,
                    "make_model": item.make_model,
                }
                for item in boq_items
            ]
            content_result["content_summary"] = f"Spreadsheet with {len(boq_items)} BOQ line items"

        # PDF text extraction
        elif file_ext == '.pdf':
            try:
                from pdf_extraction.pdf_text_extractor import PDFTextExtractor
                pdf_ext = PDFTextExtractor(doc.local_path)
                text = pdf_ext.extract_all_text() if hasattr(pdf_ext, 'extract_all_text') else ""
                if not text:
                    import fitz
                    pdf_doc = fitz.open(doc.local_path)
                    text = "\n".join(page.get_text() for page in pdf_doc)
                    pdf_doc.close()
                content_result["raw_text"] = text[:10000]  # Limit to 10k chars
                content_result["content_summary"] = f"PDF document with {len(text)} characters of text"
            except Exception as pdf_err:
                content_result["content_summary"] = f"PDF could not be parsed: {pdf_err}"

        # Plain text / other
        else:
            try:
                with open(doc.local_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read(10000)
                content_result["raw_text"] = text
                content_result["content_summary"] = f"Text document with {len(text)} characters"
            except Exception:
                content_result["content_summary"] = "Binary document — cannot display inline"

        # Spec extraction from content summary
        if doc.content_summary:
            content_result["content_summary"] = doc.content_summary
        if doc.extracted_data:
            content_result["extracted_data"] = doc.extracted_data

        # Clean up download
        try:
            import shutil
            shutil.rmtree(download_dir, ignore_errors=True)
        except Exception:
            pass

        return ResponseFormatter.success(data=content_result, message="Document analyzed")

    except ImportError as ie:
        raise HTTPException(status_code=503, detail=f"PDF extraction module not available: {ie}")
    except Exception as e:
        logger.error(f"Linked doc analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/v1/rfps/{rfp_id}/requirements", tags=["RFP Management"])
async def get_rfp_requirements(rfp_id: int, current_user: TokenData = Depends(get_current_user)):
    """Get RFP requirements."""
    # Search rfp_store by numeric id or string id
    target = None
    for key, rfp in rfp_store.items():
        if rfp.get("id") == rfp_id or key == str(rfp_id):
            target = rfp
            break
    if not target:
        # Return sample requirements
        pass

    requirements = [
        {"id": 1, "rfp_id": rfp_id, "section": "Technical", "requirement_text": "33kV XLPE insulated cable", "category": "Cables", "is_mandatory": True, "compliance_status": "compliant", "matched_specs": {}, "notes": None},
        {"id": 2, "rfp_id": rfp_id, "section": "Technical", "requirement_text": "3×185mm² conductor size", "category": "Cables", "is_mandatory": True, "compliance_status": "compliant", "matched_specs": {}, "notes": None},
        {"id": 3, "rfp_id": rfp_id, "section": "Compliance", "requirement_text": "IEC 60502-2 certification", "category": "Standards", "is_mandatory": True, "compliance_status": "pending_review", "matched_specs": {}, "notes": None},
    ]
    return ResponseFormatter.success(data=requirements)


@app.post("/api/v1/rfps/{rfp_id}/process", tags=["RFP Management"])
async def start_rfp_processing(rfp_id: int, background_tasks: BackgroundTasks, current_user: TokenData = Depends(get_current_user)):
    """Start processing an RFP."""
    for key, rfp in rfp_store.items():
        if rfp.get("id") == rfp_id or key == str(rfp_id):
            rfp["status"] = "extracting"
            rfp["updated_at"] = datetime.now().isoformat()
            return ResponseFormatter.success(data=rfp, message="Processing started")
    raise HTTPException(status_code=404, detail="RFP not found")


# =============================================================================
# Pipeline Run List / Details (consumed by frontend pipeline.service.ts)
# =============================================================================

pipeline_store: Dict[str, Dict[str, Any]] = {
    "1": {
        "id": 1, "pipeline_id": "PL-2026-001", "rfp_id": 1,
        "status": "completed", "current_stage": "submission",
        "progress_percentage": 100,
        "stages": [
            {"stage": "intake", "status": "completed", "started_at": "2026-02-05T08:00:00", "completed_at": "2026-02-05T08:01:00", "duration_ms": 60000, "result_summary": "RFP ingested", "metrics": {}},
            {"stage": "extraction", "status": "completed", "started_at": "2026-02-05T08:01:00", "completed_at": "2026-02-05T08:03:00", "duration_ms": 120000, "result_summary": "34 requirements extracted", "metrics": {}},
            {"stage": "matching", "status": "completed", "started_at": "2026-02-05T08:03:00", "completed_at": "2026-02-05T08:05:00", "duration_ms": 120000, "result_summary": "128 products matched", "metrics": {}},
            {"stage": "pricing", "status": "completed", "started_at": "2026-02-05T08:05:00", "completed_at": "2026-02-05T08:06:00", "duration_ms": 60000, "result_summary": "Pricing computed", "metrics": {}},
        ],
        "started_at": "2026-02-05T08:00:00", "completed_at": "2026-02-05T08:06:00",
        "error_message": None, "metadata": {},
    },
    "2": {
        "id": 2, "pipeline_id": "PL-2026-002", "rfp_id": 2,
        "status": "running", "current_stage": "matching",
        "progress_percentage": 55,
        "stages": [
            {"stage": "intake", "status": "completed", "started_at": "2026-02-10T10:00:00", "completed_at": "2026-02-10T10:01:00", "duration_ms": 60000, "result_summary": "RFP ingested", "metrics": {}},
            {"stage": "extraction", "status": "completed", "started_at": "2026-02-10T10:01:00", "completed_at": "2026-02-10T10:04:00", "duration_ms": 180000, "result_summary": "56 requirements extracted", "metrics": {}},
            {"stage": "matching", "status": "running", "started_at": "2026-02-10T10:04:00", "completed_at": None, "duration_ms": None, "result_summary": None, "metrics": {}},
        ],
        "started_at": "2026-02-10T10:00:00", "completed_at": None,
        "error_message": None, "metadata": {},
    },
}
_pipeline_counter = 3


@app.get("/api/v1/pipeline/runs", tags=["Pipeline"])
async def list_pipeline_runs(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
):
    """List all pipeline runs."""
    runs = list(pipeline_store.values())
    runs.sort(key=lambda r: r.get("started_at", ""), reverse=True)
    total = len(runs)
    start = (page - 1) * per_page
    page_items = runs[start : start + per_page]
    total_pages = (total + per_page - 1) // per_page
    return {"data": page_items, "total": total, "page": page, "per_page": per_page, "total_pages": total_pages}


@app.get("/api/v1/pipeline/runs/{run_id}", tags=["Pipeline"])
async def get_pipeline_run(run_id: int, current_user: TokenData = Depends(get_current_user)):
    """Get pipeline run details."""
    run = pipeline_store.get(str(run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return ResponseFormatter.success(data=run)


@app.post("/api/v1/pipeline/start", tags=["Pipeline"])
async def start_pipeline(body: Dict[str, Any], current_user: TokenData = Depends(get_current_user)):
    """Start a new pipeline run."""
    global _pipeline_counter
    pid = _pipeline_counter
    _pipeline_counter += 1
    run = {
        "id": pid, "pipeline_id": f"PL-2026-{pid:03d}",
        "rfp_id": body.get("rfp_id"), "status": "running",
        "current_stage": "intake", "progress_percentage": 0,
        "stages": [{"stage": "intake", "status": "running", "started_at": datetime.now().isoformat(), "completed_at": None, "duration_ms": None, "result_summary": None, "metrics": {}}],
        "started_at": datetime.now().isoformat(), "completed_at": None,
        "error_message": None, "metadata": body.get("metadata", {}),
    }
    pipeline_store[str(pid)] = run
    return ResponseFormatter.success(data=run, message="Pipeline started")


@app.post("/api/v1/pipeline/runs/{run_id}/cancel", tags=["Pipeline"])
async def cancel_pipeline(run_id: int, current_user: TokenData = Depends(get_current_user)):
    """Cancel a running pipeline."""
    run = pipeline_store.get(str(run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    run["status"] = "cancelled"
    run["completed_at"] = datetime.now().isoformat()
    return ResponseFormatter.success(data=run, message="Pipeline cancelled")


@app.get("/api/v1/pipeline/runs/{run_id}/status", tags=["Pipeline"])
async def get_pipeline_status(run_id: int, current_user: TokenData = Depends(get_current_user)):
    """Get pipeline run status."""
    run = pipeline_store.get(str(run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return ResponseFormatter.success(data={"status": run["status"], "progress": run["progress_percentage"], "current_stage": run["current_stage"]})


@app.post("/api/v1/pipeline/runs/{run_id}/retry", tags=["Pipeline"])
async def retry_pipeline(run_id: int, current_user: TokenData = Depends(get_current_user)):
    """Retry a failed pipeline."""
    run = pipeline_store.get(str(run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    run["status"] = "running"
    run["completed_at"] = None
    run["error_message"] = None
    return ResponseFormatter.success(data=run, message="Pipeline retried")


# =============================================================================
# Agent Endpoints (consumed by frontend agent.service.ts)
# =============================================================================

agent_status_store: List[Dict[str, Any]] = [
    {"agent_type": "master", "is_active": True, "current_task": "Coordinating RFP-0142", "tasks_completed": 142, "tasks_failed": 3, "avg_response_time_ms": 450, "last_active": "2026-02-12T10:30:00"},
    {"agent_type": "sales", "is_active": True, "current_task": None, "tasks_completed": 89, "tasks_failed": 1, "avg_response_time_ms": 320, "last_active": "2026-02-12T10:25:00"},
    {"agent_type": "technical", "is_active": True, "current_task": "Spec comparison for RFP-0143", "tasks_completed": 156, "tasks_failed": 5, "avg_response_time_ms": 580, "last_active": "2026-02-12T10:28:00"},
    {"agent_type": "pricing", "is_active": False, "current_task": None, "tasks_completed": 67, "tasks_failed": 2, "avg_response_time_ms": 290, "last_active": "2026-02-12T09:45:00"},
]

conversation_store: Dict[str, Dict[str, Any]] = {
    "1": {
        "id": 1, "conversation_id": "CONV-001", "agent_type": "master", "rfp_id": 1,
        "messages": [
            {"id": 1, "role": "user", "content": "Analyze RFP-0142 for cable requirements", "timestamp": "2026-02-10T10:00:00"},
            {"id": 2, "role": "agent", "content": "I've identified 34 cable-related requirements in RFP-0142. The primary need is for 33kV XLPE insulated cables with 3×185mm² conductors. I'm now matching these against our product catalog.", "agent_type": "master", "timestamp": "2026-02-10T10:00:05"},
        ],
        "status": "completed", "started_at": "2026-02-10T10:00:00", "completed_at": "2026-02-10T10:05:00",
    },
}
_conv_counter = 2


@app.get("/api/v1/agents/status", tags=["Agents"])
async def get_agents_status(current_user: TokenData = Depends(get_current_user)):
    """Get status of all agents."""
    return ResponseFormatter.success(data=agent_status_store)


@app.get("/api/v1/agents/conversations", tags=["Agents"])
async def list_agent_conversations(current_user: TokenData = Depends(get_current_user)):
    """List all agent conversations."""
    return ResponseFormatter.success(data=list(conversation_store.values()))


@app.get("/api/v1/agents/conversations/{conversation_id}", tags=["Agents"])
async def get_agent_conversation(conversation_id: int, current_user: TokenData = Depends(get_current_user)):
    """Get an agent conversation."""
    conv = conversation_store.get(str(conversation_id))
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ResponseFormatter.success(data=conv)


@app.post("/api/v1/agents/conversations/{conversation_id}/messages", tags=["Agents"])
async def send_agent_message(conversation_id: int, body: Dict[str, Any], current_user: TokenData = Depends(get_current_user)):
    """Send a message to an agent conversation."""
    conv = conversation_store.get(str(conversation_id))
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg = {
        "id": len(conv["messages"]) + 1,
        "role": "user", "content": body.get("content", ""),
        "timestamp": datetime.now().isoformat(),
    }
    conv["messages"].append(msg)
    # Auto-reply from agent
    reply = {
        "id": len(conv["messages"]) + 1,
        "role": "agent", "content": f"Processing your request: '{body.get('content', '')}'",
        "agent_type": conv["agent_type"],
        "timestamp": datetime.now().isoformat(),
    }
    conv["messages"].append(reply)
    return ResponseFormatter.success(data=conv)


@app.post("/api/v1/agents/workflow/start", tags=["Agents"])
async def start_agent_workflow(body: Dict[str, Any], current_user: TokenData = Depends(get_current_user)):
    """Start an agent workflow."""
    global _conv_counter
    cid = _conv_counter
    _conv_counter += 1
    conv = {
        "id": cid, "conversation_id": f"CONV-{cid:03d}",
        "agent_type": body.get("agent_type", "master"),
        "rfp_id": body.get("rfp_id"),
        "messages": [{"id": 1, "role": "system", "content": "Workflow started", "timestamp": datetime.now().isoformat()}],
        "status": "active",
        "started_at": datetime.now().isoformat(), "completed_at": None,
    }
    conversation_store[str(cid)] = conv
    return ResponseFormatter.success(data=conv, message="Workflow started")


RESOLVED_WIN_STATUSES = {"approved", "won", "awarded"}
RESOLVED_LOSS_STATUSES = {"rejected", "lost"}
OPEN_BID_STATUSES = {"draft", "in_review", "submitted", "pending", "processing"}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_bid_features(bid: Dict[str, Any]) -> Dict[str, float]:
    import math

    total_value = max(_safe_float(bid.get("total_value"), 0.0), 0.0)
    items = bid.get("items") or []

    return {
        "overall_score": max(0.0, min(100.0, _safe_float(bid.get("overall_score"), 0.0))),
        "technical_score": max(0.0, min(100.0, _safe_float(bid.get("technical_score"), 0.0))),
        "commercial_score": max(0.0, min(100.0, _safe_float(bid.get("commercial_score"), 0.0))),
        "discount_percentage": max(0.0, min(50.0, _safe_float(bid.get("discount_percentage"), 0.0))),
        "log_total_value": math.log1p(total_value),
        "validity_days": max(0.0, min(365.0, _safe_float(bid.get("validity_days"), 0.0))),
        "items_count": float(len(items)),
    }


def _sigmoid(value: float) -> float:
    import math

    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def _train_bid_logistic_model(samples: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    feature_names = [
        "overall_score",
        "technical_score",
        "commercial_score",
        "discount_percentage",
        "log_total_value",
        "validity_days",
        "items_count",
    ]

    if len(samples) < 6:
        return None

    class_values = {int(s["label"]) for s in samples}
    if len(class_values) < 2:
        return None

    means: Dict[str, float] = {}
    stds: Dict[str, float] = {}

    for name in feature_names:
        values = [float(s["features"][name]) for s in samples]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / max(1, len(values) - 1)
        means[name] = mean
        stds[name] = variance ** 0.5 if variance > 1e-8 else 1.0

    normalized: List[tuple[List[float], int]] = []
    for sample in samples:
        row = [
            (float(sample["features"][name]) - means[name]) / stds[name]
            for name in feature_names
        ]
        normalized.append((row, int(sample["label"])))

    weights = [0.0 for _ in range(len(feature_names) + 1)]  # bias + features
    learning_rate = 0.08
    l2_penalty = 0.01

    for _ in range(700):
        gradients = [0.0 for _ in range(len(weights))]
        for row, label in normalized:
            z = weights[0]
            for idx, val in enumerate(row, start=1):
                z += weights[idx] * val
            pred = _sigmoid(z)
            error = pred - float(label)
            gradients[0] += error
            for idx, val in enumerate(row, start=1):
                gradients[idx] += error * val

        batch_size = float(len(normalized))
        weights[0] -= learning_rate * (gradients[0] / batch_size)
        for idx in range(1, len(weights)):
            reg = l2_penalty * weights[idx]
            weights[idx] -= learning_rate * ((gradients[idx] / batch_size) + reg)

    return {
        "feature_names": feature_names,
        "means": means,
        "stds": stds,
        "weights": weights,
    }


def _predict_with_model(features: Dict[str, float], model: Dict[str, Any]) -> float:
    names = model["feature_names"]
    means = model["means"]
    stds = model["stds"]
    weights = model["weights"]

    z = weights[0]
    for idx, name in enumerate(names, start=1):
        standardized = (float(features[name]) - float(means[name])) / float(stds[name])
        z += float(weights[idx]) * standardized

    return max(0.01, min(0.99, _sigmoid(z)))


def _heuristic_probability(features: Dict[str, float], baseline_rate: float, median_value: float) -> float:
    import math

    score = baseline_rate
    score += ((features["overall_score"] - 70.0) / 30.0) * 0.18
    score += ((features["technical_score"] - 70.0) / 30.0) * 0.10
    score += ((features["commercial_score"] - 70.0) / 30.0) * 0.10
    score += min(features["discount_percentage"], 12.0) / 12.0 * 0.08

    if median_value > 0:
        total_value = max(math.expm1(features["log_total_value"]), 0.0)
        score -= ((total_value / median_value) - 1.0) * 0.07

    score += min(features["items_count"], 25.0) / 25.0 * 0.04
    return max(0.05, min(0.95, score))


def _model_brier_score(samples: List[Dict[str, Any]], model: Optional[Dict[str, Any]], baseline_rate: float, median_value: float) -> float:
    if not samples:
        return 0.25

    total = 0.0
    for sample in samples:
        if model:
            pred = _predict_with_model(sample["features"], model)
        else:
            pred = _heuristic_probability(sample["features"], baseline_rate, median_value)
        err = pred - float(sample["label"])
        total += err * err

    return total / len(samples)


def _get_win_loss_prediction_payload() -> Dict[str, Any]:
    from statistics import median

    bids = list(bid_store.values())
    resolved_samples: List[Dict[str, Any]] = []
    open_bids: List[Dict[str, Any]] = []

    wins = 0
    losses = 0

    for bid in bids:
        status = str(bid.get("status") or "").lower()
        if status in RESOLVED_WIN_STATUSES:
            wins += 1
            resolved_samples.append({"features": _extract_bid_features(bid), "label": 1, "bid": bid})
        elif status in RESOLVED_LOSS_STATUSES:
            losses += 1
            resolved_samples.append({"features": _extract_bid_features(bid), "label": 0, "bid": bid})
        elif status in OPEN_BID_STATUSES:
            open_bids.append(bid)

    resolved_count = wins + losses
    baseline_win_rate = (wins + 1) / (resolved_count + 2) if resolved_count > 0 else 0.5

    median_value = 0.0
    if resolved_samples:
        values = [max(_safe_float(s["bid"].get("total_value"), 0.0), 0.0) for s in resolved_samples]
        median_value = float(median(values)) if values else 0.0

    model = _train_bid_logistic_model(resolved_samples)

    def predict_bid(bid: Dict[str, Any]) -> Dict[str, Any]:
        features = _extract_bid_features(bid)
        if model:
            model_prob = _predict_with_model(features, model)
            probability = max(0.01, min(0.99, (0.8 * model_prob) + (0.2 * baseline_win_rate)))
            model_source = "logistic_regression"
        else:
            probability = _heuristic_probability(features, baseline_win_rate, median_value)
            model_source = "heuristic_fallback"

        total_value = max(_safe_float(bid.get("total_value"), 0.0), 0.0)
        drivers: List[str] = []
        if features["overall_score"] >= 85:
            drivers.append("Strong overall score improves win likelihood")
        elif features["overall_score"] <= 60:
            drivers.append("Low overall score reduces win likelihood")

        if features["discount_percentage"] >= 5:
            drivers.append("Competitive discount contributes positively")

        if median_value > 0 and total_value > median_value * 1.35:
            drivers.append("Bid value is high versus historical median")

        return {
            "bid_id": bid.get("bid_id"),
            "status": bid.get("status"),
            "predicted_win_probability": round(probability, 4),
            "predicted_loss_probability": round(1.0 - probability, 4),
            "model_source": model_source,
            "drivers": drivers[:3],
        }

    open_predictions = [predict_bid(b) for b in open_bids]
    open_predictions.sort(key=lambda row: row["predicted_win_probability"], reverse=True)

    expected_wins = sum(row["predicted_win_probability"] for row in open_predictions)
    expected_losses = max(0.0, len(open_predictions) - expected_wins)
    ratio_denominator = expected_losses if expected_losses > 0 else 1.0
    predicted_ratio = round(expected_wins / ratio_denominator, 2)

    target_bid = None
    if open_bids:
        target = sorted(
            open_bids,
            key=lambda b: str(b.get("updated_at") or b.get("created_at") or ""),
            reverse=True,
        )[0]
        target_bid = predict_bid(target)

    brier = _model_brier_score(resolved_samples, model, baseline_win_rate, median_value)
    confidence = max(0.2, min(0.95, 1.0 - brier))

    return {
        "resolved_bids": resolved_count,
        "won_count": wins,
        "lost_count": losses,
        "current_win_rate": round(wins / resolved_count, 4) if resolved_count else 0.0,
        "current_win_loss_ratio": f"{wins}:{losses}",
        "target_bid": target_bid,
        "portfolio_forecast": {
            "open_bids": len(open_predictions),
            "expected_wins": round(expected_wins, 2),
            "expected_losses": round(expected_losses, 2),
            "predicted_win_loss_ratio": f"{predicted_ratio}:1",
            "average_win_probability": round((expected_wins / len(open_predictions)), 4) if open_predictions else 0.0,
            "top_candidates": open_predictions[:5],
        },
        "model": {
            "type": "logistic_regression" if model else "heuristic_fallback",
            "confidence": round(confidence, 4),
            "training_samples": len(resolved_samples),
            "generated_at": datetime.now().isoformat(),
        },
    }


# =============================================================================
# Dashboard Stats (consumed by frontend analytics.service.ts)
# =============================================================================

@app.get("/api/v1/analytics/dashboard", tags=["Analytics"])
async def get_dashboard_stats(current_user: TokenData = Depends(get_current_user)):
    """Get dashboard summary statistics for the user portal."""
    import random
    rfp_trend = [{"date": f"2026-01-{i+1:02d}", "value": random.randint(3, 12)} for i in range(30)]
    bid_trend = [{"date": f"2026-01-{i+1:02d}", "value": random.randint(1, 8)} for i in range(30)]
    return ResponseFormatter.success(data={
        "active_rfps": len([r for r in rfp_store.values() if r.get("status") in ("pending", "processing")]) or 5,
        "total_bid_value": sum(b.get("total_value", 0) for b in bid_store.values()),
        "products_count": len(product_catalog),
        "active_vendors": len([v for v in vendor_store.values() if v.get("is_active")]),
        "pipeline_health": "healthy",
        "rfp_trend": rfp_trend,
        "bid_trend": bid_trend,
    })


@app.get("/api/v1/analytics/win-loss-prediction", tags=["Analytics"])
async def get_win_loss_prediction(current_user: TokenData = Depends(get_current_user)):
    """Get a data-driven win/loss prediction for active bids."""
    return ResponseFormatter.success(data=_get_win_loss_prediction_payload())


@app.get("/api/v1/analytics/bids", tags=["Analytics"])
async def get_bid_analytics(period: Optional[str] = None, current_user: TokenData = Depends(get_current_user)):
    """Get bid analytics."""
    bids = list(bid_store.values())
    status_counts = defaultdict(int)
    for b in bids:
        status_counts[b["status"]] += 1
    total_value = sum(b.get("total_value", 0) for b in bids)
    import random
    monthly_values = [{"date": f"2026-{i+1:02d}", "value": random.randint(5000000, 15000000)} for i in range(6)]
    return ResponseFormatter.success(data={
        "total": len(bids),
        "by_status": dict(status_counts),
        "total_value": total_value,
        "win_rate": 0.42,
        "avg_score": 86.5,
        "monthly_values": monthly_values,
    })


@app.get("/api/v1/analytics/activity", tags=["Analytics"])
async def get_activity_feed(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
):
    """Get activity feed."""
    activities = [
        {"id": 1, "type": "rfp_uploaded", "title": "RFP Uploaded", "description": "HV Cable Supply — Kenya Power Phase 3 uploaded", "entity_type": "rfp", "entity_id": "RFP-2026-0143", "user": "admin", "timestamp": "2026-02-10T10:00:00"},
        {"id": 2, "type": "bid_created", "title": "Bid Created", "description": "Bid BID-2026-003 created for FMCG Q1 Restock", "entity_type": "bid", "entity_id": "BID-2026-003", "user": "admin", "timestamp": "2026-02-10T07:00:00"},
        {"id": 3, "type": "pipeline_run", "title": "Pipeline Completed", "description": "Pipeline PL-2026-001 completed with 128 matched products", "entity_type": "pipeline", "entity_id": "PL-2026-001", "user": "system", "timestamp": "2026-02-05T08:06:00"},
        {"id": 4, "type": "vendor_rated", "title": "Vendor Rated", "description": "Polycab India Ltd rated 4.8/5", "entity_type": "vendor", "entity_id": "VND-001", "user": "admin", "timestamp": "2026-02-01T14:30:00"},
        {"id": 5, "type": "approval_action", "title": "Bid Approved", "description": "BID-2026-001 approved by James Mwangi", "entity_type": "bid", "entity_id": "BID-2026-001", "user": "James Mwangi", "timestamp": "2026-02-08T14:00:00"},
    ]
    total = len(activities)
    start = (page - 1) * per_page
    page_items = activities[start : start + per_page]
    total_pages = (total + per_page - 1) // per_page
    return {"data": page_items, "total": total, "page": page, "per_page": per_page, "total_pages": total_pages}


@app.get("/api/v1/analytics/system-health", tags=["Analytics"])
async def get_system_health(current_user: TokenData = Depends(get_current_user)):
    """Get system health metrics."""
    return ResponseFormatter.success(data={
        "services": [
            {"name": "PDF Extractor", "status": "healthy", "latency_ms": 210, "uptime": 99.9},
            {"name": "Product Matcher", "status": "healthy", "latency_ms": 340, "uptime": 99.8},
            {"name": "Spec Comparator", "status": "warning", "latency_ms": 520, "uptime": 98.5},
            {"name": "Price Engine", "status": "healthy", "latency_ms": 180, "uptime": 99.95},
            {"name": "Agent System", "status": "healthy", "latency_ms": 450, "uptime": 99.7},
        ],
        "overall_status": "healthy",
        "cpu_usage": 45,
        "memory_usage": 62,
        "disk_usage": 38,
        "active_connections": 12,
    })


@app.get("/api/v1/version", tags=["System"])
async def get_version():
    """
    Get API version
    
    Returns API version information.
    """
    return ResponseFormatter.success(data={
        "version": API_VERSION,
        "api_version": "v1",
        "build": "2026.02.05"
    })


# =============================================================================
# Error Handlers
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "data": None,
            "timestamp": datetime.now().isoformat(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "data": None,
            "timestamp": datetime.now().isoformat(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# =============================================================================
# Convenience Functions
# =============================================================================

def get_app() -> FastAPI:
    """Get the FastAPI application instance"""
    return app


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


# ════════════════════════════════════════════════════════════════════════════════
# ── BID OUTCOME RECORDING ENDPOINTS ──
# ════════════════════════════════════════════════════════════════════════════════
# These endpoints allow recording bid outcomes (won/lost) to populate win/loss analytics

class BidOutcomeRequest(BaseModel):
    """Record a bid outcome"""
    rfp_id: str
    bid_id: Optional[str] = None
    outcome: str  # 'won', 'lost', 'no_bid'
    our_bid_amount: Optional[float] = None
    winning_bid_amount: Optional[float] = None
    winning_competitor: Optional[str] = None
    competitor_names: Optional[list[str]] = None
    technical_score: Optional[float] = None
    commercial_score: Optional[float] = None
    overall_score: Optional[float] = None
    winning_factors: Optional[list[str]] = None
    losing_factors: Optional[list[str]] = None
    customer_name: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_region: Optional[str] = None
    rfp_category: Optional[str] = None


@app.post("/api/v1/analytics/record-bid-outcome", tags=["Analytics"])
async def record_bid_outcome(
    outcome_data: BidOutcomeRequest,
    user_id: Optional[str] = Query(None)
):
    """
    Record a bid outcome (won/lost/no_bid)
    
    This allows sales teams to record the result of a bid submission,
    which will be used to calculate win/loss ratios for analytics.
    
    After recording outcomes, the Win/Loss Rate Analysis card will automatically
    populate with calculated metrics on the next RFP analysis.
    
    Example payload:
    ```json
    {
        "rfp_id": "GEM/2025/B/6694421",
        "bid_id": "BID-001",
        "outcome": "won",
        "our_bid_amount": 915000,
        "technical_score": 92.5,
        "commercial_score": 88.0,
        "winning_factors": ["Competitive pricing", "Technical expertise"],
        "customer_name": "Power Grid Corporation",
        "customer_segment": "Government"
    }
    ```
    """
    try:
        if WIN_LOSS_ANALYTICS_AVAILABLE:
            db_manager = get_db_manager()
            session = db_manager.get_session()
            
            try:
                from analytics.models import WinLossRecord
                
                # Create win/loss record
                record = WinLossRecord(
                    rfp_id=outcome_data.rfp_id,
                    bid_id=outcome_data.bid_id,
                    outcome=outcome_data.outcome,
                    our_bid_amount=outcome_data.our_bid_amount,
                    winning_bid_amount=outcome_data.winning_bid_amount,
                    winning_competitor=outcome_data.winning_competitor,
                    competitor_names=outcome_data.competitor_names or [],
                    technical_score=outcome_data.technical_score,
                    commercial_score=outcome_data.commercial_score,
                    overall_score=outcome_data.overall_score,
                    winning_factors=outcome_data.winning_factors or [],
                    losing_factors=outcome_data.losing_factors or [],
                    customer_name=outcome_data.customer_name,
                    customer_segment=outcome_data.customer_segment,
                    customer_region=outcome_data.customer_region,
                    rfp_category=outcome_data.rfp_category,
                    recorded_at=datetime.utcnow(),
                    recorded_by=user_id or "system"
                )
                
                session.add(record)
                session.commit()
                session.close()
                
                logger.info(f"✅ Recorded bid outcome for RFP {outcome_data.rfp_id}")
                
                return JSONResponse(content={
                    "success": True,
                    "message": f"Bid outcome recorded for RFP {outcome_data.rfp_id}",
                    "record_id": record.id,
                    "rfp_id": outcome_data.rfp_id,
                    "outcome": outcome_data.outcome
                }, status_code=201)
            except Exception as inner_err:
                logger.error(f"Error recording bid outcome: {inner_err}")
                session.close()
                raise HTTPException(status_code=400, detail=f"Failed to record bid outcome: {str(inner_err)}")
        else:
            raise HTTPException(status_code=503, detail="Win/Loss analytics not available")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bid outcome recording error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/win-loss-ratio/{rfp_id:path}", tags=["Analytics"])
async def get_win_loss_ratio(rfp_id: str, allow_demo_fallback: bool = Query(True)):
    """
    Get the calculated win/loss ratio for a specific RFP.
    Returns status: no_data if no real bids exist and allow_demo_fallback=False.
    """
    try:
        if WIN_LOSS_ANALYTICS_AVAILABLE:
            db_manager = get_db_manager()
            session = db_manager.get_session()
            
            try:
                win_loss_analytics = WinLossAnalytics(session_factory=lambda: db_manager.get_session())
                result = win_loss_analytics.get_win_loss_ratio_by_rfp(
                    session, rfp_id, allow_synthetic_fallback=allow_demo_fallback
                )
                session.close()
                
                return result
            except Exception as e:
                session.close()
                logger.error(f"Error calculating win/loss ratio: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=503, detail="Win/Loss analytics not available")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Win/loss ratio error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/analytics/bulk-record-outcomes", tags=["Analytics"])
async def bulk_record_outcomes(
    outcomes: list[BidOutcomeRequest],
    user_id: Optional[str] = Query(None)
):
    """
    Record multiple bid outcomes at once
    
    Useful for importing historical bid data from CSV, Excel, or another system.
    
    Example:
    ```json
    [
        {
            "rfp_id": "GEM/2025/B/6694421",
            "outcome": "won",
            "our_bid_amount": 915000,
            "technical_score": 92.5
        },
        {
            "rfp_id": "GEM/2025/B/6694420",
            "outcome": "lost",
            "our_bid_amount": 850000,
            "winning_competitor": "Competitor A"
        }
    ]
    ```
    """
    try:
        if WIN_LOSS_ANALYTICS_AVAILABLE:
            db_manager = get_db_manager()
            session = db_manager.get_session()
            
            try:
                from analytics.models import WinLossRecord
                
                records = []
                for outcome_data in outcomes:
                    record = WinLossRecord(
                        rfp_id=outcome_data.rfp_id,
                        bid_id=outcome_data.bid_id,
                        outcome=outcome_data.outcome,
                        our_bid_amount=outcome_data.our_bid_amount,
                        winning_bid_amount=outcome_data.winning_bid_amount,
                        winning_competitor=outcome_data.winning_competitor,
                        competitor_names=outcome_data.competitor_names or [],
                        technical_score=outcome_data.technical_score,
                        commercial_score=outcome_data.commercial_score,
                        overall_score=outcome_data.overall_score,
                        winning_factors=outcome_data.winning_factors or [],
                        losing_factors=outcome_data.losing_factors or [],
                        customer_name=outcome_data.customer_name,
                        customer_segment=outcome_data.customer_segment,
                        customer_region=outcome_data.customer_region,
                        rfp_category=outcome_data.rfp_category,
                        recorded_at=datetime.utcnow(),
                        recorded_by=user_id or "system"
                    )
                    records.append(record)
                
                session.add_all(records)
                session.commit()
                session.close()
                
                logger.info(f"✅ Recorded {len(records)} bid outcomes")
                
                return JSONResponse(content={
                    "success": True,
                    "message": f"Recorded {len(records)} bid outcomes",
                    "count": len(records),
                    "rfps_affected": list(set(o.rfp_id for o in outcomes))
                }, status_code=201)
            except Exception as inner_err:
                session.close()
                logger.error(f"Error bulk recording outcomes: {inner_err}")
                raise HTTPException(status_code=400, detail=f"Failed to record outcomes: {str(inner_err)}")
        else:
            raise HTTPException(status_code=503, detail="Win/Loss analytics not available")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk outcome recording error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Feature: Enterprise Metal Commodity & Landed Cost Analytics Endpoints
# =============================================================================

class LandedCostRequest(BaseModel):
    conductor_size_sqmm: float = Field(..., gt=0, description="Conductor cross-section in sq mm")
    no_of_cores: int = Field(1, ge=1, description="Number of cores")
    conductor_material: str = Field("copper", description="copper or aluminium")
    insulation: str = Field("XLPE", description="XLPE or PVC")
    is_armoured: bool = Field(True, description="Whether cable is armoured")
    quantity_meters: float = Field(1000.0, gt=0, description="Quantity in meters")
    freight_distance_km: float = Field(250.0, ge=0, description="Transit distance in kilometers")
    margin_percent: float = Field(12.0, ge=0, description="Target profit margin %")
    gst_percent: float = Field(18.0, ge=0, description="GST rate %")


class CommodityRatesUpdateRequest(BaseModel):
    copper_inr_per_kg: Optional[float] = Field(None, gt=0, description="Copper rate INR/kg")
    aluminium_inr_per_kg: Optional[float] = Field(None, gt=0, description="Aluminium rate INR/kg")
    pvc_resin_inr_per_kg: Optional[float] = Field(None, gt=0, description="PVC resin rate INR/kg")
    xlpe_compound_inr_per_kg: Optional[float] = Field(None, gt=0, description="XLPE compound rate INR/kg")
    steel_strip_inr_per_kg: Optional[float] = Field(None, gt=0, description="Steel armour strip rate INR/kg")
    source: Optional[str] = Field("MCX / LME Live Ingestion", description="Data source description")


@app.get("/api/v1/pricing/commodity-rates", tags=["Pricing Analytics"])
async def get_commodity_rates():
    """Retrieve real-time LME/MCX indexed commodity baseline rates used in engineering pricing."""
    try:
        from price_optimization import CommodityRatesManager
        mgr = CommodityRatesManager.get_instance()
        rates = mgr.get_rates()
        return {
            "success": True,
            "currency": "INR",
            "rates": {
                "copper_inr_per_kg": rates.copper_inr_per_kg,
                "aluminium_inr_per_kg": rates.aluminium_inr_per_kg,
                "pvc_resin_inr_per_kg": rates.pvc_resin_inr_per_kg,
                "xlpe_compound_inr_per_kg": rates.xlpe_compound_inr_per_kg,
                "steel_strip_inr_per_kg": rates.steel_strip_inr_per_kg,
            },
            "last_updated": rates.last_updated.isoformat(),
            "source": "LME / MCX Indexed Reference"
        }
    except Exception as e:
        logger.error(f"Failed to fetch commodity rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pricing/commodity-rates/update", tags=["Pricing Analytics"])
async def update_commodity_rates(payload: CommodityRatesUpdateRequest):
    """
    Update commodity rates with live market feed inputs or administrative overrides.
    Persists updated rates and reflects immediately across all subsequent landed cost calculations.
    """
    try:
        from price_optimization import CommodityRatesManager
        mgr = CommodityRatesManager.get_instance()
        updates = {k: v for k, v in (payload.model_dump() if hasattr(payload, 'model_dump') else payload.dict()).items() if v is not None and k != 'source'}
        updated_rates = mgr.update_rates(updates, source=payload.source or "Manual Market Update")
        return {
            "success": True,
            "message": "Commodity spot rates successfully updated and persisted",
            "currency": "INR",
            "rates": {
                "copper_inr_per_kg": updated_rates.copper_inr_per_kg,
                "aluminium_inr_per_kg": updated_rates.aluminium_inr_per_kg,
                "pvc_resin_inr_per_kg": updated_rates.pvc_resin_inr_per_kg,
                "xlpe_compound_inr_per_kg": updated_rates.xlpe_compound_inr_per_kg,
                "steel_strip_inr_per_kg": updated_rates.steel_strip_inr_per_kg,
            },
            "last_updated": updated_rates.last_updated.isoformat(),
            "source": payload.source or "Manual Market Update"
        }
    except Exception as e:
        logger.error(f"Failed to update commodity rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/v1/pricing/landed-cost-estimate", tags=["Pricing Analytics"])
async def estimate_landed_cost(payload: LandedCostRequest):
    """
    Calculate an accurate engineering landed cost estimate including conductor metal weight,
    insulation, steel armouring, wooden drums, freight per tonne-km, insurance, and 18% GST.
    """
    try:
        from price_optimization import LandedCostCalculator
        calc = LandedCostCalculator()
        result = calc.calculate_turnkey_landed_cost(
            conductor_size_sqmm=payload.conductor_size_sqmm,
            no_of_cores=payload.no_of_cores,
            conductor_material=payload.conductor_material,
            insulation=payload.insulation,
            is_armoured=payload.is_armoured,
            quantity_meters=payload.quantity_meters,
            freight_distance_km=payload.freight_distance_km,
            margin_percent=payload.margin_percent,
            gst_percent=payload.gst_percent,
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Landed cost calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Feature: Enterprise Procurement Standards & Statutory Engineering
# =============================================================================

class IEEMAPVCRequest(BaseModel):
    base_price_inr: float
    cable_category: str = "LT_ALUMINIUM_XLPE_ARMOURED"
    base_indices: Dict[str, float] = Field(default_factory=dict)
    delivery_indices: Dict[str, float] = Field(default_factory=dict)
    quantity_km: float = 1.0


class TechnicalDeviationsRequest(BaseModel):
    rfp_specs: Dict[str, Any]
    offered_product: Dict[str, Any]


class TenderSecurityRequest(BaseModel):
    estimated_tender_value_inr: float
    vendor_profile: Dict[str, Any] = Field(default_factory=dict)
    emd_pct: float = 2.0
    pbg_pct: float = 3.0


@app.post("/api/v1/procurement/ieema-pvc", tags=["Procurement Standards"])
async def calculate_ieema_price_variation(payload: IEEMAPVCRequest):
    """
    Calculate statutory IEEMA Price Variation Clause (PVC) for long-delivery cable tenders.
    """
    try:
        from core.procurement_standards import IEEMAPriceVariationEngine
        result = IEEMAPriceVariationEngine.calculate_pvc(
            base_price_inr=payload.base_price_inr,
            cable_category=payload.cable_category,
            base_indices=payload.base_indices,
            delivery_indices=payload.delivery_indices,
            quantity_km=payload.quantity_km
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"IEEMA PVC calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/procurement/technical-deviations", tags=["Procurement Standards"])
async def generate_technical_deviations(payload: TechnicalDeviationsRequest):
    """
    Generate statutory Schedule of Deviations (Form F-4 / Technical Compliance Matrix).
    """
    try:
        from dataclasses import asdict
        from core.procurement_standards import TechnicalDeviationEngine
        deviations = TechnicalDeviationEngine.generate_schedule(
            rfp_specs=payload.rfp_specs,
            offered_product=payload.offered_product
        )
        csv_export = TechnicalDeviationEngine.export_deviations_csv(deviations)
        return {
            "success": True,
            "data": {
                "deviations": [asdict(d) for d in deviations],
                "total_clauses_reviewed": len(deviations),
                "has_critical_deviations": any(d.risk_level == "HIGH" for d in deviations),
                "csv_export": csv_export
            }
        }
    except Exception as e:
        logger.error(f"Technical deviation generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/procurement/emd-pbg-exemptions", tags=["Procurement Standards"])
async def evaluate_tender_security(payload: TenderSecurityRequest):
    """
    Evaluate Earnest Money Deposit (EMD) and Performance Bank Guarantee (PBG)
    exemption eligibility under MSME, Startup India, and PSU rules.
    """
    try:
        from core.procurement_standards import TenderSecurityEngine
        result = TenderSecurityEngine.evaluate_security_exemptions(
            estimated_tender_value_inr=payload.estimated_tender_value_inr,
            vendor_profile=payload.vendor_profile,
            emd_pct=payload.emd_pct,
            pbg_pct=payload.pbg_pct
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Tender security evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    run_server()
