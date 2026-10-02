"""
Test Full Multi-Agent Workflow
Tests the enhanced communication protocol and agent coordination
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

print('='*70)
print('Testing Full Multi-Agent Workflow')
print('='*70)

# Test Master Agent initialization
from master_agent.orchestrator import MasterAgent

print('\n📦 Initializing Master Agent...')
master = MasterAgent()
print(f'✅ Master Agent status: {master.get_conversation_status()}')

# Test workflow with sample RFP data
print('\n🚀 Running full workflow...')
try:
    response = master.run_full_workflow()
    
    print('\n' + '='*70)
    print('WORKFLOW COMPLETED SUCCESSFULLY')
    print('='*70)
    
    # Print scope of supply table
    print(master.print_scope_of_supply_table(response))
    
    # Print test costs
    print('\n' + '-'*70)
    print('TEST COSTS:')
    print('-'*70)
    for test in response.test_costs:
        print(f"  - {test.get('test_name', 'Unknown')}: ₹{test.get('total_cost', 0):,.2f}")
    
    print(f'\n✅ Response ID: {response.response_id}')
    print(f'✅ Overall Spec Match: {response.overall_spec_match}%')
    print(f'✅ Recommendation: {response.recommendation}')
    
    # Export to JSON
    print('\n' + '-'*70)
    print('Exporting response to JSON...')
    json_output = master.export_response_to_json(response)
    print(f'✅ JSON export length: {len(json_output)} characters')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
