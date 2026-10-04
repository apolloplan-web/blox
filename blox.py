"""
Territory Game - 4 Player Blox Game
A turn-based territory building game for 4 players using polyomino blocks.
"""

import sys
import pygame

# ============================================================================
# CONSTANTS
# ============================================================================

# Screen Configuration
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

# Board Configuration
GRID_SIZE = 20
CELL_SIZE = 30
BOARD_OFFSET_X = 50
BOARD_OFFSET_Y = 50

# UI Configuration
PALETTE_X = 750
PALETTE_Y = 50
BUTTON_Y = 700
BUTTON_WIDTH = 80
BUTTON_HEIGHT = 40

# Colors
BG_COLOR = (240, 240, 240)
GRID_COLOR = (200, 200, 200)
TEXT_COLOR = (0, 0, 0)
VALID_COLOR = (144, 238, 144)
INVALID_COLOR = (255, 100, 100)
UI_BG_COLOR = (220, 220, 220)
BUTTON_COLOR = (180, 180, 180)
BUTTON_HOVER_COLOR = (150, 150, 150)

# Player Colors
PLAYER_COLORS = [
    (70, 130, 180),      # Player 1: Steel Blue
    (220, 20, 60),       # Player 2: Crimson Red
    (34, 139, 34),       # Player 3: Forest Green
    (255, 165, 0),       # Player 4: Orange
]

# Game Blocks (21 polyomino patterns)
ALL_BLOCKS = [
    [[1, 1, 1, 1, 1]],
    [[1, 0, 0, 0], [1, 1, 1, 1]],
    [[0, 1, 0, 0], [1, 1, 1, 1]],
    [[1, 1, 0, 0], [0, 1, 1, 1]],
    [[1, 0, 1], [1, 1, 1]],
    [[1, 0], [1, 1], [1, 1]],
    [[1, 0, 0], [1, 0, 0], [1, 1, 1]],
    [[1, 0, 0], [1, 1, 0], [0, 1, 0]],
    [[1, 0, 0], [1, 1, 1], [0, 0, 1]],
    [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
    [[1, 0, 0], [1, 1, 1], [0, 1, 0]],
    [[1, 0, 0], [1, 1, 1], [1, 0, 0]],
    [[1, 0, 0], [1, 1, 1]],
    [[0, 1, 0], [1, 1, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[1, 1], [1, 1]],
    [[1, 1, 1, 1]],
    [[1, 1, 1]],
    [[1, 0], [1, 1]],
    [[1, 1]],
    [[1]],
]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def rotate_shape(shape):
    """Rotate a shape 90 degrees clockwise."""
    rows = len(shape)
    cols = len(shape[0])
    result = [[0 for _ in range(rows)] for _ in range(cols)]
    for r in range(rows):
        for c in range(cols):
            result[c][rows - 1 - r] = shape[r][c]
    return result


def flip_shape(shape):
    """Flip a shape horizontally."""
    return [row[::-1] for row in shape]


def normalize_shape(shape):
    """Remove padding from a shape and return normalized version."""
    min_r = min((r for r, row in enumerate(shape) for v in row if v), default=0)
    min_c = min((c for r, row in enumerate(shape) for c, v in enumerate(row) if v), default=0)
    rows = []
    for r in range(min_r, len(shape)):
        rows.append(shape[r][min_c:])
    return rows


def get_shape_bounds(shape):
    """Get width and height of a shape."""
    if not shape:
        return 0, 0
    height = len(shape)
    width = max(len(row) for row in shape)
    return width, height


def draw_text(screen, text, x, y, font_size=24, color=TEXT_COLOR):
    """Draw text on screen."""
    font = pygame.font.Font(None, font_size)
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))


# ============================================================================
# CLASSES
# ============================================================================

