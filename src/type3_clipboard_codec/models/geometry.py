from dataclasses import dataclass, field
from typing import List
from .parsed_object import ParsedObject

@dataclass
class Point:
    """좌표를 나타내는 단순 데이터 클래스."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

@dataclass
class GeometryObject(ParsedObject):
    """
    선, 곡선 등 기하학적 형상을 나타내는 모델의 기본 클래스.
    """
    points: List[Point] = field(default_factory=list) # 정점 리스트
    is_closed: bool = False                           # 닫힌 도형 여부
    
    def __post_init__(self):
        self.object_type = "geometry"
