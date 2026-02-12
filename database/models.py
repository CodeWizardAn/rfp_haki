"""
SQLAlchemy Database Models
Relational database schema for RFP Response System

Models:
- Product: OEM product catalog
- RFP: Request for Proposal documents
- RFPRequirement: Individual requirements within RFPs
- ProductMatch: Matches between RFP requirements and products
- AgentLog: Agent activity logging
- Bid: Generated bid documents
- BidItem: Line items within bids
- User: System users
- AuditTrail: System audit logging
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum as PyEnum

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, DateTime, 
    Text, ForeignKey, JSON, Enum, Index, UniqueConstraint, CheckConstraint,
    event, Table
)
from sqlalchemy.orm import (
    declarative_base, relationship, sessionmaker, Session,
    validates, backref
)
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import func

from agents.shared.utils import (
    # Normalize specs
    normalize_conductor_size, normalize_voltage,
    # Convert units
    convert_length, convert_temperature,
    # Map standards
    get_equivalent_standards,
    # Extract from text
    extract_conductor_specs, extract_voltage_rating,
    # Validate data
    validate_email, validate_gstin,
    # Decorators
    retry, cached, timer,
    # Logging
    get_logger, setup_logging,
    # Config
    load_config, get_config
)

Base = declarative_base()


# ==================== ENUMS ====================

class ProductStatus(PyEnum):
    """Product availability status"""
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"
    PENDING = "pending"


class RFPStatus(PyEnum):
    """RFP processing status"""
    DRAFT = "draft"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    MATCHED = "matched"
    BID_GENERATED = "bid_generated"
    SUBMITTED = "submitted"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"


class MatchStatus(PyEnum):
    """Match validation status"""
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    MANUAL_OVERRIDE = "manual_override"


class AgentType(PyEnum):
    """Types of agents in the system"""
    MASTER = "master"
    SALES = "sales"
    TECHNICAL = "technical"
    PRICING = "pricing"


class LogLevel(PyEnum):
    """Log severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BidStatus(PyEnum):
    """Bid document status"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"
    EXPIRED = "expired"


# ==================== ASSOCIATION TABLES ====================

# Many-to-many relationship between Products and Standards
product_standards = Table(
    'product_standards',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    Column('standard_id', Integer, ForeignKey('standards.id', ondelete='CASCADE'), primary_key=True)
)

# Many-to-many relationship between Products and Certifications
product_certifications = Table(
    'product_certifications',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
    Column('certification_id', Integer, ForeignKey('certifications.id', ondelete='CASCADE'), primary_key=True)
)


# ==================== REFERENCE TABLES ====================

class Standard(Base):
    """Standards compliance reference table (IS, IEC, etc.)"""
    __tablename__ = 'standards'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    issuing_body = Column(String(100))
    version = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    products = relationship('Product', secondary=product_standards, back_populates='standards')
    
    def __repr__(self):
        return f"<Standard(code='{self.code}', name='{self.name}')>"


class Certification(Base):
    """Certification reference table (BIS, ISI, etc.)"""
    __tablename__ = 'certifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    issuing_authority = Column(String(100))
    validity_years = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    products = relationship('Product', secondary=product_certifications, back_populates='certifications')
    
    def __repr__(self):
        return f"<Certification(code='{self.code}', name='{self.name}')>"


class OEM(Base):
    """Original Equipment Manufacturer (Vendor) table"""
    __tablename__ = 'oems'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(500))
    country = Column(String(100), default='India')
    website = Column(String(500))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    address = Column(Text)
    gstin = Column(String(20))
    rating = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = relationship('Product', back_populates='oem', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<OEM(code='{self.code}', name='{self.name}')>"


# ==================== PRODUCT MODEL ====================

class Product(Base):
    """
    Product model - OEM product catalog
    Stores detailed specifications for wires and cables
    """
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Foreign Keys
    oem_id = Column(Integer, ForeignKey('oems.id'), nullable=False, index=True)
    
    # Product Classification
    category = Column(String(100), index=True)
    product_type = Column(String(100))
    
    # Technical Specifications (stored as JSON for flexibility)
    specifications = Column(JSON, default={})
    
    # Common Specifications (indexed for fast searching)
    conductor_material = Column(String(50), index=True)
    conductor_size_sqmm = Column(Float, index=True)
    number_of_cores = Column(Integer, index=True)
    insulation_type = Column(String(50), index=True)
    voltage_rating = Column(String(50))
    current_rating_amps = Column(Float)
    temperature_rating_c = Column(Integer)
    armour_type = Column(String(50))
    is_flame_retardant = Column(Boolean, default=False, index=True)
    
    # Pricing
    unit_price = Column(Float, default=0.0)
    price_unit = Column(String(20), default='per_meter')
    moq = Column(Integer, default=1)
    bulk_discount_percent = Column(Float, default=0.0)
    bulk_threshold = Column(Integer, default=0)
    
    # Availability
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE, index=True)
    lead_time_days = Column(Integer, default=7)
    stock_available = Column(Integer, default=0)
    
    # Datasheet
    datasheet_url = Column(String(500))
    datasheet_data = Column(JSON, default={})
    
    # Metadata
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    oem = relationship('OEM', back_populates='products')
    standards = relationship('Standard', secondary=product_standards, back_populates='products')
    certifications = relationship('Certification', secondary=product_certifications, back_populates='products')
    matches = relationship('ProductMatch', back_populates='product', cascade='all, delete-orphan')
    bid_items = relationship('BidItem', back_populates='product')
    
    # Indexes for common search patterns
    __table_args__ = (
        Index('idx_product_search', 'conductor_material', 'conductor_size_sqmm', 'insulation_type'),
        Index('idx_product_oem_category', 'oem_id', 'category'),
    )
    
    @validates('conductor_size_sqmm')
    def validate_conductor_size(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Conductor size must be positive")
        return value
    
    @validates('unit_price')
    def validate_price(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Price must be non-negative")
        return value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'oem': self.oem.name if self.oem else None,
            'category': self.category,
            'specifications': self.specifications,
            'conductor_material': self.conductor_material,
            'conductor_size_sqmm': self.conductor_size_sqmm,
            'number_of_cores': self.number_of_cores,
            'insulation_type': self.insulation_type,
            'voltage_rating': self.voltage_rating,
            'unit_price': self.unit_price,
            'status': self.status.value if self.status else None,
            'standards': [s.code for s in self.standards],
            'certifications': [c.code for c in self.certifications]
        }
    
    def __repr__(self):
        return f"<Product(sku='{self.sku}', name='{self.name}', oem_id={self.oem_id})>"


# ==================== RFP MODELS ====================

class RFP(Base):
    """
    Request for Proposal model
    Stores RFP documents and metadata
    """
    __tablename__ = 'rfps'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rfp_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    
    # Source Information
    issuing_authority = Column(String(255), index=True)
    source_url = Column(String(500))
    source_document = Column(String(500))
    
    # Dates
    published_date = Column(DateTime)
    due_date = Column(DateTime, index=True)
    submission_date = Column(DateTime)
    
    # Financial
    estimated_value = Column(Float)
    currency = Column(String(10), default='INR')
    emd_amount = Column(Float)  # Earnest Money Deposit
    
    # Status and Processing
    status = Column(Enum(RFPStatus), default=RFPStatus.DRAFT, index=True)
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    
    # Extracted Content
    raw_text = Column(Text)
    extracted_data = Column(JSON, default={})
    standards_required = Column(JSON, default=[])
    tests_required = Column(JSON, default=[])
    
    # Metadata
    priority = Column(Integer, default=5)  # 1-10, 10 being highest
    assigned_to = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requirements = relationship('RFPRequirement', back_populates='rfp', cascade='all, delete-orphan')
    bids = relationship('Bid', back_populates='rfp', cascade='all, delete-orphan')
    agent_logs = relationship('AgentLog', back_populates='rfp', cascade='all, delete-orphan')
    
    __table_args__ = (
        Index('idx_rfp_status_due', 'status', 'due_date'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert RFP to dictionary"""
        return {
            'id': self.id,
            'rfp_id': self.rfp_id,
            'title': self.title,
            'issuing_authority': self.issuing_authority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'estimated_value': self.estimated_value,
            'status': self.status.value if self.status else None,
            'requirements_count': len(self.requirements) if self.requirements else 0,
            'standards_required': self.standards_required,
            'tests_required': self.tests_required
        }
    
    def __repr__(self):
        return f"<RFP(rfp_id='{self.rfp_id}', title='{self.title[:50]}...')>"


