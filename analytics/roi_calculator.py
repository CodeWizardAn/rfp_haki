"""
ROI Calculator
Calculates return on investment for RFP processing

Features:
- Win value tracking
- Cost-benefit analysis
- ROI trends
- What-if analysis
- Efficiency metrics
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import RFPMetric, WinLossRecord, CostRecord
from .cost_analysis import CostAnalyzer
from .win_loss_analytics import WinLossAnalytics

logger = logging.getLogger(__name__)


class ROICalculator:
    """
    Comprehensive ROI calculation for RFP processing
    """
    
    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self.cost_analyzer = CostAnalyzer(session_factory)
        self.win_loss_analytics = WinLossAnalytics(session_factory)
        
        # Default assumptions
        self._assumptions = {
            'avg_margin_percent': 15.0,  # Average profit margin on won deals
            'manual_processing_cost': 500.0,  # Cost to process RFP manually
            'manual_processing_hours': 8.0,  # Hours to process manually
            'hourly_labor_cost': 50.0,  # Labor cost per hour
            'currency': 'USD'
        }
    
    def set_assumption(self, key: str, value: float):
        """Set an assumption value"""
        self._assumptions[key] = value
    
    def get_assumptions(self) -> Dict[str, float]:
        """Get current assumptions"""
        return self._assumptions.copy()
    
    # ==================== Core ROI Calculations ====================
    
    def calculate_roi(self, session: Session,
                     start_date: datetime = None,
                     end_date: datetime = None) -> Dict[str, Any]:
        """
        Calculate comprehensive ROI metrics
        
        ROI = (Gain from Investment - Cost of Investment) / Cost of Investment * 100
        """
        # Get costs
        costs = self.cost_analyzer.get_total_costs(session, start_date, end_date)
        total_cost = costs['total_amount']
        
        # Get wins
        win_stats = session.query(
            func.count(WinLossRecord.id).label('won_count'),
            func.sum(WinLossRecord.our_bid_amount).label('won_value')
        ).filter(
            WinLossRecord.outcome == 'won',
            WinLossRecord.recorded_at >= start_date if start_date else True,
            WinLossRecord.recorded_at <= end_date if end_date else True
        ).first()
        
        won_count = win_stats.won_count or 0
        won_value = float(win_stats.won_value or 0)
        
        # Calculate estimated profit from wins
        margin_percent = self._assumptions['avg_margin_percent']
        estimated_profit = won_value * (margin_percent / 100)
        
        # Calculate manual processing savings
        rfp_count = session.query(func.count(RFPMetric.id)).filter(
            RFPMetric.recorded_at >= start_date if start_date else True,
            RFPMetric.recorded_at <= end_date if end_date else True
        ).scalar() or 0
        
        manual_cost = rfp_count * self._assumptions['manual_processing_cost']
        automation_savings = manual_cost - total_cost if manual_cost > total_cost else 0
        
        # Total gain
        total_gain = estimated_profit + automation_savings
        
        # ROI calculation
        roi_percent = ((total_gain - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'investments': {
                'total_cost': total_cost,
                'rfps_processed': rfp_count
            },
            'returns': {
                'won_deals': won_count,
                'won_value': won_value,
                'estimated_profit': estimated_profit,
                'automation_savings': automation_savings,
                'total_gain': total_gain
            },
            'roi': {
                'roi_percent': roi_percent,
                'net_benefit': total_gain - total_cost,
                'cost_per_rfp': total_cost / rfp_count if rfp_count > 0 else 0,
                'profit_per_rfp': estimated_profit / rfp_count if rfp_count > 0 else 0
            },
            'assumptions': self._assumptions
        }
    
    def calculate_efficiency_metrics(self, session: Session,
                                    start_date: datetime = None,
                                    end_date: datetime = None) -> Dict[str, Any]:
        """Calculate efficiency-related metrics"""
        
        # Processing time stats
        time_stats = session.query(
            func.avg(RFPMetric.total_processing_time_ms).label('avg_time'),
            func.min(RFPMetric.total_processing_time_ms).label('min_time'),
            func.max(RFPMetric.total_processing_time_ms).label('max_time'),
            func.count(RFPMetric.id).label('count')
        ).filter(
            RFPMetric.recorded_at >= start_date if start_date else True,
            RFPMetric.recorded_at <= end_date if end_date else True
        ).first()
        
        avg_processing_time_hours = (float(time_stats.avg_time or 0) / 1000 / 3600)
        manual_hours = self._assumptions['manual_processing_hours']
        
        time_savings_per_rfp = manual_hours - avg_processing_time_hours
        total_time_saved = time_savings_per_rfp * (time_stats.count or 0)
        
        labor_cost_saved = total_time_saved * self._assumptions['hourly_labor_cost']
        
        return {
            'processing_time': {
                'avg_hours': avg_processing_time_hours,
                'manual_hours': manual_hours,
                'time_saved_per_rfp': time_savings_per_rfp,
                'total_hours_saved': total_time_saved
            },
            'labor_savings': {
                'hourly_rate': self._assumptions['hourly_labor_cost'],
                'total_saved': labor_cost_saved
            },
            'efficiency_ratio': manual_hours / avg_processing_time_hours if avg_processing_time_hours > 0 else 0,
            'rfps_processed': time_stats.count or 0
        }
    
    def calculate_win_value_metrics(self, session: Session,
                                   start_date: datetime = None,
                                   end_date: datetime = None) -> Dict[str, Any]:
        """Calculate win value related metrics"""
        
        # Get win statistics
        win_stats = session.query(
            func.count(WinLossRecord.id).label('count'),
            func.sum(WinLossRecord.our_bid_amount).label('total_value'),
            func.avg(WinLossRecord.our_bid_amount).label('avg_value'),
            func.min(WinLossRecord.our_bid_amount).label('min_value'),
            func.max(WinLossRecord.our_bid_amount).label('max_value')
        ).filter(
            WinLossRecord.outcome == 'won',
            WinLossRecord.our_bid_amount.isnot(None),
            WinLossRecord.recorded_at >= start_date if start_date else True,
            WinLossRecord.recorded_at <= end_date if end_date else True
        ).first()
        
        # Get total bids for win rate
        total_bids = session.query(func.count(WinLossRecord.id)).filter(
            WinLossRecord.outcome.in_(['won', 'lost']),
            WinLossRecord.recorded_at >= start_date if start_date else True,
            WinLossRecord.recorded_at <= end_date if end_date else True
        ).scalar() or 0
        
        win_rate = (win_stats.count or 0) / total_bids if total_bids > 0 else 0
        
        return {
            'wins': {
                'count': win_stats.count or 0,
                'total_value': float(win_stats.total_value or 0),
                'avg_value': float(win_stats.avg_value or 0),
                'min_value': float(win_stats.min_value or 0),
                'max_value': float(win_stats.max_value or 0)
            },
            'win_rate': win_rate,
            'total_bids': total_bids,
            'estimated_profit': float(win_stats.total_value or 0) * (self._assumptions['avg_margin_percent'] / 100)
        }
    
    def calculate_cost_per_win(self, session: Session,
                              start_date: datetime = None,
                              end_date: datetime = None) -> Dict[str, Any]:
        """Calculate cost per win and related metrics"""
        
        costs = self.cost_analyzer.get_total_costs(session, start_date, end_date)
        total_cost = costs['total_amount']
        
        win_count = session.query(func.count(WinLossRecord.id)).filter(
            WinLossRecord.outcome == 'won',
            WinLossRecord.recorded_at >= start_date if start_date else True,
            WinLossRecord.recorded_at <= end_date if end_date else True
        ).scalar() or 0
        
        total_bids = session.query(func.count(WinLossRecord.id)).filter(
            WinLossRecord.outcome.in_(['won', 'lost']),
            WinLossRecord.recorded_at >= start_date if start_date else True,
            WinLossRecord.recorded_at <= end_date if end_date else True
        ).scalar() or 0
        
        rfp_count = session.query(func.count(RFPMetric.id)).filter(
            RFPMetric.recorded_at >= start_date if start_date else True,
            RFPMetric.recorded_at <= end_date if end_date else True
        ).scalar() or 0
        
        return {
            'total_cost': total_cost,
            'cost_per_rfp': total_cost / rfp_count if rfp_count > 0 else 0,
            'cost_per_bid': total_cost / total_bids if total_bids > 0 else 0,
            'cost_per_win': total_cost / win_count if win_count > 0 else 0,
            'wins': win_count,
            'bids': total_bids,
            'rfps': rfp_count
        }
    
    # ==================== What-If Analysis ====================
    
    def what_if_win_rate_change(self, session: Session,
                               new_win_rate: float,
                               start_date: datetime = None,
                               end_date: datetime = None) -> Dict[str, Any]:
        """What-if analysis for win rate changes"""
        
        current_metrics = self.calculate_win_value_metrics(session, start_date, end_date)
        current_win_rate = current_metrics['win_rate']
        total_bids = current_metrics['total_bids']
        avg_deal_value = current_metrics['wins']['avg_value']
        
        # Project new wins
        current_wins = current_metrics['wins']['count']
        projected_wins = int(total_bids * new_win_rate)
        additional_wins = projected_wins - current_wins
        
        # Calculate value impact
        additional_value = additional_wins * avg_deal_value
        additional_profit = additional_value * (self._assumptions['avg_margin_percent'] / 100)
        
        return {
            'current': {
                'win_rate': current_win_rate,
                'wins': current_wins,
                'total_value': current_metrics['wins']['total_value']
            },
            'projected': {
                'win_rate': new_win_rate,
                'wins': projected_wins,
                'additional_wins': additional_wins,
                'additional_value': additional_value,
                'additional_profit': additional_profit
            },
            'impact': {
                'win_rate_change': new_win_rate - current_win_rate,
                'win_rate_change_percent': ((new_win_rate - current_win_rate) / current_win_rate * 100) 
                    if current_win_rate > 0 else 0,
                'value_increase': additional_value,
                'profit_increase': additional_profit
            }
        }
    
    def what_if_cost_reduction(self, session: Session,
                              cost_reduction_percent: float,
                              start_date: datetime = None,
                              end_date: datetime = None) -> Dict[str, Any]:
        """What-if analysis for cost reduction"""
        
        current_roi = self.calculate_roi(session, start_date, end_date)
        current_cost = current_roi['investments']['total_cost']
        
        new_cost = current_cost * (1 - cost_reduction_percent / 100)
        cost_savings = current_cost - new_cost
        
        # Recalculate ROI with new cost
        total_gain = current_roi['returns']['total_gain']
        new_roi = ((total_gain - new_cost) / new_cost * 100) if new_cost > 0 else 0
        
        return {
            'current': {
                'total_cost': current_cost,
                'roi_percent': current_roi['roi']['roi_percent']
            },
            'projected': {
                'total_cost': new_cost,
                'cost_savings': cost_savings,
                'new_roi_percent': new_roi
            },
            'impact': {
                'cost_reduction_percent': cost_reduction_percent,
                'roi_improvement': new_roi - current_roi['roi']['roi_percent'],
                'net_benefit_increase': cost_savings
            }
        }
    
    # ==================== ROI Trends ====================
    
    def get_roi_trend(self, session: Session,
                     granularity: str = 'month',
                     periods: int = 12) -> List[Dict[str, Any]]:
        """Get ROI trend over time"""
        
        results = []
        end_date = datetime.utcnow()
        
        for i in range(periods):
            if granularity == 'month':
                period_end = end_date - timedelta(days=30 * i)
                period_start = period_end - timedelta(days=30)
            elif granularity == 'week':
                period_end = end_date - timedelta(weeks=i)
                period_start = period_end - timedelta(weeks=1)
            else:  # day
                period_end = end_date - timedelta(days=i)
                period_start = period_end - timedelta(days=1)
            
            roi = self.calculate_roi(session, period_start, period_end)
            
            results.append({
                'period': period_start.isoformat(),
                'roi_percent': roi['roi']['roi_percent'],
                'total_cost': roi['investments']['total_cost'],
                'total_gain': roi['returns']['total_gain'],
                'net_benefit': roi['roi']['net_benefit'],
                'won_deals': roi['returns']['won_deals']
            })
        
        return list(reversed(results))
    
    def get_comprehensive_report(self, session: Session, days: int = 90) -> Dict[str, Any]:
        """Generate comprehensive ROI report"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        roi = self.calculate_roi(session, start_date, end_date)
        efficiency = self.calculate_efficiency_metrics(session, start_date, end_date)
        win_metrics = self.calculate_win_value_metrics(session, start_date, end_date)
        cost_per_win = self.calculate_cost_per_win(session, start_date, end_date)
        
        # What-if scenarios
        win_rate_5_increase = self.what_if_win_rate_change(
            session, 
            win_metrics['win_rate'] + 0.05,
            start_date, 
            end_date
        )
        
        cost_reduction_10 = self.what_if_cost_reduction(
            session,
            10,
            start_date,
            end_date
        )
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'roi_summary': roi,
            'efficiency': efficiency,
            'win_metrics': win_metrics,
            'cost_per_win': cost_per_win,
            'trend': self.get_roi_trend(session, 'month', min(12, days // 30 + 1)),
            'what_if_scenarios': {
                'win_rate_5_percent_increase': win_rate_5_increase,
                'cost_reduction_10_percent': cost_reduction_10
            },
            'assumptions': self._assumptions
        }
