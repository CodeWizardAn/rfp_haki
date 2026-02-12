"""
Vendor Rating System
Multi-criteria rating, rankings, badges
"""

import sqlite3
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import logging
from enum import Enum


class RatingBadge(Enum):
    """Vendor rating badges"""
    GOLD_PARTNER = "Gold Partner"
    SILVER_PARTNER = "Silver Partner"
    BRONZE_PARTNER = "Bronze Partner"
    RELIABLE = "Reliable"
    QUALITY_CERTIFIED = "Quality Certified"
    FAST_RESPONDER = "Fast Responder"
    NEW_VENDOR = "New Vendor"
    TOP_PERFORMER = "Top Performer"


@dataclass
class RatingCriteria:
    """Individual rating criterion"""
    criterion_id: str
    name: str
    description: str
    weight: float  # 0-1
    min_acceptable: float = 0
    excellent_threshold: float = 90


@dataclass
class VendorRating:
    """Complete vendor rating"""
    vendor_id: str
    rating_date: datetime
    delivery_score: float  # 0-100
    quality_score: float  # 0-100
    response_score: float  # 0-100
    compliance_score: float  # 0-100
    price_score: float  # 0-100
    overall_rating: float  # 0-100
    trend: str = "STABLE"  # IMPROVING, STABLE, DECLINING
    badge: Optional[RatingBadge] = None


