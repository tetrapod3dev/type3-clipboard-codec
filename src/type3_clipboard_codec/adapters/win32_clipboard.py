from .input_base import InputAdapter

class Win32ClipboardAdapter(InputAdapter):
    """
    Windows Win32 API를 사용하여 클립보드 데이터를 직접 가져오는 어댑터 (향후 구현).
    """
    def fetch_data(self) -> bytes:
        """
        Windows 클립보드에서 특정 포맷의 데이터를 가져온다.
        현재는 구현되지 않았으며, 추후 확장을 위한 스텁(Stub)이다.
        """
        raise NotImplementedError("Windows 클립보드 연동은 향후 지원될 예정입니다.")
