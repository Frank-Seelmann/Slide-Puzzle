import pygame
import random

globalFont = 'freesansbold.ttf'


def main():
    # initialization process
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Slide Puzzle')
    fpsclock = pygame.time.Clock()
    fps = 60
    n = 4
    puzzle = SlidePuzzle((n, n), 120, 2)
    puzzle.rect.center = (400, 300)
    # buttons that appear on the left side of the puzzle
    buttons = {}
    buttons['mix'] = Button((50, 200), (50, 50), puzzle.randomize, 'Mix')
    buttons['solve'] = Button((50, 70), (50, 50), puzzle.solve, 'Solve')
    buttons['stop'] = Button((50, 70), (50, 50), puzzle.stop, 'Stop')

    # flag that gets set false to close the pygame window
    running = True
    while running:
        pygame.display.set_caption('15 Solver')
        mouse = pygame.mouse.get_pressed()
        mPos = pygame.mouse.get_pos()

        solve = buttons['stop' if puzzle.solving else 'solve']
        collide = None
        for b in (solve, buttons['mix']):
            if b.collide(mPos):
                collide = b
                break

        puzzle.draw(screen)
        solve.draw(screen)
        buttons['mix'].draw(screen)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if collide:
                    if collide is buttons['mix']:
                        collide(1000)
                    else:
                        collide()
        puzzle.update(fpsclock.tick(fps) / 1000, pygame.key.get_pressed(), mouse, mPos)


class Button:
    def __init__(self, pos, size, functions, text):
        self.x, self.y = pos
        self.width, self.height = size
        self.functions = functions if hasattr(functions, '__iter__') else (functions,)
        self.right, self.bottom = self.x + self.width, self.y + self.height
        self.image = CreateText(text, size)

    def __call__(self, *args):
        for function in self.functions:
            function(*args)

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y, self.width, self.height))

    def collide(self, pos):
        return self.x <= pos[0] < self.right and self.y <= pos[1] < self.bottom


class Solver:
    def __init__(self, size):
        self.lastMoves = []
        self.width, self.height = self.gs = size
        self.takeToCache = None
        self.flipped = None
        self.d = [(x, y) for y in range(self.height) for x in range(self.width)]
        self.sides = [(x, y) for y in range(self.height - 2) for x in range(self.width - 2)]

    def goto(self, pos, sides):
        for i in self.addMoves(AStar(self.o, pos, sides, self.gs)):
            yield i

    def getTarget(self, start, end, sides):
        x, y = start
        X, Y = end
        dx, dy = (0 if X == x else 1 if X > x else -1), (0 if Y == y else 1 if Y > y else -1)
        targets = ([(x + dx, y)] if dx else []) + ([(x, y + dy)] if dy else [])
        for target in targets:
            if target in sides:
                targets.remove(target)
        return min(targets, key=lambda t: max(abs(self.o[0] - t[0]), abs(self.o[1] - t[1])))

    def takeTo(self, c, d, sides=[]):
        self.takeToCache = (c, self.d[d])
        while self.c[c] != self.d[d]:
            pos = self.getTarget(self.c[c], self.d[d], sides)
            for i in self.goto(pos, sides + [self.c[c]]):
                yield i
            for i in self.addMoves([self.c[c]]):
                yield i

    def getMoves(self, coords, targetCoords=None):

        t = list(targetCoords) if targetCoords else list(self.d)
        self.c = [coords[t.index(pos)] for pos in self.d]
        self.o = self.c[-1]

        for i in range(len(self.sides)):
            n = self.d.index(self.sides[i])
            for pos in self.takeTo(n, n, self.sides[:i]):
                yield pos

        for r1, r2, d1, s, r in (
                (1, 2, self.width, self.width * (self.height - 2), self.width - 2), (self.width, self.width * 2, 1, self.width - 2, self.height - 2)):
            for x1 in range(r):
                x1 = s + x1 * r1
                x2 = x1 + d1
                if self.c[x1] != self.d[x1] or self.c[x2] != self.d[x2]:
                    for i in self.takeTo(x1, x1 + r2, self.sides):
                        yield i
                    for i in self.takeTo(x2, x1, self.sides):
                        yield i
                    for i in self.takeTo(x1, x1 + r1, [self.d[x1]] + self.sides):
                        yield i
                    for i in self.goto(self.d[x2], [self.d[x1 + r1]] + self.sides):
                        yield i
                    for i in self.goto(self.d[x1 + r1], [self.d[x2 + r1]] + self.sides):
                        yield i

        for i in self.takeTo(-2 - self.width, -2 - self.width):
            yield i
        for i in self.addMoves((self.d[-1],)):
            yield i
        for i in self.addMoves(self.lastMoves[::-1]):
            yield i
        self.takeToCache = None
        yield False

    def addMoves(self, moves):
        for p in moves:
            self.c[self.c.index(p)] = self.o
            self.o = p
            yield p


