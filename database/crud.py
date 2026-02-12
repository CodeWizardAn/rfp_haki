"""
CRUD Operations for Database Models
Create, Read, Update, Delete operations with validation

Provides repository pattern for:
- ProductRepository
- RFPRepository
- MatchRepository
- AgentLogRepository
- BidRepository

Performance Integration:
- Query caching for frequently accessed data
- Batch operations for bulk inserts/updates
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Type, TypeVar
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from .models import (
    Base, Product, OEM, Standard, Certification,
    RFP, RFPRequirement, ProductMatch, AgentLog, Bid, BidItem,
    AuditTrail, TestService,
    ProductStatus, RFPStatus, MatchStatus, AgentType, LogLevel, BidStatus
)
from .db_engine import session_scope, get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Performance Integration
try:
    perf_path = str(Path(__file__).parent.parent)
    if perf_path not in sys.path:
        sys.path.insert(0, perf_path)
    from database.db_performance import cached_query, batch_operation
    PERFORMANCE_AVAILABLE = True
except ImportError as e:
    PERFORMANCE_AVAILABLE = False
    # Define no-op decorators
    def cached_query(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator
    def batch_operation(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if args and callable(args[0]) else decorator

T = TypeVar('T')

class BaseRepository:
    """Base repository with common CRUD operations"""
    
    model: Type[T] = None
    
    def __init__(self, session: Session = None):
        """
        Initialize repository
        
        Args:
            session: SQLAlchemy session (creates new if not provided)
        """
        self._session = session
        self._owns_session = session is None
    
    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = get_session()
        return self._session
    
    def _commit(self):
        """Commit if we own the session"""
        if self._owns_session:
            try:
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                raise
    
    def create(self, **kwargs) -> T:
        """Create a new record"""
        obj = self.model(**kwargs)
        self.session.add(obj)
        self._commit()
        return obj
    
    def get_by_id(self, id: int) -> Optional[T]:
        """Get record by primary key"""
        return self.session.query(self.model).get(id)
    
    def get_all(self, limit: int = None, offset: int = None) -> List[T]:
        """Get all records with optional pagination"""
        query = self.session.query(self.model)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        """Update a record by ID"""
        obj = self.get_by_id(id)
        if obj:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            self._commit()
        return obj
    
    def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        obj = self.get_by_id(id)
        if obj:
            self.session.delete(obj)
            self._commit()
            return True
        return False
    
    def count(self) -> int:
        """Count all records"""
        return self.session.query(func.count(self.model.id)).scalar()
    
    def exists(self, id: int) -> bool:
        """Check if record exists"""
        return self.session.query(
            self.session.query(self.model).filter_by(id=id).exists()
        ).scalar()
    
    def bulk_create(self, items: List[Dict]) -> List[T]:
        """Create multiple records"""
        objects = [self.model(**item) for item in items]
        self.session.add_all(objects)
        self._commit()
        return objects
    
    def bulk_delete(self, ids: List[int]) -> int:
        """Delete multiple records by IDs"""
        count = self.session.query(self.model).filter(
            self.model.id.in_(ids)
        ).delete(synchronize_session=False)
        self._commit()
        return count


# ==================== PRODUCT REPOSITORY ====================

class ProductRepository(BaseRepository):
    """Repository for Product CRUD operations"""
    
    model = Product
    
    def create_product(
        self,
        sku: str,
        name: str,
        oem_id: int,
        **kwargs
    ) -> Product:
        """
        Create a new product
        
        Args:
            sku: Product SKU (unique)
            name: Product name
            oem_id: OEM foreign key
            **kwargs: Additional product fields
            
        Returns:
            Created Product instance
        """
        product = Product(
            sku=sku,
            name=name,
            oem_id=oem_id,
            **kwargs
        )
        self.session.add(product)
        self._commit()
        logger.info(f"Created product: {sku}")
        return product
    
    def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        return self.session.query(Product).filter_by(sku=sku).first()
    
    def get_by_oem(self, oem_id: int, active_only: bool = True) -> List[Product]:
        """Get all products for an OEM"""
        query = self.session.query(Product).filter_by(oem_id=oem_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.all()
    
    def search_products(
        self,
        conductor_material: str = None,
        conductor_size: float = None,
        insulation_type: str = None,
        number_of_cores: int = None,
        oem_id: int = None,
        category: str = None,
        min_price: float = None,
        max_price: float = None,
        status: ProductStatus = None,
        limit: int = 100
    ) -> List[Product]:
        """
        Search products with multiple criteria
        """
        query = self.session.query(Product).filter(Product.is_active == True)
        
        if conductor_material:
            query = query.filter(Product.conductor_material.ilike(f'%{conductor_material}%'))
        if conductor_size:
            query = query.filter(Product.conductor_size_sqmm == conductor_size)
        if insulation_type:
            query = query.filter(Product.insulation_type.ilike(f'%{insulation_type}%'))
        if number_of_cores:
            query = query.filter(Product.number_of_cores == number_of_cores)
        if oem_id:
            query = query.filter(Product.oem_id == oem_id)
        if category:
            query = query.filter(Product.category.ilike(f'%{category}%'))
        if min_price is not None:
            query = query.filter(Product.unit_price >= min_price)
        if max_price is not None:
            query = query.filter(Product.unit_price <= max_price)
        if status:
            query = query.filter(Product.status == status)
        
        return query.limit(limit).all()
    
    def get_products_with_specs(
        self,
        specs: Dict[str, Any],
        tolerance: float = 0.1
    ) -> List[Tuple[Product, float]]:
        """
        Find products matching specifications with tolerance
        Returns products with match scores
        """
        products = self.session.query(Product).filter(Product.is_active == True).all()
        results = []
        
        for product in products:
            score = self._calculate_spec_match(product, specs, tolerance)
            if score > 0:
                results.append((product, score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def _calculate_spec_match(
        self,
        product: Product,
        specs: Dict[str, Any],
        tolerance: float
    ) -> float:
        """Calculate specification match score"""
        total_specs = len(specs)
        if total_specs == 0:
            return 0
        
        matched = 0
        
        for spec_key, spec_value in specs.items():
            product_value = getattr(product, spec_key, None)
            if product_value is None:
                continue
            
            if isinstance(spec_value, (int, float)) and isinstance(product_value, (int, float)):
                # Numeric comparison with tolerance
                if abs(product_value - spec_value) <= abs(spec_value * tolerance):
                    matched += 1
            elif isinstance(spec_value, str) and isinstance(product_value, str):
                # String comparison (case-insensitive)
                if spec_value.lower() in product_value.lower():
                    matched += 1
            elif spec_value == product_value:
                matched += 1
        
        return (matched / total_specs) * 100
    
    def update_stock(self, sku: str, quantity: int) -> Optional[Product]:
        """Update product stock level"""
        product = self.get_by_sku(sku)
        if product:
            product.stock_available = quantity
            if quantity == 0:
                product.status = ProductStatus.OUT_OF_STOCK
            elif product.status == ProductStatus.OUT_OF_STOCK:
                product.status = ProductStatus.ACTIVE
            self._commit()
        return product
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get product statistics"""
        return {
            'total': self.count(),
            'active': self.session.query(Product).filter_by(is_active=True).count(),
            'by_status': {
                status.value: self.session.query(Product).filter_by(status=status).count()
                for status in ProductStatus
            },
            'oem_count': self.session.query(func.count(func.distinct(Product.oem_id))).scalar(),
            'avg_price': self.session.query(func.avg(Product.unit_price)).scalar() or 0
        }


