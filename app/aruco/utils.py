# Box identity travels in the DataMatrix next to the top-left marker; capping
# it at 6 decimal digits keeps the symbol at its smallest sizes.
MAX_BOX_ID = 999_999


def is_valid_box_id(box_id: int) -> bool:
    return 1 <= box_id <= MAX_BOX_ID


def markers_for_slot(slot: int) -> tuple[int, int]:
    """Slot 0 -> (0, 1), slot 1 -> (2, 3), ...

    Marker ids identify a box *slot* on the page, not the box itself.
    The even id is the top-left marker, the odd id the bottom-right.
    """
    return (2 * slot, 2 * slot + 1)
