from dataclasses import dataclass
from .parsed_object import ParsedObject

@dataclass
class TextObject(ParsedObject):
    """
    TYPE3 텍스트 객체를 나타내는 모델.
    텍스트 내용 및 관련 속성을 포함한다.
    """
    text_content: str = ""       # 실제 텍스트 내용
    font_name: str = ""          # 사용된 글꼴 이름 (추정)
    text_options: dict = None    # 텍스트 옵션 (크기, 간격 등)
    
    def __post_init__(self):
        self.object_type = "text"
        if self.text_options is None:
            self.text_options = {}