class Button:
    """Interactive button for UI controls."""
    
    def __init__(self, x, y, width, height, label, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.label = label
        self.callback = callback
        self.is_hovered = False

    def draw(self, screen):
        """Draw button with hover state."""
        color = BUTTON_HOVER_COLOR if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 2)
        font = pygame.font.Font(None, 18)
        text_surface = font.render(self.label, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        """Update hover state based on mouse position."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def check_click(self, mouse_pos):
        """Check if button is clicked and execute callback."""
        if self.rect.collidepoint(mouse_pos):
            self.callback()
            return True
        return False


class Block:
    """Represents a playable block/polyomino."""
    
    def __init__(self, shape, block_id=0, player_id=0):
        self.original_shape = [row[:] for row in shape]
        self.shape = [row[:] for row in shape]
        self.block_id = block_id
        self.player_id = player_id
        self.x = 0
        self.y = 0
        self.is_dragging = False

    def rotate(self):
        """Rotate block 90 degrees clockwise."""
        self.shape = normalize_shape(rotate_shape(self.shape))

    def flip(self):
        """Flip block horizontally."""
        self.shape = flip_shape(self.shape)

    def draw(self, screen, color):
        """Draw block on screen with specified color."""
        for r_idx, row in enumerate(self.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        screen,
                        color,
                        (
                            self.x + c_idx * CELL_SIZE,
                            self.y + r_idx * CELL_SIZE,
                            CELL_SIZE - 2,
                            CELL_SIZE - 2,
                        ),
                    )

    def get_cells(self):
        """Get list of occupied cells in the block."""
        cells = []
        for r_idx, row in enumerate(self.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    cells.append((r_idx, c_idx))
        return cells


class Board:
    """Game board and state management for 4-player game."""
    
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.corner_positions = [
            (0, 0), 
            (0, GRID_SIZE - 1), 
            (GRID_SIZE - 1, 0), 
            (GRID_SIZE - 1, GRID_SIZE - 1)
        ]
        self.current_player = 0
        self.player_scores = [0, 0, 0, 0]
        self.player_first_move = [True, True, True, True]
        self.player_skipped = [0, 0, 0, 0]
        self.player_available_blocks = [[True] * 21 for _ in range(4)]

    def draw(self, screen):
        """Draw game board with current state."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x = BOARD_OFFSET_X + c * CELL_SIZE
                y = BOARD_OFFSET_Y + r * CELL_SIZE
                cell_value = self.grid[r][c]
                
                if cell_value == 0:
                    color = (255, 255, 255)
                else:
                    player_id = cell_value - 1
                    color = PLAYER_COLORS[player_id]
                
                pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, GRID_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 1)

    def is_touching_corner(self, block, player_id):
        """Check if block touches any corner of the board."""
        grid_x = round((block.x - BOARD_OFFSET_X) / CELL_SIZE)
        grid_y = round((block.y - BOARD_OFFSET_Y) / CELL_SIZE)

        for r_idx, c_idx in block.get_cells():
            target_r = grid_y + r_idx
            target_c = grid_x + c_idx
            for corner_r, corner_c in self.corner_positions:
                if target_r == corner_r and target_c == corner_c:
                    return True
        return False

    def can_place(self, block, player_id):
        """Check if block can be placed at current position."""
        grid_x = round((block.x - BOARD_OFFSET_X) / CELL_SIZE)
        grid_y = round((block.y - BOARD_OFFSET_Y) / CELL_SIZE)

        # Check grid bounds and empty cells
        for r_idx, c_idx in block.get_cells():
            target_r = grid_y + r_idx
            target_c = grid_x + c_idx
            if not (0 <= target_r < GRID_SIZE and 0 <= target_c < GRID_SIZE):
                return False
            if self.grid[target_r][target_c] != 0:
                return False

        # First move must touch corner
        if self.player_first_move[player_id]:
            if not self.is_touching_corner(block, player_id):
                return False

        return True

    def place_block(self, block, player_id):
        """Place block on board and update score."""
        if not self.can_place(block, player_id):
            return False

        grid_x = round((block.x - BOARD_OFFSET_X) / CELL_SIZE)
        grid_y = round((block.y - BOARD_OFFSET_Y) / CELL_SIZE)

        placed = 0
        for r_idx, c_idx in block.get_cells():
            target_r = grid_y + r_idx
            target_c = grid_x + c_idx
            self.grid[target_r][target_c] = player_id + 1
            placed += 1

        self.player_scores[player_id] += placed
        self.player_first_move[player_id] = False
        self.player_available_blocks[player_id][block.block_id] = False
        return True

    def skip_turn(self, player_id):
        """Skip current player's turn."""
        self.player_first_move[player_id] = False
        self.player_skipped[player_id] += 1

    def next_player(self):
        """Advance to next player's turn."""
        self.current_player = (self.current_player + 1) % 4

    def get_player_name(self):
        """Get name of current player."""
        return f"Player {self.current_player + 1}"

    def get_available_block_count(self, player_id):
        """Get count of available blocks for player."""
        return sum(self.player_available_blocks[player_id])


