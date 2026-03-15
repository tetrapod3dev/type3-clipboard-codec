import string
from typing import List, Tuple

def scan_ascii_strings(data: bytes, min_length: int = 4) -> List[Tuple[int, str]]:
    """
    이진 데이터에서 출력 가능한 ASCII 문자열 구간을 찾아낸다.
    객체 타입 판별이나 디버깅을 위한 휴리스틱 용도로 사용된다.
    
    :return: (오프셋, 문자열) 리스트
    """
    results = []
    current_start = -1
    current_chars = []
    
    printable = set(string.printable.encode('ascii')) - {b'\x0b', b'\x0c'} # \r, \n, \t 등은 포함
    
    for i, b in enumerate(data):
        if b in printable:
            if current_start == -1:
                current_start = i
            current_chars.append(chr(b))
        else:
            if current_start != -1:
                if len(current_chars) >= min_length:
                    results.append((current_start, "".join(current_chars)))
                current_start = -1
                current_chars = []
                
    # 마지막 데이터 처리
    if current_start != -1 and len(current_chars) >= min_length:
        results.append((current_start, "".join(current_chars)))
        
    return results
