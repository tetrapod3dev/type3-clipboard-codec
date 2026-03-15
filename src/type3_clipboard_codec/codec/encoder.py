from ..models.parsed_object import ParsedObject

class Encoder:
    """
    모델 객체를 다시 이진 데이터로 변환하는 클래스 (향후 구현).
    """
    def encode(self, obj: ParsedObject) -> bytes:
        """
        수정된 모델 객체를 TYPE3 이진 포맷으로 인코딩한다.
        현재는 구현되지 않았으며, 추후 확장을 위한 구조만 제공한다.
        """
        raise NotImplementedError("인코딩 기능은 향후 구현될 예정입니다.")