# ============================================================================
# UI DRAWING FUNCTIONS
# ============================================================================

def draw_block_palette(screen, board, current_player_id):
    """Draw available blocks palette on right side of screen."""
    palette_x = PALETTE_X
    palette_y = PALETTE_Y
    
    # Draw panel background
    pygame.draw.rect(screen, UI_BG_COLOR, (palette_x - 20, palette_y - 20, 830, 850))
    pygame.draw.rect(screen, TEXT_COLOR, (palette_x - 20, palette_y - 20, 830, 850), 2)
    
    draw_text(
        screen, 
        f"Available Blocks - {['P1', 'P2', 'P3', 'P4'][current_player_id]}", 
        palette_x, palette_y, 20, PLAYER_COLORS[current_player_id]
    )
    
    cell_size = 35
    start_y = palette_y + 35
    block_idx = 0
    
    # Draw each available block
    for idx in range(21):
        if not board.player_available_blocks[current_player_id][idx]:
            continue
        
        x = palette_x + 10
        y = start_y + block_idx * (cell_size + 8)
        
        # Block label
        draw_text(screen, f"Block {idx}", x, y, 14, TEXT_COLOR)
        
        # Block shape visualization
        block_shape = ALL_BLOCKS[idx]
        for r_idx, row_data in enumerate(block_shape):
            for c_idx, cell in enumerate(row_data):
                if cell:
                    pygame.draw.rect(
                        screen,
                        PLAYER_COLORS[current_player_id],
                        (x + 80 + c_idx * 12, y + 5 + r_idx * 12, 10, 10)
                    )
        
        block_idx += 1


def draw_game_info(screen, board):
    """Draw game information panel (scores, status, etc)."""
    draw_text(screen, "blokus like - 4 Players", 10, 10, 32)
    draw_text(
        screen, 
        f"Current: {board.get_player_name()}", 
        10, 50, 24, PLAYER_COLORS[board.current_player]
    )
    
    # Scores
    draw_text(screen, "Scores | Available:", 10, 90, 18)
    for i in range(4):
        available = board.get_available_block_count(i)
        score_text = f"P{i + 1}: {board.player_scores[i]} | {available}/21 blocks"
        draw_text(screen, score_text, 10, 115 + i * 25, 16, PLAYER_COLORS[i])
    
    # Game state
    if board.player_first_move[board.current_player]:
        status_text = "First move - touch corner"
    else:
        status_text = "Normal placement"
    draw_text(screen, status_text, 10, 220, 14)


# ============================================================================
# GAME LOGIC
# ============================================================================

def find_next_available_block(board, current_idx):
    """Find the next available block for current player."""
    for i in range(21):
        next_idx = (current_idx + 1 + i) % 21
        if board.player_available_blocks[board.current_player][next_idx]:
            return next_idx
    return current_idx


def advance_to_next_player(board):
    """Move to next player and get first available block."""
    board.next_player()
    for i in range(21):
        if board.player_available_blocks[board.current_player][i]:
            return i
    return 0


# ============================================================================
# MAIN GAME
# ============================================================================

