import struct


def is_plausible_class_header_at(data: bytes, offset: int) -> bool:
    if offset < 0 or offset > len(data) - 6:
        return False
    if data[offset : offset + 2] != b"\xff\xff":
        return False

    try:
        name_len = struct.unpack("<H", data[offset + 4 : offset + 6])[0]
    except Exception:
        return False

    if not (1 < name_len < 64) or offset + 6 + name_len > len(data):
        return False

    name_bytes = data[offset + 6 : offset + 6 + name_len]
    return all(32 <= b <= 126 for b in name_bytes) and name_bytes.startswith(b"C")


def find_next_class_header_offset(data: bytes, start_idx: int = 1) -> int:
    """
    Returns the offset of the next plausible class header within `data`,
    or -1 if none is found.
    """
    idx = max(0, start_idx)
    while idx < len(data) - 5:
        if is_plausible_class_header_at(data, idx):
            return idx
        idx += 1
    return -1
