"""
Domain value objects - immutable objects that represent concepts.
"""

import re
from dataclasses import dataclass
from typing import Optional
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Word:
    """Represents a word in the system."""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Word value must be a non-empty string")
        
        if not self.value.isalpha():
            raise ValueError("Word must contain only alphabetic characters")
        
        # Store normalized version (lowercase)
        object.__setattr__(self, 'value', self.value.lower())
    
    def matches_plate(self, plate: 'LicensePlate') -> bool:
        """Check if this word matches the license plate pattern (subsequence)."""
        word_chars = list(self.value.lower())
        plate_chars = list(plate.value.lower())
        
        plate_idx = 0
        for word_char in word_chars:
            # Find the next matching character in the plate
            while plate_idx < len(plate_chars) and plate_chars[plate_idx] != word_char:
                plate_idx += 1
            
            if plate_idx >= len(plate_chars):
                return False
            
            plate_idx += 1
        
        return True
    
    def __len__(self) -> int:
        return len(self.value)
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class LicensePlate:
    """Represents a license plate combination."""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("License plate value must be a non-empty string")
        
        if not self.value.isalpha():
            raise ValueError("License plate must contain only alphabetic characters")
        
        if len(self.value) < 2 or len(self.value) > 8:
            raise ValueError("License plate must be between 2 and 8 characters")
        
        # Store normalized version (uppercase)
        object.__setattr__(self, 'value', self.value.upper())
    
    def __len__(self) -> int:
        return len(self.value)
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Score:
    """Represents a scoring value (0-100)."""
    value: float
    
    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise ValueError("Score must be a number")
        
        if not 0 <= self.value <= 100:
            raise ValueError("Score must be between 0 and 100")
        
        # Round to 2 decimal places
        object.__setattr__(self, 'value', round(float(self.value), 2))
    
    def __float__(self) -> float:
        return self.value
    
    def __str__(self) -> str:
        return f"{self.value:.1f}"


@dataclass(frozen=True)
class AggregateScore:
    """Represents an aggregate score calculated from multiple individual scores."""
    value: float
    
    def __post_init__(self):
        if not isinstance(self.value, (int, float)):
            raise ValueError("Aggregate score must be a number")
        
        if not 0 <= self.value <= 100:
            raise ValueError("Aggregate score must be between 0 and 100")
        
        # Round to 2 decimal places
        object.__setattr__(self, 'value', round(float(self.value), 2))
    
    def __float__(self) -> float:
        return self.value
    
    def __str__(self) -> str:
        return f"{self.value:.1f}"


@dataclass(frozen=True)
class Frequency:
    """Represents word frequency in the corpus."""
    value: int
    
    def __post_init__(self):
        if not isinstance(self.value, int):
            raise ValueError("Frequency must be an integer")
        
        if self.value < 0:
            raise ValueError("Frequency cannot be negative")
    
    def __int__(self) -> int:
        return self.value
    
    def __str__(self) -> str:
        return str(self.value)
    
    @property
    def is_rare(self) -> bool:
        """Check if this frequency indicates a rare word (< 1000)."""
        return self.value < 1000
    
    @property
    def is_common(self) -> bool:
        """Check if this frequency indicates a common word (>= 10000)."""
        return self.value >= 10000


@dataclass(frozen=True)
class ModelName:
    """Represents a model name/identifier."""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Model name must be a non-empty string")
        
        # Basic validation for model name format
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.value):
            raise ValueError("Model name must contain only alphanumeric characters, underscores, and hyphens")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SessionId:
    """Represents a unique session identifier."""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Session ID must be a non-empty string")
    
    @classmethod
    def generate(cls) -> 'SessionId':
        """Generate a new unique session ID."""
        return cls(str(uuid4()))
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CacheKey:
    """Represents a cache key for identifying cached data."""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Cache key must be a non-empty string")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Reasoning:
    """Represents reasoning/explanation text."""
    value: str
    
    def __post_init__(self):
        if not isinstance(self.value, str):
            raise ValueError("Reasoning must be a string")
        
        # Trim whitespace
        object.__setattr__(self, 'value', self.value.strip())
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def is_empty(self) -> bool:
        """Check if reasoning is empty."""
        return not self.value.strip()


@dataclass(frozen=True)
class FilePath:
    """Represents a file system path."""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("File path must be a non-empty string")
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def is_absolute(self) -> bool:
        """Check if this is an absolute path."""
        return self.value.startswith('/')


@dataclass(frozen=True)
class DirectoryPath:
    """Represents a directory path."""
    value: str
    
    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Directory path must be a non-empty string")
    
    def __str__(self) -> str:
        return self.value
    
    def join(self, filename: str) -> FilePath:
        """Join this directory with a filename."""
        path = self.value.rstrip('/') + '/' + filename.lstrip('/')
        return FilePath(path)