# Print layout of the symbols stamped on each box, in PDF points. Marking and
# detection both rely on these: detection locates the DataMatrix relative to
# the top-left marker using the same ratios the marking process printed with.
MARGIN = 8
MARKER_SIZE = 18
DATAMATRIX_SIZE = MARKER_SIZE
GAP = 4  # white gap so the marker border and the DataMatrix quiet zone don't touch
