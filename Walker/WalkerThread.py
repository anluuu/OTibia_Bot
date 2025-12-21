import random
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QListWidgetItem

import Addresses
from Addresses import walker_Lock, coordinates_x, coordinates_y, attack_Lock
from Functions.MemoryFunctions import *
from Functions.KeyboardFunctions import walk
from Functions.MouseFunctions import mouse_function
from Functions.PathfindingFunctions import expand_waypoints, calculate_path_astar


class WalkerThread(QThread):
    index_update = pyqtSignal(int, object)

    def __init__(self, waypoints):
        super().__init__()
        print(f"DEBUG: Initializing WalkerThread with {len(waypoints)} waypoints")
        self.last_target_pos = None
        self.waypoints = waypoints
        self.running = True

    def run(self):
        current_wpt = self.find_wpt(self.waypoints)
        timer = 0
        second_timer = 0
        self.discovered_obstacles = set()
        self.last_target_pos = None
        my_x, my_y, my_z = read_my_wpt()
        previous_pos = (my_x, my_y, my_z)
        while self.running:
            try:

                sleep_value = random.randint(10, 50)
                QThread.msleep(sleep_value)
                if not walker_Lock.locked():
                    timer += sleep_value
                    second_timer += (sleep_value / 1000)
                if (timer / 1000) >= 5: # 5 Second no wpt
                    current_wpt = self.find_wpt(self.waypoints)
                    self.discovered_obstacles.clear()
                    timer = 0
                    second_timer = 0
                self.index_update.emit(0, current_wpt)
                wpt_data = self.waypoints[current_wpt]
                wpt_action = wpt_data['Action']
                wpt_direction = wpt_data['Direction']
                map_x = wpt_data['X']
                map_y = wpt_data['Y']
                map_z = wpt_data['Z']
                my_x, my_y, my_z = read_my_wpt()
                if my_x == map_x  and my_y == map_y and my_z == map_z:
                    current_wpt = (current_wpt + 1) % len(self.waypoints)
                    self.discovered_obstacles.clear()
                    timer = 0
                    continue
                while walker_Lock.locked() and wpt_action != 4: # If attacking and not Luring
                    print("Walker is locked")
                    QThread.msleep(200)
                if wpt_action == 0:
                    if wpt_direction == 0:
                        print("Finding Path")
                        path = calculate_path_astar(my_x, my_y, map_x, map_y, self.discovered_obstacles)
                        print("Found path ", path)
                        if path:
                            next_step = path[0]
                            self.last_target_pos = (my_x + next_step[0], my_y + next_step[1])
                            walk(0, my_x, my_y, my_z, my_x + next_step[0], my_y + next_step[1], map_z)
                            print("Walking")
                    else:
                        walk(wpt_direction, my_x, my_y, my_z, map_x, map_y, map_z)
                elif wpt_action == 1: # Rope
                    QThread.msleep(random.randint(500, 600))
                    mouse_function(coordinates_x[10], coordinates_y[10], option=1)
                    QThread.msleep(random.randint(100, 200))
                    my_x, my_y, my_z = read_my_wpt()
                    map_x = wpt_data['X']
                    map_y = wpt_data['Y']
                    mouse_function(coordinates_x[0] + (map_x - my_x) * Addresses.square_size, coordinates_y[0] + (map_y - my_y) * Addresses.square_size, option=2)
                    current_wpt = (current_wpt + 1) % len(self.waypoints)
                elif wpt_action == 2: # Shovel
                    QThread.msleep(random.randint(500, 600))
                    mouse_function(coordinates_x[9], coordinates_y[9], option=1)
                    QThread.msleep(random.randint(100, 200))
                    my_x, my_y, my_z = read_my_wpt()
                    map_x = wpt_data['X']
                    map_y = wpt_data['Y']
                    mouse_function(coordinates_x[0] + (map_x - my_x) * Addresses.square_size,
                        coordinates_y[0] + (map_y - my_y) * Addresses.square_size,
                                   option=2)
                    current_wpt = (current_wpt + 1) % len(self.waypoints)
                elif wpt_action == 3: # Ladder
                    QThread.msleep(random.randint(500, 600))
                    mouse_function(coordinates_x[0], coordinates_y[0], option=1)
                    current_wpt = (current_wpt + 1) % len(self.waypoints)
                elif wpt_action == 4:  # Lure
                    if wpt_direction == 0:
                        path = calculate_path_astar(my_x, my_y, map_x, map_y, self.discovered_obstacles)
                        if path:
                            next_step = path[0]
                            self.last_target_pos = (my_x + next_step[0], my_y + next_step[1])
                            walk(0, my_x, my_y, my_z, my_x + next_step[0], my_y + next_step[1], map_z)
                    else:
                         walk(wpt_direction, my_x, my_y, my_z, map_x, map_y, map_z)
                if (my_x, my_y, my_z) == previous_pos:
                    if not walker_Lock.locked():
                        second_timer += (sleep_value / 1000)
                else:
                    previous_pos = (my_x, my_y, my_z)
                    second_timer = 0
                if second_timer > 3:
                    if self.last_target_pos:
                        self.discovered_obstacles.add(self.last_target_pos)
                        self.last_target_pos = None
                    
                    
            except Exception as e:
                print("Error", e)


    def stop(self):
        self.running = False

    def find_wpt(self, waypoints):
        x, y, z = read_my_wpt()
        for wpt in range(0, len(waypoints)):
            wpt_data = waypoints[wpt]
            map_x = wpt_data['X']
            map_y = wpt_data['Y']
            map_z = wpt_data['Z']
            wpt_direction = wpt_data['Direction']
            if z == map_z and abs(map_x - x) <= 4 and abs(map_y - y) <= 4 and wpt_direction == 0:
                return wpt
        return 0









    # Record thread.
