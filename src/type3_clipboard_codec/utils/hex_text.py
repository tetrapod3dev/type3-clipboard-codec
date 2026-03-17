import re
from ..exceptions import InvalidHexError

def normalize_hex_text(text: str) -> str:
    """
    사용자가 입력한 16진수 문자열에서 불필요한 공백, 줄바꿈, 구분자를 제거한다.
    """
    # 0x 접두어 제거
    text = text.replace('0x', '')
    # 0x00(널 문자)을 공백처럼 취급하여 제거하지 않고 유지하거나, 
    # 혹은 널 문자 자체를 hex 데이터의 일부가 아닌 구분자로 보고 제거.
    # 현재 regex는 \x00을 포함하여 제거하고 있는데, 
    # 만약 파일이 hex 문자열 사이에 null bytes를 포함하고 있다면 
    # (예: "46 46 00 30 31") 이들을 제거하는 것이 맞다.
    clean_text = re.sub(r'[\s,:\-\x00]', '', text)
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
