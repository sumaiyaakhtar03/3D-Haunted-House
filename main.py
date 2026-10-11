from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math
import time


solved_rooms = {1: False, 2: False, 3: False}
current_room = 1

# Camera / View
cam_pos = (0, 500, 500)
view_angle = 120
fps_view_toggle = False
perspective = "third"  # first or third
game_state = False  # False = playing, True = game over
cheat_flag = False

# Player
player_pos = [0, 0, 120]
plr_rot = 0
player_lives = 5
is_game_over = False

# Puzzle
puzzle_timer = None
puzzle_start_time = 0
puzzle_active = False
puzzle_input = ""
found_digits = []
room_passwords = {1: "4321", 2: "1324", 3: "2314"}
puzzle_message = ""
puzzle_message_timer = 0
puzzle_cooldown = False
cooldown_start_time = 0

# Inventory
inventory = []

# Enemy (x, y, z, scale)
enemy = [100.0, 100.0, 100.0, 1.0]
enemy_speed = 10.0 # very slow chase
last_frame_time = None  # for time difference

close_range = 80  # Distance for collision
spawn_distance = 120  # Distance to spawn in front


class Item:
    def __init__(self, name, x, y, z):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.collected = False

class PaperItem(Item):
    def __init__(self, digit, x, y, z):
        super().__init__(f"digit_{digit}", x, y, z)
        self.digit = digit

def is_near_item(player_pos, item, threshold=60):
    return (abs(player_pos[0] - item.x) < threshold and
            abs(player_pos[1] - item.y) < threshold)

room_items = {
    1: [
        Item('key', 200, 100, 0),
        PaperItem('4', -300, 200, 0),
        PaperItem('3', 100, 250, 0),
        PaperItem('2', 200, -150, 0),
        PaperItem('1', 0, -250, 0),
    ],
    2: [
        Item('note', -300, -200, 0),
        PaperItem('1', -250, 200, 0),
        PaperItem('3', 150, 250, 0),
        PaperItem('2', 200, -100, 0),
        PaperItem('4', 50, -250, 0),
    ],
    3: [
        Item('tool', 0, 400, 0),
        PaperItem('2', -100, 200, 0),
        PaperItem('3', 200, 150, 0),
        PaperItem('1', -200, -100, 0),
        PaperItem('4', 150, -150, 0),
    ],
}

def items_in_room():
    return room_items[current_room]

def try_collect_item(player_pos, items):
    global player_lives
    for item in items:
        if not item.collected and is_near_item(player_pos, item):
            item.collected = True
            if isinstance(item, PaperItem):
                found_digits.append(item.digit)
                print(f"Collected paper with number: {item.digit}")
            else:
                inventory.append(item.name)
                player_lives += 1
                print(f"Collected: {item.name} (+1 life)")


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1, 1, 1)):
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_room(room_x, room_y, furniture=None):
    grid_dim = 13
    cell_dim = 100
    half_grid = (grid_dim / 2) * cell_dim
    wall_h = 200
    offset = cell_dim * grid_dim // 2

    glPushMatrix()
    glTranslatef(room_x, room_y, 0)

    # Floor grid
    for r in range(grid_dim):
        for c in range(grid_dim):
            x_start = (c * cell_dim) - half_grid
            y_start = (r * cell_dim) - half_grid
            glColor3f(1, 1, 1) if ((r + c) % 2 == 0) else glColor3f(0.5, 0, 0)
            glBegin(GL_QUADS)
            glVertex3f(x_start, y_start, 0)
            glVertex3f(x_start + cell_dim, y_start, 0)
            glVertex3f(x_start + cell_dim, y_start + cell_dim, 0)
            glVertex3f(x_start, y_start + cell_dim, 0)
            glEnd()

    # Walls
    glBegin(GL_QUADS)
    glColor3f(0.1, 0.1, 0.1)  # top
    glVertex3f(-offset, -offset, 0)
    glVertex3f(offset, -offset, 0)
    glVertex3f(offset, -offset, wall_h)
    glVertex3f(-offset, -offset, wall_h)

    glColor3f(0.1, 0.25, 0.1)  # bottom
    glVertex3f(-offset, offset, 0)
    glVertex3f(offset, offset, 0)
    glVertex3f(offset, offset, wall_h)
    glVertex3f(-offset, offset, wall_h)

    glColor3f(0.25, 0.15, 0.08)  # right
    glVertex3f(-offset, -offset, 0)
    glVertex3f(-offset, offset, 0)
    glVertex3f(-offset, offset, wall_h)
    glVertex3f(-offset, -offset, wall_h)

    glColor3f(0.3, 0, 0)  # left
    glVertex3f(offset, -offset, 0)
    glVertex3f(offset, offset, 0)
    glVertex3f(offset, offset, wall_h)
    glVertex3f(offset, -offset, wall_h)
    glEnd()
    glPopMatrix()

    # Furniture
    if furniture:
        for fx, fy, fz, fsize, color in furniture:
            glPushMatrix()
            glColor3f(*color)
            glTranslatef(fx, fy, fz)
            if fsize == 999:
                glScalef(2.0, 4.0, 0.5)
                glutSolidCube(50)
            else:
                glutSolidCube(fsize)
            glPopMatrix()

