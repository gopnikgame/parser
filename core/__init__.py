# Core модуль для DNSCrypt Parser
# Централизованная логика парсинга

__version__ = "2.0.0"
__author__ = "DNSCrypt Parser Team"

from .base_parser import DNSCryptParser
from .driver_manager import SmartDriverManager
from .config import ParserConfig

__all__ = [
    'DNSCryptParser',
    'SmartDriverManager', 
    'ParserConfig'
]