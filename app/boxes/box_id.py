# Box identity travels in the DataMatrix next to the top-left marker; capping
# it at 6 decimal digits keeps the symbol at its smallest sizes.
MAX_BOX_ID = 999_999


def is_valid_box_id(box_id: int) -> bool:
    return 1 <= box_id <= MAX_BOX_ID
