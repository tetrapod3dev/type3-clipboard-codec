from ..models.parsed_object import ParsedObject
from ..models.text_object import TextObject

class PreviewRenderer:
    """
    디코딩된 결과를 CLI에 보기 좋게 출력하는 렌더러.
    """
    def render(self, obj: ParsedObject) -> str:
        """
        모델의 정보를 한국어로 요약하여 문자열로 반환한다.
        """
        lines = []
        lines.append("-" * 50)
        lines.append(f"[객체 정보 요약]")
        lines.append(f"- 객체 유형: {obj.object_type}")
        lines.append(f"- 데이터 크기: {obj.raw_size} bytes")
        
        if obj.markers:
            lines.append(f"- 발견된 마커: {', '.join(obj.markers)}")
            
        if isinstance(obj, TextObject):
            lines.append(f"- 텍스트 내용: {obj.text_content}")
            
        if obj.candidate_fields:
            lines.append(f"- 추정 필드: {obj.candidate_fields}")
            
        if obj.warnings:
            lines.append(f"[경고 메시지]")
            for w in obj.warnings:
                lines.append(f"  ! {w}")
                
        if obj.notes:
            lines.append(f"[분석 메모]")
            for n in obj.notes:
                lines.append(f"  * {n}")
                
        lines.append("-" * 50)
        return "\n".join(lines)
