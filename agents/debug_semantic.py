"""Debug semantic matching - Testing new find_category approach"""
from technical_agent.spec_matcher import CONDUCTOR_MATERIAL_MAP
from typing import Optional

def find_category(value: str, mapping: dict) -> Optional[str]:
    """Find the best matching category for a value using priority matching"""
    if not value:
        return None
    
    value = value.lower().strip()
    
    # Priority 1: Exact match with any equivalent
    for category, equivalents in mapping.items():
        if value in equivalents:
            print(f"  -> EXACT match: '{value}' in category '{category}'")
            return category
    
    # Priority 2: Value is contained in an equivalent (longer match preferred)
    best_match = None
    best_match_len = 0
    for category, equivalents in mapping.items():
        for equiv in equivalents:
            if value in equiv and len(equiv) > best_match_len:
                best_match = category
                best_match_len = len(equiv)
    if best_match:
        print(f"  -> CONTAINMENT match: '{value}' in category '{best_match}'")
        return best_match
    
    # Priority 3: An equivalent is contained in value (longer equiv preferred)
    best_match = None
    best_match_len = 0
    for category, equivalents in mapping.items():
        for equiv in equivalents:
            if equiv in value and len(equiv) > best_match_len:
                best_match = category
                best_match_len = len(equiv)
    
    if best_match:
        print(f"  -> REVERSE match: category '{best_match}'")
    return best_match


rfp = 'copper'
oem = 'electrolytic grade copper'

print(f'Testing: "{rfp}" vs "{oem}"')
print()

print("Finding RFP category:")
rfp_category = find_category(rfp, CONDUCTOR_MATERIAL_MAP)
print()

print("Finding OEM category:")
oem_category = find_category(oem, CONDUCTOR_MATERIAL_MAP)
print()

print(f'RFP category: {rfp_category}')
print(f'OEM category: {oem_category}')
print(f'Same category: {rfp_category == oem_category}')
