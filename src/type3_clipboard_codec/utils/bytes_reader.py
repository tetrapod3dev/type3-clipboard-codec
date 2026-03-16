import struct
from io import BytesIO


class BytesReader:
    """
    이진 데이터를 읽기 위한 유틸리티 클래스.
    리틀 엔디안 방식의 읽기를 기본으로 하며, 읽기 위치 추적 기능을 제공한다.
    """
    def __init__(self, data: bytes):
        self._buffer = BytesIO(data)
        self._size = len(data)

    def tell(self) -> int:
        """현재 읽기 위치를 반환한다."""
        return self._buffer.tell()

    def seek(self, offset: int, whence: int = 0) -> int:
        """읽기 위치를 지정된 오프셋으로 이동시킨다."""
        return self._buffer.seek(offset, whence)

    def remaining(self) -> int:
        """남은 데이터의 크기를 반환한다."""
        return self._size - self.tell()

    def read_bytes(self, size: int) -> bytes:
        """지정된 크기만큼의 바이트를 읽는다."""
        data = self._buffer.read(size)
        if len(data) < size:
            raise EOFError(f"데이터가 부족합니다. (요청: {size}, 남음: {len(data)})")
        return data

    def peek_bytes(self, size: int) -> bytes:
        """현재 위치를 변경하지 않고 지정된 크기만큼의 바이트를 읽어본다."""
        pos = self.tell()
        try:
            return self.read_bytes(size)
        finally:
            self.seek(pos)

    def read_u8(self) -> int:
        """unsigned 8-bit 정수를 읽는다."""
        return self.read_bytes(1)[0]

    def read_u16_le(self) -> int:
        """unsigned 16-bit 리틀 엔디안 정수를 읽는다."""
        return struct.unpack("<H", self.read_bytes(2))[0]

    def read_u32_le(self) -> int:
        """unsigned 32-bit 리틀 엔디안 정수를 읽는다."""
        return struct.unpack("<I", self.read_bytes(4))[0]

    def read_i32_le(self) -> int:
        """signed 32-bit 리틀 엔디안 정수를 읽는다."""
        return struct.unpack("<i", self.read_bytes(4))[0]

    def read_f64_le(self) -> float:
        """64-bit 리틀 엔디안 부동소수점 숫자를 읽는다."""
        return struct.unpack("<d", self.read_bytes(8))[0]

    def read_ascii(self, size: int) -> str:
        """지정된 크기만큼 ASCII 문자열을 읽는다."""
        return self.read_bytes(size).decode("ascii")