def generate_furniture(room_type):
    furniture = []
    grid_dim = 13
    cell_dim = 100
    random.seed(room_type * 42)

    if room_type == 1:  # Living Room
        furniture.append((-400, -400, 40, 999, (0.4, 0.2, 0.1)))
        furniture.append((-300, -400, 40, 999, (0.4, 0.2, 0.1)))
        furniture.append((-100, 0, 25, 50, (0.6, 0.4, 0.2)))
        furniture.append((400, -400, 30, 60, (0.2, 0.2, 0.2)))
        furniture.append((200, 200, 30, 40, (0.5, 0.3, 0.1)))
        furniture.append((-300, 300, 30, 40, (0.5, 0.3, 0.1)))
        furniture.append((300, 100, 25, 35, (0.6, 0.4, 0.2)))
        furniture.append((-400, 200, 25, 35, (0.6, 0.4, 0.2)))
        for _ in range(8):
            x = random.uniform(-500, 500)
            y = random.uniform(-500, 500)
            size = random.uniform(15, 25)
            furniture.append((x, y, size/2, size, (0.8, 0.6, 0.2)))

    elif room_type == 2:  # Kitchen
        furniture.append((-200, 300, 35, 999, (0.4, 0.2, 0.1)))
        for x, y in [(-300, 250), (-300, 350), (-100, 250), (-100, 350)]:
            furniture.append((x, y, 30, 40, (0.2, 0.2, 1.0)))
        appliances = [
            (400, 300, 25, 50, (1.0, 1.0, 0.0)),
            (300, 400, 20, 40, (1.0, 0.5, 0.0)),
            (-400, 400, 30, 60, (0.5, 0.0, 0.5)),
        ]
        furniture.extend(appliances)
        for _ in range(10):
            x = random.uniform(-450, 450)
            y = random.uniform(-450, 450)
            size = random.uniform(10, 30)
            color = (random.uniform(0.0, 1.0),
                     random.uniform(0.0, 1.0),
                     random.uniform(0.0, 1.0))
            furniture.append((x, y, size/2, size, color))

    else:  # Bedroom
        furniture.append((-100, -100, 25, 999, (0.8, 0.6, 0.4)))
        furniture.append((-100, -100, 35, 999, (0.9, 0.9, 0.9)))
        furniture.append((-250, -100, 25, 40, (0.6, 0.4, 0.2)))
        furniture.append((50, -100, 25, 40, (0.6, 0.4, 0.2)))
        furniture.append((400, 300, 40, 80, (0.5, 0.3, 0.1)))
        furniture.append((-450, 350, 80, 90, (0.4, 0.2, 0.1)))
        furniture.append((300, -400, 35, 70, (0.6, 0.4, 0.2)))
        furniture.append((350, -350, 30, 40, (0.5, 0.3, 0.1)))
        furniture.append((450, 400, 10, 60, (0.8, 0.8, 0.9)))
        items = [
            (-300, 400, 15, 30, (0.9, 0.1, 0.1)),
            (200, 400, 20, 40, (0.2, 0.8, 0.2)),
            (-400, -300, 12, 24, (0.8, 0.8, 0.1)),
            (400, -200, 18, 36, (0.6, 0.3, 0.8)),
        ]
        furniture.extend(items)
        for _ in range(12):
            x = random.uniform(-500, 500)
            y = random.uniform(-500, 500)
            size = random.uniform(8, 25)
            color = (random.uniform(0.2, 0.9),
                     random.uniform(0.2, 0.9),
                     random.uniform(0.2, 0.9))
            furniture.append((x, y, size/2, size, color))
    return furniture