class RecordThread(QThread):
    wpt_update = pyqtSignal(int, object)

    def __init__(self, direction_group, action_group, interval=1):
        super().__init__()
        self.running = True
        self.direction_group = direction_group
        self.action_group = action_group
        self.interval = interval
        self.last_recorded_x = None
        self.last_recorded_y = None
        self.last_recorded_z = None

    def run(self):
        x, y, z = read_my_wpt()
        
        dir_id = self.direction_group.checkedId()
        dir_text = "Center"
        btn = self.direction_group.button(dir_id)
        if btn:
            dir_text = btn.text()
            if dir_text == "C": dir_text = "Center"
            
        act_id = self.action_group.checkedId()
        act_text = "Stand"
        act_btn = self.action_group.button(act_id)
        if act_btn:
             act_text = act_btn.text()

        waypoint_data = {
            "Action": act_id,
            "Direction": dir_id,
            "X": x,
            "Y": y,
            "Z": z
        }
        
        display_text = "Unknown"
        if act_id == 0: # Stand
             display_text = f'Stand: {x} {y} {z} {dir_text}'
        elif act_id == 4: # Lure
             display_text = f'Lure: {x} {y} {z}'
        elif act_id == 1: # Rope
             display_text = f'Rope: {x} {y} {z}'
        elif act_id == 2: # Shovel
             display_text = f'Shovel: {x} {y} {z}'
        elif act_id == 3: # Ladder
             display_text = f'Ladder: {x} {y} {z}'
             
        waypoint = QListWidgetItem(display_text)
        waypoint.setData(Qt.UserRole, waypoint_data)
        self.wpt_update.emit(1, waypoint)
        
        # Track last recorded position
        self.last_recorded_x = x
        self.last_recorded_y = y
        self.last_recorded_z = z
        old_x, old_y, old_z = x, y, z
        while self.running:
            try:
                x, y, z = read_my_wpt()
                if z != old_z:  # Stair, hole, etc.
                    if y > old_y and x == old_x:  # Move South
                        waypoint_data = {
                            "Action": 0,
                            "Direction": 2,  # South index
                            "X": x,
                            "Y": y,
                            "Z": z
                        }
                        waypoint = QListWidgetItem(f'Stand: {x} {y} {z} South')
                        waypoint.setData(Qt.UserRole, waypoint_data)
                        self.wpt_update.emit(1, waypoint)
                    if y < old_y and x == old_x:  # Move North
                        waypoint_data = {
                            "Action": 0,
                            "Direction": 1,  # North index
                            "X": x,
                            "Y": y,
                            "Z": z
                        }
                        waypoint = QListWidgetItem(f'Stand: {x} {y} {z} North')
                        waypoint.setData(Qt.UserRole, waypoint_data)
                        self.wpt_update.emit(1, waypoint)
                    if y == old_y and x > old_x:  # Move East
                        waypoint_data = {
                            "Action": 0,
                            "Direction": 3,  # East index
                            "X": x,
                            "Y": y,
                            "Z": z
                        }
                        waypoint = QListWidgetItem(f'Stand: {x} {y} {z} East')
                        waypoint.setData(Qt.UserRole, waypoint_data)
                        self.wpt_update.emit(1, waypoint)

                    if y == old_y and x < old_x:  # Move West
                        waypoint_data = {
                            "Action": 0,
                            "Direction": 4,  # West index
                            "X": x,
                            "Y": y,
                            "Z": z
                        }
                        waypoint = QListWidgetItem(f'Stand: {x} {y} {z} West')
                        waypoint.setData(Qt.UserRole, waypoint_data)
                        self.wpt_update.emit(1, waypoint)

                if (x != old_x or y != old_y) and z == old_z:
                    # Check if we should record based on interval
                    if self.last_recorded_x is None:  # First move (shouldn't happen, but safe)
                        should_record = True
                    else:
                        dist_x = abs(x - self.last_recorded_x)
                        dist_y = abs(y - self.last_recorded_y)
                        distance = dist_x + dist_y
                        should_record = distance >= self.interval
                    
                    if should_record:
                        dir_id = self.direction_group.checkedId()
                        dir_text = "Center"
                        btn = self.direction_group.button(dir_id)
                        if btn:
                            dir_text = btn.text()
                            if dir_text == "C": dir_text = "Center"
                            
                        act_id = self.action_group.checkedId()
                        # act_text = "Stand" # Not used in display text logic below if we copy the logic
                        
                        waypoint_data = {
                            "Action": act_id,
                            "Direction": dir_id,
                            "X": x,
                            "Y": y,
                            "Z": z
                        }
                        
                        display_text = "Unknown"
                        if act_id == 0: # Stand
                             display_text = f'Stand: {x} {y} {z} {dir_text}'
                        elif act_id == 4: # Lure
                             display_text = f'Lure: {x} {y} {z}'
                        elif act_id == 1: # Rope
                             display_text = f'Rope: {x} {y} {z}'
                        elif act_id == 2: # Shovel
                             display_text = f'Shovel: {x} {y} {z}'
                        elif act_id == 3: # Ladder
                             display_text = f'Ladder: {x} {y} {z}'

                        waypoint = QListWidgetItem(display_text)
                        waypoint.setData(Qt.UserRole, waypoint_data)
                        self.wpt_update.emit(1, waypoint)
                        
                        # Update last recorded position
                        self.last_recorded_x = x
                        self.last_recorded_y = y
                        self.last_recorded_z = z
                
                # Always update old position for change detection
                old_x, old_y, old_z = x, y, z
                QThread.msleep(10)
            except RuntimeError:
                # Widget deleted, stop thread
                self.running = False
                break
            except Exception as e:
                print(e)

    def stop(self):
        self.running = False
