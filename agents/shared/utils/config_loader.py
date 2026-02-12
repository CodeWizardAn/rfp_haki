"""
Configuration Loader
Load and manage configuration for agents

Features:
- YAML/JSON/ENV configuration loading
- Environment variable overrides
- Configuration validation
- Hot reload support
- Nested configuration access
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional, Type, Union, TypeVar
from pathlib import Path
from dataclasses import dataclass, field
from threading import Lock
from datetime import datetime
import copy


logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ConfigValue:
    """Wrapper for configuration values with metadata"""
    value: Any
    source: str  # 'file', 'env', 'default'
    loaded_at: datetime = field(default_factory=datetime.utcnow)


class ConfigurationError(Exception):
    """Configuration related errors"""
    pass


class ConfigLoader:
    """
    Load and manage configuration for agents
    
    Supports:
    - JSON files
    - Environment variables (with prefix)
    - Default values
    - Nested key access
    - Type conversion
    """
    
    _instances: Dict[str, 'ConfigLoader'] = {}
    _global_lock = Lock()
    
    def __init__(
        self,
        config_name: str = 'default',
        config_path: Optional[str] = None,
        env_prefix: str = 'AGENT_',
        auto_reload: bool = False
    ):
        """
        Initialize configuration loader
        
        Args:
            config_name: Name for this configuration
            config_path: Path to configuration file
            env_prefix: Prefix for environment variables
            auto_reload: Enable auto-reload on file changes
        """
        self.config_name = config_name
        self.config_path = Path(config_path) if config_path else None
        self.env_prefix = env_prefix
        self.auto_reload = auto_reload
        
        self._config: Dict[str, ConfigValue] = {}
        self._defaults: Dict[str, Any] = {}
        self._lock = Lock()
        self._last_modified: Optional[float] = None
        
        # Load configuration
        if self.config_path and self.config_path.exists():
            self._load_from_file()
        
        self._load_from_env()
    
    @classmethod
    def get_instance(
        cls,
        config_name: str = 'default',
        **kwargs
    ) -> 'ConfigLoader':
        """
        Get or create a configuration loader instance
        
        Args:
            config_name: Name for the configuration
            **kwargs: Additional arguments for new instance
            
        Returns:
            ConfigLoader instance
        """
        with cls._global_lock:
            if config_name not in cls._instances:
                cls._instances[config_name] = cls(config_name, **kwargs)
            return cls._instances[config_name]
    
    def _load_from_file(self):
        """Load configuration from file"""
        if not self.config_path or not self.config_path.exists():
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix in ['.json']:
                    data = json.load(f)
                else:
                    # Try JSON for unknown extensions
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse {self.config_path} as JSON")
                        return
            
            self._flatten_and_store(data, source='file')
            self._last_modified = self.config_path.stat().st_mtime
            
            logger.info(f"Loaded configuration from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            raise ConfigurationError(f"Failed to load config: {e}")
    
    def _flatten_and_store(
        self,
        data: Dict,
        prefix: str = '',
        source: str = 'file'
    ):
        """Flatten nested dictionary and store values"""
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Store the dict itself for nested access
                with self._lock:
                    self._config[full_key] = ConfigValue(value, source)
                # Also flatten nested values
                self._flatten_and_store(value, full_key, source)
            else:
                with self._lock:
                    self._config[full_key] = ConfigValue(value, source)
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                # Convert env key to config key
                config_key = key[len(self.env_prefix):].lower().replace('__', '.')
                
                # Try to convert value to appropriate type
                converted_value = self._convert_value(value)
                
                with self._lock:
                    self._config[config_key] = ConfigValue(converted_value, 'env')
    
    def _convert_value(self, value: str) -> Any:
        """Convert string value to appropriate type"""
        # Boolean
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # None
        if value.lower() in ('none', 'null'):
            return None
        
        # Integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # JSON list/dict
        if value.startswith('[') or value.startswith('{'):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # String
        return value
    
    def set_defaults(self, defaults: Dict[str, Any]):
        """
        Set default values
        
        Args:
            defaults: Dictionary of default values
        """
        self._defaults = copy.deepcopy(defaults)
        
        # Flatten defaults
        def flatten(d: Dict, prefix: str = ''):
            result = {}
            for k, v in d.items():
                key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    result[key] = v
                    result.update(flatten(v, key))
                else:
                    result[key] = v
            return result
        
        self._defaults = flatten(defaults)
    
    def get(
        self,
        key: str,
        default: Any = None,
        type_cast: Optional[Type[T]] = None
    ) -> Union[T, Any]:
        """
        Get configuration value
        
        Args:
            key: Configuration key (dot notation for nested)
            default: Default value if not found
            type_cast: Type to cast the value to
            
        Returns:
            Configuration value
        """
        # Check if reload needed
        if self.auto_reload:
            self._check_reload()
        
        with self._lock:
            if key in self._config:
                value = self._config[key].value
            elif key in self._defaults:
                value = self._defaults[key]
            else:
                value = default
        
        # Type casting
        if type_cast is not None and value is not None:
            try:
                if type_cast == bool:
                    if isinstance(value, str):
                        value = value.lower() in ('true', 'yes', '1', 'on')
                    else:
                        value = bool(value)
                else:
                    value = type_cast(value)
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not cast {key}={value} to {type_cast}: {e}")
        
        return value
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        return self.get(key, default, int)
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value"""
        return self.get(key, default, float)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        return self.get(key, default, bool)
    
    def get_str(self, key: str, default: str = '') -> str:
        """Get string configuration value"""
        return self.get(key, default, str)
    
    def get_list(self, key: str, default: Optional[List] = None) -> List:
        """Get list configuration value"""
        value = self.get(key, default or [])
        if isinstance(value, str):
            # Try to parse as JSON
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                # Split by comma
                value = [v.strip() for v in value.split(',')]
        return value if isinstance(value, list) else [value]
    
    def get_dict(self, key: str, default: Optional[Dict] = None) -> Dict:
        """Get dictionary configuration value"""
        value = self.get(key, default or {})
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse {key} as dict")
                return default or {}
        return value if isinstance(value, dict) else {}
    
    def get_section(self, prefix: str) -> Dict[str, Any]:
        """
        Get all configuration values under a prefix
        
        Args:
            prefix: Key prefix
            
        Returns:
            Dictionary of matching configuration values
        """
        result = {}
        prefix_dot = f"{prefix}."
        
        with self._lock:
            for key, config_value in self._config.items():
                if key.startswith(prefix_dot):
                    # Remove prefix from key
                    short_key = key[len(prefix_dot):]
                    # Only include leaf values (no dots)
                    if '.' not in short_key:
                        result[short_key] = config_value.value
        
        return result
    
    def set(self, key: str, value: Any, persist: bool = False):
        """
        Set configuration value at runtime
        
        Args:
            key: Configuration key
            value: Value to set
            persist: Whether to persist to file
        """
        with self._lock:
            self._config[key] = ConfigValue(value, 'runtime')
        
        if persist and self.config_path:
            self._persist_to_file()
    
    def _persist_to_file(self):
        """Persist configuration to file"""
        if not self.config_path:
            return
        
        # Build nested dict from flattened config
        data = {}
        with self._lock:
            for key, config_value in self._config.items():
                if config_value.source in ('file', 'runtime'):
                    parts = key.split('.')
                    current = data
                    for part in parts[:-1]:
                        current = current.setdefault(part, {})
                    current[parts[-1]] = config_value.value
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Persisted configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to persist configuration: {e}")
    
    def _check_reload(self):
        """Check if configuration file needs reload"""
        if not self.config_path or not self.config_path.exists():
            return
        
        current_mtime = self.config_path.stat().st_mtime
        if self._last_modified and current_mtime > self._last_modified:
            logger.info(f"Configuration file changed, reloading...")
            self._load_from_file()
    
    def reload(self):
        """Force reload configuration from file"""
        if self.config_path:
            self._load_from_file()
        self._load_from_env()
    
    def all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        result = {}
        with self._lock:
            for key, config_value in self._config.items():
                result[key] = config_value.value
        return result
    
    def sources(self) -> Dict[str, str]:
        """Get source of each configuration value"""
        result = {}
        with self._lock:
            for key, config_value in self._config.items():
                result[key] = config_value.source
        return result
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access"""
        return self.get(key)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists"""
        with self._lock:
            return key in self._config or key in self._defaults


