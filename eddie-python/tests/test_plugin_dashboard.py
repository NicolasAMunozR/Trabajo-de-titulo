"""Tests for the dashboard's embedded PDF page preview."""
import pymupdf
from PIL import ImageChops

from plugin_dashboard import render_pdf_page


def test_pdf_preview_renders_saved_highlight(tmp_path):
    pdf_path = tmp_path / "preview.pdf"
    document = pymupdf.open()
    page = document.new_page(width=400, height=300)
    page.insert_text((40, 100), "EDDIE PDF preview")
    document.save(pdf_path)
    document.close()

    before, page_count = render_pdf_page(pdf_path, 1)
    assert page_count == 1
    assert before.size[0] <= 680
    assert before.size[1] <= 580

    document = pymupdf.open(pdf_path)
    page = document[0]
    text_rect = page.search_for("PDF preview")[0]
    page.add_highlight_annot(text_rect).update()
    document.saveIncr()
    document.close()

    after, page_count = render_pdf_page(pdf_path, 1)
    assert page_count == 1
    assert ImageChops.difference(before, after).getbbox() is not None


def test_pdf_preview_rejects_page_outside_document(tmp_path):
    pdf_path = tmp_path / "one-page.pdf"
    document = pymupdf.open()
    document.new_page()
    document.save(pdf_path)
    document.close()

    try:
        render_pdf_page(pdf_path, 2)
    except ValueError as exc:
        assert "tiene 1 páginas" in str(exc)
    else:
        raise AssertionError("Expected an out-of-range PDF page to fail")
