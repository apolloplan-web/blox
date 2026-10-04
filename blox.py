import sys
import pygame

SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 800
GRID_SIZE = 20
CELL_SIZE = 30
BOARD_OFFSET_X = 50
BOARD_OFFSET_Y = 50

BG_COLOR = (240, 240, 240)
GRID_COLOR = (200, 200, 200)
TEXT_COLOR = (0, 0, 0)
VALID_COLOR = (144, 238, 144)
INVALID_COLOR = (255, 100, 100)

# プレーヤーカラー
PLAYER_COLORS = [
    (70, 130, 180),      # Player 1: Steel Blue
    (220, 20, 60),       # Player 2: Crimson Red
    (34, 139, 34),       # Player 3: Forest Green
    (255, 165, 0),       # Player 4: Orange
]

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
    [[1, 0, 0], [1, 0, 0], [1, 1, 1]],
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
    def __init__(self, shape, block_id=0, player_id=0):
        self.original_shape = [row[:] for row in shape]
        self.shape = [row[:] for row in shape]
        self.block_id = block_id
        self.player_id = player_id
        self.x = 0
        self.y = 0
        self.is_dragging = False

    def rotate(self):
        self.shape = normalize_shape(rotate_shape(self.shape))

    def flip(self):
        self.shape = flip_shape(self.shape)

    def draw(self, screen, color):
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
        self.game_over = False

    def draw(self, screen):
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
        """指定プレーヤーのコーナーに触れているか"""
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
        """ブロックを置けるか確認"""
        grid_x = round((block.x - BOARD_OFFSET_X) / CELL_SIZE)
        grid_y = round((block.y - BOARD_OFFSET_Y) / CELL_SIZE)

        # グリッド範囲外チェック
        for r_idx, c_idx in block.get_cells():
            target_r = grid_y + r_idx
            target_c = grid_x + c_idx
            if not (0 <= target_r < GRID_SIZE and 0 <= target_c < GRID_SIZE):
                return False
            if self.grid[target_r][target_c] != 0:
                return False

        # 最初の手の場合はコーナー要件チェック
        if self.player_first_move[player_id]:
            if not self.is_touching_corner(block, player_id):
                return False

        return True

    def place_block(self, block, player_id):
        """ブロックを配置"""
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
        return True

    def skip_turn(self, player_id):
        """ターンをスキップ"""
        self.player_first_move[player_id] = False
        self.player_skipped[player_id] += 1

    def next_player(self):
        """次のプレーヤーにターンを移す"""
        self.current_player = (self.current_player + 1) % 4

    def get_player_name(self):
        """現在のプレーヤー名"""
        return f"Player {self.current_player + 1}"


def draw_text(screen, text, x, y, font_size=24, color=TEXT_COLOR):
    font = pygame.font.Font(None, font_size)
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("blox - 4 Player Game")
    clock = pygame.time.Clock()
    board = Board()

    current_block_idx = 0
    current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx, board.current_player)
    current_block.x = 950
    current_block.y = 100

    running = True
    offset_x = 0
    offset_y = 0
    message = ""

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
                    current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx, board.current_player)
                    current_block.x = 950
                    current_block.y = 100
                    message = "Next block"
                elif event.key == pygame.K_s:
                    board.skip_turn(board.current_player)
                    board.next_player()
                    current_block_idx = (current_block_idx + 1) % len(ALL_BLOCKS)
                    current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx, board.current_player)
                    current_block.x = 950
                    current_block.y = 100
                    message = f"{board.get_player_name()} - Turn skipped"
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
                    if board.place_block(current_block, board.current_player):
                        board.next_player()
                        current_block_idx = (current_block_idx + 1) % len(ALL_BLOCKS)
                        current_block = Block(ALL_BLOCKS[current_block_idx], current_block_idx, board.current_player)
                        current_block.x = 950
                        current_block.y = 100
                        message = f"{board.get_player_name()} - Placed!"
                    else:
                        current_block.x = 950
                        current_block.y = 100
                        message = "Cannot place here"

        if current_block.is_dragging:
            current_block.x = mouse_x + offset_x
            current_block.y = mouse_y + offset_y

        board.draw(screen)

        # プレビューブロック描画（右側）
        preview = Block(current_block.shape, current_block.block_id, board.current_player)
        preview.x = 950
        preview.y = 100
        preview.draw(screen, PLAYER_COLORS[board.current_player])

        # ボード上のプレビュー（置ける/置けない）
        if board.can_place(current_block, board.current_player):
            current_block.draw(screen, VALID_COLOR)
        else:
            current_block.draw(screen, INVALID_COLOR)

        # UI描画
        draw_text(screen, "Territory Game - 4 Players", 10, 10, 32)
        draw_text(screen, f"Current: {board.get_player_name()}", 950, 10, 24, PLAYER_COLORS[board.current_player])
        
        # プレーヤースコア
        draw_text(screen, "Scores:", 950, 50, 20)
        for i in range(4):
            score_text = f"P{i + 1}: {board.player_scores[i]}"
            draw_text(screen, score_text, 950, 75 + i * 25, 18, PLAYER_COLORS[i])
        
        # 状態表示
        if board.player_first_move[board.current_player]:
            status_text = "First move - touch corner"
        else:
            status_text = "Normal placement"
        draw_text(screen, status_text, 950, 185, 16)
        
        # コントロール
        draw_text(screen, "R: Rotate  F: Flip  SPACE: Next", 950, 210, 14)
        draw_text(screen, "S: Skip    Drag to place", 950, 230, 14)
        
        # メッセージ
        draw_text(screen, message, 950, 250, 16)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
