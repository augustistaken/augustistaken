"""
Demo script showcasing the deterministic two-line name formatter.
"""

from name_formatter import format_name, NameParser


def print_separator(char="=", width=70):
    print(char * width)


def demo_basic_usage():
    """Demonstrate basic usage with a complex name."""
    print_separator()
    print("DEMO: Basic Usage")
    print_separator()
    
    name = "Prof. Dr. Jean-Pierre Henri de la Fontaine III PhD"
    max_length = 30
    
    print(f"\nFormatting: {name}")
    print(f"Maximum line length: {max_length}\n")
    
    results = format_name(name, max_length)
    
    for i, display in enumerate(results, 1):
        print(f"Option {i}: {display.strategy}")
        print(f"  Information preserved: {display.info_preserved:.0%}")
        print(f"  Score: {display.score:.2f}")
        print(f"  ┌{'─' * (max_length + 2)}┐")
        print(f"  │ {display.line1:<{max_length}} │")
        print(f"  │ {display.line2:<{max_length}} │")
        print(f"  └{'─' * (max_length + 2)}┘")
        print()


def demo_parsing():
    """Demonstrate the parsing capabilities."""
    print_separator()
    print("DEMO: Name Parsing")
    print_separator()
    
    parser = NameParser()
    
    test_names = [
        "Sir Arthur Ignatius Conan Doyle",
        "Dr. Ludwig van der Rohe Jr.",
        "Jean-Pierre de la Fontaine III",
        "Mary-Anne O'Brien",
    ]
    
    print("\nDemonstrating deterministic parsing:\n")
    
    for name in test_names:
        components = parser.parse(name)
        print(f"Input: {name}")
        print(f"  • Titles: {components.titles or '(none)'}")
        print(f"  • First: {components.first}")
        print(f"  • Middle: {components.middle or '(none)'}")
        print(f"  • Particles: {components.particles or '(none)'}")
        print(f"  • Last: {components.last}")
        print(f"  • Suffixes: {components.suffixes or '(none)'}")
        print()


def demo_length_constraints():
    """Demonstrate how the system handles different length constraints."""
    print_separator()
    print("DEMO: Length Constraints")
    print_separator()
    
    name = "Dr. Martin Luther King Jr."
    lengths = [30, 25, 20]
    
    print(f"\nName: {name}\n")
    
    for length in lengths:
        print(f"With max_line_length = {length}:")
        print("-" * 50)
        
        try:
            results = format_name(name, length)
            
            for display in results:
                print(f"  {display.line1}")
                print(f"  {display.line2}")
                print()
        except Exception as e:
            print(f"  Error: {e}\n")


def demo_international_names():
    """Demonstrate support for international naming conventions."""
    print_separator()
    print("DEMO: International Names")
    print_separator()
    
    international_names = [
        ("Spanish", "María de las Mercedes García López", 28),
        ("Dutch", "Jan van de Berg", 20),
        ("German", "Ludwig von der Müller", 25),
        ("French", "Pierre de la Fontaine", 25),
    ]
    
    print("\nDemonstrating particles from different languages:\n")
    
    for culture, name, max_len in international_names:
        print(f"{culture}: {name}")
        try:
            results = format_name(name, max_len)
            display = results[0]  # Show best option
            print(f"  {display.line1}")
            print(f"  {display.line2}")
        except Exception as e:
            print(f"  Error: {e}")
        print()


def demo_abbreviation_rules():
    """Demonstrate how abbreviations preserve punctuation."""
    print_separator()
    print("DEMO: Abbreviation Rules")
    print_separator()
    
    names_with_hyphens = [
        "Jean-Pierre Martin",
        "Mary-Anne Smith",
        "Hans-Georg Müller",
    ]
    
    print("\nHyphenated names preserve structure in abbreviations:\n")
    
    for name in names_with_hyphens:
        print(f"Name: {name}")
        try:
            results = format_name(name, 20)
            # Find option with abbreviated first name
            for display in results:
                if "abbreviated" in display.strategy.lower():
                    print(f"  Abbreviated: {display.line1} / {display.line2}")
                    break
        except Exception as e:
            print(f"  Error: {e}")
        print()


def demo_custom_vocabularies():
    """Demonstrate using custom vocabularies."""
    print_separator()
    print("DEMO: Custom Vocabularies")
    print_separator()
    
    print("\nYou can extend the vocabularies for specific use cases:\n")
    
    # Example with military ranks
    custom_titles = ["Gen", "Col", "Maj", "Cpt", "Lt", "Sgt", "Cpl"]
    
    from name_formatter import NameFormatter
    
    formatter = NameFormatter(
        max_line_length=25,
        known_titles=custom_titles
    )
    
    name = "Gen Douglas MacArthur"
    print(f"Name: {name}")
    print("Using custom military title vocabulary\n")
    
    results = formatter.format(name)
    
    for i, display in enumerate(results, 1):
        print(f"Option {i}:")
        print(f"  {display.line1}")
        print(f"  {display.line2}")
        print()


def run_all_demos():
    """Run all demonstration scenarios."""
    print("\n" + "=" * 70)
    print("DETERMINISTIC TWO-LINE NAME FORMATTER - DEMONSTRATIONS")
    print("=" * 70 + "\n")
    
    demo_basic_usage()
    demo_parsing()
    demo_length_constraints()
    demo_international_names()
    demo_abbreviation_rules()
    demo_custom_vocabularies()
    
    print_separator()
    print("DEMONSTRATIONS COMPLETE")
    print_separator()
    print()


if __name__ == "__main__":
    run_all_demos()
