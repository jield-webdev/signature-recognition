# Print layout of the symbols stamped on each box, in PDF points. Marking and
# detection both rely on these: detection locates the DataMatrix relative to
# the top-left marker using the same ratios the marking process printed with.
MARGIN = 8
MARKER_SIZE = 24
DATAMATRIX_SIZE = MARKER_SIZE
GAP = 4  # white gap so the marker border and the DataMatrix quiet zone don't touch

# A box usually lands on something the form already prints — a table cell
# border, a rule — which then runs flush against a symbol's black border.
# Contour segmentation merges the two and the marker is silently dropped, so
# each symbol is stamped on a white patch this wide to keep its quiet zone
# whatever lies underneath.
QUIET_ZONE = 4

# Smallest box a placement may request: the top-left marker, its DataMatrix
# and the bottom-right marker must fit without touching each other.
MIN_BOX_WIDTH = MARKER_SIZE + GAP + DATAMATRIX_SIZE + GAP + MARKER_SIZE
MIN_BOX_HEIGHT = 2 * MARKER_SIZE + GAP
