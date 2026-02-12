"""
Cost Analysis
Tracks and analyzes costs associated with RFP processing

Features:
- Cost tracking by category
- Cost per RFP analysis
- Cost trends
- Budget monitoring
- Cost optimization recommendations
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from .models import CostRecord
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)


class CostAnalyzer:
    """
    Comprehensive cost analysis for RFP processing
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self.collector = MetricsCollector()
        
        # Default cost rates
        self._cost_rates = {
            'llm': {
                'openai_gpt4': 0.03,  # per 1K tokens
                'openai_gpt35': 0.002,
                'azure_openai': 0.025
            },
            'compute': {
                'cpu_hour': 0.05,
                'gpu_hour': 2.50,
                'memory_gb_hour': 0.01
            },
            'storage': {
                'storage_gb_month': 0.023,
                'requests_1k': 0.005
            },
            'api': {
                'pdf_extraction': 0.01,
                'ocr': 0.05,
                'external_api': 0.001
            }
        }
    
    def set_cost_rate(self, category: str, subcategory: str, rate: float):
        """Set cost rate for a category"""
        if category not in self._cost_rates:
            self._cost_rates[category] = {}
        self._cost_rates[category][subcategory] = rate
    
    # ==================== Recording ====================
    
    def record_cost(self, cost_category: str, amount: float,
                   rfp_id: str = None, operation_id: str = None,
                   cost_subcategory: str = None, currency: str = 'USD',
                   units_consumed: float = None, unit_type: str = None,
                   agent_type: str = None, operation_type: str = None,
                   period_start: datetime = None, period_end: datetime = None) -> CostRecord:
        """Record a cost"""
        
        # Calculate unit cost if not provided
        unit_cost = None
        if units_consumed and units_consumed > 0:
            unit_cost = amount / units_consumed
        
        cost_data = {
            'rfp_id': rfp_id,
            'operation_id': operation_id,
            'cost_category': cost_category,
            'cost_subcategory': cost_subcategory,
            'amount': amount,
            'currency': currency,
            'units_consumed': units_consumed,
            'unit_type': unit_type,
            'unit_cost': unit_cost,
            'agent_type': agent_type,
            'operation_type': operation_type,
            'period_start': period_start,
            'period_end': period_end,
            'recorded_at': datetime.utcnow()
        }
        
        # Record to collector
        self.collector.histogram(f'cost.{cost_category}', amount)
        if rfp_id:
            self.collector.histogram('cost.per_rfp', amount)
        
        if self.session_factory:
            return self._save_cost(cost_data)
        
        return cost_data
    
    def _save_cost(self, cost_data: Dict[str, Any]) -> CostRecord:
        """Save cost to database"""
        session = self.session_factory()
        try:
            cost = CostRecord(**cost_data)
            session.add(cost)
            session.commit()
            session.refresh(cost)
            return cost
        finally:
            session.close()
    
    def record_llm_cost(self, tokens_used: int, model: str = 'openai_gpt4',
                       rfp_id: str = None, agent_type: str = None):
        """Record LLM usage cost"""
        rate = self._cost_rates['llm'].get(model, 0.03)
        amount = (tokens_used / 1000) * rate
        
        return self.record_cost(
            cost_category='llm',
            cost_subcategory=model,
            amount=amount,
            rfp_id=rfp_id,
            units_consumed=tokens_used,
            unit_type='tokens',
            agent_type=agent_type,
            operation_type='llm_inference'
        )
    
    # ==================== Analysis ====================
    
    def get_total_costs(self, session: Session,
                       start_date: datetime = None,
                       end_date: datetime = None,
                       group_by: str = None) -> Dict[str, Any]:
        """Get total costs, optionally grouped"""
        query = session.query(
            func.sum(CostRecord.amount).label('total'),
            func.count(CostRecord.id).label('count'),
            func.avg(CostRecord.amount).label('average')
        )
        
        if start_date:
            query = query.filter(CostRecord.recorded_at >= start_date)
        if end_date:
            query = query.filter(CostRecord.recorded_at <= end_date)
        
        result = query.first()
        
        return {
            'total_amount': float(result.total or 0),
            'transaction_count': result.count,
            'average_per_transaction': float(result.average or 0)
        }
    
    def get_costs_by_category(self, session: Session,
                             start_date: datetime = None,
                             end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get costs broken down by category"""
        query = session.query(
            CostRecord.cost_category,
            func.sum(CostRecord.amount).label('total'),
            func.count(CostRecord.id).label('count'),
            func.sum(CostRecord.units_consumed).label('total_units')
        ).group_by(CostRecord.cost_category).order_by(desc('total'))
        
        if start_date:
            query = query.filter(CostRecord.recorded_at >= start_date)
        if end_date:
            query = query.filter(CostRecord.recorded_at <= end_date)
        
        results = []
        total = sum(float(row.total or 0) for row in query.all())
        
        for row in query.all():
            results.append({
                'category': row.cost_category,
                'total_amount': float(row.total or 0),
                'percentage': (float(row.total or 0) / total * 100) if total > 0 else 0,
                'transaction_count': row.count,
                'total_units': float(row.total_units or 0)
            })
        
        return results
    
    def get_costs_by_subcategory(self, session: Session,
                                category: str = None,
                                start_date: datetime = None,
                                end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get costs broken down by subcategory"""
        query = session.query(
            CostRecord.cost_category,
            CostRecord.cost_subcategory,
            func.sum(CostRecord.amount).label('total'),
            func.sum(CostRecord.units_consumed).label('units')
        ).group_by(CostRecord.cost_category, CostRecord.cost_subcategory).order_by(desc('total'))
        
        if category:
            query = query.filter(CostRecord.cost_category == category)
        if start_date:
            query = query.filter(CostRecord.recorded_at >= start_date)
        if end_date:
            query = query.filter(CostRecord.recorded_at <= end_date)
        
        return [
            {
                'category': row.cost_category,
                'subcategory': row.cost_subcategory,
                'total_amount': float(row.total or 0),
                'total_units': float(row.units or 0)
            }
            for row in query.all()
        ]
    
    def get_cost_per_rfp(self, session: Session,
                        start_date: datetime = None,
                        end_date: datetime = None) -> Dict[str, Any]:
        """Analyze cost per RFP"""
        query = session.query(
            CostRecord.rfp_id,
            func.sum(CostRecord.amount).label('total_cost')
        ).filter(
            CostRecord.rfp_id.isnot(None)
        ).group_by(CostRecord.rfp_id)
        
        if start_date:
            query = query.filter(CostRecord.recorded_at >= start_date)
        if end_date:
            query = query.filter(CostRecord.recorded_at <= end_date)
        
        rfp_costs = [float(row.total_cost or 0) for row in query.all()]
        
        if not rfp_costs:
            return {
                'rfp_count': 0,
                'total_cost': 0,
                'avg_cost_per_rfp': 0,
                'min_cost': 0,
                'max_cost': 0
            }
        
        return {
            'rfp_count': len(rfp_costs),
            'total_cost': sum(rfp_costs),
            'avg_cost_per_rfp': sum(rfp_costs) / len(rfp_costs),
            'min_cost': min(rfp_costs),
            'max_cost': max(rfp_costs),
            'median_cost': sorted(rfp_costs)[len(rfp_costs) // 2]
        }
    
    def get_cost_by_agent(self, session: Session,
                         start_date: datetime = None,
                         end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get costs by agent type"""
        query = session.query(
            CostRecord.agent_type,
            func.sum(CostRecord.amount).label('total'),
            func.sum(CostRecord.units_consumed).label('units'),
            func.count(CostRecord.id).label('count')
        ).filter(
            CostRecord.agent_type.isnot(None)
        ).group_by(CostRecord.agent_type).order_by(desc('total'))
        
        if start_date:
            query = query.filter(CostRecord.recorded_at >= start_date)
        if end_date:
            query = query.filter(CostRecord.recorded_at <= end_date)
        
        return [
            {
                'agent_type': row.agent_type,
                'total_cost': float(row.total or 0),
                'total_units': float(row.units or 0),
                'request_count': row.count,
                'avg_cost_per_request': float(row.total or 0) / row.count if row.count > 0 else 0
            }
            for row in query.all()
        ]
    
    def get_cost_trend(self, session: Session,
                      granularity: str = 'day',
                      category: str = None,
                      start_date: datetime = None,
                      end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get cost trend over time"""
        date_trunc = func.date_trunc(granularity, CostRecord.recorded_at)
        
        query = session.query(
            date_trunc.label('period'),
            func.sum(CostRecord.amount).label('total'),
            func.count(CostRecord.id).label('count')
        ).group_by(date_trunc).order_by(date_trunc)
        
        if category:
            query = query.filter(CostRecord.cost_category == category)
        if start_date:
            query = query.filter(CostRecord.recorded_at >= start_date)
        if end_date:
            query = query.filter(CostRecord.recorded_at <= end_date)
        
        return [
            {
                'period': row.period.isoformat() if row.period else None,
                'total_cost': float(row.total or 0),
                'transaction_count': row.count
            }
            for row in query.all()
        ]
    
    def get_budget_status(self, session: Session,
                         budget: float,
                         period_start: datetime,
                         period_end: datetime = None) -> Dict[str, Any]:
        """Check budget status for a period"""
        end_date = period_end or datetime.utcnow()
        
        total = session.query(func.sum(CostRecord.amount)).filter(
            CostRecord.recorded_at >= period_start,
            CostRecord.recorded_at <= end_date
        ).scalar() or 0
        
        total = float(total)
        remaining = budget - total
        usage_percent = (total / budget * 100) if budget > 0 else 0
        
        # Calculate burn rate
        days_elapsed = (end_date - period_start).days or 1
        daily_burn = total / days_elapsed
        
        # Project end of period
        total_days = (period_end - period_start).days if period_end else 30
        projected_total = daily_burn * total_days
        
        return {
            'budget': budget,
            'spent': total,
            'remaining': remaining,
            'usage_percent': usage_percent,
            'daily_burn_rate': daily_burn,
            'projected_total': projected_total,
            'projected_over_budget': projected_total > budget,
            'status': 'over_budget' if total > budget else 
                     'warning' if usage_percent > 80 else 'ok'
        }
    
    def get_optimization_recommendations(self, session: Session,
                                        days: int = 30) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        recommendations = []
        
        # Analyze by category
        category_costs = self.get_costs_by_category(session, start_date, end_date)
        
        # Check for high LLM costs
        llm_costs = next((c for c in category_costs if c['category'] == 'llm'), None)
        if llm_costs and llm_costs['percentage'] > 50:
            recommendations.append({
                'category': 'llm',
                'priority': 'high',
                'title': 'High LLM Costs',
                'description': f"LLM costs represent {llm_costs['percentage']:.1f}% of total costs",
                'suggestion': 'Consider using cheaper models for simpler tasks or implementing caching',
                'potential_savings': llm_costs['total_amount'] * 0.3
            })
        
        # Check for inefficient agents
        agent_costs = self.get_cost_by_agent(session, start_date, end_date)
        for agent in agent_costs:
            if agent['avg_cost_per_request'] > 0.10:  # $0.10 per request threshold
                recommendations.append({
                    'category': 'agent',
                    'priority': 'medium',
                    'title': f"High Cost Agent: {agent['agent_type']}",
                    'description': f"Average cost per request: ${agent['avg_cost_per_request']:.4f}",
                    'suggestion': 'Review agent implementation for optimization opportunities',
                    'potential_savings': agent['total_cost'] * 0.2
                })
        
        # Check for cost spikes
        trend = self.get_cost_trend(session, 'day', start_date=start_date, end_date=end_date)
        if len(trend) >= 7:
            avg_cost = sum(t['total_cost'] for t in trend) / len(trend)
            recent_avg = sum(t['total_cost'] for t in trend[-3:]) / 3
            
            if recent_avg > avg_cost * 1.5:
                recommendations.append({
                    'category': 'trend',
                    'priority': 'high',
                    'title': 'Recent Cost Spike Detected',
                    'description': f"Recent costs are {(recent_avg/avg_cost - 1)*100:.1f}% above average",
                    'suggestion': 'Investigate recent changes that may have increased costs',
                    'potential_savings': (recent_avg - avg_cost) * 30
                })
        
        return sorted(recommendations, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['priority']])
    
    def get_cost_report(self, session: Session, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive cost report"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'summary': self.get_total_costs(session, start_date, end_date),
            'by_category': self.get_costs_by_category(session, start_date, end_date),
            'by_subcategory': self.get_costs_by_subcategory(session, start_date=start_date, end_date=end_date),
            'per_rfp': self.get_cost_per_rfp(session, start_date, end_date),
            'by_agent': self.get_cost_by_agent(session, start_date, end_date),
            'trend': self.get_cost_trend(session, 'day', start_date=start_date, end_date=end_date),
            'recommendations': self.get_optimization_recommendations(session, days)
        }
