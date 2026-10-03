"""
Master Agent - Main Orchestrator
Coordinates all worker agents for RFP response generation

Per Specification:
- Tier 1 Agent: Central coordinator
- Prepares contextual summaries for Technical and Pricing agents
- Receives responses from worker agents
- Consolidates overall RFP response with:
  * OEM product SKUs suggested
  * Product prices
  * Costs for tests required in the RFP
"""

import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import json
import logging
import uuid

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import enhanced communication protocol
try:
    from shared.communication_protocol import (
        AgentMessage, AgentType, MessageType, MessagePriority, MessageContext,
        get_message_broker, create_rfp_technical_summary, create_rfp_pricing_summary,
        create_consolidated_response
    )
    COMM_PROTOCOL_AVAILABLE = True
except ImportError:
    COMM_PROTOCOL_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """States of the RFP response conversation"""
    IDLE = "idle"
    SCANNING_RFPS = "scanning_rfps"
    RFP_SELECTED = "rfp_selected"
    PREPARING_SUMMARIES = "preparing_summaries"
    TECHNICAL_ANALYSIS = "technical_analysis"
    PRICING_ANALYSIS = "pricing_analysis"
    CONSOLIDATING = "consolidating"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class RFPSummary:
    """Summary of an RFP for agent communication"""
    rfp_id: str
    rfp_title: str
    due_date: datetime
    issuing_authority: str
    estimated_value: float
    products_in_scope: List[Dict[str, Any]]
    technical_requirements: List[str]
    tests_required: List[str]
    acceptance_criteria: List[str]
    submission_requirements: Dict[str, Any]
    source_document: str


@dataclass
class ConsolidatedResponse:
    """
    Final consolidated RFP response
    
    Contains:
    - Scope of supply with OEM SKUs, spec match %, and prices
    - Test requirements with costs
    - Consolidated totals
    """
    rfp_id: str
    response_id: str
    generated_date: datetime
    # Scope of supply table (per specification)
    scope_of_supply: List[Dict[str, Any]]  # {sl_no, rfp_product, oem_sku, spec_match%, unit_price, quantity, total}
    # Legacy fields for compatibility
    products_table: List[Dict[str, Any]]
    oem_recommendations: List[Dict[str, Any]]
    # Test costs
    test_costs: List[Dict[str, Any]]
    # Pricing summary
    pricing_summary: Dict[str, Any]
    total_material_cost: float
    total_services_cost: float
    taxes: float
    grand_total: float
    # Compliance
    overall_spec_match: float
    compliance_checklist: List[Dict[str, bool]]
    recommendation: str
    response_status: str


