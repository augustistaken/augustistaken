"""
Comprehensive test suite for the name formatter system.
"""

from name_formatter import (
    NameFormatter, NameParser, NameAbbreviator,
    format_name, NameComponents
)


def test_abbreviation_rules():
    """Test that abbreviations preserve punctuation correctly."""
    print("=" * 60)
    print("TEST: Abbreviation Rules")
    print("=" * 60)
    
    abbrev = NameAbbreviator()
    
    tests = [
        ("Jean-Pierre", "J.-P."),
        ("John", "J."),
        ("J.", "J."),
        ("Mary-Anne", "M.-A."),
        ("R", "R."),
    ]
    
    for input_name, expected in tests:
        result = abbrev.abbreviate_token(input_name)
        status = "✓" if result == expected else "✗"
        print(f"{status} {input_name:15s} → {result:10s} (expected: {expected})")
    
    print()


def test_particle_detection():
    """Test multi-token particle detection."""
    print("=" * 60)
    print("TEST: Particle Detection")
    print("=" * 60)
    
    parser = NameParser()
    
    tests = [
        ("Jean de la Fontaine", ["de la"]),
        ("Ludwig van der Rohe", ["van der"]),
        ("Maria von Trapp", ["von"]),
        ("Pedro de las Casas", ["de las"]),
        ("Jan van de Berg", ["van de"]),
    ]
    
    for full_name, expected_particles in tests:
        components = parser.parse(full_name)
        status = "✓" if components.particles == expected_particles else "✗"
        print(f"{status} {full_name:25s} → particles: {components.particles}")
        if components.particles != expected_particles:
            print(f"   Expected: {expected_particles}")
    
    print()


def test_complex_parsing():
    """Test parsing of complex names with all components."""
    print("=" * 60)
    print("TEST: Complex Name Parsing")
    print("=" * 60)
    
    parser = NameParser()
    
    name = "Prof. Dr. Jean-Pierre Henri de la Fontaine III PhD"
    components = parser.parse(name)
    
    print(f"Input: {name}")
    print(f"  Titles:    {components.titles}")
    print(f"  First:     {components.first}")
    print(f"  Middle:    {components.middle}")
    print(f"  Particles: {components.particles}")
    print(f"  Last:      {components.last}")
    print(f"  Suffixes:  {components.suffixes}")
    
    assert components.titles == ["Prof.", "Dr."]
    assert components.first == "Jean-Pierre"
    assert components.middle == ["Henri"]
    assert components.particles == ["de la"]
    assert components.last == "Fontaine"
    assert components.suffixes == ["III", "PhD"]
    
    print("✓ All components parsed correctly")
    print()


def test_two_line_formatting():
    """Test two-line display generation for various names."""
    print("=" * 60)
    print("TEST: Two-Line Formatting")
    print("=" * 60)
    
    test_cases = [
        ("John Smith", 20),
        ("Prof. Dr. Maria von Trapp", 25),
        ("Jean-Pierre de la Fontaine III", 30),
        ("Sir Arthur Conan Doyle", 22),
        ("Dr. Martin Luther King Jr.", 25),
    ]
    
    for full_name, max_length in test_cases:
        print(f"\nName: {full_name}")
        print(f"Max length: {max_length}")
        print("-" * 40)
        
        try:
            results = format_name(full_name, max_length)
            
            for i, display in enumerate(results, 1):
                print(f"\nOption {i}: {display.strategy}")
                print(f"  Score: {display.score:.2f} | Info: {display.info_preserved:.0%}")
                print(f"  Line 1 ({len(display.line1):2d}): {display.line1}")
                print(f"  Line 2 ({len(display.line2):2d}): {display.line2}")
                
                # Validate constraints
                assert len(display.line1) <= max_length, f"Line 1 too long: {len(display.line1)} > {max_length}"
                assert len(display.line2) <= max_length, f"Line 2 too long: {len(display.line2)} > {max_length}"
            
            print(f"\n✓ Generated {len(results)} valid options")
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n")


