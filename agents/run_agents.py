"""
Agent System Runner
Main entry point to run the multi-agent RFP response system
"""

import sys
from pathlib import Path
import json
import logging
from datetime import datetime

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent))

from master_agent.orchestrator import MasterAgent
from sales_agent.rfp_scanner import SalesAgent
from technical_agent.spec_matcher import TechnicalAgent
from pricing_agent.price_calculator import PricingAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_rfp_response_workflow(rfp_urls: list = None, output_file: str = None):
    """
    Run complete RFP response workflow
    
    Args:
        rfp_urls: List of URLs to scan for RFPs (optional)
        output_file: Path to save the response JSON (optional)
    
    Returns:
        Consolidated RFP response
    """
    logger.info("=" * 60)
    logger.info("🚀 STARTING MULTI-AGENT RFP RESPONSE SYSTEM")
    logger.info("=" * 60)
    
    # Initialize Master Agent
    master = MasterAgent()
    
    try:
        # Run the full workflow
        response = master.run_full_workflow(rfp_urls)
        
        # Export to JSON
        response_json = master.export_response_to_json(response)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(response_json)
            logger.info(f"📄 Response saved to: {output_file}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 RFP RESPONSE SUMMARY")
        print("=" * 60)
        print(f"RFP ID: {response.rfp_id}")
        print(f"Response ID: {response.response_id}")
        print(f"Products Analyzed: {len(response.products_table)}")
        print(f"Total Material Cost: ₹{response.total_material_cost:,.2f}")
        print(f"Total Services Cost: ₹{response.total_services_cost:,.2f}")
        print(f"Grand Total: ₹{response.grand_total:,.2f}")
        print(f"Status: {response.response_status}")
        print("=" * 60)
        
        # Print product recommendations
        print("\n📦 PRODUCT RECOMMENDATIONS:")
        print("-" * 60)
        for product in response.products_table:
            print(f"  {product['sl_no']}. {product['rfp_product_name']}")
            print(f"     → OEM: {product['oem_product_name']} ({product['recommended_oem_sku']})")
            print(f"     → Spec Match: {product['spec_match_percent']}%")
            print(f"     → Unit Price: ₹{product['unit_price']:,.2f}")
            print(f"     → Total: ₹{product['total_price']:,.2f}")
            print()
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Workflow failed: {e}")
        raise


def run_sales_agent_only():
    """Run only the Sales Agent to scan and identify RFPs"""
    logger.info("Running Sales Agent...")
    
    sales = SalesAgent()
    selected = sales.select_rfp_for_response()
    
    print("\n" + "=" * 60)
    print("📋 SALES AGENT - SELECTED RFP")
    print("=" * 60)
    print(json.dumps(selected, indent=2, default=str))
    
    return selected


def run_technical_agent_only(rfp_products: list):
    """Run only the Technical Agent for product matching"""
    logger.info("Running Technical Agent...")
    
    tech = TechnicalAgent()
    result = tech.process_rfp({
        'rfp_id': 'MANUAL_TEST',
        'products_in_scope': rfp_products
    })
    
    print("\n" + "=" * 60)
    print("🔧 TECHNICAL AGENT - RECOMMENDATIONS")
    print("=" * 60)
    print(json.dumps(result, indent=2, default=str))
    
    return result


def run_pricing_agent_only(tests_required: list, product_recommendations: list):
    """Run only the Pricing Agent for cost calculation"""
    logger.info("Running Pricing Agent...")
    
    pricing = PricingAgent()
    result = pricing.calculate_pricing({
        'rfp_id': 'MANUAL_TEST',
        'tests_required': tests_required,
        'product_recommendations': product_recommendations
    })
    
    print("\n" + "=" * 60)
    print("💰 PRICING AGENT - QUOTATION")
    print("=" * 60)
    print(pricing.generate_quote_summary(result))
    
    return result


def interactive_mode():
    """Run agents in interactive mode"""
    print("\n" + "=" * 60)
    print("🤖 MULTI-AGENT RFP RESPONSE SYSTEM")
    print("=" * 60)
    print("\nAvailable commands:")
    print("  1. full     - Run full RFP response workflow")
    print("  2. sales    - Run Sales Agent only")
    print("  3. tech     - Run Technical Agent only")
    print("  4. pricing  - Run Pricing Agent only")
    print("  5. demo     - Run demo with sample data")
    print("  6. exit     - Exit the system")
    print()
    
    while True:
        try:
            command = input("Enter command: ").strip().lower()
            
            if command == '1' or command == 'full':
                run_rfp_response_workflow(
                    output_file=f"rfp_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
            
            elif command == '2' or command == 'sales':
                run_sales_agent_only()
            
            elif command == '3' or command == 'tech':
                # Sample products for testing
                sample_products = [
                    {
                        'name': 'PVC Wire 1.5 sq mm',
                        'specifications': {
                            'conductor': 'Copper',
                            'cross_section_sqmm': 1.5,
                            'voltage_grade': '1100V',
                            'standard': 'IS 694:2010'
                        },
                        'quantity': 10000,
                        'unit': 'meters'
                    }
                ]
                run_technical_agent_only(sample_products)
            
            elif command == '4' or command == 'pricing':
                sample_tests = [
                    'Conductor Resistance Test',
                    'High Voltage Test',
                    'Flame Retardancy Test'
                ]
                sample_recs = [
                    {
                        'rfp_product': 'PVC Wire 1.5 sq mm',
                        'selected_sku': 'POL-PVC-1.5-R',
                        'quantity': 10000
                    }
                ]
                run_pricing_agent_only(sample_tests, sample_recs)
            
            elif command == '5' or command == 'demo':
                print("\n🎯 Running Demo with Sample Data...\n")
                run_rfp_response_workflow()
            
            elif command == '6' or command == 'exit':
                print("\nGoodbye! 👋")
                break
            
            else:
                print("Unknown command. Please try again.")
        
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'full':
            output = sys.argv[2] if len(sys.argv) > 2 else None
            run_rfp_response_workflow(output_file=output)
        
        elif command == 'demo':
            run_rfp_response_workflow()
        
        elif command == 'interactive':
            interactive_mode()
        
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run_agents.py [full|demo|interactive]")
    else:
        interactive_mode()
