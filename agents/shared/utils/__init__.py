"""
Shared Utilities Module
Common utility functions used across all agents

Modules:
- spec_normalizer: Specification normalization
- unit_converter: Unit conversion utilities
- standard_mapper: Standard equivalence mapping
- text_utils: Text cleaning and processing
- date_utils: Date parsing utilities
- param_extractor: Parameter extraction
- validators: Validation helpers
- decorators: Error handling and logging decorators
- logging_utils: Logging configuration
- config_loader: Configuration management
"""

from .spec_normalizer import (
    SpecificationNormalizer,
    normalize_specification,
    normalize_conductor_size,
    normalize_voltage,
    normalize_temperature,
    normalize_material
)

from .unit_converter import (
    UnitConverter,
    convert_length,
    convert_area,
    convert_temperature,
    convert_voltage,
    convert_current,
    convert_weight
)

from .standard_mapper import (
    StandardMapper,
    get_equivalent_standards,
    map_standard_code,
    is_standard_equivalent,
    get_standard_info
)

from .text_utils import (
    TextCleaner,
    clean_text,
    normalize_whitespace,
    remove_special_chars,
    extract_numbers,
    extract_alphanumeric,
    fuzzy_match,
    tokenize
)

from .date_utils import (
    DateParser,
    parse_date,
    format_date,
    get_date_range,
    is_valid_date,
    calculate_deadline
)

from .param_extractor import (
    ParameterExtractor,
    extract_conductor_specs,
    extract_voltage_rating,
    extract_dimensions,
    extract_quantity,
    extract_standards_from_text
)

from .validators import (
    Validator,
    validate_sku,
    validate_email,
    validate_phone,
    validate_gstin,
    validate_specification,
    validate_price,
    validate_quantity
)

from .decorators import (
    retry,
    log_execution,
    timer,
    cached,
    validate_input,
    handle_exceptions,
    async_retry,
    rate_limit
)

from .logging_utils import (
    AgentLogger,
    setup_logging,
    get_logger,
    log_agent_action,
    log_error,
    log_performance
)

from .config_loader import (
    ConfigLoader,
    load_config,
    get_config,
    reload_config,
    get_env_config
)

__all__ = [
    # Spec Normalizer
    'SpecificationNormalizer', 'normalize_specification', 'normalize_conductor_size',
    'normalize_voltage', 'normalize_temperature', 'normalize_material',
    
    # Unit Converter
    'UnitConverter', 'convert_length', 'convert_area', 'convert_temperature',
    'convert_voltage', 'convert_current', 'convert_weight',
    
    # Standard Mapper
    'StandardMapper', 'get_equivalent_standards', 'map_standard_code',
    'is_standard_equivalent', 'get_standard_info',
    
    # Text Utils
    'TextCleaner', 'clean_text', 'normalize_whitespace', 'remove_special_chars',
    'extract_numbers', 'extract_alphanumeric', 'fuzzy_match', 'tokenize',
    
    # Date Utils
    'DateParser', 'parse_date', 'format_date', 'get_date_range',
    'is_valid_date', 'calculate_deadline',
    
    # Parameter Extractor
    'ParameterExtractor', 'extract_conductor_specs', 'extract_voltage_rating',
    'extract_dimensions', 'extract_quantity', 'extract_standards_from_text',
    
    # Validators
    'Validator', 'validate_sku', 'validate_email', 'validate_phone',
    'validate_gstin', 'validate_specification', 'validate_price', 'validate_quantity',
    
    # Decorators
    'retry', 'log_execution', 'timer', 'cached', 'validate_input',
    'handle_exceptions', 'async_retry', 'rate_limit',
    
    # Logging Utils
    'AgentLogger', 'setup_logging', 'get_logger', 'log_agent_action',
    'log_error', 'log_performance',
    
    # Config Loader
    'ConfigLoader', 'load_config', 'get_config', 'reload_config', 'get_env_config'
]