# Default agent configuration schema
DEFAULT_AGENT_CONFIG = {
    # Database settings
    'database': {
        'url': 'sqlite:///agents.db',
        'echo': False,
        'pool_size': 5,
        'max_overflow': 10,
    },
    
    # ChromaDB settings
    'chromadb': {
        'path': './chroma_data',
        'collection_name': 'products',
    },
    
    # API settings
    'api': {
        'timeout': 30,
        'max_retries': 3,
        'retry_delay': 1.0,
    },
    
    # Logging settings
    'logging': {
        'level': 'INFO',
        'format': 'standard',  # 'standard' or 'json'
        'file_enabled': True,
        'console_enabled': True,
    },
    
    # Agent settings
    'agents': {
        'master': {
            'max_concurrent': 5,
            'timeout': 60,
        },
        'sales': {
            'discount_limit': 0.15,
            'approval_threshold': 100000,
        },
        'technical': {
            'matching_threshold': 0.7,
            'strict_compliance': True,
        },
        'pricing': {
            'margin_target': 0.20,
            'dynamic_pricing': True,
        },
    },
    
    # RFP processing settings
    'rfp': {
        'max_line_items': 500,
        'deadline_warning_days': 3,
        'auto_approve_threshold': 50000,
    },
}


# Module-level convenience functions
_default_loader: Optional[ConfigLoader] = None


def load_config(
    config_path: Optional[str] = None,
    env_prefix: str = 'AGENT_'
) -> ConfigLoader:
    """
    Load configuration from file and environment
    
    Args:
        config_path: Path to configuration file
        env_prefix: Prefix for environment variables
        
    Returns:
        ConfigLoader instance
    """
    global _default_loader
    _default_loader = ConfigLoader(
        config_name='default',
        config_path=config_path,
        env_prefix=env_prefix
    )
    _default_loader.set_defaults(DEFAULT_AGENT_CONFIG)
    return _default_loader


def get_config(key: str = None, default: Any = None) -> Any:
    """
    Get configuration value
    
    Args:
        key: Configuration key (None returns entire config)
        default: Default value if not found
        
    Returns:
        Configuration value or entire config dict
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = load_config()
    
    if key is None:
        return _default_loader.all()
    return _default_loader.get(key, default)


def reload_config():
    """Reload configuration from file"""
    global _default_loader
    if _default_loader:
        _default_loader.reload()


def get_env_config(key: str, default: Any = None) -> Any:
    """
    Get configuration from environment variable
    
    Args:
        key: Environment variable name (without prefix)
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    env_key = f"AGENT_{key.upper()}"
    value = os.environ.get(env_key)
    
    if value is None:
        return default
    
    # Convert to appropriate type
    loader = ConfigLoader('temp')
    return loader._convert_value(value)
