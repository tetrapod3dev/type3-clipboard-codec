from ..models.parsed_object import ParsedObject
from ..parsers.object_detector import ObjectDetector
from ..utils.bytes_reader import BytesReader
from ..utils.hex_text import hex_to_bytes

class Decoder:
    """
    이진 데이터를 정형화된 모델로 변환하는 메인 디코더 클래스.
    """
    def __init__(self):
        self._detector = ObjectDetector()

    def decode_bytes(self, data: bytes) -> ParsedObject:
        """
        바이트 데이터를 분석하여 적절한 모델 객체로 변환한다.
        """
        reader = BytesReader(data)
        
        # 1. 객체 타입 감지
        parser = self._detector.detect_parser(reader)
        
        # 2. 파싱 수행
        return parser.parse(reader)

    def decode_hex_text(self, hex_text: str) -> ParsedObject:
        """
        16진수 텍스트를 입력받아 분석을 수행한다.
        """
        data = hex_to_bytes(hex_text)
        return self.decode_bytes(data)
