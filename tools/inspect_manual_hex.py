import sys
from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.services.inspect_service import InspectService
from type3_clipboard_codec.exceptions import Type3CodecError

def main():
    """
    수동으로 입력된 Hex 텍스트를 분석하는 CLI 도구.
    """
    # 간단한 verbose 모드 지원
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("=" * 60)
    print("TYPE3 Clipboard Manual Hex Inspector")
    if verbose:
        print("Mode: Verbose")
    print("=" * 60)
    print("분석할 Hex 텍스트를 입력하세요 (0x 접두어 및 공백은 무시됨).")
    print("입력을 마치려면 빈 줄을 입력하십시오.")
    print("-" * 60)

    input_lines = []
    while True:
        try:
            line = input("> ").strip()
            if not line:
                break
            input_lines.append(line)
        except EOFError:
            break

    full_hex = "".join(input_lines)
    if not full_hex:
        print("입력된 데이터가 없습니다.")
        return

    try:
        # 서비스 인스턴스 생성 및 분석 수행
        service = InspectService()
        adapter = ManualHexInput(full_hex)
        
        result = service.inspect(adapter, verbose=verbose)
        
        print("\n분석 결과:")
        print(result)
        
    except Type3CodecError as e:
        print(f"\n[오류] 데이터 분석 중 오류가 발생했습니다: {e}")
    except Exception as e:
        print(f"\n[알 수 없는 오류] 예상치 못한 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