class MasterAgent:
    """
    Master Agent - Main Orchestrator (Tier 1)
    
    Responsibilities (per specification):
    1. Prepares contextual summaries for Technical and Pricing agents
       - Technical: Products, specifications, standards
       - Pricing: Tests, acceptance criteria, expected outputs
    2. Receives responses from worker agents
    3. Consolidates overall RFP response with:
       - OEM product SKUs suggested
       - Product prices
       - Costs for tests required in the RFP
    4. Starts and ends conversations
    """
    
    def __init__(self):
        self.agent_id = AgentType.MASTER if COMM_PROTOCOL_AVAILABLE else "MASTER_ORCHESTRATOR"
        self.conversation_state = ConversationState.IDLE
        self.current_rfp: Optional[RFPSummary] = None
        self.current_conversation_id: str = ""
        self.message_queue: List[Any] = []  # AgentMessage or dict
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Message broker for inter-agent communication
        self.broker = get_message_broker() if COMM_PROTOCOL_AVAILABLE else None
        
        # Responses from worker agents
        self.technical_response: Optional[Dict[str, Any]] = None
        self.pricing_response: Optional[Dict[str, Any]] = None
        
        # Agent references (lazy loaded)
        self._sales_agent = None
        self._technical_agent = None
        self._pricing_agent = None
        
        logger.info(f"✅ Master Agent (Orchestrator) initialized")
    
    @property
    def sales_agent(self):
        if self._sales_agent is None:
            from sales_agent.rfp_scanner import SalesAgent
            self._sales_agent = SalesAgent()
        return self._sales_agent
    
    @property
    def technical_agent(self):
        if self._technical_agent is None:
            from technical_agent.spec_matcher import TechnicalAgent
            self._technical_agent = TechnicalAgent()
        return self._technical_agent
    
    @property
    def pricing_agent(self):
        if self._pricing_agent is None:
            from pricing_agent.price_calculator import PricingAgent
            self._pricing_agent = PricingAgent()
        return self._pricing_agent
    
    def start_conversation(self, context: Dict[str, Any] = None) -> str:
        """Start a new RFP response conversation"""
        self.conversation_state = ConversationState.SCANNING_RFPS
        self.current_conversation_id = f"CONV_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6].upper()}"
        
        # Reset responses
        self.technical_response = None
        self.pricing_response = None
        self.message_queue = []
        
        self.conversation_history.append({
            'conversation_id': self.current_conversation_id,
            'started_at': datetime.now().isoformat(),
            'context': context or {},
            'events': []
        })
        
        logger.info(f"🚀 Conversation started: {self.current_conversation_id}")
        return self.current_conversation_id
    
    def end_conversation(self, conversation_id: str, status: str = "completed") -> Dict[str, Any]:
        """End the current conversation"""
        self.conversation_state = ConversationState.COMPLETED if status == "completed" else ConversationState.ERROR
        
        summary = {
            'conversation_id': conversation_id,
            'ended_at': datetime.now().isoformat(),
            'status': status,
            'rfp_processed': self.current_rfp.rfp_id if self.current_rfp else None,
            'messages_exchanged': len(self.message_queue)
        }
        
        logger.info(f"🏁 Conversation ended: {conversation_id} - Status: {status}")
        return summary
    
    def prepare_technical_summary(self, rfp: RFPSummary) -> Union[AgentMessage, Dict[str, Any]]:
        """
        Prepare RFP summary CONTEXTUAL to Technical Agent's role
        
        Per specification:
        - Focus on products, specifications, technical requirements
        - Include expected outputs (top 3 OEM products, spec match %, comparison table)
        - Include spec match formula reference
        """
        self.conversation_state = ConversationState.PREPARING_SUMMARIES
        
        technical_context = {
            'rfp_id': rfp.rfp_id,
            'rfp_title': rfp.rfp_title,
            'products_in_scope': rfp.products_in_scope,
            'technical_requirements': rfp.technical_requirements,
            'acceptance_criteria': rfp.acceptance_criteria,
            'focus_areas': [
                'Product specifications matching',
                'OEM product recommendations (top 3 per item)',
                'Spec match percentage calculation (equal weightage)',
                'Comparison table preparation (RFP spec vs OEM 1, 2, 3)'
            ],
            'spec_match_formula': {
                'description': 'MatchScore = Σ(ParameterMatch_i × Weight_i) / Σ(Weight_i) × 100',
                'parameter_match': '1 if full match, 0 if no match, or partial score (0-1)',
                'weight': 'Equal weightage for all specifications'
            },
            'expected_output': {
                'product_recommendations': 'Top 3 OEM products per scope item',
                'spec_match_metrics': 'Percentage match for each recommendation',
                'comparison_table': 'RFP specs vs OEM specs (columns: Spec, RFP Requirement, OEM1, OEM2, OEM3)',
                'selected_products': 'Best matching OEM product per item with SKU'
            }
        }
        
        if COMM_PROTOCOL_AVAILABLE:
            message = create_rfp_technical_summary(
                conversation_id=self.current_conversation_id,
                rfp_id=rfp.rfp_id,
                products_in_scope=rfp.products_in_scope,
                technical_requirements=rfp.technical_requirements,
                acceptance_criteria=rfp.acceptance_criteria,
                source_document=rfp.source_document
            )
            self.message_queue.append(message)
            if self.broker:
                self.broker.send_message(message)
            logger.info(f"📤 Technical summary prepared for RFP: {rfp.rfp_id}")
            return message
        else:
            logger.info(f"📤 Technical summary prepared for RFP: {rfp.rfp_id}")
            return technical_context
    
    def prepare_pricing_summary(self, rfp: RFPSummary) -> Union[AgentMessage, Dict[str, Any]]:
        """
        Prepare RFP summary CONTEXTUAL to Pricing Agent's role
        
        Per specification:
        - Focus on tests required, acceptance tests, pricing requirements
        - Include expected outputs (unit prices, test costs, totals)
        - Will receive product recommendations from Technical Agent
        """
        pricing_context = {
            'rfp_id': rfp.rfp_id,
            'rfp_title': rfp.rfp_title,
            'tests_required': rfp.tests_required,
            'acceptance_criteria': rfp.acceptance_criteria,
            'estimated_value': rfp.estimated_value,
            'focus_areas': [
                'Unit pricing assignment from pricing table',
                'Test cost calculation from services price table',
                'Material cost consolidation (Σ unit_price × quantity)',
                'Services cost consolidation (Σ test costs)',
                'Tax calculation and grand total'
            ],
            'expected_output': {
                'unit_prices': 'Price per product SKU from pricing table',
                'test_costs': 'Cost per required test from services table',
                'material_total': 'Total material cost',
                'services_total': 'Total services cost',
                'grand_total': 'Material + Services + Taxes'
            },
            'note': 'Will receive product recommendations (SKUs) from Technical Agent'
        }
        
        if COMM_PROTOCOL_AVAILABLE:
            message = create_rfp_pricing_summary(
                conversation_id=self.current_conversation_id,
                rfp_id=rfp.rfp_id,
                tests_required=rfp.tests_required,
                acceptance_criteria=rfp.acceptance_criteria,
                estimated_value=rfp.estimated_value,
                source_document=rfp.source_document
            )
            self.message_queue.append(message)
            if self.broker:
                self.broker.send_message(message)
            logger.info(f"📤 Pricing summary prepared for RFP: {rfp.rfp_id}")
            return message
        else:
            logger.info(f"📤 Pricing summary prepared for RFP: {rfp.rfp_id}")
            return pricing_context
    
    def receive_sales_response(self, selected_rfp: Dict[str, Any]) -> RFPSummary:
        """Receive selected RFP from Sales Agent"""
        self.conversation_state = ConversationState.RFP_SELECTED
        
        # Create RFP summary from sales agent response
        self.current_rfp = RFPSummary(
            rfp_id=selected_rfp.get('rfp_id'),
            rfp_title=selected_rfp.get('title'),
            due_date=datetime.fromisoformat(selected_rfp.get('due_date')) if selected_rfp.get('due_date') else datetime.now(),
            issuing_authority=selected_rfp.get('issuing_authority'),
            estimated_value=selected_rfp.get('estimated_value', 0),
            products_in_scope=selected_rfp.get('products', []),
            technical_requirements=selected_rfp.get('technical_requirements', []),
            tests_required=selected_rfp.get('tests_required', []),
            acceptance_criteria=selected_rfp.get('acceptance_criteria', []),
            submission_requirements=selected_rfp.get('submission_requirements', {}),
            source_document=selected_rfp.get('source_document', '')
        )
        
        logger.info(f"📥 Received RFP from Sales Agent: {self.current_rfp.rfp_id}")
        return self.current_rfp
    
    def receive_technical_response(self, technical_response: Dict[str, Any]) -> None:
        """
        Receive product recommendations from Technical Agent
        
        Expected content:
        - recommendations: List with selected SKUs, spec match %
        - comparison_table: RFP specs vs OEM specs
        - compliance_summary: Overall compliance metrics
        """
        self.conversation_state = ConversationState.PRICING_ANALYSIS
        self.technical_response = technical_response
        
        logger.info(f"📥 Received technical response with {len(technical_response.get('recommendations', []))} recommendations")
        logger.info(f"   Average spec match: {technical_response.get('compliance_summary', {}).get('average_spec_match', 0)}%")
    
    def receive_pricing_response(self, pricing_response: Dict[str, Any]) -> None:
        """
        Receive pricing from Pricing Agent
        
        Expected content:
        - product_prices: List with SKUs and prices
        - test_costs: List with test costs
        - total_material_cost, total_services_cost, grand_total
        """
        self.conversation_state = ConversationState.CONSOLIDATING
        self.pricing_response = pricing_response
        
        logger.info(f"📥 Received pricing response - Grand Total: ₹{pricing_response.get('grand_total', 0):,.2f}")
    
    def consolidate_response(self) -> ConsolidatedResponse:
        """
        Consolidate responses from all agents into final RFP response
        
        Per specification, the overall response contains:
        - OEM product SKUs suggested
        - Product prices
        - Costs for tests required in the RFP
        
        Output format: Scope of Supply table with:
        - Sl No, RFP Product, Recommended OEM SKU, Spec Match %, Unit Price, Quantity, Total
        """
        if not self.current_rfp:
            raise ValueError("No RFP loaded for consolidation")
        
        technical_data = self.technical_response or {}
        pricing_data = self.pricing_response or {}
        
        # Build Scope of Supply table (per specification)
        scope_of_supply = []
        products_table = []
        
        recommendations = technical_data.get('recommendations', [])
        product_prices = pricing_data.get('product_prices', [])
        
        for idx, product in enumerate(self.current_rfp.products_in_scope):
            # Get recommendation from technical response
            rec = recommendations[idx] if idx < len(recommendations) else {}
            
            # Get pricing from pricing response
            price_data = product_prices[idx] if idx < len(product_prices) else {}
            
            # Build scope of supply row
            scope_row = {
                'sl_no': idx + 1,
                'rfp_product_name': product.get('name', rec.get('rfp_product', '')),
                'rfp_specifications': product.get('specifications', {}),
                'quantity': rec.get('quantity', product.get('quantity', 1)),
                'unit': rec.get('unit', product.get('unit', 'Nos')),
                'recommended_oem_sku': rec.get('selected_sku', ''),
                'oem_product_name': rec.get('product_name', ''),
                'manufacturer': rec.get('manufacturer', ''),
                'spec_match_percent': rec.get('spec_match_percent', 0),
                'hard_constraint_passed': rec.get('hard_constraint_passed', True),
                'disqualification_risk': rec.get('disqualification_risk', 'LOW'),
                'hard_constraint_violations': rec.get('hard_constraint_violations', []),
                'citations': rec.get('citations', []),
                'unit_price': price_data.get('discounted_unit_price', price_data.get('unit_price', 0)),
                'discount_percent': price_data.get('discount_percent', 0),
                'total_price': price_data.get('total_price', 0),
                'top_3_options': rec.get('top_3_options', [])
            }
            scope_of_supply.append(scope_row)
            
            # Legacy products table format
            products_table.append({
                'sl_no': idx + 1,
                'rfp_product_name': scope_row['rfp_product_name'],
                'quantity': scope_row['quantity'],
                'unit': scope_row['unit'],
                'recommended_oem_sku': scope_row['recommended_oem_sku'],
                'oem_product_name': scope_row['oem_product_name'],
                'spec_match_percent': scope_row['spec_match_percent'],
                'hard_constraint_passed': scope_row['hard_constraint_passed'],
                'disqualification_risk': scope_row['disqualification_risk'],
                'unit_price': scope_row['unit_price'],
                'total_price': scope_row['total_price']
            })
        
        # Get test costs
        test_costs = pricing_data.get('test_costs', [])
        
        # Calculate overall spec match
        if scope_of_supply:
            overall_spec_match = sum(s['spec_match_percent'] for s in scope_of_supply) / len(scope_of_supply)
        else:
            overall_spec_match = 0
        
        # Check hard constraint violations across all line items
        has_hard_violations = any(not s.get('hard_constraint_passed', True) for s in scope_of_supply)
        total_violations = sum(len(s.get('hard_constraint_violations', [])) for s in scope_of_supply)
        
        # Generate recommendation
        if has_hard_violations:
            recommendation = f"CRITICAL REJECTION RISK - {total_violations} mandatory tender hard constraint(s) failed. Requires formal Schedule of Deviations."
        elif overall_spec_match >= 90:
            recommendation = "HIGHLY RECOMMENDED - 100% hard constraints satisfied, verified audit citations"
        elif overall_spec_match >= 75:
            recommendation = "RECOMMENDED - Hard constraints met with minor commercial deviations"
        elif overall_spec_match >= 60:
            recommendation = "CONDITIONALLY RECOMMENDED - Technical review required for marginal items"
        else:
            recommendation = "REVIEW REQUIRED - Significant spec deviations detected"
        
        # Build taxes
        taxes = pricing_data.get('taxes', {})
        total_tax = taxes.get('total_tax', 0) if isinstance(taxes, dict) else 0
        
        # Create consolidated response
        response = ConsolidatedResponse(
            rfp_id=self.current_rfp.rfp_id,
            response_id=f"RESP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_date=datetime.now(),
            scope_of_supply=scope_of_supply,
            products_table=products_table,
            oem_recommendations=technical_data.get('comparison_table', []),
            test_costs=test_costs,
            pricing_summary={
                'scope_of_supply': scope_of_supply,
                'tests': test_costs,
                'material_cost': pricing_data.get('total_material_cost', 0),
                'services_cost': pricing_data.get('total_services_cost', 0),
                'taxes': taxes
            },
            total_material_cost=pricing_data.get('total_material_cost', 0),
            total_services_cost=pricing_data.get('total_services_cost', 0),
            taxes=total_tax,
            grand_total=pricing_data.get('grand_total', 0),
            overall_spec_match=round(overall_spec_match, 2),
            compliance_checklist=self._build_compliance_checklist(),
            recommendation=recommendation,
            response_status="READY_FOR_REVIEW"
        )
        
        self.conversation_state = ConversationState.COMPLETED
        logger.info(f"✅ Response consolidated: {response.response_id}")
        logger.info(f"   Overall Spec Match: {overall_spec_match:.1f}%")
        logger.info(f"   Grand Total: ₹{response.grand_total:,.2f}")
        
        return response
    
    def _build_compliance_checklist(self) -> List[Dict[str, bool]]:
        """Build compliance checklist based on RFP requirements"""
        if not self.current_rfp:
            return []
        
        has_technical = self.technical_response is not None
        has_pricing = self.pricing_response is not None
        
        checklist = [
            {'item': 'All products in scope addressed', 'compliant': has_technical},
            {'item': 'OEM recommendations provided', 'compliant': has_technical and len(self.technical_response.get('recommendations', [])) > 0},
            {'item': 'Spec match metrics calculated', 'compliant': has_technical},
            {'item': 'Comparison tables generated', 'compliant': has_technical and len(self.technical_response.get('comparison_table', [])) > 0},
            {'item': 'Unit prices assigned', 'compliant': has_pricing},
            {'item': 'Test costs included', 'compliant': has_pricing and len(self.pricing_response.get('test_costs', [])) > 0},
            {'item': 'Total pricing calculated', 'compliant': has_pricing and self.pricing_response.get('grand_total', 0) > 0}
        ]
        
        return checklist
    
    def run_full_workflow(self, rfp_urls: List[str] = None) -> ConsolidatedResponse:
        """
        Run the complete RFP response workflow
        
        Communication Flow (per specification):
        1. Sales Agent scans and selects RFP
        2. Master prepares contextual summaries (Technical & Pricing)
        3. Technical Agent analyzes and recommends (sends to Master AND Pricing)
        4. Pricing Agent calculates costs (receives products from Technical)
        5. Master consolidates final response
        """
        conversation_id = self.start_conversation({'rfp_urls': rfp_urls})
        
        try:
            # ================================================================
            # FLOW 1: RFP Identification to Analysis
            # Sales Agent -> Master Agent
            # ================================================================
            logger.info("📋 Step 1: Sales Agent scanning RFPs...")
            self.conversation_state = ConversationState.SCANNING_RFPS
            selected_rfp = self.sales_agent.select_rfp_for_response(rfp_urls)
            rfp_summary = self.receive_sales_response(selected_rfp)
            
            # ================================================================
            # FLOW 2 & 3: Prepare Contextual Summaries
            # Master -> Technical Agent (products, specs)
            # Master -> Pricing Agent (tests, acceptance criteria)
            # ================================================================
            logger.info("📝 Step 2: Preparing agent-specific contextual summaries...")
            self.conversation_state = ConversationState.PREPARING_SUMMARIES
            
            # Technical summary focuses on products and specifications
            tech_summary = self.prepare_technical_summary(rfp_summary)
            
            # Pricing summary focuses on tests and acceptance criteria
            pricing_summary = self.prepare_pricing_summary(rfp_summary)
            
            # ================================================================
            # FLOW 2: Technical Analysis
            # Technical Agent -> Master Agent & Pricing Agent
            # ================================================================
            logger.info("🔧 Step 3: Technical Agent analyzing products...")
            self.conversation_state = ConversationState.TECHNICAL_ANALYSIS
            
            # Get technical context (either from message or dict)
            tech_context = tech_summary.payload if COMM_PROTOCOL_AVAILABLE and hasattr(tech_summary, 'payload') else tech_summary
            
            # Technical agent processes and returns recommendations
            tech_response = self.technical_agent.process_rfp(tech_context)
            self.receive_technical_response(tech_response)
            
            # ================================================================
            # FLOW 3: Pricing Estimation
            # Pricing Agent receives:
            # - Test summary from Master
            # - Product recommendations from Technical Agent
            # ================================================================
            logger.info("💰 Step 4: Pricing Agent calculating costs...")
            self.conversation_state = ConversationState.PRICING_ANALYSIS
            
            # Get pricing context
            pricing_context = pricing_summary.payload if COMM_PROTOCOL_AVAILABLE and hasattr(pricing_summary, 'payload') else pricing_summary
            
            # Merge product recommendations from Technical Agent
            pricing_input = {
                **pricing_context,
                'product_recommendations': tech_response.get('recommendations', [])
            }
            
            # Pricing agent calculates costs
            pricing_response = self.pricing_agent.calculate_pricing(pricing_input)
            self.receive_pricing_response(pricing_response)
            
            # ================================================================
            # FLOW 4: Final Consolidation
            # Master Agent consolidates all responses
            # ================================================================
            logger.info("📊 Step 5: Consolidating final response...")
            self.conversation_state = ConversationState.CONSOLIDATING
            final_response = self.consolidate_response()
            
            self.end_conversation(conversation_id, "completed")
            return final_response
            
        except Exception as e:
            logger.error(f"❌ Workflow error: {e}")
            import traceback
            traceback.print_exc()
            self.end_conversation(conversation_id, "error")
            raise
    
    def get_conversation_status(self) -> Dict[str, Any]:
        """Get current conversation status"""
        return {
            'conversation_id': self.current_conversation_id,
            'state': self.conversation_state.value,
            'current_rfp': self.current_rfp.rfp_id if self.current_rfp else None,
            'has_technical_response': self.technical_response is not None,
            'has_pricing_response': self.pricing_response is not None,
            'messages_in_queue': len(self.message_queue),
            'history_count': len(self.conversation_history)
        }
    
    def export_response_to_json(self, response: ConsolidatedResponse) -> str:
        """Export consolidated response to JSON"""
        return json.dumps({
            'rfp_id': response.rfp_id,
            'response_id': response.response_id,
            'generated_date': response.generated_date.isoformat(),
            'scope_of_supply': response.scope_of_supply,
            'test_costs': response.test_costs,
            'pricing_summary': {
                'total_material_cost': response.total_material_cost,
                'total_services_cost': response.total_services_cost,
                'taxes': response.taxes,
                'grand_total': response.grand_total
            },
            'overall_spec_match': response.overall_spec_match,
            'recommendation': response.recommendation,
            'compliance_checklist': response.compliance_checklist,
            'response_status': response.response_status
        }, indent=2)
    
    def print_scope_of_supply_table(self, response: ConsolidatedResponse) -> str:
        """Print formatted scope of supply table with compliance risk and citations"""
        lines = []
        lines.append("\n" + "="*135)
        lines.append("ENTERPRISE SCOPE OF SUPPLY & COMPLIANCE MATRIX")
        lines.append("="*135)
        lines.append(f"{'Sl':<4} {'RFP Product':<28} {'OEM SKU':<18} {'Spec%':<7} {'Risk Status':<18} {'Qty':<8} {'Unit Price':<12} {'Total':<15}")
        lines.append("-"*135)
        
        for item in response.scope_of_supply:
            risk = item.get('disqualification_risk', 'LOW')
            if risk == 'CRITICAL_DISQUALIFIED':
                risk_badge = "❌ CRITICAL RISK"
            elif risk == 'HIGH':
                risk_badge = "⚠️ HIGH RISK"
            elif risk == 'MEDIUM':
                risk_badge = "⚡ MEDIUM RISK"
            else:
                risk_badge = "✅ COMPLIANT"
            
            lines.append(
                f"{item['sl_no']:<4} "
                f"{item['rfp_product_name'][:26]:<28} "
                f"{item['recommended_oem_sku'][:16]:<18} "
                f"{item['spec_match_percent']:<7.1f} "
                f"{risk_badge:<18} "
                f"{item['quantity']:<8} "
                f"₹{item['unit_price']:<11,.2f} "
                f"₹{item['total_price']:<14,.2f}"
            )
        
        lines.append("-"*135)
        lines.append(f"{'TOTAL MATERIAL COST':<85} ₹{response.total_material_cost:>15,.2f}")
        lines.append(f"{'TOTAL SERVICES COST':<85} ₹{response.total_services_cost:>15,.2f}")
        lines.append(f"{'TAXES':<85} ₹{response.taxes:>15,.2f}")
        lines.append("="*135)
        lines.append(f"{'GRAND TOTAL':<85} ₹{response.grand_total:>15,.2f}")
        lines.append("="*135)
        lines.append(f"\nOverall Spec Match: {response.overall_spec_match}%")
        lines.append(f"Recommendation: {response.recommendation}")
        
        # Add Verifiable Audit Citations
        lines.append("\n" + "-"*135)
        lines.append("VERIFIABLE SOURCE CITATIONS (AUDIT TRAIL FOR BID DEFENSE):")
        lines.append("-"*135)
        citation_count = 0
        for item in response.scope_of_supply:
            citations = item.get('citations', [])
            if citations:
                lines.append(f"\n  📌 Item #{item['sl_no']} [{item['recommended_oem_sku']}]:")
                for c in citations[:3]:  # Show top 3 citations per product for display
                    citation_count += 1
                    status_icon = "✓" if c.get('passed_constraint', True) else "✗"
                    lines.append(
                        f"     [{status_icon}] Page {c.get('page_number', 1)} | {c.get('clause_ref', 'N/A')}: "
                        f"'{c.get('source_snippet', '')}'"
                    )
        lines.append(f"\n  Total Verified Audit Citations Linked: {citation_count}")
        lines.append("-"*135)
        
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    master = MasterAgent()
    print(f"Master Agent Status: {master.get_conversation_status()}")