def main():
    """Main game loop."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("blox - 4 Player Game")
    clock = pygame.time.Clock()
    board = Board()

    # Initialize current block
    current_block_idx = 0
    current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx, board.current_player)
    current_block.x = 100
    current_block.y = 750

    running = True
    offset_x = 0
    offset_y = 0
    message = ""

    # ========================================================================
    # Button Callbacks
    # ========================================================================
    
    def rotate_action():
        nonlocal message
        current_block.rotate()
        message = "Rotated"

    def flip_action():
        nonlocal message
        current_block.flip()
        message = "Flipped"

    def next_block_action():
        nonlocal current_block_idx, current_block, message
        current_block_idx = find_next_available_block(board, current_block_idx)
        current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx, board.current_player)
        current_block.x = 100
        current_block.y = 750
        message = "Next block"

    def skip_action():
        nonlocal current_block_idx, current_block, message
        board.skip_turn(board.current_player)
        current_block_idx = advance_to_next_player(board)
        current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx, board.current_player)
        current_block.x = 100
        current_block.y = 750
        message = f"{board.get_player_name()} - Turn skipped"

    # Create UI buttons
    buttons = [
        Button(10, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT, "Rotate (R)", rotate_action),
        Button(100, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT, "Flip (F)", flip_action),
        Button(190, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT, "Next (SPACE)", next_block_action),
        Button(280, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT, "Skip (S)", skip_action),
    ]

    # ========================================================================
    # Main Game Loop
    # ========================================================================
    
    while running:
        screen.fill(BG_COLOR)
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Update button hover states
        for button in buttons:
            button.check_hover((mouse_x, mouse_y))

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    rotate_action()
                elif event.key == pygame.K_f:
                    flip_action()
                elif event.key == pygame.K_SPACE:
                    next_block_action()
                elif event.key == pygame.K_s:
                    skip_action()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Check button clicks first
                    clicked_button = False
                    for button in buttons:
                        if button.check_click((mouse_x, mouse_y)):
                            clicked_button = True
                            break
                    
                    # If no button clicked, try to drag block
                    if not clicked_button:
                        block_width, block_height = get_shape_bounds(current_block.shape)
                        rect = pygame.Rect(
                            current_block.x, current_block.y, 
                            block_width * CELL_SIZE, block_height * CELL_SIZE
                        )
                        if rect.collidepoint(mouse_x, mouse_y):
                            current_block.is_dragging = True
                            offset_x = current_block.x - mouse_x
                            offset_y = current_block.y - mouse_y
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and current_block.is_dragging:
                    current_block.is_dragging = False
                    if board.place_block(current_block, board.current_player):
                        current_block_idx = advance_to_next_player(board)
                        current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx, board.current_player)
                        current_block.x = 100
                        current_block.y = 750
                        message = f"{board.get_player_name()} - Placed!"
                    else:
                        current_block.x = 100
                        current_block.y = 750
                        message = "Cannot place here"

        # Update block position while dragging
        if current_block.is_dragging:
            current_block.x = mouse_x + offset_x
            current_block.y = mouse_y + offset_y

        # ====================================================================
        # Rendering
        # ====================================================================
        
        # Draw board
        board.draw(screen)

        # Draw block preview (bottom left)
        preview = Block(current_block.shape, current_block.block_id, board.current_player)
        preview.x = 100
        preview.y = 750
        preview.draw(screen, PLAYER_COLORS[board.current_player])

        # Draw block on board with validity feedback
        if current_block.is_dragging:
            if board.can_place(current_block, board.current_player):
                current_block.draw(screen, VALID_COLOR)
            else:
                current_block.draw(screen, INVALID_COLOR)
        else:
            current_block.draw(screen, PLAYER_COLORS[board.current_player])

        # Draw UI panels
        draw_game_info(screen, board)
        draw_text(screen, message, 10, 245, 14)
        
        # Draw buttons
        for button in buttons:
            button.draw(screen)

        # Draw block palette
        draw_block_palette(screen, board, board.current_player)

        # Update display
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
