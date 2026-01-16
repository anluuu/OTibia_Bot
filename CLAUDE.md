# CLAUDE.md - OTibia Bot (EasyBot)

## Project Overview

This is an external game automation bot for Tibia and Open Tibia Servers (OTS). It operates by reading process memory and analyzing game screenshots, allowing it to work with minimized windows without interfering with other activities.

**Key characteristics:**
- External bot (no injection) using Windows API for memory reading
- Works on any Tibia/OTS client with proper memory addresses configured
- Supports multiple simultaneous bot instances
- Low CPU/RAM consumption
- Randomized behaviors to avoid detection

## Quick Start

```bash
# Install dependencies (Python 3.10.0 required)
python -m pip install -r requirements.txt

# Run the bot
python StartBot.py

# Build executable
pyinstaller --onefile --noconsole StartBot.py --name="EasyBot" --icon="Images/Icon.jpg"
```

**Tesseract OCR** must be installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` for text recognition features.

## Project Structure

```
OTibia_Bot/
├── StartBot.py              # Entry point - initializes app and shows process selector
├── Addresses.py             # Global state: memory addresses, game handles, coordinates, UI theme
├── requirements.txt         # PyQt5, pywin32, opencv-python, pytesseract, numpy, pillow, psutil
│
├── Functions/               # Core utility modules
│   ├── MemoryFunctions.py   # Memory reading/writing, pointer resolution, memory scanning
│   ├── GeneralFunctions.py  # Window capture, image processing, profile save/load
│   ├── KeyboardFunctions.py # Keyboard input via PostMessage (works minimized)
│   ├── MouseFunctions.py    # Mouse operations via Windows API
│   └── PathfindingFunctions.py  # A* algorithm for movement
│
├── General/                 # Application shell
│   ├── SelectTibiaTab.py    # Process selection window (lists running processes)
│   └── MainWindowTab.py     # Main tabbed interface with feature buttons
│
├── Settings/                # Calibration system
│   ├── SettingsTab.py       # Coordinate picker UI (character, loot area, backpacks, runes)
│   ├── SettingsThread.py    # Settings worker thread
│   └── SelectionOverlay.py  # Visual overlay for coordinate selection
│
├── Target/                  # Combat/Targeting
│   ├── TargetTab.py         # Target configuration UI
│   ├── TargetThread.py      # Combat automation
│   ├── TargetLootTab.py     # Combined targeting + looting UI
│   └── TargetLootThread.py  # Combined worker thread
│
├── Walker/                  # Movement/Waypoints
│   ├── WalkerTab.py         # Path recording UI
│   └── WalkerThread.py      # PathfindingThread + RecordThread
│
├── Looting/                 # Loot collection
│   ├── LootingTab.py        # Loot priority configuration
│   └── LootingThread.py     # Automated collection with OpenCV template matching
│
├── HealAttack/              # Health/Combat automation
│   ├── HealingAttackTab.py  # Healing thresholds UI
│   └── HealingAttackThread.py  # HealThread + AttackThread
│
├── Spell/                   # Spell casting
│   ├── SpellTab.py          # Spell configuration
│   └── SpellThread.py       # Timed spell automation
│
├── Hotkeys/                 # Standard hotkeys
│   ├── HotkeysTab.py        # Hotkey binding UI
│   └── HotkeysThread.py     # Hotkey listener/executor
│
├── SmartHotkeys/            # 7.4-compatible hotkeys
│   ├── SmartHotkeysTab.py   # Smart hotkey UI
│   └── SmartHotkeysThread.py  # Works on servers without native hotkeys
│
├── Training/                # Skill training
│   ├── TrainingTab.py       # Training mode UI
│   └── TrainingThread.py    # Click/fish/AFK training
│
├── Images/                  # Asset storage
│   └── {ClientName}/        # Per-client item images, Background.png
│
└── Save/                    # User configuration (JSON)
    ├── Settings/addresses.json  # Memory addresses per client
    ├── Targeting/           # Saved target lists
    ├── Waypoints/           # Recorded paths
    ├── HealingAttack/       # Healing configs
    ├── SmartHotkeys/        # Smart hotkey bindings
    └── Hotkeys/             # Hotkey configs
```

## Architecture Patterns

### Tab-Thread Pattern
Every feature follows a consistent design:
- **Tab class** (QWidget): Handles UI, creates/controls the worker thread
- **Thread class** (QThread): Background operations, emits signals for state changes

```python
# Example: TargetTab creates and controls TargetThread
class TargetTab(QWidget):
    def __init__(self):
        self.target_thread = TargetThread()
        self.target_thread.start()
```

### Global State via Addresses.py
All configuration, memory handles, and coordinates are stored in `Addresses.py` as module-level globals:
- `Addresses.process_handle` - Handle to game process
- `Addresses.base_address` - Process base address for memory offsets
- `Addresses.game` - Window handle (HWND)
- `Addresses.coordinates_x/y` - Screen coordinate arrays
- `Addresses.item_list` - Loaded item images for template matching

### Memory Reading
Two patterns for reading game memory:

```python
# Direct address (base + address + offset)
read_memory_address(address, offset, type_code)