# ==================== OEM REPOSITORY ====================

class OEMRepository(BaseRepository):
    """Repository for OEM CRUD operations"""
    
    model = OEM
    
    def get_by_code(self, code: str) -> Optional[OEM]:
        """Get OEM by code"""
        return self.session.query(OEM).filter_by(code=code).first()
    
    def get_by_name(self, name: str) -> Optional[OEM]:
        """Get OEM by name (case-insensitive)"""
        return self.session.query(OEM).filter(
            OEM.name.ilike(f'%{name}%')
        ).first()
    
    def get_active_oems(self) -> List[OEM]:
        """Get all active OEMs"""
        return self.session.query(OEM).filter_by(is_active=True).all()
    
    def get_oem_with_products(self, oem_id: int) -> Optional[OEM]:
        """Get OEM with eagerly loaded products"""
        return self.session.query(OEM).options(
            joinedload(OEM.products)
        ).filter_by(id=oem_id).first()


# ==================== RFP REPOSITORY ====================

class RFPRepository(BaseRepository):
    """Repository for RFP CRUD operations"""
    
    model = RFP
    
    def create_rfp(
        self,
        rfp_id: str,
        title: str,
        **kwargs
    ) -> RFP:
        """Create a new RFP"""
        rfp = RFP(
            rfp_id=rfp_id,
            title=title,
            **kwargs
        )
        self.session.add(rfp)
        self._commit()
        logger.info(f"Created RFP: {rfp_id}")
        return rfp
    
    def get_by_rfp_id(self, rfp_id: str) -> Optional[RFP]:
        """Get RFP by its RFP ID"""
        return self.session.query(RFP).filter_by(rfp_id=rfp_id).first()
    
    def get_by_status(self, status: RFPStatus) -> List[RFP]:
        """Get RFPs by status"""
        return self.session.query(RFP).filter_by(status=status).all()
    
    def get_due_within_days(self, days: int) -> List[RFP]:
        """Get RFPs due within specified days"""
        cutoff = datetime.utcnow() + timedelta(days=days)
        return self.session.query(RFP).filter(
            and_(
                RFP.due_date <= cutoff,
                RFP.due_date >= datetime.utcnow(),
                RFP.status.in_([RFPStatus.OPEN, RFPStatus.IN_PROGRESS])
            )
        ).order_by(RFP.due_date).all()
    
    def get_with_requirements(self, rfp_id: int) -> Optional[RFP]:
        """Get RFP with eagerly loaded requirements"""
        return self.session.query(RFP).options(
            joinedload(RFP.requirements)
        ).filter_by(id=rfp_id).first()
    
    def add_requirement(
        self,
        rfp_id: int,
        original_text: str,
        **kwargs
    ) -> RFPRequirement:
        """Add a requirement to an RFP"""
        req = RFPRequirement(
            rfp_id=rfp_id,
            original_text=original_text,
            **kwargs
        )
        self.session.add(req)
        self._commit()
        return req
    
    def add_requirements_bulk(
        self,
        rfp_id: int,
        requirements: List[Dict]
    ) -> List[RFPRequirement]:
        """Add multiple requirements to an RFP"""
        reqs = []
        for i, req_data in enumerate(requirements):
            req = RFPRequirement(
                rfp_id=rfp_id,
                requirement_number=i + 1,
                **req_data
            )
            reqs.append(req)
        self.session.add_all(reqs)
        self._commit()
        return reqs
    
    def update_status(self, rfp_id: int, status: RFPStatus) -> Optional[RFP]:
        """Update RFP status"""
        rfp = self.get_by_id(rfp_id)
        if rfp:
            rfp.status = status
            if status == RFPStatus.IN_PROGRESS and not rfp.processing_started_at:
                rfp.processing_started_at = datetime.utcnow()
            elif status in [RFPStatus.MATCHED, RFPStatus.BID_GENERATED]:
                rfp.processing_completed_at = datetime.utcnow()
            self._commit()
        return rfp
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RFP statistics"""
        return {
            'total': self.count(),
            'by_status': {
                status.value: self.session.query(RFP).filter_by(status=status).count()
                for status in RFPStatus
            },
            'due_this_week': len(self.get_due_within_days(7)),
            'due_this_month': len(self.get_due_within_days(30)),
            'avg_value': self.session.query(func.avg(RFP.estimated_value)).scalar() or 0
        }


# ==================== REQUIREMENT REPOSITORY ====================

class RequirementRepository(BaseRepository):
    """Repository for RFP Requirements"""
    
    model = RFPRequirement
    
    def get_by_rfp(self, rfp_id: int) -> List[RFPRequirement]:
        """Get all requirements for an RFP"""
        return self.session.query(RFPRequirement).filter_by(
            rfp_id=rfp_id
        ).order_by(RFPRequirement.requirement_number).all()
    
    def get_unmatched(self, rfp_id: int = None) -> List[RFPRequirement]:
        """Get unmatched requirements"""
        query = self.session.query(RFPRequirement).filter_by(is_matched=False)
        if rfp_id:
            query = query.filter_by(rfp_id=rfp_id)
        return query.all()
    
    def mark_as_matched(
        self,
        requirement_id: int,
        confidence: float
    ) -> Optional[RFPRequirement]:
        """Mark requirement as matched"""
        req = self.get_by_id(requirement_id)
        if req:
            req.is_matched = True
            req.match_confidence = confidence
            self._commit()
        return req


# ==================== MATCH REPOSITORY ====================

class MatchRepository(BaseRepository):
    """Repository for ProductMatch CRUD operations"""
    
    model = ProductMatch
    
    def create_match(
        self,
        requirement_id: int,
        product_id: int,
        overall_match_score: float,
        **kwargs
    ) -> ProductMatch:
        """Create a new product match"""
        match = ProductMatch(
            requirement_id=requirement_id,
            product_id=product_id,
            overall_match_score=overall_match_score,
            **kwargs
        )
        self.session.add(match)
        self._commit()
        return match
    
    def get_by_requirement(
        self,
        requirement_id: int,
        top_n: int = None
    ) -> List[ProductMatch]:
        """Get matches for a requirement, ordered by score"""
        query = self.session.query(ProductMatch).filter_by(
            requirement_id=requirement_id
        ).order_by(desc(ProductMatch.overall_match_score))
        
        if top_n:
            query = query.limit(top_n)
        
        return query.all()
    
    def get_top_matches_for_rfp(
        self,
        rfp_id: int,
        top_n: int = 3
    ) -> Dict[int, List[ProductMatch]]:
        """Get top N matches for each requirement in an RFP"""
        requirements = self.session.query(RFPRequirement).filter_by(
            rfp_id=rfp_id
        ).all()
        
        result = {}
        for req in requirements:
            matches = self.get_by_requirement(req.id, top_n=top_n)
            result[req.id] = matches
        
        return result
    
    def select_match(self, match_id: int) -> Optional[ProductMatch]:
        """Select a match as the chosen product"""
        match = self.get_by_id(match_id)
        if match:
            # Deselect other matches for same requirement
            self.session.query(ProductMatch).filter(
                and_(
                    ProductMatch.requirement_id == match.requirement_id,
                    ProductMatch.id != match_id
                )
            ).update({'is_selected': False})
            
            match.is_selected = True
            match.status = MatchStatus.VALIDATED
            match.validated_at = datetime.utcnow()
            self._commit()
        return match
    
    def reject_match(
        self,
        match_id: int,
        reason: str
    ) -> Optional[ProductMatch]:
        """Reject a match"""
        match = self.get_by_id(match_id)
        if match:
            match.status = MatchStatus.REJECTED
            match.rejection_reason = reason
            self._commit()
        return match
    
    def get_match_statistics(self, rfp_id: int = None) -> Dict[str, Any]:
        """Get match statistics"""
        query = self.session.query(ProductMatch)
        if rfp_id:
            query = query.join(RFPRequirement).filter(
                RFPRequirement.rfp_id == rfp_id
            )
        
        total = query.count()
        avg_score = query.with_entities(
            func.avg(ProductMatch.overall_match_score)
        ).scalar() or 0
        
        return {
            'total_matches': total,
            'avg_match_score': round(avg_score, 2),
            'selected': query.filter(ProductMatch.is_selected == True).count(),
            'by_status': {
                status.value: query.filter(ProductMatch.status == status).count()
                for status in MatchStatus
            }
        }


# ==================== AGENT LOG REPOSITORY ====================

class AgentLogRepository(BaseRepository):
    """Repository for AgentLog CRUD operations"""
    
    model = AgentLog
    
    def log_action(
        self,
        agent_type: AgentType,
        action: str,
        message: str = None,
        **kwargs
    ) -> AgentLog:
        """Log an agent action"""
        log = AgentLog(
            agent_type=agent_type,
            action=action,
            message=message,
            **kwargs
        )
        self.session.add(log)
        self._commit()
        return log
    
    def log_error(
        self,
        agent_type: AgentType,
        action: str,
        error_message: str,
        error_type: str = None,
        stack_trace: str = None,
        **kwargs
    ) -> AgentLog:
        """Log an agent error"""
        return self.log_action(
            agent_type=agent_type,
            action=action,
            level=LogLevel.ERROR,
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace,
            **kwargs
        )
    
    def get_by_conversation(self, conversation_id: str) -> List[AgentLog]:
        """Get all logs for a conversation"""
        return self.session.query(AgentLog).filter_by(
            conversation_id=conversation_id
        ).order_by(AgentLog.created_at).all()
    
    def get_by_rfp(self, rfp_id: int) -> List[AgentLog]:
        """Get all logs for an RFP"""
        return self.session.query(AgentLog).filter_by(
            rfp_id=rfp_id
        ).order_by(AgentLog.created_at).all()
    
    def get_by_agent_type(
        self,
        agent_type: AgentType,
        since: datetime = None,
        level: LogLevel = None
    ) -> List[AgentLog]:
        """Get logs by agent type"""
        query = self.session.query(AgentLog).filter_by(agent_type=agent_type)
        
        if since:
            query = query.filter(AgentLog.created_at >= since)
        if level:
            query = query.filter(AgentLog.level == level)
        
        return query.order_by(desc(AgentLog.created_at)).all()
    
    def get_errors(
        self,
        since: datetime = None,
        limit: int = 100
    ) -> List[AgentLog]:
        """Get error logs"""
        query = self.session.query(AgentLog).filter(
            AgentLog.level.in_([LogLevel.ERROR, LogLevel.CRITICAL])
        )
        
        if since:
            query = query.filter(AgentLog.created_at >= since)
        
        return query.order_by(desc(AgentLog.created_at)).limit(limit).all()
    
    def get_performance_metrics(
        self,
        agent_type: AgentType = None,
        since: datetime = None
    ) -> Dict[str, Any]:
        """Get agent performance metrics"""
        query = self.session.query(AgentLog)
        
        if agent_type:
            query = query.filter_by(agent_type=agent_type)
        if since:
            query = query.filter(AgentLog.created_at >= since)
        
        return {
            'total_actions': query.count(),
            'avg_duration_ms': query.with_entities(
                func.avg(AgentLog.duration_ms)
            ).scalar() or 0,
            'error_count': query.filter(AgentLog.level == LogLevel.ERROR).count(),
            'total_tokens': query.with_entities(
                func.sum(AgentLog.tokens_used)
            ).scalar() or 0
        }
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """Delete logs older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        count = self.session.query(AgentLog).filter(
            AgentLog.created_at < cutoff
        ).delete()
        self._commit()
        logger.info(f"Deleted {count} old agent logs")
        return count


