import sys
import pygame

SCREEN_WIDTH = 600
SCREEN_HEIGHT =600
GRID_SIZE = 10 
CELL_SIZE = 40
BOARD_OFFSET_X = 100
BOARD_OFFSET_Y =100
BG_COLOR = (240, 240, 240)
GRID_COLOR = (200, 200, 200)
BLOCK_COLOR = (70, 130, 180)
TERRITORY_COLOR = (34, 139, 34)

class Block:
    def __init__(self, shape):
        self.shape = shape
        self.x = 0
        self.y = 0
        self.is_dragging = False

    def draw(self, screen):
        for r_idx, row in enumerate(self.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        screen,
                        BLOCK_COLOR,
                        (self.x + c_idx * CELL_SIZE, self.y + r_idx * CELL_SIZE, CELL_SIZE - 2, CELL_SIZE - 2)
                    )

class Board:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def draw(self, screen):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x = BOARD_OFFSET_X + c * CELL_SIZE
                y = BOARD_OFFSET_Y + r * CELL_SIZE
                color = TERRITORY_COLOR if self.grid[r][c] == 1 else (255,255,255)
                pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, GRID_COLOR, (x, y, CELL_SIZE, CELL_SIZE), 1)

    def try_place(self, block):
        grid_x = round((block.x - BOARD_OFFSET_X) / CELL_SIZE)
        grid_y = round((block.y - BOARD_OFFSET_Y) / CELL_SIZE)

        for r_idx, row in enumerate(block.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    target_r = grid_y + r_idx
                    target_c = grid_x + c_idx

                    if not(0 <= target_r < GRID_SIZE and 0 <= target_c < GRID_SIZE):
                        return False
                    if self.gird[target_r][target_c] != 0:
                        return False
        for r_idx, row in enumerate(block.shape):
            for c_idx, cell in enumerate(row):
                if cell:
                    self.grid[grid_y + r_idx][grid_x + c_idx] =1
        return True

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.diplay.set_caption("blox")
    clock = pygame.time.set_Clock()
    board = Board()

    current_block = Block([[1,0], [1,0], [1,1]])
    current_block.x = 250
    current_block.y = 480

    running = True
    while running:
        screen.fill(BG_COLOR)
        mouse_x, mouse_y = pygame.mouse.get_pos()

        for event in pygame.event.get_pos():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 #LEFT CLCK
                    block_rect = pygame.Rect(current_block.x, current_block.y, CELL_SIZE * 2, CELL_SIZE * 3)
                    if block_rect.collidepoint(mouse_x, mouse_y):
                        current_block.is_dragging = True
                        offset_x = current_block.x - mouse_x
                        offset_y = current_block.y - mouse_y
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and current_block.is_dragging:
                    current_block.is_dragging = False
                    if board.try_place(current_block):
                        current_block.x = 250
                        current_block.y = 480
                    else:
                        current_block.x = 250
                        current_block.y = 480

    if current_block.is_dragging:
        current_block.x = mouse_x + offset_x
        current_block.y = mouse_y + offset_y
    board.draw(screen)
    current_block.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

if __name__== "__main__":
    main()
