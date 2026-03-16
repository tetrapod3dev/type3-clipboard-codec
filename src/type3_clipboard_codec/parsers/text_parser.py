from .base import BaseParser
from ..models.text_object import TextObject
from ..utils.bytes_reader import BytesReader
from ..utils.ascii_scan import scan_ascii_strings

class TextParser(BaseParser):
    """
    TYPE3 텍스트 객체를 분석하는 파서.
    Heuristic 방식으로 ASCII 문자열 마커를 찾아 텍스트를 추출한다.
    """
    # 텍스트 객체를 식별하기 위한 주요 마커들 (Heuristic)
    TEXT_MARKERS = ["CParagraph", "CZone"]

    def can_parse(self, reader: BytesReader) -> bool:
        """
        데이터의 시작 부분에서 텍스트 관련 마커가 발견되는지 확인한다.
        """
        pos = reader.tell()
        try:
            # 상위 128바이트 내에서 마커 검색
            header = reader.peek_bytes(min(128, reader.remaining()))
            markers = [s for _, s in scan_ascii_strings(header)]
            return any(m in self.TEXT_MARKERS for m in markers)
        except EOFError:
            return False
        finally:
            reader.seek(pos)

    def parse(self, reader: BytesReader, **kwargs) -> TextObject:
        """
        텍스트 데이터를 추출하여 TextObject를 생성한다.
        """
        start_pos = reader.tell()
        data = reader.read_bytes(reader.remaining())
        
        # Heuristic: 가장 긴 ASCII 문자열을 텍스트 내용으로 추정
        all_strings = scan_ascii_strings(data)
        
    # 마커를 제외한 문자열 중 가장 긴 것 선택
        content_candidates = [s for _, s in all_strings if s not in self.TEXT_MARKERS]
        main_content = ""
        if content_candidates:
            # If multiple candidates have the same maximum length, pick the last one
            # to avoid picking generic headers that might appear before the content.
            max_len = max(len(s) for s in content_candidates)
            best_candidates = [s for s in content_candidates if len(s) == max_len]
            main_content = best_candidates[-1]
            
        return TextObject(
            object_type="text",
            raw_size=len(data),
            raw_data=data,
            markers=[s for _, s in all_strings if s in self.TEXT_MARKERS],
            text_content=main_content,
            notes=["TextParser (Heuristic)에 의해 분석되었습니다. 속성 값은 추정치입니다."]
        )