def draw_puzzle_box():
    glPushMatrix()
    glTranslatef(500, -500, 50)
    glColor3f(0.5, 0.5, 0.5)
    glScalef(2.0, 1.0, 0.5)
    glutSolidCube(80)
    glPopMatrix()

    for i in range(4):
        glPushMatrix()
        button_spacing = 40
        button_x = 485 - 60 + (i * button_spacing) + 10
        button_y = -500
        button_z = 77
        glTranslatef(button_x, button_y, button_z)
        glScalef(0.8, 0.8, 0.2)
        glColor3f(1.0, 1.0, 1.0)
        glutSolidCube(20)
        glPopMatrix()

def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(plr_rot, 0, 0, 1)
    if game_state: #game over
        glRotatef(90, 0, 1, 0) 

    glColor3f(51/255, 102/255, 0)
    glPushMatrix()
    glScalef(0.5, 0.7, 1)
    glutSolidCube(100)
    glPopMatrix()

    glColor3f(192/255, 192/255, 192/255)
    glPushMatrix()
    glTranslatef(0, 0, 35)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 15, 10, 80, 20, 20)
    glPopMatrix()

    glColor3f(1, 204/255, 153/255)
    glPushMatrix()
    glTranslatef(0, -35, 35)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 15, 10, 60, 20, 20)
    glPopMatrix()

    glColor3f(1, 204/255, 153/255)
    glPushMatrix()
    glTranslatef(0, 35, 35)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 15, 10, 60, 20, 20)
    glPopMatrix()

    glColor3f(0, 0, 1)
    glPushMatrix()
    glTranslatef(0, -25, -120)
    glRotatef(90, 0, 0, 1)
    gluCylinder(gluNewQuadric(), 9, 15, 70, 20, 20)
    glPopMatrix()

    glColor3f(0, 0, 1)
    glPushMatrix()
    glTranslatef(0, 25, -120)
    glRotatef(90, 0, 0, 1)
    gluCylinder(gluNewQuadric(), 9, 15, 70, 20, 20)
    glPopMatrix()

    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(0, 0, 65)
    gluSphere(gluNewQuadric(), 35, 20, 30)
    glPopMatrix()

    glPopMatrix()

def draw_door():
    glPushMatrix()
    glTranslatef(640, 0, 75)
    glScalef(10, 100, 120)
    if solved_rooms[current_room]:
        glColor3f(0, 0, 0)
    else:
        glColor3f(0.3, 0.25, 0.2)
    glutSolidCube(1.5)
    glPopMatrix()

def draw_enemy(e):
    glPushMatrix()
    glTranslatef(e[0], e[1], e[2])
    glScalef(e[3], e[3], e[3])
    glColor3f(0.8, 0.8, 0.8)  

    glPushMatrix()
    glTranslatef(0, 0, 40)
    gluSphere(gluNewQuadric(), 40, 21, 21)
    glPopMatrix()
    glColor3f(0.8, 0.8, 0.8)
    glPushMatrix()
    glTranslatef(0, 0, 85)
    gluSphere(gluNewQuadric(), 20, 10, 10)
    glPopMatrix()
    glPopMatrix()


def is_colliding_with_furniture(player_pos, furniture_list, player_size=40):
    px, py = player_pos[0], player_pos[1]
    half_p = player_size / 2
    for fx, fy, fz, fsize, _ in furniture_list:
        if fsize == 999:
            half_fx = 50 * 2.0 / 2
            half_fy = 50 * 4.0 / 2
        else:
            half_fx = half_fy = fsize / 2
        if (abs(px - fx) < half_p + half_fx and
            abs(py - fy) < half_p + half_fy):
            return True
    return False

def is_within_room(player_pos, room_size=1300, wall_thickness=50, player_size=40):
    px, py = player_pos[0], player_pos[1]
    half_room = room_size / 2 - wall_thickness - player_size / 2
    return (-half_room <= px <= half_room) and (-half_room <= py <= half_room)

def move_player(new_pos, furniture_list, player_size=40, room_size=1300, wall_thickness=50):
    if (not is_colliding_with_furniture(new_pos, furniture_list, player_size)
        and is_within_room(new_pos, room_size, wall_thickness, player_size)):
        return new_pos
    return None


