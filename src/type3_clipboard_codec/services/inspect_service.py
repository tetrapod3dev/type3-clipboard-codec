from ..adapters.input_base import InputAdapter
from ..codec.decoder import Decoder
from ..codec.preview import PreviewRenderer

class InspectService:
    """
    입력 어댑터, 디코더, 미리보기 기능을 조합하여 분석 서비스를 제공한다.
    """
    def __init__(self):
        self._decoder = Decoder()
        self._renderer = PreviewRenderer()

    def inspect(self, adapter: InputAdapter) -> str:
        """
        어댑터를 통해 데이터를 가져와 분석하고 미리보기 결과를 반환한다.
        """
        # 1. 데이터 수집
        data = adapter.fetch_data()
        
        # 2. 분석 (디코딩)
        parsed_obj = self._decoder.decode_bytes(data)
        
        # 3. 미리보기 결과 생성
        return self._renderer.render(parsed_obj)