class RFPRequirement(Base):
    """
    Individual requirement within an RFP
    Each requirement can be matched to multiple products
    """
    __tablename__ = 'rfp_requirements'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rfp_id = Column(Integer, ForeignKey('rfps.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Requirement Details
    requirement_number = Column(Integer)
    original_text = Column(Text, nullable=False)
    parsed_specifications = Column(JSON, default={})
    
    # Extracted Specifications
    product_type = Column(String(100))
    conductor_material = Column(String(50))
    conductor_size_sqmm = Column(Float)
    number_of_cores = Column(Integer)
    insulation_type = Column(String(50))
    voltage_rating = Column(String(50))
    
    # Quantity
    quantity = Column(Float, default=0)
    quantity_unit = Column(String(20), default='meters')
    
    # Matching Status
    is_matched = Column(Boolean, default=False, index=True)
    match_confidence = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rfp = relationship('RFP', back_populates='requirements')
    matches = relationship('ProductMatch', back_populates='requirement', cascade='all, delete-orphan')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert requirement to dictionary"""
        return {
            'id': self.id,
            'requirement_number': self.requirement_number,
            'original_text': self.original_text,
            'parsed_specifications': self.parsed_specifications,
            'quantity': self.quantity,
            'quantity_unit': self.quantity_unit,
            'is_matched': self.is_matched,
            'match_confidence': self.match_confidence,
            'matches_count': len(self.matches) if self.matches else 0
        }
    
    def __repr__(self):
        return f"<RFPRequirement(id={self.id}, rfp_id={self.rfp_id}, matched={self.is_matched})>"


# ==================== MATCH MODEL ====================

class ProductMatch(Base):
    """
    Product Match model
    Links RFP requirements to matching products with scores
    """
    __tablename__ = 'product_matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    requirement_id = Column(Integer, ForeignKey('rfp_requirements.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Match Scores
    overall_match_score = Column(Float, nullable=False, index=True)  # 0-100
    spec_match_score = Column(Float)  # Technical specification match
    price_score = Column(Float)       # Price competitiveness score
    availability_score = Column(Float) # Stock availability score
    
    # Detailed Match Information
    matched_specs = Column(JSON, default={})   # Which specs matched
    unmatched_specs = Column(JSON, default=[])  # Which specs didn't match
    partial_matches = Column(JSON, default=[])  # Partially matched specs
    
    # Ranking
    rank = Column(Integer)  # 1, 2, 3 for top 3 recommendations
    is_selected = Column(Boolean, default=False, index=True)  # Final selection
    
    # Status
    status = Column(Enum(MatchStatus), default=MatchStatus.PENDING, index=True)
    validated_by = Column(String(100))
    validated_at = Column(DateTime)
    
    # Pricing at match time
    unit_price_at_match = Column(Float)
    quantity = Column(Float)
    total_price = Column(Float)
    
    # Notes
    recommendation_notes = Column(Text)
    rejection_reason = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requirement = relationship('RFPRequirement', back_populates='matches')
    product = relationship('Product', back_populates='matches')
    
    __table_args__ = (
        UniqueConstraint('requirement_id', 'product_id', name='uq_requirement_product'),
        Index('idx_match_scores', 'requirement_id', 'overall_match_score'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert match to dictionary"""
        return {
            'id': self.id,
            'requirement_id': self.requirement_id,
            'product_id': self.product_id,
            'product_sku': self.product.sku if self.product else None,
            'product_name': self.product.name if self.product else None,
            'oem': self.product.oem.name if self.product and self.product.oem else None,
            'overall_match_score': self.overall_match_score,
            'spec_match_score': self.spec_match_score,
            'rank': self.rank,
            'is_selected': self.is_selected,
            'status': self.status.value if self.status else None,
            'unit_price': self.unit_price_at_match,
            'total_price': self.total_price
        }
    
    def __repr__(self):
        return f"<ProductMatch(req_id={self.requirement_id}, prod_id={self.product_id}, score={self.overall_match_score})>"


# ==================== AGENT LOG MODEL ====================

class AgentLog(Base):
    """
    Agent activity logging
    Tracks all agent actions for debugging and audit
    """
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Agent Information
    agent_type = Column(Enum(AgentType), nullable=False, index=True)
    agent_name = Column(String(100))
    conversation_id = Column(String(100), index=True)
    
    # Context
    rfp_id = Column(Integer, ForeignKey('rfps.id', ondelete='SET NULL'), index=True)
    workflow_id = Column(String(100), index=True)
    
    # Log Details
    level = Column(Enum(LogLevel), default=LogLevel.INFO, index=True)
    action = Column(String(200), nullable=False)
    message = Column(Text)
    
    # Input/Output
    input_data = Column(JSON, default={})
    output_data = Column(JSON, default={})
    
    # Performance Metrics
    duration_ms = Column(Integer)  # Execution time in milliseconds
    tokens_used = Column(Integer)   # For LLM-based agents
    
    # Error Information
    error_type = Column(String(100))
    error_message = Column(Text)
    stack_trace = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    rfp = relationship('RFP', back_populates='agent_logs')
    
    __table_args__ = (
        Index('idx_agent_log_search', 'agent_type', 'level', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log to dictionary"""
        return {
            'id': self.id,
            'agent_type': self.agent_type.value if self.agent_type else None,
            'conversation_id': self.conversation_id,
            'rfp_id': self.rfp_id,
            'level': self.level.value if self.level else None,
            'action': self.action,
            'message': self.message,
            'duration_ms': self.duration_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f"<AgentLog(agent={self.agent_type.value}, action='{self.action}')>"


# ==================== BID MODELS ====================

class Bid(Base):
    """
    Bid document model
    Generated bid responses to RFPs
    """
    __tablename__ = 'bids'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bid_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Foreign Keys
    rfp_id = Column(Integer, ForeignKey('rfps.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Bid Details
    version = Column(Integer, default=1)
    title = Column(String(500))
    
    # Pricing Summary
    subtotal = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    discount_percent = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    tax_percent = Column(Float, default=18.0)  # GST
    shipping_cost = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    
    # Test Costs
    test_costs_total = Column(Float, default=0.0)
    test_costs_breakdown = Column(JSON, default=[])
    
    # Grand Total
    grand_total = Column(Float, default=0.0)
    
    # Status
    status = Column(Enum(BidStatus), default=BidStatus.DRAFT, index=True)
    
    # Dates
    created_date = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    submitted_date = Column(DateTime)
    
    # Terms
    delivery_timeline = Column(String(200))
    payment_terms = Column(String(500))
    warranty_terms = Column(String(500))
    
    # Documents
    document_path = Column(String(500))
    document_format = Column(String(20))  # pdf, xlsx
    
    # Approval
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)
    
    # Metadata
    created_by = Column(String(100))
    notes = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rfp = relationship('RFP', back_populates='bids')
    items = relationship('BidItem', back_populates='bid', cascade='all, delete-orphan')
    
    def calculate_totals(self):
        """Recalculate bid totals from items"""
        self.subtotal = sum(item.total_price for item in self.items if item.total_price)
        self.discount_amount = self.subtotal * (self.discount_percent / 100)
        self.tax_amount = (self.subtotal - self.discount_amount) * (self.tax_percent / 100)
        self.total_amount = self.subtotal - self.discount_amount + self.tax_amount + self.shipping_cost
        self.grand_total = self.total_amount + self.test_costs_total
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bid to dictionary"""
        return {
            'id': self.id,
            'bid_id': self.bid_id,
            'rfp_id': self.rfp_id,
            'version': self.version,
            'status': self.status.value if self.status else None,
            'subtotal': self.subtotal,
            'total_amount': self.total_amount,
            'test_costs_total': self.test_costs_total,
            'grand_total': self.grand_total,
            'items_count': len(self.items) if self.items else 0,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None
        }
    
    def __repr__(self):
        return f"<Bid(bid_id='{self.bid_id}', rfp_id={self.rfp_id}, total={self.grand_total})>"


class BidItem(Base):
    """
    Individual line item in a bid
    """
    __tablename__ = 'bid_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    bid_id = Column(Integer, ForeignKey('bids.id', ondelete='CASCADE'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='SET NULL'), index=True)
    
    # Item Details
    line_number = Column(Integer)
    description = Column(Text)
    specifications = Column(JSON, default={})
    
    # Pricing
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), default='meters')
    unit_price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0.0)
    discounted_unit_price = Column(Float)
    total_price = Column(Float)
    
    # Match Information
    spec_match_percent = Column(Float)
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bid = relationship('Bid', back_populates='items')
    product = relationship('Product', back_populates='bid_items')
    
    def calculate_total(self):
        """Calculate total price for this item"""
        self.discounted_unit_price = self.unit_price * (1 - self.discount_percent / 100)
        self.total_price = self.discounted_unit_price * self.quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bid item to dictionary"""
        return {
            'id': self.id,
            'line_number': self.line_number,
            'product_id': self.product_id,
            'product_sku': self.product.sku if self.product else None,
            'description': self.description,
            'quantity': self.quantity,
            'unit': self.unit,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'spec_match_percent': self.spec_match_percent
        }
    
    def __repr__(self):
        return f"<BidItem(bid_id={self.bid_id}, line={self.line_number}, total={self.total_price})>"


# ==================== AUDIT TRAIL ====================

class AuditTrail(Base):
    """
    System-wide audit trail
    Tracks all significant actions for compliance
    """
    __tablename__ = 'audit_trail'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # What happened
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # product, rfp, bid, etc.
    entity_id = Column(String(100), index=True)
    
    # Who did it
    user_id = Column(String(100), index=True)
    user_name = Column(String(200))
    ip_address = Column(String(50))
    
    # Details
    old_values = Column(JSON, default={})
    new_values = Column(JSON, default={})
    description = Column(Text)
    
    # When
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_user_time', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditTrail(action='{self.action}', entity='{self.entity_type}:{self.entity_id}')>"


# ==================== TEST SERVICE PRICES ====================

class TestService(Base):
    """
    Test/Service pricing table
    Stores costs for various testing services
    """
    __tablename__ = 'test_services'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Pricing
    price = Column(Float, nullable=False)
    price_unit = Column(String(50), default='per_sample')
    
    # Classification
    category = Column(String(100), index=True)  # Routine Test, Type Test, etc.
    standard = Column(String(100))  # IS 694, IEC 60332, etc.
    
    # Timing
    turnaround_days = Column(Integer, default=3)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'service_id': self.service_id,
            'name': self.name,
            'price': self.price,
            'category': self.category,
            'standard': self.standard,
            'turnaround_days': self.turnaround_days
        }
    
    def __repr__(self):
        return f"<TestService(service_id='{self.service_id}', price={self.price})>"
