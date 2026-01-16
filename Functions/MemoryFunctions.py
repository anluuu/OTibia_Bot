import win32api
import win32con
import win32security
import Addresses
import ctypes as c
import struct

# Structure for VirtualQueryEx
class MEMORY_BASIC_INFORMATION(c.Structure):
    _fields_ = [
        ("BaseAddress", c.c_void_p),
        ("AllocationBase", c.c_void_p),
        ("AllocationProtect", c.c_uint32),
        ("RegionSize", c.c_size_t),
        ("State", c.c_uint32),
        ("Protect", c.c_uint32),
        ("Type", c.c_uint32),
    ]



# Writes a 4-byte value to memory
def write_memory_address(address_write, value):
    """Write a 4-byte integer to the specified address (relative to base)."""
    try:
        address = c.c_void_p(Addresses.base_address + address_write)
        buffer = c.c_uint(value)
        bytes_written = c.c_size_t()
        result = c.windll.kernel32.WriteProcessMemory(
            Addresses.process_handle, address, c.byref(buffer), 4, c.byref(bytes_written)
        )
        return result != 0
    except Exception as e:
        print(f'Write Memory Exception: {e}')
        return False


def set_attack_target(creature_address):
    """
    Set the attack target by writing creature pointer to attack address.
    creature_address should be the absolute address of the creature object.
    """
    if not Addresses.attack_address:
        return False
    return write_memory_address(Addresses.attack_address, creature_address)


# Reads value from memory
def read_memory_address(address_read, offsets, option):
    try:
        address = c.c_void_p(Addresses.base_address + address_read + offsets)
        if option < 6:
            buffer_size = int(Addresses.application_architecture/8)
        else:
            buffer_size = 32
        buffer = c.create_string_buffer(buffer_size)
        result = c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, address, buffer, buffer_size, c.byref(c.c_size_t()))
        if not result:
            return None
        match option:
            case 1:
                return c.cast(buffer, c.POINTER(c.c_byte)).contents.value
            case 2:
                return c.cast(buffer, c.POINTER(c.c_short)).contents.value
            case 3:
                return c.cast(buffer, c.POINTER(c.c_int)).contents.value
            case 4:
                return c.cast(buffer, c.POINTER(c.c_ulonglong)).contents.value
            case 5:
                return c.cast(buffer, c.POINTER(c.c_double)).contents.value
            case 6:
                try:
                    decoded_value = buffer.value.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case 7:
                try:
                    decoded_value = buffer.raw.decode('utf-16').split('\x00')[0]
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case _:
                return bytes(buffer)
    except Exception as e:
        print('Memory Exception:', e)
        return None


def read_pointer_address(address_read, offsets, option):
    try:
        address = c.c_void_p(Addresses.base_address + address_read)
        if option == 6 or option == 7:
            buffer_size = 64
        else:
            buffer_size = int(Addresses.application_architecture/8)
        buffer = c.create_string_buffer(buffer_size)
        for offset in offsets:
            result = c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, address, buffer, buffer_size, c.byref(c.c_size_t()))
            if not result:
                return None
            if buffer_size == 4:
                address = c.c_void_p(c.cast(buffer, c.POINTER(c.c_int)).contents.value + offset)
            else:
                address = c.c_void_p(c.cast(buffer, c.POINTER(c.c_longlong)).contents.value + offset)
        result = c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, address, buffer, buffer_size, c.byref(c.c_size_t()))
        if not result:
            return None
        match option:
            case 1:
                return c.cast(buffer, c.POINTER(c.c_byte)).contents.value
            case 2:
                return c.cast(buffer, c.POINTER(c.c_short)).contents.value
            case 3:
                return c.cast(buffer, c.POINTER(c.c_int)).contents.value
            case 4:
                return c.cast(buffer, c.POINTER(c.c_ulonglong)).contents.value
            case 5:
                return c.cast(buffer, c.POINTER(c.c_double)).contents.value
            case 6:
                try:
                    decoded_value = buffer.value.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case 7:
                try:
                    decoded_value = buffer.raw.decode('utf-16').split('\x00')[0]
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case _:
                return bytes(buffer)
    except Exception as e:
        print('Pointer Exception:', e)
        return None