def chase_enemy(enemy, player_pos, dt_seconds):
   
    dx = player_pos[0] - enemy[0]
    dy = player_pos[1] - enemy[1]
    dist = math.hypot(dx, dy)
    if dist <= 1e-6:
        return
    step = enemy_speed * dt_seconds
    
    if step > dist:
        step = dist
    enemy[0] += (dx / dist) * step
    enemy[1] += (dy / dist) * step
   
    enemy[2] += (player_pos[2] - enemy[2]) * 1 * dt_seconds

def check_enemy_collision(enemy, player_pos):
    global player_lives, is_game_over
    dx = player_pos[0] - enemy[0]
    dy = player_pos[1] - enemy[1]
    dz = player_pos[2] - enemy[2]
    dist = (dx**2 + dy**2 + dz**2)**0.5
    if dist < close_range and not is_game_over:
        player_lives -= 1
        print(f"Enemy caught you! Lives left: {player_lives}")
        enemy[0] = player_pos[0] + spawn_distance
        enemy[1] = player_pos[1]
        enemy[2] = player_pos[2]
        if player_lives <= 0:
            is_game_over = True
            print("Game Over! Press 'R' to restart.")


def reset_game():
    global player_lives, inventory, found_digits, puzzle_input, puzzle_active
    global puzzle_start_time, puzzle_cooldown, current_room, player_pos, enemy, is_game_over
    print("Game reset! Lives depleted.")
    player_lives = 5
    inventory.clear()
    found_digits.clear()
    puzzle_input = ""
    puzzle_active = False
    puzzle_start_time = 0
    puzzle_cooldown = False
    current_room = 1
    player_pos[:] = [0, 0, 120]
    enemy[:] = [100.0, 100.0, 100.0, 1.0]
    is_game_over = False

    for room in room_items.values():
        for item in room:
            item.collected = False

    for room in solved_rooms:
        solved_rooms[room] = False

def reset_puzzle():
    global puzzle_input, puzzle_start_time
    puzzle_input = ""
    puzzle_start_time = time.time()

def check_puzzle_trigger():
    global puzzle_active, puzzle_input, puzzle_message, puzzle_message_timer, puzzle_start_time, puzzle_cooldown
    if solved_rooms[current_room] or puzzle_cooldown or puzzle_active:
        return
    if len(found_digits) < 4:
        return 

    if (420 <= player_pos[0] <= 580) and (-540 <= player_pos[1] <= -460):
        puzzle_active = True
        puzzle_start_time = time.time()
        puzzle_input = ""
        puzzle_message = "Puzzle activated! Enter code in terminal."
        puzzle_message_timer = time.time()


def check_door_trigger():
    global current_room, player_pos, puzzle_message, is_game_over, inventory, found_digits

    if not solved_rooms[current_room]:
        return

    door_x_min, door_x_max = 550, 700
    door_y_min, door_y_max = -60, 90

    if door_x_min <= player_pos[0] <= door_x_max and door_y_min <= player_pos[1] <= door_y_max:
        if current_room < 3:
            current_room += 1
            player_pos[0], player_pos[1] = -500, 0
            puzzle_message = f"Entered Room {current_room}"
            found_digits.clear()  
        else:
            puzzle_message = "You Win! All puzzles solved."
            inventory = ["Congratulations you win the game!"]
            is_game_over = True


