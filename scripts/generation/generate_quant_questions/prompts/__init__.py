"""
Prompts Package
===============

This package contains all prompt templates for generating:
- Data Interpretation (DI) questions
- Arithmetic questions
- Number Series questions
- Quadratic Equations questions
- Other quantitative aptitude content

Modules:
    - di_prompts: Prompts for DI set generation
    - arithmetic_prompts: Prompts for arithmetic question generation
    - number_series_prompts: Prompts for number series question generation
    - quadratic_prompts: Prompts for quadratic equation question generation
"""

from .di_prompts import (
    get_di_generation_prompt,
    get_di_system_prompt,
    DI_TYPES,
    DI_TOPICS
)

from .arithmetic_prompts import (
    get_arithmetic_generation_prompt,
    get_arithmetic_system_prompt,
    ARITHMETIC_TOPICS
)

from .number_series_prompts import (
    get_number_series_generation_prompt,
    get_number_series_system_prompt,
    get_number_series_validation_prompt
)

from .quadratic_prompts import (
    get_quadratic_generation_prompt,
    get_quadratic_system_prompt,
    get_quadratic_validation_prompt
)

__all__ = [
    # DI Prompts
    'get_di_generation_prompt',
    'get_di_system_prompt',
    'DI_TYPES',
    'DI_TOPICS',
    
    # Arithmetic Prompts
    'get_arithmetic_generation_prompt',
    'get_arithmetic_system_prompt',
    'ARITHMETIC_TOPICS',
    
    # Number Series Prompts
    'get_number_series_generation_prompt',
    'get_number_series_system_prompt',
    'get_number_series_validation_prompt',
    
    # Quadratic Prompts
    'get_quadratic_generation_prompt',
    'get_quadratic_system_prompt',
    'get_quadratic_validation_prompt'
]

__version__ = "1.0.0"
