import sys
import pygame

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
GRID_SIZE = 20
CELL_SIZE = 40
BOARD_OFFSET_X = 150
BOARD_OFFSET_Y = 50

BG_COLOR = (240, 240, 240)
GRID_COLOR = (200, 200, 200)
BLOCK_COLOR = (70, 130, 180)
TERRITORY_COLOR = (34, 139, 34)
TEXT_COLOR = (0, 0, 0)
VALID_COLOR = (144, 238, 144)
INVALID_COLOR = (255, 100, 100)

# 1マスから5マスまでの全21パターン
ALL_BLOCKS = [
    [[1]],
    [[1, 1]],
    [[1, 1, 1]],
    [[1, 0], [1, 1]],
    [[1, 1, 1, 1]],
    [[1, 0, 0], [1, 1, 1]],
    [[0, 1, 0], [1, 1, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[1, 1], [1, 1]],
    [[1, 1, 1, 1, 1]],
    [[1, 0, 0, 0], [1, 1, 1, 1]],
    [[0, 1, 0, 0], [1, 1, 1, 1]],
    [[1, 1, 0, 0], [0, 1, 1, 1]],
    [[1, 0, 1], [1, 1, 1]],
    [[1, 0], [1, 1], [1, 1]],
    [[1, 0, 0],[1, 0, 0], [1, 1, 1]],
    [[1, 0, 0], [1, 1, 0], [0, 1, 0]],
    [[1, 0, 0], [1, 1, 1], [0, 0, 1]],
    [[0, 1, 0], [1, 1, 1], [0, 1, 0]],
    [[1, 0, 0], [1, 1, 1], [0, 1, 0]],
    [[1, 0, 0], [1, 1, 1], [1, 0, 0]],
]


def rotate_shape(shape):
    rows = len(shape)
    cols = len(shape[0])
    result = [[0 for _ in range(rows)] for _ in range(cols)]
    for r in range(rows):
        for c in range(cols):
            result[c][rows - 1 - r] = shape[r][c]
    return result


def flip_shape(shape):
    return [row[::-1] for row in shape]


def normalize_shape(shape):
    min_r = min((r for r, row in enumerate(shape) for v in row if v), default=0)
    min_c = min((c for r, row in enumerate(shape) for c, v in enumerate(row) if v), default=0)
    rows = []
    for r in range(min_r, len(shape)):
        rows.append(shape[r][min_c:])
    return rows


def get_shape_bounds(shape):
    if not shape:
        return 0, 0
    height = len(shape)
    width = max(len(row) for row in shape)
    return width, height


class Block:
    def __init__(self, shape, block_id=0):
        self.original_shape = [row[:] for row in shape]
        self.shape = [row[:] for row in shape]
        self.block_id = block_id
        self.x = 0
        self.y = 0
        self.is_dragging = False

    def rotate(self):
        self.shape = normalize_shape(rotate_shape(self.shape))

    def flip(self):
        self.shape = flip_shape(self.shape)

    def draw(self, screen, color=BLOCK_COLOR):
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
        cells = []
        for r_idx, row in enumerate(self.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    cells.append((r_idx, c_idx))
        return cells


class Board:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.corner_positions = [(0, 0), (0, GRID_SIZE - 1), (GRID_SIZE - 1, 0), (GRID_SIZE - 1, GRID_SIZE - 1)]
        self.is_first_move = True
        self.skipped_turns = 0

    def draw(self, screen):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x = BOARD_OFFSET_X + c * CELL_SIZE
                y = BOARD_OFFSET_Y + r * CELL_SIZE
                color = TERRITORY_COLOR if self.grid[r][c] == 1 else (255, 255, 255)
                pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, GRID_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 1)

    def is_touching_corner(self, block):
        grid_x = round((block.x - BOARD_OFFSET_X) / CELL_SIZE)
        grid_y = round((block.y - BOARD_OFFSET_Y) / CELL_SIZE)

        for r_idx, c_idx in block.get_cells():
            target_r = grid_y + r_idx
            target_c = grid_x + c_idx
            for corner_r, corner_c in self.corner_positions:
                if target_r == corner_r and target_c == corner_c:
                    return True
        return False

    def can_place(self, block, require_corner=False):
        grid_x = round((block.x - BOARD_OFFSET_X) / CELL_SIZE)
        grid_y = round((block.y - BOARD_OFFSET_Y) / CELL_SIZE)

        for r_idx, c_idx in block.get_cells():
            target_r = grid_y + r_idx
            target_c = grid_x + c_idx
            if not (0 <= target_r < GRID_SIZE and 0 <= target_c < GRID_SIZE):
                return False
            if self.grid[target_r][target_c] != 0:
                return False

        if require_corner and not self.is_touching_corner(block):
            return False

        return True

    def place_block(self, block):
        if not self.can_place(block, self.is_first_move):
            return False

        grid_x = round((block.x - BOARD_OFFSET_X) / CELL_SIZE)
        grid_y = round((block.y - BOARD_OFFSET_Y) / CELL_SIZE)

        for r_idx, c_idx in block.get_cells():
            target_r = grid_y + r_idx
            target_c = grid_x + c_idx
            self.grid[target_r][target_c] = 1

        self.is_first_move = False
        return True

    def skip_turn(self):
        """ターンをスキップ"""
        self.is_first_move = False
        self.skipped_turns += 1
        return True

    def get_score(self):
        return sum(cell for row in self.grid for cell in row)


def draw_text(screen, text, x, y, font_size=24, color=TEXT_COLOR):
    font = pygame.font.Font(None, font_size)
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("blox")
    clock = pygame.time.Clock()
    board = Board()

    current_block_idx = 0
    current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx)
    current_block.x = SCREEN_WIDTH - 220
    current_block.y = 120

    running = True
    offset_x = 0
    offset_y = 0
    message = "R: rotate  F: flip  SPACE: next  S: skip"

    while running:
        screen.fill(BG_COLOR)
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    current_block.rotate()
                    message = "Rotated"
                elif event.key == pygame.K_f:
                    current_block.flip()
                    message = "Flipped"
                elif event.key == pygame.K_SPACE:
                    current_block_idx = (current_block_idx + 1) % len(ALL_BLOCKS)
                    current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx)
                    current_block.x = SCREEN_WIDTH - 220
                    current_block.y = 120
                    message = "Next block"
                elif event.key == pygame.K_s:
                    board.skip_turn()
                    current_block_idx = (current_block_idx + 1) % len(ALL_BLOCKS)
                    current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx)
                    current_block.x = SCREEN_WIDTH - 220
                    current_block.y = 120
                    message = "Turn skipped!"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    block_width, block_height = get_shape_bounds(current_block.shape)
                    rect = pygame.Rect(current_block.x, current_block.y, block_width * CELL_SIZE, block_height * CELL_SIZE)
                    if rect.collidepoint(mouse_x, mouse_y):
                        current_block.is_dragging = True
                        offset_x = current_block.x - mouse_x
                        offset_y = current_block.y - mouse_y
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and current_block.is_dragging:
                    current_block.is_dragging = False
                    if board.place_block(current_block):
                        current_block_idx = (current_block_idx + 1) % len(ALL_BLOCKS)
                        current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx)
                        current_block.x = SCREEN_WIDTH - 220
                        current_block.y = 120
                        message = "Placed!"
                    else:
                        current_block.x = SCREEN_WIDTH - 220
                        current_block.y = 120
                        message = "Cannot place here"

        if current_block.is_dragging:
            current_block.x = mouse_x + offset_x
            current_block.y = mouse_y + offset_y

        board.draw(screen)

        # 右側の選択ブロック描画
        preview = Block(current_block.shape, current_block.block_id)
        preview.x = SCREEN_WIDTH - 220
        preview.y = 120
        preview.draw(screen, BLOCK_COLOR)

        # ボード上に置けるかのプレビュー
        if board.can_place(current_block, board.is_first_move):
            current_block.draw(screen, VALID_COLOR)
        else:
            current_block.draw(screen, INVALID_COLOR)

        draw_text(screen, "Territory Game", 10, 10, 30)
        draw_text(screen, f"Score: {board.get_score()}", 10, 50, 24)
        draw_text(screen, f"Skipped: {board.skipped_turns}", 10, 80, 18)
        draw_text(screen, "First move must touch a corner" if board.is_first_move else "Normal placement", 10, 110, 18)
        draw_text(screen, message, 10, SCREEN_HEIGHT - 40, 18)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
