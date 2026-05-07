from type3_clipboard_codec.models.colors import TYPE3_COLORS_BY_RAW, TYPE3_PALETTE


def test_type3_palette_contains_known_color_list():
    assert len(TYPE3_PALETTE) == 107

    by_name_and_hex = {(color.name, color.hex_rgb) for color in TYPE3_PALETTE}
    assert ("Black", "000000") in by_name_and_hex
    assert ("Light Cyan", "00FFFF") in by_name_and_hex
    assert ("Deep Blue", "4A16E6") in by_name_and_hex
    assert ("10% Black", "F2F2F2") in by_name_and_hex


def test_type3_palette_raw_candidate_byte_order():
    by_name = {color.name: color for color in TYPE3_PALETTE}

    assert by_name["Blue"].raw_candidate == 0x00008000
    assert by_name["Green"].raw_candidate == 0x00000080
    assert by_name["Cyan"].raw_candidate == 0x00008080
    assert by_name["Light Cyan"].raw_candidate == 0x0000FFFF


def test_type3_palette_raw_lookup_prefers_first_palette_name_for_duplicates():
    assert TYPE3_COLORS_BY_RAW[0x00000000].name == "Black"
    assert TYPE3_COLORS_BY_RAW[0x00C0C0C0].name == "Light Gray"