def read_targeting_status():
    if Addresses.attack_address_offset == [-1]:
        # Case where Attack Address holds the ID directly
        attack_id = read_memory_address(Addresses.attack_address, 0, Addresses.my_attack_type)
        return attack_id if attack_id and attack_id > 0 else 0
    else:
        # Standard pointer case
        attack = read_pointer_address(Addresses.attack_address, Addresses.attack_address_offset, Addresses.my_attack_type)
        return attack


def read_my_stats():
    current_hp = read_pointer_address(Addresses.my_stats_address, Addresses.my_hp_offset, Addresses.my_hp_type)
    current_max_hp = read_pointer_address(Addresses.my_stats_address, Addresses.my_hp_max_offset, Addresses.my_hp_type)
    current_mp = read_pointer_address(Addresses.my_stats_address, Addresses.my_mp_offset, Addresses.my_mp_type)
    current_max_mp = read_pointer_address(Addresses.my_stats_address, Addresses.my_mp_max_offset, Addresses.my_mp_type)
    return current_hp, current_max_hp, current_mp, current_max_mp


def read_my_wpt():
    x = read_pointer_address(Addresses.my_x_address, Addresses.my_x_address_offset, Addresses.my_x_type)
    y = read_pointer_address(Addresses.my_y_address, Addresses.my_y_address_offset, Addresses.my_y_type)
    z = read_pointer_address(Addresses.my_z_address, Addresses.my_z_address_offset, Addresses.my_z_type)
    return x, y, z


def read_target_info():
    if Addresses.attack_address_offset == [-1]:
        # Scan for ID mode
        target_id = read_memory_address(Addresses.attack_address, 0, Addresses.my_attack_type)
        if target_id and target_id > 0:
            exclude_addr = Addresses.base_address + Addresses.attack_address
            absolute_address = scan_memory_for_value(target_id, exclude_address=exclude_addr)
            if absolute_address is not None:
                # We need an offset that when added to base_address gives absolute_address
                # read_memory_address uses: base_address + address_read + offsets
                attack_address = absolute_address - Addresses.base_address
            else:
                 return 0, 0, 0, "", 0
        else:
             return 0, 0, 0, "", 0
    else:
        # Standard pointer case
        attack_address = read_memory_address(Addresses.attack_address, 0, Addresses.my_attack_type) - Addresses.base_address

    target_x = read_memory_address(attack_address, Addresses.target_x_offset, Addresses.target_x_type)
    target_y = read_memory_address(attack_address, Addresses.target_y_offset, Addresses.target_y_type)
    target_z = read_memory_address(attack_address, Addresses.target_z_offset, Addresses.target_z_type)
    target_name = read_memory_address(attack_address, Addresses.target_name_offset, Addresses.target_name_type)
    target_hp = read_memory_address(attack_address, Addresses.target_hp_offset, Addresses.target_hp_type)
    return target_x, target_y, target_z, target_name, target_hp


def scan_memory_for_value(value, exclude_address=None):
    """
    Scans the process memory for a specific 4-byte integer value.
    Iterates through all committed memory pages.
    Returns the ABSOLUTE address if found, else None.
    """
    try:
        current_address = 0
        mbi = MEMORY_BASIC_INFORMATION()
        value_bytes = struct.pack("I", value & 0xFFFFFFFF)
        
        # Determine scan limit based on architecture
        max_address = 0x7FFFFFFF if Addresses.application_architecture == 32 else 0x7FFFFFFFFFFF
        
        while current_address < max_address:
            # Query memory region
            if not c.windll.kernel32.VirtualQueryEx(Addresses.process_handle, c.c_void_p(current_address), c.byref(mbi), c.sizeof(mbi)):
                break
            
            # Check if region is COMMITTED and not NOACCESS or GUARD
            if mbi.State == 0x1000 and not (mbi.Protect & (0x100 | 0x01)):
                region_size = mbi.RegionSize
                if region_size < 100 * 1024 * 1024: # 100MB limit
                    buffer = c.create_string_buffer(region_size)
                    bytes_read = c.c_size_t()
                    
                    if c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, mbi.BaseAddress, buffer, region_size, c.byref(bytes_read)):
                        data = buffer.raw[:bytes_read.value]
                        
                        search_start = 0
                        while True:
                            found_index = data.find(value_bytes, search_start)
                            if found_index == -1:
                                break
                            
                            absolute_found = current_address + found_index
                            if exclude_address is not None and absolute_found == exclude_address:
                                # Skip this one and keep looking in the same region
                                search_start = found_index + 1
                                continue
                                
                            return absolute_found
            
            # Move to the start of the next region
            current_address += mbi.RegionSize
            
        return None
        
    except Exception as e:
        print(f"Error scanning memory: {e}")