# Pointer chain (follows pointer chain then reads)
read_pointer_address(address, [offset1, offset2, ...], type_code)

# Type codes: 1=Byte, 2=Short, 3=Int, 4=Long, 5=Double, 6=String, 7=Unicode
```

### Thread Locks
Use `Addresses.walker_Lock` and `Addresses.attack_Lock` when accessing shared state:

```python
with Addresses.walker_Lock:
    # Thread-safe walker operations
```

### Input Delivery
Uses `PostMessage()` for non-blocking input that works with minimized windows:

```python
# Keyboard via PostMessage (doesn't require window focus)
win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, key_code, lParam)
```

## Key Technical Details

### Memory Address Configuration
Addresses are loaded from `Save/Settings/addresses.json`:
```json
{
  "game_config": {
    "square_size": 75,
    "architecture": "32",
    "collect_threshold": 0.95
  },
  "my_x": {"address": "0x12345", "offset": "0x10,0x20", "type": "Int"},
  "my_hp": {"address": "0x12345", "offset": "0x30", "type": "Short"}
}
```

### Image Processing Pipeline
1. `WindowCapture.get_screenshot()` - Captures game window region
2. OpenCV processing (resize, blur, grayscale)
3. Template matching or OCR (pytesseract)
4. Coordinate extraction

### Coordinate System
- 3D world coordinates (x, y, z) from memory
- Screen coordinates stored in `Addresses.coordinates_x/y` arrays (12 positions max)
- Distance: `sqrt((x1-x2)^2 + (y1-y2)^2)`

## Common Development Tasks

### Adding a New Feature
1. Create `{Feature}/` directory
2. Create `{Feature}Tab.py` (QWidget) for UI
3. Create `{Feature}Thread.py` (QThread) for logic
4. Add button in `General/MainWindowTab.py`
5. Add save directory in `StartBot.py` if needed

### Reading New Memory Values
1. Find address using Cheat Engine
2. Add to `Save/Settings/addresses.json`
3. Create reader function in `Functions/MemoryFunctions.py`
4. Access via `Addresses.py` globals

### Adding Item Recognition
1. Add item image to `Images/{ClientName}/{ItemName}.png`
2. Item will be loaded via `load_items_images()` in `GeneralFunctions.py`
3. Looting uses OpenCV template matching with configurable threshold

## Dependencies

| Package | Purpose |
|---------|---------|
| PyQt5 | Desktop GUI framework |
| pywin32 | Windows API (memory, windows, input) |
| opencv-python | Image processing, template matching |
| pytesseract | OCR for battle list text recognition |
| numpy | Image array operations |
| pillow | Image loading/manipulation |
| psutil | Process information |
| requests/beautifulsoup4 | Web scraping (item images from wiki) |

## Important Constraints

- **Windows-only**: Requires win32 API extensively
- **Python 3.10+**: Uses match/case statements
- **Tesseract required**: Must be installed for OCR features
- **Per-client setup**: Memory addresses must be configured per game version
- **No tests**: Manual verification required
- **Global state**: Heavy use of module-level globals in `Addresses.py`

## Debugging Tips

- Check `Addresses.process_handle` is valid after connecting
- Verify memory addresses match game version
- Print statements go to console (use `--noconsole` flag sparingly during dev)
- Thread exceptions may be silent - add try/except with prints
- Image matching sensitive to game resolution/scaling

## File Naming Conventions

- Tab files: `{Feature}Tab.py`
- Thread files: `{Feature}Thread.py`
- Functions are module-level, not classes (except WindowCapture)
- JSON for all configuration persistence
- PNG for item images (32x32, with Background.png for empty slot detection)

## Known Issues & Technical Debt

### Critical Issues

| Issue | Location | Description |
|-------|----------|-------------|
| **Global Mutable State** | `Addresses.py:28-95` | Extensive use of global variables for process handles, coordinates, and configuration. Creates potential race conditions between threads. |
| **Missing Input Validation** | `MemoryFunctions.py:23-61` | Memory addresses read without bounds checking; `option` parameter not validated against allowed values (1-7). |
| **Unsafe Lock Release** | `TargetThread.py:59-60` | `walker_Lock.release()` called after checking `locked()` but without ownership verification - may raise `RuntimeError` if another thread releases first. |

### Code Quality Issues

| Issue | Location | Description |
|-------|----------|-------------|
| **Code Duplication** | `MemoryFunctions.py:23-110` | `read_memory_address` and `read_pointer_address` share ~70% identical code (type handling match statements). Consider extracting to helper. |
| **Magic Numbers** | `KeyboardFunctions.py:16-25` | Hardcoded hex values `0X00480001`, `0x00500001` for key codes without constants or documentation. |
| **Long Methods** | `TargetThread.py:36-154` | `run()` method is 118 lines with nested while loops. Should be split into `_attack_target()`, `_handle_looting()`, etc. |
| **Bare Exception Handling** | Multiple files | Generic `except Exception as e: print(e)` loses stack traces and makes debugging difficult. |
| **Dead Code** | `SettingsTab.py:134-138` | `set_tools()` marked as deprecated but still present. |
| **Inconsistent Naming** | Multiple files | Mix of `snake_case` and `camelCase`: `chaseDiagonal_monster` vs `chase_monster`. |

### Recommended Lock Pattern

```python
# Current (unsafe):
if walker_Lock.locked():
    walker_Lock.release()

