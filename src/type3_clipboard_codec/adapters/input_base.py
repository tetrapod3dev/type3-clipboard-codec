from abc import ABC, abstractmethod

class InputAdapter(ABC):
    """
    다양한 소스(텍스트, 클립보드, 파일 등)로부터 원시 바이트 데이터를 획득하기 위한 추상 기본 클래스.
    """
    @abstractmethod
    def fetch_data(self) -> bytes:
        """
        입력 소스로부터 원시 바이트 데이터를 가져와 반환한다.
        """
        pass
