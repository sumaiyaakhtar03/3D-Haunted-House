# 3D Haunted House — Escape Room Game

A 3D escape-room game built with **Python** and **PyOpenGL (GLUT/GLU)**. Explore three rooms, collect clues, solve four-digit puzzles, and avoid a pursuing enemy to escape the haunted house.

## Features

- **Three themed rooms:** Living Room, Kitchen, and Bedroom, each with its own furniture and obstacles.
- **3D environment:** A tiled floor, enclosing walls, furniture, a door, collectible objects, and a puzzle box.
- **Player movement and collision:** Walk around the room, turn, and avoid passing through furniture or walls.
- **Collectibles and inventory:** Pick up four numbered papers in each room to reveal puzzle clues. Each room also contains a special item (key, note, or tool); collecting it adds it to the inventory and grants **+1 life**.
- **Room-specific code puzzles:** Collect four numbered papers, approach the puzzle box, and enter the room's four-digit code before the **30-second timer** runs out.
- **Progression through locked doors:** Solving a room's puzzle unlocks its exit. Walk toward the door to enter the next room; solve all three rooms to win.
- **Enemy pursuit:** An enemy slowly chases the player. Contact costs a life and moves the enemy away from the player.
- **Lives and failure:** Start with **5 lives**; incorrect codes, timeouts, and enemy collisions can reduce them. Reaching zero triggers a game-over/reset path depending on the event.
- **Camera controls:** Switch between first-person and third-person views and reposition the third-person camera with arrow keys.
- **Cheat mode:** Reveal the current room's password and suspend enemy chasing while enabled.
- **On-screen HUD:** Shows room number, camera mode, remaining lives, inventory, collected digits, puzzle messages, and remaining puzzle time.
- **Restart support:** Restart after game over with `R`.

## Controls

| Button / Input | Action |
|---|---|
| `W` | Move forward in the direction the player faces |
| `S` | Move backward |
| `A` | Rotate player left |
| `D` | Rotate player right |
| `E` | Collect a nearby item or numbered paper |
| **Right mouse button** | Toggle **first-person / third-person** perspective |
| **Up arrow** | Adjust third-person camera position along the Y axis |
| **Down arrow** | Adjust third-person camera position along the Y axis in the opposite direction |
| **Left arrow** | Adjust third-person camera position along the X axis |
| **Right arrow** | Adjust third-person camera position along the X axis in the opposite direction |
| `C` | Turn cheat mode on/off; display the current room password and pause enemy chasing while on |
| `V` | Toggle the special camera view flag (used in **first-person view while cheat mode is on**) |
| `0`–`9` | Enter the four-digit puzzle code **when a puzzle is active** |
| `R` | Restart the game **on the game-over screen** |

**Note:** Movement keys do not move the player while a puzzle is active. You do **not** need to press a key to open a solved door—walk into its trigger area.

## How to Play

1. Start in **Room 1 (Living Room)** with five lives.
2. Move around the room using `W`, `S`, `A`, and `D`.
3. Stand near the numbered papers and press `E` to collect them. Collect all **four papers** in the current room.
4. Optionally collect the room's special item to gain one extra life.
5. Approach the **puzzle box near `(500, -500)`**. Once all four digits have been collected, the puzzle starts automatically.
6. Enter the correct **four-digit room password** using the number keys within **30 seconds**.
7. After solving the puzzle, approach the unlocked **door on the right-hand side of the room** to move to the next room.
8. Repeat in the **Kitchen (Room 2)** and **Bedroom (Room 3)**. Solve the third room and reach its exit to win.

**Watch out:** The enemy chases you. Getting caught, entering an incorrect password, or running out of puzzle time costs a life. Incorrect entries also trigger a short cooldown.

### Room overview

| Room | Theme | Special collectible | Puzzle |
|---|---|---|---|
| 1 | Living Room | Key | Four-digit code |
| 2 | Kitchen | Note | Four-digit code |
| 3 | Bedroom | Tool | Four-digit code |

For a challenge, discover the codes through gameplay. To reveal the current room's programmed password during play, press `C` to enable cheat mode.

## Requirements

- Python **3.13.5** (the version used during setup; other versions may also work)
- [PyOpenGL](https://pypi.org/project/PyOpenGL/)
- [PyOpenGL-accelerate](https://pypi.org/project/PyOpenGL-accelerate/) (optional accelerator)
- A working native **GLUT** implementation / framework for your operating system
- A desktop capable of opening an OpenGL window

The `random`, `math`, and `time` modules are part of Python's standard library and do not need separate installation.

## Installation and Running (VS Code / macOS)

1. Open the project folder in **Visual Studio Code** and save the game code as `main.py`.
2. Open **Terminal → New Terminal**.
3. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   python -m pip install PyOpenGL PyOpenGL-accelerate
   ```

5. If needed, install a GLUT implementation. On macOS with Homebrew, you can try:

   ```bash
   brew install freeglut
   ```

   > **macOS note:** Installing FreeGLUT does not necessarily make it automatically discoverable by PyOpenGL. If `glutInit` fails or the library cannot load, your GLUT framework/library configuration may need platform-specific adjustment. macOS also has limitations with legacy OpenGL support.

6. Run:

   ```bash
   python main.py
   ```

### Windows / Linux

Create a virtual environment and install the same Python packages. Windows may require a compatible FreeGLUT DLL accessible to Python; on Ubuntu/Debian, the native library can commonly be installed using `sudo apt install freeglut3-dev`.

## Project Structure

```text
3D Haunted House/
├── main.py       # Game source code
├── README.md     # Project documentation
└── .venv/        # Local virtual environment (do not commit to GitHub)
```

## Troubleshooting

- **`ModuleNotFoundError: No module named 'OpenGL'`:** Activate `.venv` and install PyOpenGL in that environment.
- **`NullFunctionError` for `glutInit`:** The native GLUT implementation was not loaded correctly. Install/configure a supported GLUT library.
- **`SyntaxError` or `IndentationError`:** Ensure `main.py` contains valid Python code. Do not paste Markdown-escaped characters (such as `\*` in place of `*`) or a flattened one-line copy of the game.
- **Window does not open / closes unexpectedly:** Run from the VS Code terminal to inspect the complete error; check GLUT availability and platform OpenGL support.

## Tech Stack

**Language:** Python  
**Rendering:** OpenGL through PyOpenGL, GLU, and GLUT  
**Game logic:** Python functions, collision checks, keyboard/mouse callbacks, and a GLUT idle loop

## Notes

This README documents the features and controls implemented in the provided source code. A successful graphical launch depends on having valid Python source and working native OpenGL/GLUT dependencies on your machine.
