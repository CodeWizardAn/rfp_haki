"""
PDF Extraction - Vendor Management Bridge
Integrates vendor lookup and information into PDF extraction workflow
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

# Import vendor management modules
try:
    from vendor_management.vendor_database import get_vendor_database
    from vendor_management.vendor_rating import get_rating_engine
    HAS_VENDOR_MGT = True
except ImportError:
    HAS_VENDOR_MGT = False

logger = logging.getLogger('pdf_vendor_bridge')


class PDFVendorBridge:
    """Bridge PDF extraction with vendor management"""

    def __init__(self):
        """Initialize PDF vendor bridge"""
        if HAS_VENDOR_MGT:
            self.vendor_db = get_vendor_database()
            self.rating_engine = get_rating_engine()
        else:
            self.vendor_db = None
            self.rating_engine = None
            logger.warning("Vendor management modules not available")

    def enrich_extracted_text_with_vendor_info(self, extracted_text: str,
                                             vendor_name: str = None) -> Dict:
        """Enrich extracted text with vendor information"""
        if not self.vendor_db:
            return {
                'extracted_text': extracted_text,
                'vendor_info': None,
                'message': 'Vendor management not available'
            }

        try:
            vendor_info = None
            
            if vendor_name:
                # Try to find vendor by name
                vendor_info = self.vendor_db.get_vendor_by_name(vendor_name)
            
            return {
                'extracted_text': extracted_text,
                'vendor_info': vendor_info,
                'vendor_found': vendor_info is not None
            }
        except Exception as e:
            logger.error(f"Error enriching text with vendor info: {e}")
            return {
                'extracted_text': extracted_text,
                'error': str(e)
            }

    def get_vendor_performance_for_specs(self, vendor_id: str) -> Optional[Dict]:
        """Get vendor performance for specification comparison"""
        if not self.vendor_db or not self.rating_engine:
            return None

        try:
            vendor = self.vendor_db.get_vendor(vendor_id)
            if not vendor:
                return None

            rating = self.rating_engine.get_vendor_rating(vendor_id)
            
            return {
                'vendor_id': vendor_id,
                'vendor_name': vendor.get('name'),
                'email': vendor.get('email'),
                'phone': vendor.get('phone'),
                'rating': rating.get('overall_rating') if rating else None,
                'status': vendor.get('status'),
                'badges': self.rating_engine.get_vendor_badges(vendor_id)
            }
        except Exception as e:
            logger.error(f"Error getting vendor performance: {e}")
            return None

    def extract_vendor_info_from_pdf_content(self, pdf_content: str) -> List[Dict]:
        """Extract potential vendor information from PDF content"""
        try:
            potential_vendors = []
            
            # Search for common vendor name patterns
            lines = pdf_content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Look for "From:" or "Vendor:" patterns
                if line.lower().startswith(('from:', 'vendor:', 'supplier:', 'company:')):
                    potential_name = line.split(':', 1)[1].strip()
                    
                    if potential_name:
                        # Try to find in database
                        vendor = self.vendor_db.search_vendors(potential_name)
                        
                        if vendor:
                            potential_vendors.append({
                                'found_text': line,
                                'vendor_info': vendor[0]
                            })
                        else:
                            potential_vendors.append({
                                'found_text': line,
                                'potential_name': potential_name,
                                'vendor_info': None
                            })
            
            return potential_vendors
        except Exception as e:
            logger.error(f"Error extracting vendor info: {e}")
            return []

    def generate_vendor_comparison_from_specs(self, spec1_vendor_id: str,
                                            spec2_vendor_id: str) -> Dict:
        """Generate vendor comparison from specifications"""
        if not self.vendor_db:
            return {'error': 'Vendor management not available'}

        try:
            vendor1 = self.vendor_db.get_vendor(spec1_vendor_id)
            vendor2 = self.vendor_db.get_vendor(spec2_vendor_id)

            if not vendor1 or not vendor2:
                return {'error': 'One or both vendors not found'}

            rating1 = self.rating_engine.get_vendor_rating(spec1_vendor_id) if self.rating_engine else None
            rating2 = self.rating_engine.get_vendor_rating(spec2_vendor_id) if self.rating_engine else None

            comparison = {
                'vendor1': {
                    'id': spec1_vendor_id,
                    'name': vendor1.get('name'),
                    'email': vendor1.get('email'),
                    'phone': vendor1.get('phone'),
                    'rating': rating1.get('overall_rating') if rating1 else None,
                    'status': vendor1.get('status')
                },
                'vendor2': {
                    'id': spec2_vendor_id,
                    'name': vendor2.get('name'),
                    'email': vendor2.get('email'),
                    'phone': vendor2.get('phone'),
                    'rating': rating2.get('overall_rating') if rating2 else None,
                    'status': vendor2.get('status')
                },
                'better_vendor': None
            }

            # Determine better vendor
            rating1_val = rating1.get('overall_rating', 0) if rating1 else 0
            rating2_val = rating2.get('overall_rating', 0) if rating2 else 0

            if rating1_val > rating2_val:
                comparison['better_vendor'] = spec1_vendor_id
            elif rating2_val > rating1_val:
                comparison['better_vendor'] = spec2_vendor_id

            return comparison
        except Exception as e:
            logger.error(f"Error generating vendor comparison: {e}")
            return {'error': str(e)}

    def add_vendor_to_extracted_specs(self, extracted_specs: Dict, vendor_id: str) -> Dict:
        """Add vendor information to extracted specifications"""
        if not self.vendor_db:
            return extracted_specs

        try:
            vendor = self.vendor_db.get_vendor(vendor_id)
            
            if vendor:
                extracted_specs['vendor'] = {
                    'vendor_id': vendor_id,
                    'vendor_name': vendor.get('name'),
                    'contact_email': vendor.get('email'),
                    'contact_phone': vendor.get('phone')
                }
            
            return extracted_specs
        except Exception as e:
            logger.error(f"Error adding vendor to specs: {e}")
            return extracted_specs


# Module-level bridge instance
_pdf_vendor_bridge = None


def get_pdf_vendor_bridge() -> PDFVendorBridge:
    """Get or create PDF vendor bridge"""
    global _pdf_vendor_bridge
    if _pdf_vendor_bridge is None:
        _pdf_vendor_bridge = PDFVendorBridge()
    return _pdf_vendor_bridge


if __name__ == '__main__':
    bridge = get_pdf_vendor_bridge()
    
    # Example: Get vendor performance
    performance = bridge.get_vendor_performance_for_specs('V001')
    if performance:
        print(f"✅ Vendor performance: {performance['vendor_name']} - {performance['rating']}")
    else:
        print("⚠️ Vendor not found or service unavailable")
