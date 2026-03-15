from typing import List, Optional
from .base import BaseParser
from .registry import ParserRegistry
from .text_parser import TextParser
from .unknown_parser import UnknownParser
from ..utils.bytes_reader import BytesReader

class ObjectDetector:
    """
    이진 데이터를 분석하여 적절한 파서를 선택한다.
    Heuristic 방식을 사용하여 객체 타입을 추측한다.
    """
    def __init__(self):
        # 파서 등록 (순서가 중요할 수 있음)
        # 이미 등록되어 있는지 확인하지 않고 초기화 단계에서 추가
        # 실제 운영 환경에서는 앱 초기화 시점에 한 번만 수행하도록 설계
        pass

    def detect_parser(self, reader: BytesReader) -> BaseParser:
        """
        데이터를 검사하여 가장 적합한 파서를 반환한다.
        """
        # 등록된 파서들을 순회하며 처리가능 여부 확인
        for parser in ParserRegistry.get_all_parsers():
            if parser.can_parse(reader):
                return parser
        
        # 일치하는 파서가 없는 경우 UnknownParser 반환
        return UnknownParser()

# 전역 레지스트리에 기본 파서 등록
ParserRegistry.register(TextParser())
