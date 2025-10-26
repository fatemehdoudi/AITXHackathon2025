"""
Exact mapping of Cigna specialties to their internal categoryId values.
These names must match EXACTLY the `searchTerm`, `resultTitle`, and display text on Cigna’s site.
"""

CIGNA_CATEGORIES = {
    "Primary Care Provider (No Pediatrics)": 15876,
    "Obstetrics and Gynecology (Ob-Gyn)": 15955,
    "Pediatrician": 15957,
    "Cardiologist": 15930,
    "Gastroenterologist": 15790,
    "Nephrologist": 15793,
    "Orthopedic Doctor": 17340,
    "Dermatologist": 15875,
    "Optometrist": 15964,
}

def get_cigna_category(specialty: str):
    """
    Return (name, categoryId) for the given specialty if it matches exactly (case-insensitive).
    Raises KeyError if not found.

    Example:
        >>> get_cigna_category("Cardiologist")
        ('Cardiologist', 15930)
    """
    specialty_clean = specialty.strip().lower()
    for name, cid in CIGNA_CATEGORIES.items():
        if name.lower() == specialty_clean:
            return name, cid

    raise KeyError(
        f"❌ Unknown Cigna specialty '{specialty}'.\n"
        f"Valid options are:\n  {list(CIGNA_CATEGORIES.keys())}"
    )

if __name__ == "__main__":
    # Quick sanity check
    for s in CIGNA_CATEGORIES:
        print(f"{s}: {get_cigna_category(s)}")
