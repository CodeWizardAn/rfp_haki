"""
OEM Vendor Optimization Configuration
Best practices, templates, and guidelines for OEM vendor management
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta


class OEMOptimizationCategory(Enum):
    """Categories of OEM optimization"""
    VENDOR_SELECTION = "vendor_selection"
    CAPACITY_PLANNING = "capacity_planning"
    QUALITY_ASSURANCE = "quality_assurance"
    COST_MANAGEMENT = "cost_management"
    DELIVERY_EXCELLENCE = "delivery_excellence"
    TECHNICAL_CAPABILITY = "technical_capability"
    RELATIONSHIP_MANAGEMENT = "relationship_management"
    COMPLIANCE_MONITORING = "compliance_monitoring"


@dataclass
class OEMQualificationCriteria:
    """Criteria for OEM vendor qualification"""
    min_years_in_business: int = 5
    min_capacity_monthly_units: int = 100000
    required_certifications: list = None
    min_quality_score: float = 75.0
    min_on_time_delivery_percent: float = 90.0
    min_capability_score: float = 70.0
    max_defect_rate_ppm: int = 100
    required_nre_capabilities: bool = True
    
    def __post_init__(self):
        if self.required_certifications is None:
            self.required_certifications = ['ISO_9001', 'ISO_14001']


@dataclass
class OEMPricingGuidelines:
    """Guidelines for OEM pricing strategies"""
    nre_cost_recovery_period_months: int = 12
    volume_discount_tiers: dict = None
    min_moq_multiplier: float = 1.0
    max_lead_time_days: int = 90
    expedited_premium_percent: float = 15.0
    express_premium_percent: float = 25.0
    default_tax_percent: float = 18.0
    default_shipping_percent: float = 2.0
    default_insurance_percent: float = 2.0
    
    def __post_init__(self):
        if self.volume_discount_tiers is None:
            self.volume_discount_tiers = {
                '100-499': 2.0,
                '500-999': 5.0,
                '1000-4999': 8.0,
                '5000+': 12.0
            }


@dataclass
class OEMPerformanceKPIs:
    """Key Performance Indicators for OEM vendors"""
    # Quality KPIs
    target_defect_rate_ppm: int = 50
    target_first_pass_yield_percent: float = 98.5
    target_rework_rate_percent: float = 1.0
    target_audit_score: float = 95.0
    
    # Delivery KPIs
    target_on_time_delivery_percent: float = 98.0
    target_lead_time_variance_days: int = 2
    target_shipment_quality_percent: float = 99.5
    
    # Capacity KPIs
    target_utilization_percent: float = 75.0
    target_equipment_uptime_percent: float = 95.0
    target_worker_efficiency_percent: float = 90.0
    
    # Response KPIs
    target_response_time_hours: int = 4
    target_issue_resolution_days: int = 5
    
    # Technical KPIs
    min_design_capability_level: str = 'INTERMEDIATE'
    min_testing_capability_level: str = 'ADVANCED'
    
    # Compliance KPIs
    target_certification_validity_months: int = 36
    max_compliance_violations_per_year: int = 0


class OEMVendorScreeningTemplate:
    """Template for OEM vendor screening workflow"""
    
    screening_stages = [
        {
            'stage_id': 'INITIAL_ASSESSMENT',
            'stage_name': 'Initial Assessment',
            'duration_days': 5,
            'check_items': [
                'Company registration verification',
                'Tax compliance check',
                'Financial stability assessment',
                'Years in business validation'
            ]
        },
        {
            'stage_id': 'CAPACITY_EVALUATION',
            'stage_name': 'Capacity Evaluation',
            'duration_days': 10,
            'check_items': [
                'Manufacturing facility inspection',
                'Equipment capability assessment',
                'Workforce capacity check',
                'MOQ and lead time confirmation',
                'Production volume feasibility'
            ]
        },
        {
            'stage_id': 'QUALITY_ASSESSMENT',
            'stage_name': 'Quality Assessment',
            'duration_days': 15,
            'check_items': [
                'Quality management system audit',
                'Certification validation (ISO 9001, 14001)',
                'Sample quality evaluation',
                'Testing capability assessment',
                'Compliance with standards'
            ]
        },
        {
            'stage_id': 'TECHNICAL_EVALUATION',
            'stage_name': 'Technical Evaluation',
            'duration_days': 10,
            'check_items': [
                'Design capability assessment',
                'Prototyping capability review',
                'NRE experience evaluation',
                'Engineering team assessment',
                'Technical documentation review'
            ]
        },
        {
            'stage_id': 'SITE_VISIT',
            'stage_name': 'Site Visit',
            'duration_days': 3,
            'check_items': [
                'Facility tour and assessment',
                'Key personnel meetings',
                'Process capability verification',
                'Quality system observation',
                'Relationship building'
            ]
        },
        {
            'stage_id': 'FINAL_APPROVAL',
            'stage_name': 'Final Approval',
            'duration_days': 5,
            'check_items': [
                'Scorecard finalization',
                'Risk assessment',
                'Contract negotiation',
                'Performance expectations alignment',
                'GO/NO-GO decision'
            ]
        }
    ]
    
    @staticmethod
    def get_total_screening_duration_days():
        """Get total time for complete OEM screening"""
        return sum(stage['duration_days'] for stage in OEMVendorScreeningTemplate.screening_stages)


class OEMPerformanceReportingTemplate:
    """Template for OEM performance reporting"""
    
    report_sections = {
        'EXECUTIVE_SUMMARY': {
            'title': 'Executive Summary',
            'subsections': [
                'Overall Performance Score',
                'Key Achievements',
                'Areas of Concern',
                'Recommendations'
            ]
        },
        'QUALITY_PERFORMANCE': {
            'title': 'Quality Performance',
            'subsections': [
                'Defect Rates',
                'First Pass Yield',
                'Audit Scores',
                'CAPA Effectiveness',
                'Compliance Issues'
            ]
        },
        'DELIVERY_PERFORMANCE': {
            'title': 'Delivery Performance',
            'subsections': [
                'On-Time Delivery Rate',
                'Lead Time Performance',
                'Shipment Quality',
                'Documentation Accuracy'
            ]
        },
        'CAPACITY_PERFORMANCE': {
            'title': 'Capacity Performance',
            'subsections': [
                'Utilization Rate',
                'Equipment Performance',
                'Workforce Capacity',
                'Scalability Assessment'
            ]
        },
        'TECHNICAL_CAPABILITY': {
            'title': 'Technical Capability',
            'subsections': [
                'Design Capability',
                'Testing Capability',
                'Certifications',
                'Innovation Rating'
            ]
        },
        'FINANCIAL_ANALYSIS': {
            'title': 'Financial Analysis',
            'subsections': [
                'Cost Competitiveness',
                'Price Stability',
                'Payment Terms Compliance',
                'Discount Effectiveness'
            ]
        },
        'RELATIONSHIP_HEALTH': {
            'title': 'Relationship Health',
            'subsections': [
                'Communication Effectiveness',
                'Issue Resolution',
                'Flexibility & Responsiveness',
                'Strategic Alignment'
            ]
        },
        'RISK_ASSESSMENT': {
            'title': 'Risk Assessment',
            'subsections': [
                'Financial Risk',
                'Quality Risk',
                'Supply Risk',
                'Compliance Risk'
            ]
        },
        'RECOMMENDATIONS': {
            'title': 'Recommendations',
            'subsections': [
                'Short-term Actions',
                'Medium-term Development',
                'Long-term Strategic Plans',
                'Continuation Decision'
            ]
        }
    }


class OEMCommunicationTemplate:
    """Templates for OEM vendor communications"""
    
    communication_types = {
        'TECHNICAL_INQUIRY': {
            'template': '''
            Subject: Technical Inquiry - [Project/Product Name]
            
            Dear [Vendor Name],
            
            We have a technical question regarding [topic]:
            
            [Detailed question]
            
            Could you please provide:
            1. [Specific requirement 1]
            2. [Specific requirement 2]
            3. [Specific requirement 3]
            
            Timeline: [Expected response date]
            
            Thank you,
            [Your Name]
            '''
        },
        'CAPACITY_VERIFICATION': {
            'template': '''
            Subject: Capacity Verification Request - [Project Name]
            
            Dear [Vendor Name],
            
            We are planning [project/order] and need to verify your capacity:
            
            Requirement: [Quantity] units
            Timeline: [Delivery date]
            
            Please confirm:
            1. Can you manufacture [quantity] units?
            2. Lead time for [quantity] units?
            3. Any constraints or concerns?
            4. Recommended MOQ?
            
            Please respond by [Date].
            
            Best regards,
            [Your Name]
            '''
        },
        'QUALITY_ISSUE': {
            'template': '''
            Subject: Quality Issue Notification - [Part/Product]
            
            Dear [Vendor Name],
            
            We have identified quality issues with the recent shipment:
            
            Part: [Part number]
            Batch: [Batch number]
            Issue: [Description of issue]
            Defect count: [Number]
            
            Required Actions:
            1. Root cause analysis
            2. Corrective action plan
            3. Preventive measures
            4. Updated sample submission
            
            Timeline: [Expected response date]
            
            We look forward to your swift response.
            
            [Your Name]
            '''
        },
        'NRE_ESTIMATION': {
            'template': '''
            Subject: NRE Cost Estimation Request - [Project]
            
            Dear [Vendor Name],
            
            We are requesting NRE cost estimation for:
            
            Project: [Project name]
            Product: [Product description]
            Scope:
            - Design engineering: [Hours/scope]
            - Tooling: [Description]
            - Setup: [Description]
            - Testing: [Scope]
            - Certification: [Scope if applicable]
            
            Please provide:
            1. Detailed NRE breakdown
            2. Engineering team availability
            3. Timeline for completion
            4. Payment milestone schedule
            5. Warranty/support terms
            
            Target NRE budget: [Budget if applicable]
            
            Please submit your proposal by [Date].
            
            Best regards,
            [Your Name]
            '''
        },
        'CERTIFICATION_REQUIREMENT': {
            'template': '''
            Subject: Certification Requirements - [Project/Product]
            
            Dear [Vendor Name],
            
            For this project, we require the following certifications:
            
            Required Certifications:
            1. [Certification name and details]
            2. [Certification name and details]
            3. [Certification name and details]
            
            Compliance Standards:
            - [Standard 1]
            - [Standard 2]
            
            Please confirm:
            1. Current certification status
            2. Expiry dates
            3. Plans for recertification if needed
            4. Compliance capability for new standards
            
            Please respond by [Date].
            
            Thank you,
            [Your Name]
            '''
        },
        'PERFORMANCE_REVIEW': {
            'template': '''
            Subject: Quarterly Performance Review - [Quarter/Year]
            
            Dear [Vendor Name],
            
            We would like to discuss your performance for Q[Quarter] [Year]:
            
            Performance Highlights:
            - On-time delivery: [%]
            - Quality score: [Score]
            - Capacity utilization: [%]
            - Key achievements: [List]
            
            Areas for Improvement:
            - [Issue 1]: [Details]
            - [Issue 2]: [Details]
            
            Development Opportunities:
            - [Opportunity 1]
            - [Opportunity 2]
            
            Next Steps:
            1. Schedule: [Date/time for meeting]
            2. Agenda items: [List]
            3. Required documents: [List]
            
            Looking forward to a productive discussion.
            
            [Your Name]
            '''
        }
    }


class OEMNREBestPractices:
    """Best practices for OEM NRE (Non-Recurring Engineering) management"""
    
    nre_components = {
        'ENGINEERING': {
            'description': 'Design and engineering services',
            'typical_percent': 20,
            'included_items': ['CAD design', 'Simulation', 'Design review', 'Documentation'],
            'cost_drivers': ['Complexity', 'Design hours', 'Tools used', 'Review cycles']
        },
        'TOOLING': {
            'description': 'Dies, fixtures, molds, and equipment setup',
            'typical_percent': 40,
            'included_items': ['Dies', 'Fixtures', 'Gauges', 'Setup'],
            'cost_drivers': ['Complexity', 'Material', 'Precision', 'Durability']
        },
        'SETUP': {
            'description': 'Process setup and optimization',
            'typical_percent': 15,
            'included_items': ['Machine setup', 'Process optimization', 'Parameter tuning'],
            'cost_drivers': ['Process complexity', 'Setup time', 'Testing iterations']
        },
        'TESTING': {
            'description': 'Prototype and quality testing',
            'typical_percent': 10,
            'included_items': ['Sample production', 'Testing', 'Analysis', 'Refinement'],
            'cost_drivers': ['Test scope', 'Sample quantity', 'Standards', 'Iterations']
        },
        'DOCUMENTATION': {
            'description': 'Technical documentation and manuals',
            'typical_percent': 5,
            'included_items': ['Process docs', 'QA procedures', 'Work instructions'],
            'cost_drivers': ['Detail level', 'Languages', 'Format requirements']
        },
        'CERTIFICATION': {
            'description': 'Compliance and certification activities',
            'typical_percent': 10,
            'included_items': ['Compliance testing', 'Certification', 'Audit support'],
            'cost_drivers': ['Standard complexity', 'Testing labs', 'Audit requirements']
        }
    }
    
    nre_payment_milestones = [
        {
            'milestone': 'Design Approval',
            'percent': 25,
            'deliverables': ['Design drawings', 'Material specifications', 'Process flow']
        },
        {
            'milestone': 'Tooling Completion',
            'percent': 40,
            'deliverables': ['Dies/tools delivered', 'Setup completed', 'First samples']
        },
        {
            'milestone': 'Sample Approval',
            'percent': 20,
            'deliverables': ['Approved samples', 'Test reports', 'Documentation']
        },
        {
            'milestone': 'Production Ready',
            'percent': 15,
            'deliverables': ['Process documentation', 'Operator training', 'Production sign-off']
        }
    ]
    
    @staticmethod
    def calculate_typical_nre_cost(product_complexity: str, annual_volume: int) -> dict:
        """Estimate typical NRE cost based on complexity and volume"""
        complexity_factors = {
            'LOW': 50000,
            'MEDIUM': 150000,
            'HIGH': 300000,
            'VERY_HIGH': 500000
        }
        
        volume_adjustment = max(0.8, min(1.2, 1.0 + (annual_volume - 100000) / 1000000))
        
        base_nre = complexity_factors.get(product_complexity, 150000)
        estimated_nre = base_nre * volume_adjustment
        
        return {
            'estimated_nre': estimated_nre,
            'breakdown': {
                component: estimated_nre * (data['typical_percent'] / 100)
                for component, data in OEMNREBestPractices.nre_components.items()
            },
            'monthly_repayment': estimated_nre / 12,
            'per_unit_amortization_12_months': estimated_nre / annual_volume
        }


# OEM Optimization Checklist
OEM_OPTIMIZATION_CHECKLIST = {
    'VENDOR_ONBOARDING': [
        'Complete qualification process',
        'Certifications verified and documented',
        'Capacity confirmed in writing',
        'Quality baseline established',
        'Pricing and MOQ agreed',
        'Lead times confirmed',
        'Technical capabilities assessed',
        'NRE capabilities documented',
        'Payment terms finalized',
        'Communication channels established'
    ],
    'ONGOING_MANAGEMENT': [
        'Monthly performance tracking',
        'Quarterly business reviews',
        'Capacity planning updates',
        'Quality metric monitoring',
        'On-time delivery verification',
        'Cost competitiveness review',
        'Technical capability updates',
        'Certification expiry tracking',
        'Relationship health assessment',
        'Risk mitigation planning'
    ],
    'PROBLEM_RESOLUTION': [
        'Issue escalation procedures',
        'Root cause analysis',
        'Corrective action tracking',
        'Resolution timeline management',
        'Impact mitigation',
        'Communication cadence',
        'Follow-up verification',
        'Preventive measures implementation',
        'Documentation and learning'
    ],
    'PERFORMANCE_IMPROVEMENT': [
        'Identify improvement opportunities',
        'Set SMART improvement goals',
        'Provide technical support',
        'Share best practices',
        'Offer training opportunities',
        'Monitor improvement progress',
        'Provide feedback and recognition',
        'Adjust pricing/volume incentives',
        'Plan joint projects/initiatives'
    ]
}
