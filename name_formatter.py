"""
Deterministic Two-Line Name Formatter for Banking/Official Documents

This module provides a rule-based system to parse personal names and generate
exactly three optimized two-line display options under length constraints.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import re


@dataclass
class NameComponents:
    """Structured representation of a parsed name."""
    titles: List[str]
    first: str
    middle: List[str]
    particles: List[str]
    last: str
    suffixes: List[str]
    
    def __str__(self):
        parts = []
        if self.titles:
            parts.extend(self.titles)
        parts.append(self.first)
        if self.middle:
            parts.extend(self.middle)
        if self.particles:
            parts.extend(self.particles)
        parts.append(self.last)
        if self.suffixes:
            parts.extend(self.suffixes)
        return " ".join(parts)


@dataclass
class TwoLineDisplay:
    """A two-line name display option with metadata."""
    line1: str
    line2: str
    score: float
    strategy: str
    info_preserved: float  # 0.0 to 1.0
    
    def __str__(self):
        return f"{self.line1}\n{self.line2}"
    
    def __eq__(self, other):
        """Two displays are equal if they have identical content."""
        if not isinstance(other, TwoLineDisplay):
            return False
        return self.line1 == other.line1 and self.line2 == other.line2
    
    def __hash__(self):
        return hash((self.line1, self.line2))


class NameParser:
    """Deterministic name parser using vocabulary-based rules."""
    
    def __init__(
        self,
        known_titles: Optional[List[str]] = None,
        known_particles: Optional[List[str]] = None,
        known_suffixes: Optional[List[str]] = None
    ):
        # Default vocabularies (expandable)
        self.titles = set(known_titles or [
            "Mr", "Mrs", "Ms", "Dr", "Prof", "Rev", "Hon", 
            "Sir", "Dame", "Lord", "Lady", "Captain", "Capt",
            "Major", "Col", "Gen", "Lt", "Sgt"
        ])
        
        self.particles = known_particles or [
            "de", "da", "di", "du", "del", "della", "des",
            "van", "von", "der", "den", "het", "ter",
            "de la", "de las", "de los", "van de", "van der", "von der",
            "al", "el", "bin", "ibn", "bint", "abu"
        ]
        # Sort by length (longest first) for greedy matching
        self.particles = sorted(self.particles, key=len, reverse=True)
        
        self.suffixes = set(known_suffixes or [
            "Jr", "Sr", "II", "III", "IV", "V", "VI",
            "PhD", "MD", "DDS", "JD", "Esq", "CPA", "MBA"
        ])
    
    def normalize_punctuation(self, text: str) -> str:
        """Normalize common punctuation while preserving hyphens and apostrophes."""
        # Remove commas, semicolons, colons
        text = re.sub(r'[,;:]', '', text)
        # Normalize multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def is_title(self, token: str) -> bool:
        """Check if token is a title (with or without period)."""
        clean = token.rstrip('.')
        return clean in self.titles
    
    def is_suffix(self, token: str) -> bool:
        """Check if token is a suffix (with or without period)."""
        clean = token.rstrip('.')
        return clean in self.suffixes
    
    def extract_particles(self, tokens: List[str]) -> Tuple[List[str], int, int]:
        """
        Extract particles from the end of token list (before last name).
        Returns (particles, last_name_index, num_particle_tokens).
        """
        if not tokens:
            return [], -1, 0
        
        # Work backwards from the end
        i = len(tokens) - 1
        
        # Skip suffixes first
        while i >= 0 and self.is_suffix(tokens[i]):
            i -= 1
        
        if i < 0:
            return [], -1, 0
        
        # Last name is at position i
        last_name_idx = i
        
        # Now look backwards for particles before the last name
        particles_found = []
        tokens_consumed = 0
        search_idx = i - 1
        
        while search_idx >= 0:
            # Try multi-token particles first (longest first due to sorting)
            matched = False
            
            for particle in self.particles:
                particle_tokens = particle.split()
                n = len(particle_tokens)
                
                # Check if we have enough tokens
                if search_idx - n + 1 >= 0:
                    # Extract candidate tokens
                    start = search_idx - n + 1
                    end = search_idx + 1
                    candidate = " ".join(tokens[start:end])
                    
                    if candidate.lower() == particle.lower():
                        # Found a match - preserve original casing
                        particles_found.insert(0, candidate)
                        tokens_consumed += n
                        search_idx -= n
                        matched = True
                        break
            
            if not matched:
                # No more particles found
                break
        
        return particles_found, last_name_idx, tokens_consumed
    
    def parse(self, full_name: str) -> NameComponents:
        """
        Parse a full name into structured components.
        
        Returns NameComponents with all fields populated.
        Raises ValueError if parsing fails structural requirements.
        """
        # Normalize
        normalized = self.normalize_punctuation(full_name)
        tokens = normalized.split()
        
        if len(tokens) < 2:
            raise ValueError(f"Name must have at least first and last name: '{full_name}'")
        
        # Extract titles from front
        titles = []
        idx = 0
        while idx < len(tokens) and self.is_title(tokens[idx]):
            titles.append(tokens[idx])
            idx += 1
        
        remaining = tokens[idx:]
        
        if len(remaining) < 2:
            raise ValueError(f"Name must have at least first and last name after titles: '{full_name}'")
        
        # Extract suffixes from end
        suffixes = []
        while remaining and self.is_suffix(remaining[-1]):
            suffixes.insert(0, remaining.pop())
        
        if len(remaining) < 2:
            raise ValueError(f"Name must have at least first and last name: '{full_name}'")
        
        # Extract particles and find last name
        particles, last_idx, num_particle_tokens = self.extract_particles(remaining)
        
        if last_idx < 0 or last_idx >= len(remaining):
            raise ValueError(f"Could not identify last name in: '{full_name}'")
        
        # Calculate where particles start in the token list
        # Particles are immediately before the last name
        particle_start_idx = last_idx - num_particle_tokens if particles else last_idx
        
        # Everything before particle_start_idx is first/middle
        name_tokens = remaining[:particle_start_idx]
        
        if not name_tokens:
            raise ValueError(f"Could not identify first name in: '{full_name}'")
        
        first = name_tokens[0]
        middle = name_tokens[1:] if len(name_tokens) > 1 else []
        last = remaining[last_idx]
        
        return NameComponents(
            titles=titles,
            first=first,
            middle=middle,
            particles=particles,
            last=last,
            suffixes=suffixes
        )


class NameAbbreviator:
    """Handles abbreviation rules for name components."""
    
    @staticmethod
    def abbreviate_token(token: str) -> str:
        """
        Convert a name token to its initial with proper punctuation.
        
        Examples:
            Jean-Pierre → J.-P.
            John → J.
            J. → J. (already abbreviated)
        """
        # Already an initial
        if len(token) <= 2 and token.endswith('.'):
            return token
        
        # Handle hyphenated names
        if '-' in token:
            parts = token.split('-')
            abbreviated = '-'.join(p[0].upper() + '.' for p in parts if p)
            return abbreviated
        
        # Simple case
        if token:
            return token[0].upper() + '.'
        return token
    
    @staticmethod
    def abbreviate_list(tokens: List[str]) -> List[str]:
        """Abbreviate a list of name tokens."""
        return [NameAbbreviator.abbreviate_token(t) for t in tokens]


class TwoLineOptimizer:
    """
    Optimizes name display into two lines under length constraints.
    """
    
    def __init__(self, max_line_length: int):
        self.max_line_length = max_line_length
    
    def fits(self, parts: List[str]) -> bool:
        """Check if parts fit in one line."""
        return len(" ".join(parts)) <= self.max_line_length
    
    def find_best_split(self, parts: List[str]) -> Tuple[List[str], List[str]]:
        """
        Find optimal split point for two lines.
        Prioritizes balance and minimizes wasted space.
        
        Returns (line1_parts, line2_parts)
        """
        n = len(parts)
        if n == 0:
            return [], []
        if n == 1:
            if self.fits(parts):
                return parts, []
            else:
                return [], []  # Can't fit
        
        best_split = None
        best_score = float('-inf')
        
        # Try all possible split points
        for i in range(1, n + 1):
            line1_parts = parts[:i]
            line2_parts = parts[i:]
            
            line1 = " ".join(line1_parts)
            line2 = " ".join(line2_parts) if line2_parts else ""
            
            len1 = len(line1)
            len2 = len(line2)
            
            # Both must fit
            if len1 > self.max_line_length or len2 > self.max_line_length:
                continue
            
            # Score based on balance and space utilization
            # Prefer balanced lines, but prioritize fitting
            balance = 1.0 - abs(len1 - len2) / self.max_line_length
            utilization = (len1 + len2) / (2 * self.max_line_length)
            
            score = 0.6 * utilization + 0.4 * balance
            
            if score > best_score:
                best_score = score
                best_split = (line1_parts, line2_parts)
        
        if best_split is None:
            return [], []  # Could not fit
        
        return best_split
    
    def create_display(
        self,
        components: NameComponents,
        strategy: str,
        info_level: float
    ) -> Optional[TwoLineDisplay]:
        """
        Create a two-line display from name components.
        
        Args:
            components: The name components to display
            strategy: Description of the strategy used
            info_level: Information preservation level (0.0 - 1.0)
        
        Returns:
            TwoLineDisplay if successful, None if cannot fit
        """
        # Build parts list in display order
        parts = []
        if components.titles:
            parts.extend(components.titles)
        parts.append(components.first)
        if components.middle:
            parts.extend(components.middle)
        if components.particles:
            parts.extend(components.particles)
        parts.append(components.last)
        if components.suffixes:
            parts.extend(components.suffixes)
        
        line1_parts, line2_parts = self.find_best_split(parts)
        
        if not line1_parts:  # Could not fit
            return None
        
        line1 = " ".join(line1_parts)
        line2 = " ".join(line2_parts) if line2_parts else ""
        
        # Calculate score: heavily weight information preservation
        len1 = len(line1)
        len2 = len(line2)
        balance = 1.0 - abs(len1 - len2) / self.max_line_length if len2 else 1.0
        utilization = (len1 + len2) / (2 * self.max_line_length)
        
        # Information preservation is 10x more important than layout
        score = 10.0 * info_level + 0.5 * utilization + 0.5 * balance
        
        return TwoLineDisplay(
            line1=line1,
            line2=line2,
            score=score,
            strategy=strategy,
            info_preserved=info_level
        )


class NameFormatter:
    """
    Main interface for generating optimized two-line name displays.
    """
    
    def __init__(
        self,
        max_line_length: int,
        known_titles: Optional[List[str]] = None,
        known_particles: Optional[List[str]] = None,
        known_suffixes: Optional[List[str]] = None
    ):
        self.max_line_length = max_line_length
        self.parser = NameParser(known_titles, known_particles, known_suffixes)
        self.optimizer = TwoLineOptimizer(max_line_length)
        self.abbreviator = NameAbbreviator()
    
    def calculate_info_level(self, original: NameComponents, variant: NameComponents) -> float:
        """
        Calculate information preservation score (0.0 - 1.0).
        
        Weights:
        - LAST name: must be present (verified elsewhere)
        - FIRST name: 30% (full=30, initial=15)
        - MIDDLE names: 25% (full=25, initials=12.5, none=0)
        - TITLES: 15% (full=15, initials=7.5, none=0)
        - PARTICLES: must be present (verified elsewhere)
        - SUFFIXES: 30% (full=30, partial=15, none=0)
        """
        score = 0.0
        
        # First name (30%)
        if variant.first == original.first:
            score += 0.30
        elif len(variant.first) == 2 and variant.first.endswith('.'):
            score += 0.15  # Abbreviated
        
        # Middle names (25%)
        if variant.middle == original.middle:
            score += 0.25
        elif variant.middle:
            # Check if abbreviated
            if all(len(m) == 2 and m.endswith('.') for m in variant.middle):
                score += 0.125
        
        # Titles (15%)
        if variant.titles == original.titles:
            score += 0.15
        elif variant.titles:
            # Check if abbreviated
            if all(len(t) <= 2 or t.endswith('.') for t in variant.titles):
                score += 0.075
        
        # Suffixes (30%)
        if variant.suffixes == original.suffixes:
            score += 0.30
        elif variant.suffixes:
            ratio = len(variant.suffixes) / len(original.suffixes)
            score += 0.30 * ratio
        
        return score
    
    def generate_variant(
        self,
        components: NameComponents,
        abbreviate_middle: bool = False,
        abbreviate_titles: bool = False,
        remove_suffixes: bool = False,
        remove_titles: bool = False,
        remove_middle: bool = False,
        abbreviate_first: bool = False
    ) -> NameComponents:
        """
        Generate a name variant with specified transformations.
        
        INVARIANTS:
        - LAST name is never modified
        - PARTICLES are never modified
        """
        return NameComponents(
            titles=(
                [] if remove_titles 
                else self.abbreviator.abbreviate_list(components.titles) if abbreviate_titles
                else components.titles.copy()
            ),
            first=(
                self.abbreviator.abbreviate_token(components.first) if abbreviate_first
                else components.first
            ),
            middle=(
                [] if remove_middle
                else self.abbreviator.abbreviate_list(components.middle) if abbreviate_middle
                else components.middle.copy()
            ),
            particles=components.particles.copy(),  # Never modified
            last=components.last,  # Never modified
            suffixes=[] if remove_suffixes else components.suffixes.copy()
        )
    
    def format(self, full_name: str) -> List[TwoLineDisplay]:
        """
        Generate exactly 3 distinct optimized two-line display options.
        
        Args:
            full_name: Single-line personal name string
        
        Returns:
            List of exactly 3 TwoLineDisplay objects, ranked by score
        
        Raises:
            ValueError: If name cannot be parsed or no valid displays can be generated
        """
        # Parse name
        components = self.parser.parse(full_name)
        
        # Generate candidate variants with progressive degradation
        # We'll try many strategies and pick the best 3 unique ones
        strategies = [
            # Strategy 1: Maximum fidelity
            {
                'name': 'Maximum fidelity',
                'params': {}
            },
            # Strategy 2: Abbreviate middle only
            {
                'name': 'Middle names abbreviated',
                'params': {'abbreviate_middle': True}
            },
            # Strategy 3: Abbreviate titles only
            {
                'name': 'Titles abbreviated',
                'params': {'abbreviate_titles': True}
            },
            # Strategy 4: Abbreviate middle and titles
            {
                'name': 'Moderate abbreviation',
                'params': {'abbreviate_middle': True, 'abbreviate_titles': True}
            },
            # Strategy 5: Remove suffixes
            {
                'name': 'Suffixes removed',
                'params': {'remove_suffixes': True}
            },
            # Strategy 6: Abbreviate middle + remove suffixes
            {
                'name': 'Middle abbreviated, suffixes removed',
                'params': {'abbreviate_middle': True, 'remove_suffixes': True}
            },
            # Strategy 7: Abbreviate titles + middle, remove suffixes
            {
                'name': 'Moderate abbreviation, suffixes removed',
                'params': {'abbreviate_middle': True, 'abbreviate_titles': True, 'remove_suffixes': True}
            },
            # Strategy 8: Remove titles
            {
                'name': 'Titles removed',
                'params': {'remove_titles': True}
            },
            # Strategy 9: Remove middle
            {
                'name': 'Middle names removed',
                'params': {'remove_middle': True}
            },
            # Strategy 10: Aggressive compaction
            {
                'name': 'Aggressive compaction',
                'params': {'remove_titles': True, 'remove_middle': True}
            },
            # Strategy 11: Aggressive + remove suffixes
            {
                'name': 'Aggressive compaction, suffixes removed',
                'params': {'remove_titles': True, 'remove_middle': True, 'remove_suffixes': True}
            },
            # Strategy 12: Abbreviate first (last resort)
            {
                'name': 'First name abbreviated',
                'params': {'abbreviate_first': True, 'remove_titles': True, 'remove_middle': True}
            },
            # Strategy 13: Maximum compaction
            {
                'name': 'Maximum compaction',
                'params': {'abbreviate_first': True, 'remove_titles': True, 'remove_middle': True, 'remove_suffixes': True}
            },
        ]
        
        candidates = []
        seen = set()
        
        for strategy in strategies:
            variant = self.generate_variant(components, **strategy['params'])
            display = self.optimizer.create_display(
                variant,
                strategy['name'],
                self.calculate_info_level(components, variant)
            )
            
            if display:
                # Check if this is unique
                key = (display.line1, display.line2)
                if key not in seen:
                    seen.add(key)
                    candidates.append(display)
                    
                    # Stop once we have enough unique candidates
                    if len(candidates) >= 10:  # Get more than 3 to ensure good selection
                        break
        
        # Sort by score (descending)
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        # Return exactly top 3
        if len(candidates) < 3:
            raise ValueError(
                f"Could not generate 3 distinct displays for '{full_name}' "
                f"with max_line_length={self.max_line_length}. "
                f"Only generated {len(candidates)} options."
            )
        
        return candidates[:3]


def format_name(
    full_name: str,
    max_line_length: int,
    known_titles: Optional[List[str]] = None,
    known_particles: Optional[List[str]] = None,
    known_suffixes: Optional[List[str]] = None
) -> List[TwoLineDisplay]:
    """
    Convenience function to format a name into three two-line displays.
    
    Args:
        full_name: Single-line personal name
        max_line_length: Maximum characters per line
        known_titles: Optional custom title vocabulary
        known_particles: Optional custom particle vocabulary
        known_suffixes: Optional custom suffix vocabulary
    
    Returns:
        List of exactly 3 TwoLineDisplay objects
    
    Example:
        >>> results = format_name("Prof. Dr. Jean-Pierre de la Fontaine III", 25)
        >>> for i, display in enumerate(results, 1):
        ...     print(f"Option {i} ({display.strategy}):")
        ...     print(display)
        ...     print()
    """
    formatter = NameFormatter(
        max_line_length,
        known_titles,
        known_particles,
        known_suffixes
    )
    return formatter.format(full_name)
