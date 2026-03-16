import sys
import os
from type3_clipboard_codec.adapters.manual_hex_input import ManualHexInput
from type3_clipboard_codec.services.inspect_service import InspectService

def main():
    if len(sys.argv) < 2:
        print("Usage: python inspect_file.py <hex_file_path>")
        return

    file_path = sys.argv[1]
    with open(file_path, "r") as f:
        hex_data = f.read().strip()

    service = InspectService()
    adapter = ManualHexInput(hex_data)
    
    result = service.inspect(adapter, verbose=True)
    print(result)

if __name__ == "__main__":
    main()
