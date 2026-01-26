- 👋 Hi, I’m @augustistaken
- 👀 I’m interested in ...
- 🌱 I’m currently learning ...
- 💞️ I’m looking to collaborate on ...
- 📫 How to reach me ...

<!---
augustistaken/augustistaken is a ✨ special ✨ repository because its `README.md` (this file) appears on your GitHub profile.
You can click the Preview link to take a look at your changes.
--->
import re
import unicodedata
from typing import List, Tuple, Dict

# --- Configuration ---

# Regex for allowed German Banking characters
# Allows: a-z, 0-9, umlauts (äöüß), space, and basic punctuation (.,-')
ALLOWED_CHARS_PATTERN = re.compile(r"[^a-zA-Z0-9äöüÄÖÜß\.\,\-\'\s]")

# Lists for context (used if specific tokenization rules apply,
# generally handled by regex boundaries in this implementation)
PREFIXES = {
    "mr", "mister", "mrs", "ms", "miss", "mx", "dr", "prof", "sir",
    "dame", "lord", "lady", "rev", "fr", "sr", "sra", "srta",
    "hon", "judge", "justice", "capt", "cpt", "cmdr", "col", "gen", "lt", "maj", "sgt"
}

SUFFIXES = {
    "phd", "ph.d", "md", "m.d", "dds", "d.d.s", "dvm", "d.v.m",
    "esq", "esquire", "jr", "sr", "ii", "iii", "iv",
    "mba", "m.b.a", "msc", "m.sc", "bsc", "b.sc",
    "ba", "b.a", "ma", "m.a", "jd", "j.d", "llm", "ll.m",
    "cpa", "c.f.a", "cfa"
}

PARTICLES = {
    "von", "van", "de", "del", "della", "di", "da", "dos", "das", "du",
    "la", "le", "des", "den", "der", "ter", "ten", "zu", "zum", "zur",
    "al", "bin", "ibn", "binti", "st", "st.", "mac", "mc", "o'"
}


# --- Core Functions ---

def clean_banking_text(text: str) -> str:
    """
    Normalizes text to NFKC, strips whitespace, and removes
    any characters strictly not allowed in German banking.
    """
    if not text:
        return ""

    # 1. Unicode Normalize
    text = unicodedata.normalize("NFKC", text)

    # 2. Remove Disallowed Characters (replace with empty string)
    text = ALLOWED_CHARS_PATTERN.sub("", text)

    # 3. Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize(text: str) -> List[str]:
    """
    Splits text into tokens based on whitespace and punctuation boundaries.
    Keeps punctuation attached if it is part of an abbreviation (e.g., Ph.D.),
    otherwise splits it.
    """
    # Simple split by whitespace is usually sufficient after cleaning,
    # but strictly we separate words from distinct punctuation if needed.
    return text.split()


def generate_token_map(full_name: str, line1: str, line2: str) -> List[Dict[str, str]]:
    """
    Compares the Full Name against the combined Name Lines.
    Returns a list of dicts: {'token': 'NameToken', 'status': 'KEEP/REMOVE/SHORTEN'}
    """

    # 1. Clean Inputs
    clean_full = clean_banking_text(full_name)
    clean_l1 = clean_banking_text(line1)
    clean_l2 = clean_banking_text(line2)

    # 2. Tokenize
    full_tokens = tokenize(clean_full)

    # Create the comparison target: Line 1 + <NEW> + Line 2
    l1_tokens = tokenize(clean_l1)
    l2_tokens = tokenize(clean_l2)

    # We combine them for searching, keeping track of the NEW token strictly for separation
    # Note: We filter out the <NEW> token for the actual string comparison logic
    target_tokens = l1_tokens + ["<NEW>"] + l2_tokens

    mapping_result = []

    # Pointer for the target_tokens list (greedy matching)
    target_idx = 0
    max_target = len(target_tokens)

    for f_tok in full_tokens:
        match_found = False

        # Strip trailing dots for comparison (e.g., "Dr." vs "Dr")
        f_norm = f_tok.rstrip('.').lower()

        # Look ahead in the target lines starting from current position
        for i in range(target_idx, max_target):
            t_tok = target_tokens[i]

            # Skip the newline marker during comparison
            if t_tok == "<NEW>":
                continue

            t_norm = t_tok.rstrip('.').lower()

            # Check 1: Exact Match (KEEP)
            # We compare normalized versions to handle "Dr" vs "Dr."
            if f_norm == t_norm:
                mapping_result.append({"token": f_tok, "status": "KEEP"})
                target_idx = i + 1  # Move pointer forward
                match_found = True
                break

            # Check 2: Shortened (SHORTEN)
            # Target is a prefix of Full (e.g., Full="Thomas", Target="T" or "T.")
            elif f_norm.startswith(t_norm) and len(t_norm) < len(f_norm):
                mapping_result.append({"token": f_tok, "status": "SHORTEN"})
                target_idx = i + 1  # Move pointer forward
                match_found = True
                break

        # Check 3: Not Found (REMOVE)
        if not match_found:
            mapping_result.append({"token": f_tok, "status": "REMOVE"})

    return mapping_result


# --- Execution ---

if __name__ == "__main__":
    # Example Input
    full_name_in = "Prof. Dr. Thomas Müller-Westernhagen Ph.D."
    nameline1_in = "Prof. Dr. T. Müller-"
    nameline2_in = "Westernhagen"

    # Run Logic
    result_map = generate_token_map(full_name_in, nameline1_in, nameline2_in)

    # Output Display
    print(f"Full Name: {clean_banking_text(full_name_in)}")
    print(f"Line 1:    {clean_banking_text(nameline1_in)}")
    print(f"Line 2:    {clean_banking_text(nameline2_in)}")
    print("-" * 40)
    print(f"{'TOKEN':<25} | {'STATUS'}")
    print("-" * 40)

    for item in result_map:
        print(f"{item['token']:<25} | {item['status']}")