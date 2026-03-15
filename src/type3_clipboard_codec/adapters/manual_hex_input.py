from .input_base import InputAdapter
from ..utils.hex_text import hex_to_bytes

class ManualHexInput(InputAdapter):
    """
    사용자가 수동으로 붙여넣은 16진수 문자열을 바이트 데이터로 변환하는 어댑터.
    """
    def __init__(self, hex_text: str):
        self._hex_text = hex_text

    def fetch_data(self) -> bytes:
        """
        입력된 Hex 텍스트를 정규화하고 바이트로 변환한다.
        """
        return hex_to_bytes(self._hex_text)
