"""Debug script to test if addresses are reading correctly"""
import ctypes as c
import win32gui
import win32process
import win32api
import win32con

def find_pokealliance():
    """Find PokeAlliance window"""
    result = []
    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if "PokeAlliance" in title:
            result.append((hwnd, title))
    win32gui.EnumWindows(callback, None)
    return result[0] if result else None

def read_uint(process_handle, address):
    """Read 4 bytes as unsigned int"""
    buffer = c.create_string_buffer(4)
    result = c.windll.kernel32.ReadProcessMemory(
        process_handle,
        c.c_void_p(address),
        buffer,
        4,
        c.byref(c.c_size_t())
    )
    if result:
        return c.cast(buffer, c.POINTER(c.c_uint)).contents.value
    return None

def main():
    # Find game window
    window = find_pokealliance()
    if not window:
        print("PokeAlliance not found!")
        return

    hwnd, title = window
    print(f"Found: {title}")

    # Get process info
    _, proc_id = win32process.GetWindowThreadProcessId(hwnd)
    print(f"Process ID: {proc_id}")

    # Get base address using pywin32
    pywin_handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc_id)
    modules = win32process.EnumProcessModules(pywin_handle)
    base_address = modules[0]
    win32api.CloseHandle(pywin_handle)
    print(f"Base Address: 0x{base_address:08X}")

    # Open process for memory reading
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    print(f"Process Handle: {process_handle}")

    # Our addresses (found as absolute addresses when base was likely 0x00400000)
    LOCAL_PLAYER_STATIC_PTR = 0x015F2CC8
    DEFAULT_BASE = 0x00400000  # Standard 32-bit Windows image base

    # Calculate relative offset
    relative_offset = LOCAL_PLAYER_STATIC_PTR - DEFAULT_BASE
    print(f"\n=== Address Calculations ===")
    print(f"Original address (absolute): 0x{LOCAL_PLAYER_STATIC_PTR:08X}")
    print(f"Assumed original base: 0x{DEFAULT_BASE:08X}")
    print(f"Relative offset: 0x{relative_offset:08X}")

    # Method 1: Try as ABSOLUTE address (how our bot uses it)
    print(f"\n=== Method 1: Absolute Address (our bot method) ===")
    ptr_address = LOCAL_PLAYER_STATIC_PTR
    print(f"Reading at: 0x{ptr_address:08X}")
    local_player_ptr = read_uint(process_handle, ptr_address)
    if local_player_ptr:
        print(f"LocalPlayer pointer: 0x{local_player_ptr:08X}")
        test_position(process_handle, local_player_ptr)
    else:
        print("Failed to read (address may be outside process memory)")

    # Method 2: base + relative offset
    print(f"\n=== Method 2: Base + Relative Offset ===")
    ptr_address = base_address + relative_offset
    print(f"Reading at: 0x{ptr_address:08X}")
    local_player_ptr = read_uint(process_handle, ptr_address)
    if local_player_ptr:
        print(f"LocalPlayer pointer: 0x{local_player_ptr:08X}")
        test_position(process_handle, local_player_ptr)
    else:
        print("Failed to read")

    # Method 3: base + original address (EasyBot current method - likely wrong)
    print(f"\n=== Method 3: Base + Original (EasyBot method) ===")
    ptr_address = base_address + LOCAL_PLAYER_STATIC_PTR
    print(f"Reading at: 0x{ptr_address:08X}")
    local_player_ptr = read_uint(process_handle, ptr_address)
    if local_player_ptr:
        print(f"LocalPlayer pointer: 0x{local_player_ptr:08X}")
        test_position(process_handle, local_player_ptr)
    else:
        print("Failed to read (this is expected to fail)")

    c.windll.kernel32.CloseHandle(process_handle)

def test_position(process_handle, player_ptr):
    """Test reading position from player pointer"""
    if not player_ptr or player_ptr < 0x10000000:
        print("Invalid player pointer")
        return

    buffer = c.create_string_buffer(4)
    for name, offset in [("X", 0x10), ("Y", 0x14), ("Z", 0x18)]:
        addr = player_ptr + offset
        result = c.windll.kernel32.ReadProcessMemory(
            process_handle,
            c.c_void_p(addr),
            buffer,
            4,
            c.byref(c.c_size_t())
        )
        if result:
            val = c.cast(buffer, c.POINTER(c.c_int)).contents.value
            if name == "Z":
                val = val & 0xFF
            print(f"  Position {name}: {val}")
        else:
            print(f"  Failed to read {name}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    input("\nPress Enter to exit...")