def keyboardListener(key, x, y):
    global cheat_flag, fps_view_toggle, plr_rot, player_pos
    global puzzle_input, puzzle_active, puzzle_message, puzzle_message_timer
    global player_lives, puzzle_start_time, puzzle_cooldown, cooldown_start_time
    global is_game_over

    if puzzle_active and key in b'0123456789':
        digit = key.decode()
        puzzle_input += digit
        print(f"Digit entered: {digit} | Current input: {puzzle_input}")

        if len(puzzle_input) == 4:
            if puzzle_input == room_passwords[current_room]:
                print("Puzzle Solved! Room unlocked.")
                puzzle_message = "Correct Code!"
                solved_rooms[current_room] = True
                puzzle_active = False
                puzzle_start_time = 0
            else:
                puzzle_cooldown = True
                cooldown_start_time = time.time()
                print("Wrong password! You lost a life.")
                puzzle_message = "Incorrect Code. Try Again!"
                puzzle_message_timer = time.time()
                player_lives -= 1
                if player_lives <= 0:
                    print("Game Over. Resetting...")
                    reset_game()
                else:
                    reset_puzzle()
            return  

    if is_game_over and key == b'r':
        reset_game()
        print("Game restarted!")
        return

    if not puzzle_active:
        if key == b'c':
            cheat_flag = not cheat_flag
            if cheat_flag:
                print("Cheat mode ON!")
                # Reveal password for current room
                print(f"Room {current_room} password: {room_passwords[current_room]}")
            else:
                print("Cheat mode OFF!")
        elif key == b'v':
            fps_view_toggle = not fps_view_toggle
        elif key == b'd':
            plr_rot -= 5
        elif key == b'a':
            plr_rot += 5
        elif key == b's':
            rad = math.radians(plr_rot)
            new_x = player_pos[0] - math.cos(rad) * 10
            new_y = player_pos[1] - math.sin(rad) * 10
            new_pos = move_player([new_x, new_y, player_pos[2]], room_furniture[current_room])
            if new_pos:
                player_pos[0], player_pos[1] = new_pos[0], new_pos[1]
        elif key == b'w':
            rad = math.radians(plr_rot)
            new_x = player_pos[0] + math.cos(rad) * 10
            new_y = player_pos[1] + math.sin(rad) * 10
            new_pos = move_player([new_x, new_y, player_pos[2]], room_furniture[current_room])
            if new_pos:
                player_pos[0], player_pos[1] = new_pos[0], new_pos[1]
        elif key == b'e':
            try_collect_item(player_pos, items_in_room())

    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global cam_pos
    cx, cy, cz = cam_pos
    if not game_state:
        if key == GLUT_KEY_UP:
            cy -= 10
        elif key == GLUT_KEY_DOWN:
            cy += 10
        elif key == GLUT_KEY_LEFT:
            cx += 10
        elif key == GLUT_KEY_RIGHT:
            cx -= 10
    cam_pos = (cx, cy, cz)
    glutPostRedisplay()

def mouseListener(button, state, x, y):
    global perspective, game_state
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN and not game_state:
        perspective = "first" if perspective == "third" else "third"
        glutPostRedisplay()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(view_angle, 1.25, 0.1, 1500)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if perspective == "third":
        cam_x, cam_y, cam_z = cam_pos
        gluLookAt(cam_x, cam_y, cam_z, 0, 0, 0, 0, 0, 1)
    else:
        facing_angle = math.radians(plr_rot)
        offset_fwd = 50
        offset_side = 30
        offset_up = 40
        eye_x = player_pos[0] + offset_side * math.sin(facing_angle) - math.cos(facing_angle) * offset_fwd
        eye_y = player_pos[1] - offset_side * math.cos(facing_angle) - math.sin(facing_angle) * offset_fwd
        eye_z = player_pos[2] + offset_up
        if cheat_flag:
            if fps_view_toggle:
                eye_x, eye_y, eye_z = 50, 50, 50
                look_x, look_y, look_z = player_pos[0], player_pos[1], player_pos[2]
            else:
                look_x = eye_x + (math.cos(facing_angle)) * 100
                look_y = eye_y + (math.sin(facing_angle)) * 100

                look_z = eye_z
        else:
            look_x = eye_x + (math.cos(facing_angle)) * 100
            look_y = eye_y + (math.sin(facing_angle)) * 100

            look_z = eye_z
        gluLookAt(eye_x, eye_y, eye_z, look_x, look_y, look_z, 0, 0, 1)


room_furniture = {
    1: generate_furniture(1),
    2: generate_furniture(2),
    3: generate_furniture(3),
}

def draw_rooms():
    draw_room(0, 0, room_furniture[current_room])


