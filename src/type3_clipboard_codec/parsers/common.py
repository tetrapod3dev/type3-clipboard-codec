from typing import List, Optional
from ..utils.bytes_reader import BytesReader
from ..models.geometry import ObjectHeader, BBox3D, ContourPoint, ContourPayload

def read_object_header(reader: BytesReader) -> ObjectHeader:
    """
    Type3 객체 공통 헤더를 읽는다.
    Format: [marker: u16] [class_id: u16] [name_len: u16] [class_name: ascii]
    """
    marker = reader.read_u16_le()
    class_id = reader.read_u16_le()
    name_len = reader.read_u16_le()
    class_name = reader.read_ascii(name_len)
    
    return ObjectHeader(
        marker=marker,
        class_id=class_id,
        name_len=name_len,
        class_name=class_name
    )

def read_bbox(reader: BytesReader) -> BBox3D:
    """
    6개의 double(f64)로 구성된 3D BBox를 읽는다. (단위: 미터)
    """
    return BBox3D(
        xmin_m=reader.read_f64_le(),
        ymin_m=reader.read_f64_le(),
        zmin_m=reader.read_f64_le(),
        xmax_m=reader.read_f64_le(),
        ymax_m=reader.read_f64_le(),
        zmax_m=reader.read_f64_le()
    )

def read_contour_points(reader: BytesReader, count: int) -> List[ContourPoint]:
    """
    CContour 내의 정점 리스트를 읽는다.
    Format: [x: f64] [y: f64] [z: f64] [w: f64] [tag: u32]
    
    [Reverse-engineering Note]
    Each contour record is exactly 36 bytes:
    - x, y, z, w (8 bytes each, doubles) = 32 bytes
    - tag (4 bytes, uint32) = 4 bytes
    Total = 36 bytes.
    """
    points = []
    for _ in range(count):
        x = reader.read_f64_le()
        y = reader.read_f64_le()
        z = reader.read_f64_le()
        w = reader.read_f64_le()
        tag = reader.read_u32_le()
        points.append(ContourPoint(x_m=x, y_m=y, z_m=z, w=w, tag=tag))
    return points
