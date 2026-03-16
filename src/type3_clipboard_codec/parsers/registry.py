from typing import List

from .base import BaseParser


class ParserRegistry:
    """
    객체 타입별 파서를 등록하고 조회하는 레지스트리.
    """
    _parsers: List[BaseParser] = []

    @classmethod
    def register(cls, parser: BaseParser) -> None:
        """새로운 파서를 레지스트리에 등록한다."""
        cls._parsers.append(parser)

    @classmethod
    def get_all_parsers(cls) -> List[BaseParser]:
        """등록된 모든 파서 목록을 반환한다."""
        return cls._parsers
