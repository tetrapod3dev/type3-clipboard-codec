from type3_clipboard_codec.utils.ascii_scan import scan_ascii_strings

def test_scan_ascii_strings():
    data = b"\x00\x00Hello\x00\x00World\x01"
    results = scan_ascii_strings(data, min_length=4)

    assert len(results) == 2
    assert results[0] == (2, "Hello")
    assert results[1] == (9, "World")

def test_scan_ascii_strings_too_short():
    data = b"ABC\x00DEF"
    results = scan_ascii_strings(data, min_length=4)
    assert len(results) == 0
