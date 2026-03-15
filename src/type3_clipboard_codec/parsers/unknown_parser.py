from .base import BaseParser
from ..models.parsed_object import ParsedObject
from ..utils.bytes_reader import BytesReader
from ..utils.ascii_scan import scan_ascii_strings

class UnknownParser(BaseParser):
    """
    적절한 전용 파서를 찾지 못했을 때의 기본 파서.
    원시 데이터를 보존하고 ASCII 마커 등 식별 가능한 정보를 추출한다.
    """
    def can_parse(self, reader: BytesReader) -> bool:
        """모든 데이터는 최소한 UnknownParser로 처리 가능하다."""
        return True

    def parse(self, reader: BytesReader, **kwargs) -> ParsedObject:
        """
        원시 데이터를 읽어 기본 ParsedObject를 생성한다.
        """
        start_pos = reader.tell()
        data = reader.read_bytes(reader.remaining())
        
        # ASCII 마커 추출 (휴리스틱)
        found_markers = [s for _, s in scan_ascii_strings(data)]
        
        return ParsedObject(
            object_type="unknown",
            raw_size=len(data),
            raw_data=data,
            markers=found_markers,
            notes=["UnknownParser를 통해 분석되었습니다. 상세 포맷 분석이 필요합니다."]
        )
