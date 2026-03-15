import re
from ..exceptions import InvalidHexError

def normalize_hex_text(text: str) -> str:
    """
    사용자가 입력한 16진수 문자열에서 불필요한 공백, 줄바꿈, 구분자를 제거한다.
    """
    # 0x 접두어 제거 및 공백/줄바꿈 제거
    clean_text = re.sub(r'[\s,:\-\x00]', '', text.replace('0x', ''))
    return clean_text

def hex_to_bytes(hex_text: str) -> bytes:
    """
    16진수 텍스트를 바이트 배열로 변환한다.
    """
    normalized = normalize_hex_text(hex_text)
    if not normalized:
        return b""
    
    if len(normalized) % 2 != 0:
        raise InvalidHexError("16진수 문자열의 길이가 홀수입니다. 올바른 쌍으로 입력되었는지 확인하십시오.")
    
    try:
        return bytes.fromhex(normalized)
    except ValueError as e:
        raise InvalidHexError(f"16진수 변환 중 오류가 발생했습니다: {e}")