# ==================== BID REPOSITORY ====================

class BidRepository(BaseRepository):
    """Repository for Bid CRUD operations"""
    
    model = Bid
    
    def create_bid(
        self,
        bid_id: str,
        rfp_id: int,
        **kwargs
    ) -> Bid:
        """Create a new bid"""
        bid = Bid(
            bid_id=bid_id,
            rfp_id=rfp_id,
            **kwargs
        )
        self.session.add(bid)
        self._commit()
        logger.info(f"Created bid: {bid_id}")
        return bid
    
    def get_by_bid_id(self, bid_id: str) -> Optional[Bid]:
        """Get bid by its bid ID"""
        return self.session.query(Bid).filter_by(bid_id=bid_id).first()
    
    def get_by_rfp(self, rfp_id: int) -> List[Bid]:
        """Get all bids for an RFP"""
        return self.session.query(Bid).filter_by(
            rfp_id=rfp_id
        ).order_by(desc(Bid.version)).all()
    
    def get_by_status(self, status: BidStatus) -> List[Bid]:
        """Get bids by status"""
        return self.session.query(Bid).filter_by(status=status).all()
    
    def add_item(
        self,
        bid_id: int,
        product_id: int,
        quantity: float,
        unit_price: float,
        **kwargs
    ) -> BidItem:
        """Add an item to a bid"""
        # Get next line number
        max_line = self.session.query(func.max(BidItem.line_number)).filter_by(
            bid_id=bid_id
        ).scalar() or 0
        
        item = BidItem(
            bid_id=bid_id,
            product_id=product_id,
            line_number=max_line + 1,
            quantity=quantity,
            unit_price=unit_price,
            **kwargs
        )
        item.calculate_total()
        self.session.add(item)
        
        # Recalculate bid totals
        bid = self.get_by_id(bid_id)
        if bid:
            self.session.flush()  # Ensure item is added
            bid.calculate_totals()
        
        self._commit()
        return item
    
    def update_status(
        self,
        bid_id: int,
        status: BidStatus,
        notes: str = None
    ) -> Optional[Bid]:
        """Update bid status"""
        bid = self.get_by_id(bid_id)
        if bid:
            bid.status = status
            if status == BidStatus.APPROVED:
                bid.approved_at = datetime.utcnow()
            elif status == BidStatus.SUBMITTED:
                bid.submitted_date = datetime.utcnow()
            if notes:
                bid.approval_notes = notes
            self._commit()
        return bid
    
    def get_with_items(self, bid_id: int) -> Optional[Bid]:
        """Get bid with eagerly loaded items"""
        return self.session.query(Bid).options(
            joinedload(Bid.items).joinedload(BidItem.product)
        ).filter_by(id=bid_id).first()
    
    def create_new_version(self, original_bid_id: int) -> Optional[Bid]:
        """Create a new version of a bid"""
        original = self.get_with_items(original_bid_id)
        if not original:
            return None
        
        # Create new bid with incremented version
        new_bid = Bid(
            bid_id=f"{original.bid_id}_v{original.version + 1}",
            rfp_id=original.rfp_id,
            version=original.version + 1,
            title=original.title,
            discount_percent=original.discount_percent,
            tax_percent=original.tax_percent,
            delivery_timeline=original.delivery_timeline,
            payment_terms=original.payment_terms,
            warranty_terms=original.warranty_terms
        )
        self.session.add(new_bid)
        self.session.flush()
        
        # Copy items
        for item in original.items:
            new_item = BidItem(
                bid_id=new_bid.id,
                product_id=item.product_id,
                line_number=item.line_number,
                description=item.description,
                specifications=item.specifications,
                quantity=item.quantity,
                unit=item.unit,
                unit_price=item.unit_price,
                discount_percent=item.discount_percent
            )
            new_item.calculate_total()
            self.session.add(new_item)
        
        self.session.flush()
        new_bid.calculate_totals()
        self._commit()
        
        return new_bid


