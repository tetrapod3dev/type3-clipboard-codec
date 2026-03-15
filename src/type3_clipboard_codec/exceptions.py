"""
TYPE3 클립보드 코덱 전용 예외 클래스 정의.
"""

class Type3CodecError(Exception):
    """라이브러리 전반에서 발생하는 기본 예외 클래스."""
    pass

class InvalidHexError(Type3CodecError):
    """입력된 Hex 텍스트가 올바르지 않을 때 발생한다."""
    pass

class DecodingError(Type3CodecError):
    """이진 데이터 디코딩 중 오류가 발생할 때 발생한다."""
    pass

class UnsupportedFormatError(DecodingError):
    """지원하지 않는 데이터 포맷인 경우 발생한다."""
    pass