def enable_debug_privilege_pywin32():
    try:
        hToken = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(),
            win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
        )
        privilege_id = win32security.LookupPrivilegeValue(None, win32security.SE_DEBUG_NAME)
        win32security.AdjustTokenPrivileges(hToken, False, [(privilege_id, win32con.SE_PRIVILEGE_ENABLED)])
        return True
    except Exception as e:
        print("Error:", e)
        return False


# =============================================================================
# CREATURE SCANNING FUNCTIONS (for memory-based targeting)
# =============================================================================

def read_uint_at(address):
    """Read a 4-byte unsigned integer at an absolute address."""
    try:
        buffer = c.create_string_buffer(4)
        result = c.windll.kernel32.ReadProcessMemory(
            Addresses.process_handle, c.c_void_p(address), buffer, 4, c.byref(c.c_size_t())
        )
        if result:
            return c.cast(buffer, c.POINTER(c.c_uint)).contents.value
        return None
    except:
        return None


def read_byte_at(address):
    """Read a single byte at an absolute address."""
    try:
        buffer = c.create_string_buffer(1)
        result = c.windll.kernel32.ReadProcessMemory(
            Addresses.process_handle, c.c_void_p(address), buffer, 1, c.byref(c.c_size_t())
        )
        if result:
            return c.cast(buffer, c.POINTER(c.c_ubyte)).contents.value
        return None
    except:
        return None


def read_bytes_at(address, size):
    """Read raw bytes at an absolute address."""
    try:
        buffer = c.create_string_buffer(size)
        result = c.windll.kernel32.ReadProcessMemory(
            Addresses.process_handle, c.c_void_p(address), buffer, size, c.byref(c.c_size_t())
        )
        if result:
            return buffer.raw
        return None
    except:
        return None


def read_msvc_string(address, max_len=64):
    """
    Read MSVC std::string from memory.

    MSVC std::string layout:
      +0x00: union { char buf[16]; char* ptr; }  - inline buffer or heap pointer
      +0x10: size_t size
      +0x14: size_t capacity

    If capacity < 16, string is stored inline in the first 16 bytes.
    Otherwise, first 4 bytes are a pointer to heap-allocated string.
    """
    try:
        size = read_uint_at(address + 0x10)
        capacity = read_uint_at(address + 0x14)

        if size is None or capacity is None:
            return None
        if size == 0 or size > max_len:
            return None

        if capacity < 16:
            # String is stored inline
            data = read_bytes_at(address, size)
        else:
            # String is on heap, first 4 bytes are pointer
            ptr = read_uint_at(address)
            if ptr is None or ptr < 0x10000000 or ptr > 0x60000000:
                return None
            data = read_bytes_at(ptr, size)

        if not data:
            return None

        text = data.decode('utf-8', errors='replace').rstrip('\x00')
        # Validate it's a reasonable string
        if text and all(c.isprintable() or c in ' \t\n' for c in text):
            return text
        return None
    except:
        return None


def read_creature_at(creature_ptr):
    """
    Read creature data from a memory pointer.

    Returns dict with creature info or None if invalid.
    """
    if not creature_ptr or creature_ptr < 0x10000000 or creature_ptr > 0x60000000:
        return None

    try:
        # Read vtable to verify it's a creature
        vtable = read_uint_at(creature_ptr)
        valid_vtables = [
            Addresses.CREATURE_VTABLE_MONSTER,
            Addresses.CREATURE_VTABLE_PLAYER,
            Addresses.CREATURE_VTABLE_NPC
        ]
        if vtable not in valid_vtables:
            return None

        # Read position
        x = read_uint_at(creature_ptr + Addresses.CREATURE_OFFSET_POSITION_X)
        y = read_uint_at(creature_ptr + Addresses.CREATURE_OFFSET_POSITION_Y)
        z_raw = read_uint_at(creature_ptr + Addresses.CREATURE_OFFSET_POSITION_Z)

        if x is None or y is None or z_raw is None:
            return None

        z = z_raw & 0xFF

        # Validate position
        if not (100 <= x <= 65000 and 100 <= y <= 65000 and 0 <= z <= 15):
            return None

        # Read creature ID
        creature_id = read_uint_at(creature_ptr + Addresses.CREATURE_OFFSET_ID)
        if not creature_id:
            return None

        # Read name
        name = read_msvc_string(creature_ptr + Addresses.CREATURE_OFFSET_NAME)
        if not name:
            return None

        # Read HP percent
        hp_percent = read_byte_at(creature_ptr + Addresses.CREATURE_OFFSET_HP_PERCENT)
        if hp_percent is None or hp_percent > 100:
            hp_percent = 100

        # Determine type
        if vtable == Addresses.CREATURE_VTABLE_PLAYER:
            creature_type = "player"
        elif vtable == Addresses.CREATURE_VTABLE_NPC:
            creature_type = "npc"
        else:
            creature_type = "monster"

        return {
            "address": creature_ptr,
            "id": creature_id,
            "name": name,
            "x": x,
            "y": y,
            "z": z,
            "hp_percent": hp_percent,
            "type": creature_type
        }
    except Exception as e:
        return None