class SlidePuzzle:
    previous = None
    moves = None
    solveSpeed = 3
    moveSpeed = 5

    def __init__(self, gs, ts, ms):
        self.gs, self.ts, self.ms = gs, ts, ms
        self.s = int(ts * 0.15)
        self.s2 = self.s // 2
        self.width, self.height = self.gs
        self.tileCenter = (ts // 2, ts // 2)
        self.lenTiles = self.width * self.height - 1
        self.solvedCoords = [(x, y) for y in range(self.height) for x in range(self.width)]
        self.solver = Solver(gs)
        self.rect = pygame.Rect(0, 0, self.width * (ts + ms) + ms, self.height * (ts + ms) + ms)
        self.target = {(x, y): [x * (ts + ms) + ms, y * (ts + ms) + ms] for y in range(self.height) for x in range(self.width)}
        self.set()
        self.genImages(self.coords)

    # getter & setter for blank tile(s)
    def getBlank(self):
        return self.coords[-1]
    def setBlank(self, pos):
        self.coords[-1] = pos
    openTile = property(getBlank, setBlank)

    # this is supposed to allow the puzzle to form a picture, but it doesn't work, so a white image is used in place
    def genImages(self, coords=None):
        if not coords: coords = self.solvedCoords
        gs, ts, ms = self.gs, self.ts, self.ms

        font = pygame.font.Font(globalFont, 200)
        self.image = pygame.transform.smoothscale(pygame.image.load("white.png"), self.rect.size)
        self.images = []

        for i in range(len(coords)):
            x, y = coords[i]
            number = str(i + 1)
            tileImage = self.image.subsurface(x * (ts + ms) + ms, y * (ts + ms) + ms, ts, ts)
            text = pygame.font.Font(globalFont, int(ts * 150 / max(font.size(number)))).render(number, 2,
                                                                                               (40, 180, 240))
            tileImage.blit(text, text.get_rect(center=self.tileCenter))
            self.images += [tileImage]

    # sets the board (initialize)
    def set(self):
        self.stop()
        ts = self.ts
        ms = self.ms
        self.tilePos = [[x * (ts + ms) + ms, y * (ts + ms) + ms] for y in range(self.height) for x in range(self.width)]
        self.coords = [(x, y) for y in range(self.height) for x in range(self.width)]

    # switches tile position when Mixing
    def switch(self, pos, solving=False):
        number = self.coords.index(pos)
        self.coords[number], self.openTile, self.previous = self.openTile, self.coords[number], self.openTile
        if not solving:
            self.stop()

    def inGrid(self, x, y):
        return x >= 0 and x < self.width and y >= 0 and y < self.height

    def adjacent(self, x, y):
        return tuple((X, Y) for X, Y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)) if self.inGrid(X, Y))

    def randomize(self, amount=1):
        for loop in range(amount):
            if self.width == 1 or self.height == 1:
                self.previous = None
            adjacent = self.adjacent(*self.openTile)
            adj = tuple(i for i in adjacent if i != self.previous)
            if adj:
                self.switch(random.choice(adj))

    def isMoveable(self):
        for i in range(self.lenTiles):
            if self.tilePos[i] != self.target[self.coords[i]]:
                return False
        return True

    def slideTiles(self):
        for i in range(self.lenTiles):
            a, b = self.tilePos[i], self.target[self.coords[i]]
            if a == b:
                continue
            for j in range(2):
                a[j] = b[j] if abs(a[j] - b[j]) < self.moveSpeed else a[j] + self.moveSpeed if a[j] < b[j] else \
                    a[j] - self.moveSpeed

    def setTarget(self, coords=None):
        self.solvedCoords = list(coords) if coords else list(self.coords)

    def solve(self):
        self.play(self.solver.getMoves(self.coords, self.solvedCoords))

    def play(self, moves):
        self.moves = moves

    def stop(self):
        self.moves = None
        self.time = 0
        self.solving = False

    def update(self, dt, key, mouse, mPos):
        if key[pygame.K_SPACE]:
            self.randomize(2)

        moveable = self.isMoveable()

        if not moveable:
            self.slideTiles()

        elif mouse[0]:
            x, y = mPos[0] - self.rect.x, mPos[1] - self.rect.y
            s = self.ts + self.ms
            if x % s > self.ms and y % s > self.ms:
                tile = x // s, y // s
                if self.inGrid(*tile):
                    for i in range(2):
                        while tile[i] == self.openTile[i] and self.openTile[i - 1] != tile[i - 1]:
                            self.switch(tuple(
                                (self.openTile[d] + (0 if i == d else 1 if tile[d] > self.openTile[d] else -1)) for d in
                                (0, 1)))

        if self.moves:
            self.time += dt * self.solveSpeed
            n = 0
            while self.time >= 1:
                self.time -= 1
                n += 1

            for i in range(n):
                pos = next(self.moves)
                if pos:
                    self.switch(pos, True)
                    self.solving = True
                else:
                    self.stop()
                    break

    def drawTile(self, screen, pos, color, t=0):
        pygame.draw.rect(screen, color, (self.rect.x + pos[0], self.rect.y + pos[1], self.ts, self.ts), t)

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 0, 0), self.rect)
        for i in range(self.lenTiles):
            x, y = self.tilePos[i]
            screen.blit(self.images[i], (self.rect.x + x, self.rect.y + y))

        if self.solving:
            cache = self.solver.takeToCache
            if cache:
                self.drawTile(screen, self.target[cache[1]], (255, 0, 0), 4)
                self.drawTile(screen, self.tilePos[self.coords.index(self.solver.c[cache[0]])], (0, 255, 0), 4)


