def clean_bcbs_address(raw_address: str) -> str:
    """Cleans and formats the raw address string from BCBS HTML."""
    clean_address = raw_address.split("•")[0].strip()
    return clean_address