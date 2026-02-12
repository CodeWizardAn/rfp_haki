"""
Multi-Agent RFP Response System
Orchestrates Sales, Technical, and Pricing agents for automated RFP responses
"""

from .master_agent.orchestrator import MasterAgent
from .sales_agent.rfp_scanner import SalesAgent
from .technical_agent.spec_matcher import TechnicalAgent
from .pricing_agent.price_calculator import PricingAgent

__all__ = ['MasterAgent', 'SalesAgent', 'TechnicalAgent', 'PricingAgent']
__version__ = '1.0.0'
