import random
import time
import win32api
import win32gui
import Addresses
import win32con
from PyQt5.QtCore import QThread, Qt
from PyQt5.QtWidgets import QCheckBox, QLineEdit, QComboBox

class HotkeysThread(QThread):
    def __init__(self, hotkeys_tableWidget):
        super().__init__()
        self.running = True
        self.hotkeys_tableWidget = hotkeys_tableWidget
        self.last_execution_times = {}
        self.next_delays = {}

    def run(self):
        while self.running:
            current_time = time.time()
            
            try:
                for row in range(self.hotkeys_tableWidget.rowCount()):
                    # Get values from table cells
                    hotkey_combo = self.hotkeys_tableWidget.cellWidget(row, 0)
                    time_edit = self.hotkeys_tableWidget.cellWidget(row, 1)
                    random_edit = self.hotkeys_tableWidget.cellWidget(row, 2)
                    checkbox_widget = self.hotkeys_tableWidget.cellWidget(row, 3)
                    
                    if not hotkey_combo or not time_edit or not random_edit or not checkbox_widget:
                        continue
                    
                    # Check if active
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if not checkbox or not checkbox.isChecked():
                        continue
                    
                    # Get values
                    hotkey_name = hotkey_combo.currentText()
                    try:
                        interval = float(time_edit.text())
                        randomize = float(random_edit.text())
                    except ValueError:
                        continue
                    
                    # Initialize last execution time if not present
                    if row not in self.last_execution_times:
                        self.last_execution_times[row] = current_time
                        self.next_delays[row] = interval + random.uniform(0, randomize)
                        continue
                    
                    last_time = self.last_execution_times[row]
                    
                    # Check if enough time has passed
                    if current_time - last_time >= self.next_delays[row]:
                        # Execute Hotkey
                        self.press_hotkey(hotkey_name)
                        
                        # Update time and calculate next delay
                        self.last_execution_times[row] = current_time
                        self.next_delays[row] = interval + random.uniform(0, randomize)
            except RuntimeError:
                # Widget deleted, stop thread
                self.running = False
                break
            except Exception as e:
                print(f"HotkeysThread error: {e}")
            
            QThread.msleep(10)

    def press_hotkey(self, hotkey_name):
        # Map F1-F12 to VK codes
        # F1 is 0x70 (112)
        try:
            f_key_num = int(hotkey_name[1:])
            vk_code = 111 + f_key_num # F1=112, so 111+1
            
            # Use keybd_event for key simulation
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYDOWN, vk_code, vk_code)
            win32gui.PostMessage(Addresses.game, win32con.WM_KEYUP, vk_code, vk_code)
            
        except Exception as e:
            print(f"Error pressing hotkey {hotkey_name}: {e}")

    def stop(self):
        self.running = False
