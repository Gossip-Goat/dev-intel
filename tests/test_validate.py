from dev_intel.extraction.schema import ExtractedDocument, ExtractedLot, PropertyType
from dev_intel.extraction.validate import check_document


def lot(n, price, area=85.0, t=PropertyType.apartment):
    return ExtractedLot(lot_number=n, property_type=t, price_aud=price, internal_m2=area)


def doc(*lots):
    return ExtractedDocument(development_name="X", developer=None, address=None, suburb="Newstead", lots=list(lots))


def test_clean_document():
    assert check_document(doc(lot("101", 850_000), lot("102", 920_000))) == []


def test_dropped_zero_flagged():
    assert check_document(doc(lot("101", 85_000)))


def test_rate_per_m2_flagged():
    assert check_document(doc(lot("101", 850_000, area=8.5)))


def test_duplicate_lot_flagged():
    assert check_document(doc(lot("101", 850_000), lot("101", 850_000)))


def test_empty_document_flagged():
    assert check_document(doc())
