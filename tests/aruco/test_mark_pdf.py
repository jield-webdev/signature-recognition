import fitz

from aruco.mark_pdf import mark_pdf


async def test_inserts_four_markers_on_first_page(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=1), filetype="pdf")

    marked = await mark_pdf(doc)

    assert marked is doc
    assert len(marked[0].get_images()) == 4


async def test_only_marks_the_first_page(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes(pages=3), filetype="pdf")

    await mark_pdf(doc)

    assert len(doc[0].get_images()) == 4
    assert len(doc[1].get_images()) == 0
    assert len(doc[2].get_images()) == 0
