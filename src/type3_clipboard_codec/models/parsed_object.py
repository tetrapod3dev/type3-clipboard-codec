from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ParsedObject:
    """
    디코딩된 TYPE3 객체의 기본 정보와 상태를 담는 최상위 모델.
    모든 필드는 향후 수정 및 재인코딩을 위해 가변(Mutable) 상태로 설계한다.
    """
    object_type: str = "unknown"             # 객체 타입 식별자
    raw_size: int = 0                         # 원시 데이터 크기 (바이트 단위)
    raw_data: bytes = b""                     # 분석 전 원시 데이터
    markers: List[str] = field(default_factory=list) # 발견된 주요 ASCII 마커
    candidate_fields: Dict[str, Any] = field(default_factory=dict) # 의미가 확정되지 않은 추정 필드들
    warnings: List[str] = field(default_factory=list) # 파싱 과정에서의 경고 메시지
    notes: List[str] = field(default_factory=list)    # 역공학 분석용 메모

    def summary(self) -> str:
        """객체의 핵심 요약 정보를 문자열로 반환한다."""
        return f"Type: {self.object_type}, Size: {self.raw_size} bytes"