def CreateText(text, size):
    s = 200
    factor = s * max(size) * 0.85
    f = pygame.font.Font(globalFont, s)
    center = (size[0] // 2, size[1] // 2)
    image = pygame.Surface(size).convert_alpha()
    image.fill((255, 255, 255, 255))
    text = pygame.font.Font(globalFont, int(factor / max(f.size(text)))).render(text, 2, (0, 0, 0))
    image.blit(text, text.get_rect(center=center))
    return image


# return a list of grid coords from start to end it is an A* search algorithm:
# https://en.wikipedia.org/wiki/A*_search_algorithm
# https://en.wikipedia.org/wiki/A*_search_algorithm#/media/File:Astar_progress_animation.gif
# At each iteration of its main loop, A* needs to determine which
# of its paths to extend. It does so based on the cost of the path and an estimate of the cost required to extend the
# path all the way to the goal. Specifically, A* selects the path that minimizes
# f(n) = g(n) + h(n)
# where n is the next node on the path, g(n) is the cost of the path from the start node to n,
# and h(n) is a heuristic function that
# estimates the cost of the cheapest path from n to the goal. A* terminates when the path it chooses to extend is a
# path from start to goal or if there are no paths eligible to be extended. The heuristic function is
# problem-specific. If the heuristic function is admissible, meaning that it never overestimates the actual cost to
# get to the goal, A* is guaranteed to return a least-cost path from start to goal.
def AStar(start, end, walls, size):
    # build entire grid. 'pos' = grid pos, 'parent' = parent tile, g = lowest cost, h = guess cost, and if it's a wall.
    cells = {(x, y): {'pos': (x, y), 'parent': None, 'g': 0, 'h': max(abs(x - end[0]), abs(y - end[1])), 'wall': (x, y) in walls} for y in range(size[1]) for x in range(size[0])}
    # opened search, closed search, path filled at end of search
    opened = [cells[start]]
    closed = []
    path = []
    # search
    while opened:
        # get "best" cell to search, mark searched
        current = min(opened, key=lambda i: i['g'] + i['h'])
        closed.append(current)
        opened.remove(current)
        # when end is reached, build path back to start
        if current['pos'] == end:
            while current['parent']:
                path.append(current['pos'])
                current = current['parent']
            return path[::-1]

        # search neighboring tiles
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            # change grid position
            x, y = current['pos'][0] + dx, current['pos'][1] + dy
            # skip if out of bounds
            if x < 0 or y < 0 or x >= size[0] or y >= size[1]:
                continue
            adj = cells[(x, y)]  # adj cell data
            # skip if wall or already searched
            if adj['wall'] or adj in closed:
                continue

            newCell = adj not in opened  # not queued or searched cell to be search
            newG = current['g'] + 1

            if newCell or newG < adj['g']:
                adj['parent'] = current
                adj['g'] = newG  # new or quicker route
            if newCell:
                opened.append(adj)  # new cell, possibly search it later

    # return empty if no route
    return []


if __name__ == '__main__':
    main()
