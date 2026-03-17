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

def read_contour_points(reader: BytesReader, count: int, stride: int = 36) -> List[ContourPoint]:
    """
    CContour 내의 정점 리스트를 읽는다.
    
    [Reverse-engineering Note]
    - Default stride is 36 bytes (x, y, z, w: 8 bytes each, tag: 4 bytes).
    - Rounded rectangle (default_rounded_rectangle.txt) uses a 44-byte stride.
    - Stride can be passed to skip unknown trailing bytes in each record.
    """
    points = []
    for _ in range(count):
        start_pos = reader.tell()
        x = reader.read_f64_le()
        y = reader.read_f64_le()
        z = reader.read_f64_le()
        w = reader.read_f64_le()
        
        # tag는 4바이트 uint32로 가정
        if reader.remaining() >= 4:
            tag = reader.read_u32_le()
        else:
            tag = 0
            
        points.append(ContourPoint(x_m=x, y_m=y, z_m=z, w=w, tag=tag))
        
        # 다음 레코드로 이동 (stride 적용)
        reader.seek(start_pos + stride)
        
    return points
