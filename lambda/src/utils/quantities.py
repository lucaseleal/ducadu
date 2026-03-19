def parse_quantity(quantity_raw: str):
    """
    Ex: '0.0014UN' -> (0.0014, 'UN')
    """
    if not quantity_raw:
        return None, None

    num = ""
    unit = ""

    for c in quantity_raw.strip():
        if c.isdigit() or c in ".,":
            num += c
        else:
            unit += c

    try:
        num = float(num.replace(",", "."))
    except Exception:
        num = None

    return num, unit.strip() or None
