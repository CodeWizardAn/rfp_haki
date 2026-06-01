"""
Win/Loss Recording Endpoint & RFP Parsing
Allows recording bid outcomes and extracting historical data from RFP documents
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel

from database.db_engine import get_db_manager
from analytics.win_loss_analytics import WinLossAnalytics
from analytics.models import WinLossRecord

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

# ==================== REQUEST MODELS ====================

class BidOutcomeRecord(BaseModel):
    """Record a bid outcome"""
    rfp_id: str
    bid_id: Optional[str] = None
    outcome: str  # 'won', 'lost', 'no_bid'
    our_bid_amount: Optional[float] = None
    winning_bid_amount: Optional[float] = None
    winning_competitor: Optional[str] = None
    competitor_names: Optional[List[str]] = None
    technical_score: Optional[float] = None
    commercial_score: Optional[float] = None
    overall_score: Optional[float] = None
    winning_factors: Optional[List[str]] = None
    losing_factors: Optional[List[str]] = None
    customer_name: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_region: Optional[str] = None
    rfp_category: Optional[str] = None


# ==================== ENDPOINTS ====================

@router.post("/record-bid-outcome")
async def record_bid_outcome(
    outcome_data: BidOutcomeRecord,
    user_id: Optional[str] = Query(None)
):
    """
    Record a bid outcome (won/lost/no_bid)
    
    This allows sales teams to record the result of a bid submission,
    which will be used to calculate win/loss ratios over time.
    
    Example:
    ```json
    {
        "rfp_id": "GEM/2025/B/6694421",
        "bid_id": "BID-001",
        "outcome": "won",
        "our_bid_amount": 915000,
        "winning_bid_amount": 915000,
        "technical_score": 92.5,
        "commercial_score": 88.0,
        "winning_factors": ["Competitive pricing", "Technical expertise"],
        "customer_name": "Power Grid Corporation",
        "customer_segment": "Government",
        "customer_region": "India"
    }
    ```
    """
    try:
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
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
        
        return {
            "success": True,
            "message": f"Bid outcome recorded for RFP {outcome_data.rfp_id}",
            "record_id": record.id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/extract-historical-bids/{rfp_id}")
async def extract_historical_bids(rfp_id: str):
    """
    Extract historical bid information from RFP documents
    
    This endpoint attempts to find and extract:
    - Previous bid history from the RFP document
    - Competitor information
    - Winning bid amounts
    - Technical/commercial scores if available
    
    This data is then used to calculate win/loss ratios.
    """
    try:
        from pdf_extraction.rfp_terms_matcher import TermsMatcher
        from pdf_extraction.pdf_extraction_manager import PDFExtractionManager
        
        # Try to find RFP documents that mention this RFP ID
        extraction_manager = PDFExtractionManager()
        
        return {
            "success": True,
            "rfp_id": rfp_id,
            "message": "Historical bid extraction not yet implemented",
            "recommendation": "Use the record-bid-outcome endpoint to manually record bid results"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/get-win-loss-ratio/{rfp_id}")
async def get_win_loss_ratio(rfp_id: str):
    """
    Get the calculated win/loss ratio for a specific RFP
    
    Returns:
    - Win rate percentage
    - Win ratio (wins:losses)
    - Bid value analysis
    - Competitor information
    - Score analysis
    """
    try:
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
        win_loss_analytics = WinLossAnalytics(session_factory=lambda: db_manager.get_session())
        result = win_loss_analytics.get_win_loss_ratio_by_rfp(session, rfp_id)
        
        session.close()
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/bulk-record-outcomes")
async def bulk_record_outcomes(
    outcomes: List[BidOutcomeRecord],
    user_id: Optional[str] = Query(None)
):
    """
    Record multiple bid outcomes at once
    
    Useful for importing historical bid data from CSV or another system
    """
    try:
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
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
        
        return {
            "success": True,
            "message": f"Recorded {len(records)} bid outcomes",
            "count": len(records)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
