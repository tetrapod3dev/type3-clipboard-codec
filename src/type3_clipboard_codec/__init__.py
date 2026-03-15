"""
TYPE3 Clipboard Codec 패키지 초기화.
공개 API를 노출한다.
"""

from .codec.decoder import Decoder
from .codec.preview import PreviewRenderer
from .models.parsed_object import ParsedObject
from .models.text_object import TextObject
from .models.geometry import GeometryObject, Point

# 편리한 접근을 위한 별칭 또는 팩토리 함수 제공 가능
def decode_bytes(data: bytes) -> ParsedObject:
    """바이트 데이터를 디코딩한다."""
    return Decoder().decode_bytes(data)

def decode_hex_text(hex_text: str) -> ParsedObject:
    """16진수 텍스트를 디코딩한다."""
    return Decoder().decode_hex_text(hex_text)

def render_preview(obj: ParsedObject) -> str:
    """모델 객체의 미리보기를 렌더링한다."""
    return PreviewRenderer().render(obj)

__all__ = [
    "Decoder",
    "PreviewRenderer",
    "ParsedObject",
    "TextObject",
    "GeometryObject",
    "Point",
    "decode_bytes",
    "decode_hex_text",
    "render_preview",
]