def scan_creatures_vtable():
    """
    Scan memory for creatures by looking for vtable patterns.
    This is slower but doesn't require hash map address.

    Returns list of creature dicts.
    """
    creatures = []
    vtables = [
        Addresses.CREATURE_VTABLE_MONSTER,
        Addresses.CREATURE_VTABLE_PLAYER,
        Addresses.CREATURE_VTABLE_NPC
    ]

    try:
        current_address = 0x10000000
        max_address = 0x50000000
        mbi = MEMORY_BASIC_INFORMATION()

        while current_address < max_address:
            if not c.windll.kernel32.VirtualQueryEx(
                Addresses.process_handle, c.c_void_p(current_address),
                c.byref(mbi), c.sizeof(mbi)
            ):
                break

            # Check if region is readable
            if mbi.State == 0x1000 and mbi.Protect in (0x04, 0x02, 0x20, 0x40):
                region_size = mbi.RegionSize
                if region_size < 0x1000000:  # Skip regions > 16MB
                    buffer = c.create_string_buffer(region_size)
                    bytes_read = c.c_size_t()

                    if c.windll.kernel32.ReadProcessMemory(
                        Addresses.process_handle, mbi.BaseAddress,
                        buffer, region_size, c.byref(bytes_read)
                    ):
                        data = buffer.raw[:bytes_read.value]

                        for vtable in vtables:
                            vtable_bytes = struct.pack('<I', vtable)
                            idx = 0
                            while True:
                                idx = data.find(vtable_bytes, idx)
                                if idx == -1:
                                    break

                                addr = current_address + idx
                                creature = read_creature_at(addr)
                                if creature:
                                    # Avoid duplicates by ID
                                    if not any(c["id"] == creature["id"] for c in creatures):
                                        creatures.append(creature)

                                idx += 4

            current_address += mbi.RegionSize
            if current_address <= mbi.BaseAddress:
                current_address = mbi.BaseAddress + 0x1000

    except Exception as e:
        print(f"Error scanning creatures: {e}")

    return creatures


def scan_creatures():
    """
    Scan for all nearby creatures.
    Uses vtable scanning method.

    Returns list of creature dicts with: address, id, name, x, y, z, hp_percent, type
    """
    return scan_creatures_vtable()


def get_creatures_by_name(target_names, same_floor=True):
    """
    Find creatures matching any of the target names.

    Args:
        target_names: List of creature names to search for (case-insensitive)
        same_floor: If True, only return creatures on the same floor as player

    Returns:
        List of matching creature dicts, sorted by distance to player
    """
    creatures = scan_creatures()

    if not creatures:
        return []

    # Get player position
    my_x, my_y, my_z = read_my_wpt()
    if my_x is None:
        return []

    # Normalize target names
    target_names_lower = [name.lower() for name in target_names]

    # Filter creatures
    matches = []
    for creature in creatures:
        # Skip dead creatures
        if creature["hp_percent"] == 0:
            continue

        # Check floor
        if same_floor and creature["z"] != my_z:
            continue

        # Check name match (or wildcard *)
        creature_name_lower = creature["name"].lower()
        if "*" in target_names or creature_name_lower in target_names_lower:
            # Calculate distance
            dist = abs(creature["x"] - my_x) + abs(creature["y"] - my_y)
            creature["distance"] = dist
            matches.append(creature)

    # Sort by distance
    matches.sort(key=lambda c: c["distance"])

    return matches
