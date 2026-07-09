# DICT_4X4_50 provides 50 marker ids and each slot consumes a pair, so a
# single page can carry at most 25 boxes.
MAX_SLOTS_PER_PAGE = 25


def markers_for_slot(slot: int) -> tuple[int, int]:
    """Slot 0 -> (0, 1), slot 1 -> (2, 3), ...

    Marker ids identify a box *slot* on the page, not the box itself.
    The even id is the top-left marker, the odd id the bottom-right.
    """
    return (2 * slot, 2 * slot + 1)