def showScreen():
    global is_game_over
    if is_game_over:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        glTranslatef(player_pos[0], player_pos[1], player_pos[2])
        glRotatef(plr_rot, 0, 0, 1)
        glRotatef(90, 0, 1, 0)  # Lay player sideways 
        glColor3f(51/255, 102/255, 0)
        glPushMatrix()
        glScalef(0.5, 0.7, 1)
        glutSolidCube(100)
        glPopMatrix()
        glColor3f(192/255, 192/255, 192/255)
        glPushMatrix()
        glTranslatef(0, 0, 35)
        glRotatef(90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 15, 10, 80, 20, 20)
        glPopMatrix()
        glColor3f(1, 204/255, 153/255)
        glPushMatrix()
        glTranslatef(0, -35, 35)
        glRotatef(90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 15, 10, 60, 20, 20)
        glPopMatrix()
        glColor3f(1, 204/255, 153/255)
        glPushMatrix()
        glTranslatef(0, 35, 35)
        glRotatef(90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 15, 10, 60, 20, 20)
        glPopMatrix()
        glColor3f(0, 0, 1)
        glPushMatrix()
        glTranslatef(0, -25, -120)
        glRotatef(90, 0, 0, 1)
        gluCylinder(gluNewQuadric(), 9, 15, 70, 20, 20)
        glPopMatrix()
        glColor3f(0, 0, 1)
        glPushMatrix()
        glTranslatef(0, 25, -120)
        glRotatef(90, 0, 0, 1)
        gluCylinder(gluNewQuadric(), 9, 15, 70, 20, 20)
        glPopMatrix()
        glColor3f(0, 0, 0)
        glPushMatrix()
        glTranslatef(0, 0, 65)
        gluSphere(gluNewQuadric(), 35, 20, 30)
        glPopMatrix()
        glPopMatrix()
        draw_text(400, 400, "Game Over! Press 'R' to restart")
        glutSwapBuffers()
        return

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()
    draw_rooms()
    draw_door()

    if perspective == "third":
        draw_player()

    # Items
    for item in items_in_room():
        if not item.collected:
            glPushMatrix()
            glTranslatef(item.x, item.y, item.z)
            if isinstance(item, PaperItem):
                glColor3f(1, 1, 1)
                glScalef(1, 1.5, 0.1)
                glutSolidCube(20)
            else:
                glColor3f(1, 1, 0)
                glutSolidSphere(10, 10, 10)
            glPopMatrix()

   
    draw_puzzle_box()
    draw_text(10, 770, f"Room: {current_room}")
    draw_text(10, 740, f"Camera: {perspective} (Right-click to toggle)")
    draw_text(10, 710, f"Player Life: {player_lives}")
    inventory_display = ', '.join(inventory) if inventory else 'Empty'
    if cheat_flag:
        inventory_display += f" | Password: {room_passwords[current_room]}"
    draw_text(10, 690, f"Inventory: {inventory_display}")

    draw_text(10, 660, f"Digits Found: {' '.join(found_digits)}")

    if puzzle_message and time.time() - puzzle_message_timer < 3:
        draw_text(350, 430, puzzle_message, color=(0, 0, 0))

    if puzzle_active:
        draw_text(10, 600, f"Enter Code: {puzzle_input}")
        remaining = max(0, 30 - int(time.time() - puzzle_start_time))
        draw_text(10, 630, f"Time Left: {remaining}s")


    draw_enemy(enemy)

    # Game Over message
    if is_game_over:
        draw_text(400, 400, "Game Over! Press 'R' to restart", color=(1, 0, 0))

    glutSwapBuffers()
    if cheat_flag:
        draw_text(10, 630, f"CHEAT MODE ON Password: {room_passwords[current_room]}", color=(1, 0.2, 0.2))



def idle():
    global puzzle_message, puzzle_message_timer, puzzle_cooldown, player_lives
    global puzzle_active, cooldown_start_time, last_frame_time, is_game_over

    now = time.time()
    if last_frame_time is None:
        last_frame_time = now
        dt = 0.016
    else:
        dt = max(0.0, min(0.1, now - last_frame_time)) 
        last_frame_time = now

    # Puzzle 30s timer
    if puzzle_active and not solved_rooms[current_room]:
        if time.time() - puzzle_start_time > 30:
            puzzle_message = "Puzzle failed. Time's up!"
            puzzle_message_timer = time.time()
            player_lives -= 1
            if player_lives <= 0:
                reset_game()
            else:
                reset_puzzle()
            puzzle_active = False
            puzzle_cooldown = True
            cooldown_start_time = time.time()

    # 3-second cooldown
    if puzzle_cooldown and time.time() - cooldown_start_time > 3:
        puzzle_cooldown = False

    # Triggers
    check_puzzle_trigger()
    check_door_trigger()

   
    if not is_game_over:
        if not cheat_flag:  
            chase_enemy(enemy, player_pos, dt)
            check_enemy_collision(enemy, player_pos)


    glutPostRedisplay()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D Room with Player and Camera Controls")
    glEnable(GL_DEPTH_TEST)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()