def test_structural_invariants():
    """Test that structural rules are never violated."""
    print("=" * 60)
    print("TEST: Structural Invariants")
    print("=" * 60)
    
    formatter = NameFormatter(max_line_length=25)
    parser = NameParser()
    
    test_names = [
        "Prof. Jean-Pierre de la Fontaine III PhD",
        "Dr. Ludwig van der Rohe Jr.",
        "Sir Arthur Ignatius Conan Doyle",
    ]
    
    all_passed = True
    
    for name in test_names:
        print(f"\nTesting: {name}")
        original = parser.parse(name)
        
        try:
            results = formatter.format(name)
            
            for display in results:
                # Parse the displayed name to check invariants
                displayed = f"{display.line1} {display.line2}".strip()
                
                # Check that last name is present and unmodified
                assert original.last in displayed, f"Last name '{original.last}' missing"
                
                # Check that particles are present if original had them
                if original.particles:
                    for particle in original.particles:
                        assert particle in displayed, f"Particle '{particle}' missing or modified"
                
                # Check that first name is present (full or abbreviated)
                first_present = (
                    original.first in displayed or
                    original.first[0] + "." in displayed
                )
                assert first_present, f"First name '{original.first}' missing"
            
            print(f"  ✓ All invariants preserved")
            
        except AssertionError as e:
            print(f"  ✗ Invariant violated: {e}")
            all_passed = False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_passed = False
    
    if all_passed:
        print("\n✓ All structural invariants maintained")
    else:
        print("\n✗ Some invariants were violated")
    
    print()


def test_determinism():
    """Test that output is deterministic."""
    print("=" * 60)
    print("TEST: Determinism")
    print("=" * 60)
    
    name = "Prof. Dr. Jean-Pierre de la Fontaine III"
    max_length = 28
    
    # Run 5 times
    results_list = []
    for _ in range(5):
        results = format_name(name, max_length)
        results_list.append(results)
    
    # Check all runs produced identical results
    first_run = results_list[0]
    all_identical = True
    
    for i, run in enumerate(results_list[1:], 2):
        for j, (display1, display2) in enumerate(zip(first_run, run)):
            if display1.line1 != display2.line1 or display1.line2 != display2.line2:
                print(f"✗ Run {i} option {j+1} differs from run 1")
                all_identical = False
    
    if all_identical:
        print("✓ All 5 runs produced identical output")
    else:
        print("✗ Output varied between runs")
    
    print()


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("=" * 60)
    print("TEST: Edge Cases")
    print("=" * 60)
    
    test_cases = [
        # Very short name
        ("John Doe", 15),
        # Name with initials already
        ("J. R. R. Tolkien", 20),
        # Multiple particles
        ("Jean de la van der Berg", 25),
        # Long hyphenated first name
        ("Jean-Pierre-Marie Smith", 22),
        # Many middle names
        ("John Paul George Ringo Smith", 25),
    ]
    
    for name, max_length in test_cases:
        print(f"\nTesting: {name} (max: {max_length})")
        try:
            results = format_name(name, max_length)
            print(f"  ✓ Generated {len(results)} options")
            
            # Show first option
            display = results[0]
            print(f"    Line 1: {display.line1}")
            print(f"    Line 2: {display.line2}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print()


def test_information_preservation_scoring():
    """Test that info loss is penalized correctly."""
    print("=" * 60)
    print("TEST: Information Preservation Scoring")
    print("=" * 60)
    
    name = "Prof. Dr. Jean-Pierre Henri de la Fontaine III PhD"
    max_length = 30
    
    results = format_name(name, max_length)
    
    print(f"Name: {name}")
    print(f"Max length: {max_length}\n")
    
    # Results should be ordered by score (descending)
    prev_score = float('inf')
    
    for i, display in enumerate(results, 1):
        print(f"Option {i}:")
        print(f"  Strategy: {display.strategy}")
        print(f"  Score: {display.score:.2f}")
        print(f"  Info preserved: {display.info_preserved:.0%}")
        print(f"  Line 1: {display.line1}")
        print(f"  Line 2: {display.line2}")
        print()
        
        # Verify ordering
        assert display.score <= prev_score, "Results not properly sorted by score"
        prev_score = display.score
    
    # Verify that more info = higher score
    assert results[0].info_preserved >= results[-1].info_preserved, \
        "Higher scored option should preserve more info"
    
    print("✓ Information preservation is properly weighted in scoring")
    print()


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "=" * 60)
    print("DETERMINISTIC NAME FORMATTER - COMPREHENSIVE TEST SUITE")
    print("=" * 60 + "\n")
    
    test_abbreviation_rules()
    test_particle_detection()
    test_complex_parsing()
    test_two_line_formatting()
    test_structural_invariants()
    test_determinism()
    test_edge_cases()
    test_information_preservation_scoring()
    
    print("=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