# ==================== AUDIT REPOSITORY ====================

class AuditRepository(BaseRepository):
    """Repository for AuditTrail operations"""
    
    model = AuditTrail
    
    def log_action(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: str = None,
        **kwargs
    ) -> AuditTrail:
        """Log an audit action"""
        audit = AuditTrail(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            **kwargs
        )
        self.session.add(audit)
        self._commit()
        return audit
    
    def get_by_entity(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[AuditTrail]:
        """Get audit trail for an entity"""
        return self.session.query(AuditTrail).filter_by(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by(desc(AuditTrail.created_at)).all()
    
    def get_by_user(
        self,
        user_id: str,
        since: datetime = None
    ) -> List[AuditTrail]:
        """Get audit trail for a user"""
        query = self.session.query(AuditTrail).filter_by(user_id=user_id)
        if since:
            query = query.filter(AuditTrail.created_at >= since)
        return query.order_by(desc(AuditTrail.created_at)).all()


# ==================== TEST SERVICE REPOSITORY ====================

class TestServiceRepository(BaseRepository):
    """Repository for TestService operations"""
    
    model = TestService
    
    def get_by_service_id(self, service_id: str) -> Optional[TestService]:
        """Get test service by service ID"""
        return self.session.query(TestService).filter_by(service_id=service_id).first()
    
    def get_by_category(self, category: str) -> List[TestService]:
        """Get test services by category"""
        return self.session.query(TestService).filter_by(
            category=category,
            is_active=True
        ).all()
    
    def get_by_standard(self, standard: str) -> List[TestService]:
        """Get test services for a standard"""
        return self.session.query(TestService).filter(
            and_(
                TestService.standard.ilike(f'%{standard}%'),
                TestService.is_active == True
            )
        ).all()
    
    def calculate_total_cost(self, service_ids: List[str]) -> Dict[str, Any]:
        """Calculate total cost for multiple services"""
        services = self.session.query(TestService).filter(
            TestService.service_id.in_(service_ids)
        ).all()
        
        total = sum(s.price for s in services)
        
        return {
            'total_cost': total,
            'services': [s.to_dict() for s in services],
            'count': len(services),
            'not_found': [sid for sid in service_ids if sid not in [s.service_id for s in services]]
        }
