from abc import ABC, abstractmethod
from ..models.parsed_object import ParsedObject
from ..utils.bytes_reader import BytesReader

class BaseParser(ABC):
    """
    특정 객체 타입에 대한 파싱 로직을 구현하기 위한 추상 기본 클래스.
    """
    @abstractmethod
    def parse(self, reader: BytesReader, **kwargs) -> ParsedObject:
        """
        이진 데이터를 읽어 모델 객체로 변환한다.
        """
        pass

    @abstractmethod
    def can_parse(self, reader: BytesReader) -> bool:
        """
        해당 파서가 이진 데이터를 처리할 수 있는지 여부를 반환한다. (Heuristic)
        """
        pass
