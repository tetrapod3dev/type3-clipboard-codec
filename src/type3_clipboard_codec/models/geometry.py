from dataclasses import dataclass, field
from typing import List, Optional
from .parsed_object import ParsedObject


@dataclass
class BBox3D:
    """
    3D 경계 상자(Bounding Box)를 나타내는 모델.
    Type3 클립보드 페이로드에는 미터(m) 단위로 저장된다.
    """
    xmin_m: float = 0.0
    ymin_m: float = 0.0
    zmin_m: float = 0.0
    xmax_m: float = 0.0
    ymax_m: float = 0.0
    zmax_m: float = 0.0

    @property
    def xmin_mm(self) -> float:
        return self.xmin_m * 1000.0

    @property
    def ymin_mm(self) -> float:
        return self.ymin_m * 1000.0

    @property
    def zmin_mm(self) -> float:
        return self.zmin_m * 1000.0

    @property
    def xmax_mm(self) -> float:
        return self.xmax_m * 1000.0

    @property
    def ymax_mm(self) -> float:
        return self.ymax_m * 1000.0

    @property
    def zmax_mm(self) -> float:
        return self.zmax_m * 1000.0

    @property
    def width_m(self) -> float:
        return self.xmax_m - self.xmin_m

    @property
    def height_m(self) -> float:
        return self.ymax_m - self.ymin_m

    @property
    def width_mm(self) -> float:
        return self.width_m * 1000.0

    @property
    def height_mm(self) -> float:
        return self.height_m * 1000.0

    @property
    def depth_m(self) -> float:
        return self.zmax_m - self.zmin_m

    @property
    def depth_mm(self) -> float:
        return self.depth_m * 1000.0

    @property
    def center_m(self) -> Point:
        return Point(
            x=(self.xmin_m + self.xmax_m) / 2.0,
            y=(self.ymin_m + self.ymax_m) / 2.0,
            z=(self.zmin_m + self.zmax_m) / 2.0
        )

    @property
    def center_mm(self) -> Point:
        c = self.center_m
        return Point(x=c.x * 1000.0, y=c.y * 1000.0, z=c.z * 1000.0)

    @property
    def radius_m(self) -> float:
        return self.width_m / 2.0

    @property
    def radius_mm(self) -> float:
        return self.radius_m * 1000.0

    @property
    def diameter_m(self) -> float:
        return self.width_m

    @property
    def diameter_mm(self) -> float:
        return self.diameter_m * 1000.0


@dataclass
class ObjectHeader:
    """
    Type3 객체의 공통 헤더 정보를 나타내는 모델.
    """
    marker: int = 0xFFFF      # 0xFFFF 고정 마커
    class_id: int = 0         # 클래스 식별 아이디
    name_len: int = 0         # 클래스 이름 길이
    class_name: str = ""      # ASCII 클래스 이름


@dataclass
class ContourPoint:
    """
    CContour 내의 정점 정보를 나타내는 모델.
    """
    x_m: float = 0.0
    y_m: float = 0.0
    z_m: float = 0.0
    w: float = 1.0            # 동차 좌표계(Homogeneous coordinates) 가중치로 추정
    tag: int = 0              # 아직 의미가 확정되지 않은 태그 값
    role: str = "unknown"     # "anchor" 또는 "control"

    @property
    def x_mm(self) -> float:
        return self.x_m * 1000.0

    @property
    def y_mm(self) -> float:
        return self.y_m * 1000.0

    @property
    def z_mm(self) -> float:
        return self.z_m * 1000.0


@dataclass
class Type3Node:
    """
    Type3 클립보드 객체 체인의 각 노드를 나타내는 모델.
    여러 클래스가 체인 형태로 연결되므로 이를 구조화한다.
    """
    header: ObjectHeader
    bbox: Optional[BBox3D] = None
    payload: bytes = b""
    children: List["Type3Node"] = field(default_factory=list)


@dataclass
class ContourPayload:
    """
    CContour 객체의 페이로드 데이터를 구조화한 모델.
    """
    point_count: int = 0
    points: List[ContourPoint] = field(default_factory=list)


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
    contour_records: List[ContourPoint] = field(default_factory=list) # 원시 컨투어 레코드 리스트
    is_closed: bool = False                           # 닫힌 도형 여부
    bbox: Optional[BBox3D] = None                     # 경계 상자 정보

    @property
    def anchor_records(self) -> List[ContourPoint]:
        """앵커 포인트 리스트 반환."""
        return [r for r in self.contour_records if r.role == "anchor"]

    @property
    def control_records(self) -> List[ContourPoint]:
        """제어 포인트 리스트 반환."""
        return [r for r in self.contour_records if r.role == "control"]

    @property
    def start_anchor(self) -> Optional[ContourPoint]:
        """시작 앵커 포인트 반환."""
        anchors = self.anchor_records
        return anchors[0] if anchors else None

    @property
    def end_anchor(self) -> Optional[ContourPoint]:
        """종료 앵커 포인트 반환."""
        anchors = self.anchor_records
        return anchors[-1] if anchors else None

    def __post_init__(self):
        self.object_type = "geometry"