class VendorRatingEngine:
    """Rate vendors based on multiple criteria"""

    def __init__(self, db_path: str = None):
        """Initialize rating engine"""
        if db_path is None:
            # Use centralized database path
            from db_paths import get_vendor_ratings_db_path
            db_path = get_vendor_ratings_db_path()
        
        self.db_path = db_path
        self.connection = None
        self.logger = logging.getLogger('vendor_rating')
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        cursor = self.connection.cursor()

        # Criteria definition
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rating_criteria (
                criterion_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                weight REAL,
                min_acceptable REAL,
                excellent_threshold REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Vendor ratings history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendor_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id TEXT NOT NULL,
                rating_date DATETIME,
                delivery_score REAL,
                quality_score REAL,
                response_score REAL,
                compliance_score REAL,
                price_score REAL,
                overall_rating REAL,
                trend TEXT,
                badge TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # Vendor badges
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendor_badges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id TEXT NOT NULL,
                badge_name TEXT,
                awarded_date DATETIME,
                expires_date DATETIME,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # Vendor rankings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vendor_rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id TEXT NOT NULL,
                rank INTEGER,
                percentile REAL,
                category TEXT,
                ranking_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id)
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor_id_rating ON vendor_ratings(vendor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor_id_badge ON vendor_badges(vendor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendor_id_rank ON vendor_rankings(vendor_id)')

        # Initialize standard criteria
        self._init_criteria()

        self.connection.commit()
        self.logger.info(f"✅ Rating engine initialized")

    def _init_criteria(self):
        """Initialize standard rating criteria"""
        standard_criteria = [
            RatingCriteria('delivery', 'On-Time Delivery', 'Delivery performance', 0.25),
            RatingCriteria('quality', 'Product Quality', 'Defect rate and quality', 0.25),
            RatingCriteria('response', 'Response Time', 'Communication responsiveness', 0.15),
            RatingCriteria('compliance', 'Compliance', 'Regulatory compliance', 0.20),
            RatingCriteria('price', 'Price Competitiveness', 'Price vs market', 0.15),
        ]
        
        for criterion in standard_criteria:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO rating_criteria
                (criterion_id, name, description, weight, min_acceptable, excellent_threshold)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                criterion.criterion_id, criterion.name, criterion.description,
                criterion.weight, criterion.min_acceptable, criterion.excellent_threshold
            ))

    def record_rating(self, rating: VendorRating) -> bool:
        """Record vendor rating"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO vendor_ratings
                (vendor_id, rating_date, delivery_score, quality_score, response_score,
                 compliance_score, price_score, overall_rating, trend, badge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                rating.vendor_id, rating.rating_date.isoformat(),
                rating.delivery_score, rating.quality_score, rating.response_score,
                rating.compliance_score, rating.price_score, rating.overall_rating,
                rating.trend, rating.badge.value if rating.badge else None
            ))
            self.connection.commit()
            self.logger.info(f"Recorded rating for {rating.vendor_id}: {rating.overall_rating}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to record rating: {e}")
            return False

    def calculate_rating(self, delivery: float, quality: float, response: float,
                        compliance: float, price: float) -> float:
        """Calculate weighted overall rating"""
        weights = {
            'delivery': 0.25,
            'quality': 0.25,
            'response': 0.15,
            'compliance': 0.20,
            'price': 0.15
        }
        
        overall = (
            delivery * weights['delivery'] +
            quality * weights['quality'] +
            response * weights['response'] +
            compliance * weights['compliance'] +
            price * weights['price']
        )
        
        return round(overall, 2)

    def assign_badge(self, vendor_id: str, overall_rating: float) -> Optional[RatingBadge]:
        """Assign badge based on rating"""
        if overall_rating >= 95:
            badge = RatingBadge.GOLD_PARTNER
        elif overall_rating >= 85:
            badge = RatingBadge.SILVER_PARTNER
        elif overall_rating >= 75:
            badge = RatingBadge.BRONZE_PARTNER
        else:
            badge = None
        
        if badge:
            try:
                cursor = self.connection.cursor()
                cursor.execute('''
                    INSERT INTO vendor_badges (vendor_id, badge_name, awarded_date, reason)
                    VALUES (?, ?, ?, ?)
                ''', (vendor_id, badge.value, datetime.now().isoformat(),
                      f"Achieved {overall_rating} overall rating"))
                self.connection.commit()
                self.logger.info(f"Assigned badge '{badge.value}' to {vendor_id}")
            except Exception as e:
                self.logger.error(f"Failed to assign badge: {e}")
        
        return badge

    def get_vendor_badges(self, vendor_id: str) -> List[Dict]:
        """Get all badges for vendor"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT badge_name, awarded_date, reason FROM vendor_badges
            WHERE vendor_id = ? AND (expires_date IS NULL OR expires_date > datetime('now'))
            ORDER BY awarded_date DESC
        ''', (vendor_id,))
        
        columns = ['badge_name', 'awarded_date', 'reason']
        badges = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return badges

    def calculate_trend(self, vendor_id: str) -> str:
        """Calculate rating trend"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT overall_rating FROM vendor_ratings
            WHERE vendor_id = ?
            ORDER BY rating_date DESC
            LIMIT 3
        ''', (vendor_id,))
        
        ratings = [row[0] for row in cursor.fetchall()]
        
        if len(ratings) < 2:
            return "STABLE"
        
        # Compare last 2 ratings
        if ratings[0] > ratings[1] + 2:
            return "IMPROVING"
        elif ratings[0] < ratings[1] - 2:
            return "DECLINING"
        else:
            return "STABLE"

    def get_vendor_rating(self, vendor_id: str) -> Optional[Dict]:
        """Get latest vendor rating"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM vendor_ratings
            WHERE vendor_id = ?
            ORDER BY rating_date DESC
            LIMIT 1
        ''', (vendor_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        columns = [description[0] for description in cursor.description]
        return dict(zip(columns, row))

    def rank_vendors(self, category: str = 'ALL', top_n: int = None) -> List[Dict]:
        """Rank vendors"""
        cursor = self.connection.cursor()
        
        # Get latest rating for each vendor (SQLite compatible)
        cursor.execute('''
            SELECT vr.vendor_id, vr.overall_rating
            FROM vendor_ratings vr
            WHERE vr.rating_date = (
                SELECT MAX(rating_date) FROM vendor_ratings WHERE vendor_id = vr.vendor_id
            )
            GROUP BY vr.vendor_id
            ORDER BY vr.overall_rating DESC
        ''')
        
        vendor_ratings = cursor.fetchall()
        
        # Sort by rating descending
        vendor_ratings.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate percentiles and assign ranks
        rankings = []
        total = len(vendor_ratings)
        
        for rank, (vendor_id, rating) in enumerate(vendor_ratings, 1):
            percentile = ((total - rank) / total) * 100
            rankings.append({
                'rank': rank,
                'vendor_id': vendor_id,
                'rating': rating,
                'percentile': round(percentile, 2)
            })
        
        if top_n:
            rankings = rankings[:top_n]
        
        return rankings

    def get_rating_history(self, vendor_id: str, limit: int = 12) -> List[Dict]:
        """Get rating history"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM vendor_ratings
            WHERE vendor_id = ?
            ORDER BY rating_date DESC
            LIMIT ?
        ''', (vendor_id, limit))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def close(self):
        """Close database"""
        if self.connection:
            self.connection.close()


# Singleton instance
_rating_engine = None

def get_rating_engine() -> VendorRatingEngine:
    """Get or create rating engine"""
    global _rating_engine
    if _rating_engine is None:
        _rating_engine = VendorRatingEngine()
    return _rating_engine


if __name__ == '__main__':
    engine = VendorRatingEngine()

    # Create sample rating
    rating = VendorRating(
        vendor_id='V001',
        rating_date=datetime.now(),
        delivery_score=92.0,
        quality_score=88.0,
        response_score=95.0,
        compliance_score=90.0,
        price_score=85.0,
        overall_rating=engine.calculate_rating(92, 88, 95, 90, 85)
    )
    
    if engine.record_rating(rating):
        print("✅ Rating recorded")
        
        # Assign badge
        badge = engine.assign_badge('V001', rating.overall_rating)
        print(f"Badge: {badge.value if badge else 'None'}")
        
        # Get ranking
        rankings = engine.rank_vendors(top_n=5)
        print(f"Top vendors: {len(rankings)}")

    engine.close()