# Recommended (use context manager or track ownership):
class OwnedLock:
    def __init__(self):
        self._lock = threading.Lock()
        self._owner = None

    def acquire(self, owner_id):
        self._lock.acquire()
        self._owner = owner_id

    def release(self, owner_id):
        if self._owner == owner_id:
            self._owner = None
            self._lock.release()
```

## Performance Considerations

### Identified Bottlenecks

| Severity | Location | Issue | Recommendation |
|----------|----------|-------|----------------|
| **HIGH** | `LootingThread.py:70-73` | Screenshot captured inside template loop - recaptured for every item template. | Move `capture_screen.get_screenshot()` outside the item loop. |
| **HIGH** | `MemoryFunctions.py:166-216` | `scan_memory_for_value()` linearly scans up to 100MB per memory region with no caching. | Add result caching or limit scan frequency. |
| **MEDIUM** | `LootingThread.py:73-77` | Uses `cv.INTER_CUBIC` for resize which is expensive. | Use `cv.INTER_LINEAR` for real-time processing. |
| **MEDIUM** | `TargetThread.py:163-214` | OCR (`pytesseract.image_to_data`) called on every battle list scan cycle. | Cache OCR results for ~500ms or use simpler pixel-based detection. |
| **LOW** | `PathfindingFunctions.py:71-136` | A* creates new tuple objects for every neighbor, causing GC pressure. | Pre-allocate neighbor list or use numpy arrays. |

### Resource Usage

```
Memory per screenshot: ~3-5 MB (depends on game resolution)
Template matching: O(W*H*w*h) where W,H=screenshot, w,h=template
Memory scan: Up to 100 MB buffer per region
OCR processing: ~50-200ms per call (single-threaded, blocks GIL)
```

### Optimization: Screenshot Caching Example

```python
# In LootingThread.py - capture once per cycle
def process_looting(self, capture_screen):
    screenshot = capture_screen.get_screenshot()  # Move outside loop
    screenshot = cv.cvtColor(screenshot, cv.COLOR_BGR2GRAY)
    screenshot = cv.GaussianBlur(screenshot, (7, 7), 0)
    screenshot = cv.resize(screenshot, None, fx=3, fy=3, interpolation=cv.INTER_LINEAR)

    for image_path, data in self.item_templates.items():
        # Use pre-captured screenshot
        for template in data['templates']:
            result = cv.matchTemplate(screenshot, template, cv.TM_CCOEFF_NORMED)
            # ... rest of matching logic
```

## Security Notes

### Privileged Operations

| Operation | Location | Risk Level | Notes |
|-----------|----------|------------|-------|
| **Debug Privilege** | `MemoryFunctions.py:218-229` | HIGH | `SE_DEBUG_NAME` enabled at module import. Required for memory reading but runs automatically. |
| **Process Access** | `Addresses.py:152` | MEDIUM | Opens with `PROCESS_ALL_ACCESS` (0x1F0FFF). Could use `PROCESS_VM_READ \| PROCESS_QUERY_INFORMATION` instead. |
| **File Path Handling** | `GeneralFunctions.py:89-101` | MEDIUM | `manage_profile()` concatenates paths without sanitization. Validate `profile_name` doesn't contain `..` or absolute paths. |
| **Image Loading** | `LootingThread.py:97-98` | LOW | Image paths from JSON could reference arbitrary files. Validate paths are within `Images/` directory. |

### Input Validation Recommendations

```python
# For profile names (GeneralFunctions.py)
import re
def sanitize_profile_name(name):
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ValueError("Invalid profile name")
    return name

# For memory addresses (MemoryFunctions.py)
def validate_type_code(option):
    if option not in range(1, 8):
        raise ValueError(f"Invalid type code: {option}")
```

## Testing Gaps

Current test coverage: **0%** (no test files found)

### Recommended Test Priorities

1. **MemoryFunctions.py** - Critical path, easy to unit test with mocks
2. **PathfindingFunctions.py** - Pure algorithms, no external dependencies
3. **GeneralFunctions.py** - File I/O can be tested with temp directories
4. **Thread coordination** - Integration tests for lock behavior

### Example Test Structure

```
tests/
├── test_memory_functions.py
├── test_pathfinding.py
├── test_general_functions.py
└── conftest.py  # pytest fixtures
```
