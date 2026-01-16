"""
Find the correct relative address for EasyBot.

EasyBot formula: final_address = base_address + address_read + offsets

We need to find what 'address_read' should be so that:
  base_address + address_read = our_absolute_address

Therefore:
  address_read = our_absolute_address - base_address
"""
import ctypes as c
import win32gui
import win32process
import win32api
import win32con

def find_pokealliance():
    result = []
    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if "PokeAlliance" in title:
            result.append((hwnd, title))
    win32gui.EnumWindows(callback, None)
    return result[0] if result else None

def read_uint(process_handle, address):
    buffer = c.create_string_buffer(4)
    result = c.windll.kernel32.ReadProcessMemory(
        process_handle, c.c_void_p(address), buffer, 4, c.byref(c.c_size_t())
    )
    if result:
        return c.cast(buffer, c.POINTER(c.c_uint)).contents.value
    return None

def main():
    window = find_pokealliance()
    if not window:
        print("PokeAlliance not found!")
        return

    hwnd, title = window
    print(f"Found: {title}")

    _, proc_id = win32process.GetWindowThreadProcessId(hwnd)

    # Get base address
    pywin_handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc_id)
    modules = win32process.EnumProcessModules(pywin_handle)
    base_address = modules[0]
    win32api.CloseHandle(pywin_handle)

    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)

    # Our known working absolute addresses
    ABSOLUTE_ADDRESSES = {
        "LOCAL_PLAYER_STATIC_PTR": 0x015F2CC8,
        "ATTACKING_CREATURE_STATIC_PTR": 0x015F2CD8,
    }

    print(f"\n{'='*60}")
    print(f"Base Address: 0x{base_address:08X}")
    print(f"{'='*60}")

    print(f"\n--- Calculating Relative Addresses for EasyBot ---\n")

    for name, abs_addr in ABSOLUTE_ADDRESSES.items():
        relative = abs_addr - base_address

        # Test if the relative address works
        test_addr = base_address + relative
        ptr_value = read_uint(process_handle, test_addr)

        print(f"{name}:")
        print(f"  Absolute address: 0x{abs_addr:08X}")
        print(f"  Relative address: 0x{relative:08X}")
        print(f"  Test read at base+relative: ", end="")

        if ptr_value is not None:
            print(f"0x{ptr_value:08X} (SUCCESS)")

            # For LOCAL_PLAYER, also test reading position
            if "LOCAL_PLAYER" in name and ptr_value > 0x10000000:
                x = read_uint(process_handle, ptr_value + 0x10)
                y = read_uint(process_handle, ptr_value + 0x14)
                z = read_uint(process_handle, ptr_value + 0x18)
                if x and y:
                    print(f"  -> Position: X={x}, Y={y}, Z={z & 0xFF}")
        else:
            print("FAILED")
        print()

    print(f"{'='*60}")
    print("FOR EASYBOT addresses.json, use these RELATIVE addresses:")
    print(f"{'='*60}")

    for name, abs_addr in ABSOLUTE_ADDRESSES.items():
        relative = abs_addr - base_address
        # EasyBot expects hex string without 0x prefix
        hex_str = f"{relative:08X}"
        print(f'  "{name}": "{hex_str}"')

    print(f"\nNOTE: These relative addresses are calculated for base 0x{base_address:08X}")
    print("If the game restarts and base changes, you'll need to recalculate!")

    # Check if base seems stable (typical ASLR-disabled base is 0x00400000)
    if base_address == 0x00400000:
        print("\n*** Base is 0x00400000 - ASLR appears DISABLED. Addresses should be stable! ***")
    else:
        print(f"\n*** Base is 0x{base_address:08X} - ASLR may be enabled. ***")
        print("*** Restart the game and run this again to check if base changes. ***")

    c.windll.kernel32.CloseHandle(process_handle)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    input("\nPress Enter to exit...")
