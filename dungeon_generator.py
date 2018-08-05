##################################################################
#                                                                #
# Procedural Dungeon Generator v1.1                              #
#                                                                #
# By Jay (Battery)                                               #
#                                                                #
# https://whatjaysaid.wordpress.com/                             #
# for how use it got to:                                         #
# https://whatjaysaid.wordpress.com/2016/01/15/1228              #
#                                                                #
# Feel free to use this as you wish, but please keep this header #
#                                                                #
##################################################################
 
 
from random import randint, choice, randrange
 
# tile constants
EMPTY = 0
FLOOR = 1
CORRIDOR = 2
DOOR = 3
DEAD_END = 4
WALL = 5
OBSTACLE = 6
CAVE = 7
 
 
class DungeonRoom:
    """ 
    a simple container for dungeon rooms
    since you may want to return to constructing a room, edit it, etc. it helps to have some way to save them
    without having to search through the whole game grid
         
    Args:
        x and y coordinates for the room
        width and height for the room
    Attributes:
        x, y: the starting coordinates in the 2d array
        width: the amount of cells the room spans
        height: the amount of cells the room spans
    """
     
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class DungeonGenerator:
    """
    A renderer/framework/engine independent functions for generating random dungeons, including rooms, corridors,
    connects and path finding
     
    The dungeon is built around a 2D list, the resulting dungeon is a 2D tile map, where each x,y point holds a
    constant. The grid can then be iterated through using the contained constant to determine the tile to render and
    the x,y indices can be multiplied by x,y size of the tile. The class it's self can be iterated through. For example:
        tileSize = 2
        for x, y, tile in dungeonGenerator:
            if tile = FLOOR:
                render(floorTile)
                floorTile.xPosition = x * tileSize
                floorTile.yPosition = y * tileSize
            and so forth...
     
    Alternatively:
        for x in range(dungeonGenerator.width):
            for y in range(dungeonGenerator.height):
                if dungeonGenerator.grid[x][y] = FLOOR:
                    render(floorTile)
                    floorTile.xPosition = x * tileSize
                    floorTile.yPosition = y * tileSize
                and so forth...
     
    Throughout x,y refer to indices in the tile map, nx,ny are used to refer to neighbours of x,y
     
    Args:
        height and width of the dungeon to be generated
    Attributes:
        width: size of the dungeon in the x dimension
        height: size of the dungeon in the y dimension
        grid: a 2D list (grid[x][y]) for storing tile constants (read tile map)
        rooms: **list of all the DungeonRoom objects in the dungeon, empty until place_random_rooms() is called
        rooms: **list of all the DungeonRoom objects in the dungeon, empty until place_random_rooms() is called
        doors: **list of all grid coordinates of the corridor to room connections, elements are tuples (x,y),
        empty until connect_all_rooms() is called
        corridors: **list of all the corridor tiles in the grid, elements are tuples (x,y), empty until
        generate_corridors() is called
        dead_ends: list of all corridor tiles only connected to one other tile, elements are tuples (x,y),
        empty until find_dead_ends() is called
        graph: dictionary where keys are the coordinates of all floor/corridor tiles and values are a list of
        floor/corridor directly connected, ie (x, y): [(x+1, y), (x-1, y), (x, y+1), (x, y-1)],
        empty until constructGraph() is called
         
        ** once created these will not be re-instanced, therefore any user made changes to grid will also need to
        update these lists for them to remain valid
    """
     
    def __init__(self, height, width):
        self.height = abs(height)
        self.width = abs(width)
        self.grid = [[EMPTY for i in range(self.height)] for i in range(self.width)]
        self.rooms = []
        self.doors = []
        self.corridors = []
        self.dead_ends = []
        self.graph = {}
         
    def __iter__(self):
        for xi in range(self.width):
            for yi in range(self.height):
                yield xi, yi, self.grid[xi][yi]
  
    # HELPER FUNCTIONS
     
    def find_neighbours(self, x, y):
        """
        finds all cells that touch a cell in a 2D grid
         
        Args:
            x and y: integer, indices for the cell to search around
        Returns:
            returns a generator object with the x,y indices of cell neighbours
        """
        xi = (0, -1, 1) if 0 < x < self.width - 1 else ((0, -1) if x > 0 else (0, 1))
        yi = (0, -1, 1) if 0 < y < self.height - 1 else ((0, -1) if y > 0 else (0, 1))
        for a in xi:
            for b in yi:
                if a == b == 0:
                    continue
                yield (x+a, y+b)
                 
    def find_neighbours_direct(self, x, y):
        """
        finds all neighbours of a cell that directly touch it (up, down, left, right) in a 2D grid
         
        Args:
            x and y: integer, indices for the cell to search around
        Returns:
            returns a generator object with the x,y indices of cell neighbours
        """
        xi = (0, -1, 1) if 0 < x < self.width - 1 else ((0, -1) if x > 0 else (0, 1))
        yi = (0, -1, 1) if 0 < y < self.height - 1 else ((0, -1) if y > 0 else (0, 1))
        for a in xi:
            for b in yi:
                if abs(a) == abs(b):
                    continue
                yield (x+a, y+b)
             
    def can_carve(self, x, y, xd, yd):
        """
        checks to see if a path can move in certain direction, used by get_possible_moves()
         
        Args:
            x and y: integer, indices in the 2D grid of the starting cell
            xd and xy: integer, direction trying to move in where (-1,0) = left, (1,0) = right, (0,1) = up, (0,-1) = down
        Returns:
            True if it is safe to move that way
        """
        xi = (-1, 0, 1) if not xd else (1*xd, 2*xd)
        yi = (-1, 0, 1) if not yd else (1*yd, 2*yd)
        for a in xi:
            for b in yi:
                if self.grid[a+x][b+y]:
                    return False
        return True
     
    def get_possible_moves(self, x, y):
        """
        searches for potential directions that a corridor can expand in
        used by generatePath()
         
        Args:
            x and y: integer, indices of the tile on grid to find potential moves (up, down, left, right) for
        Returns:
            a list of potential x,y coords that the path could move it, each entry stored as a tuple
        """
        available_squares = []
        for nx, ny in self.find_neighbours_direct(x, y):
            if nx < 1 or ny < 1 or nx > self.width-2 or ny > self.height-2:
                continue
            xd = nx - x
            yd = ny - y
            if self.can_carve(x, y, xd, yd):
                available_squares.append((nx, ny))
        return available_squares
     
    def quad_fits(self, sx, sy, rx, ry, margin):
        """
        looks to see if a quad shape will fit in the grid without colliding with any other tiles
        used by place_room() and place_random_rooms()
         
        Args:
            sx and sy: integer, the bottom left coords of the quad to check
            rx and ry: integer, the width and height of the quad, where rx > sx and ry > sy
            margin: integer, the space in grid cells (ie, 0 = no cells, 1 = 1 cell, 2 = 2 cells) to be away from other
            tiles on the grid
        returns:
            True if the quad fits
        """
        sx -= margin
        sy -= margin
        rx += margin*2
        ry += margin*2
        if sx + rx < self.width and sy + ry < self.height and sx >= 0 and sy >= 0:
            for x in range(rx):
                for y in range(ry):
                    if self.grid[sx+x][sy+y]: 
                        return False
            return True
        return False
     
    def flood_fill(self, x, y, fill_with, tiles_to_fill=[], grid=None):
        """
        Fills tiles connected to the starting tile
        passing the same fill_with value as the starting tile value will produce no results since they're already filled
         
        Args:
            x and y: integers, the grid coords to star the flood fill, all filled tiles will be connected to this tile
            fill_with: integer, the constant of the tile to fill with
            tiles_to_fill: list of integers, allows you to control what tile get filled, all if left out
            grid: list[[]], a 2D array to flood fill, by default this is dungeonGenerator.grid, however if you do not
            want to overwrite this you can provide your own 2D array (such as a deep copy of dungeonGenerator.grid)
        Returns:
            none
        """
        if not grid:
            grid = self.grid
        to_fill = set()
        to_fill.add((x, y))
        count = 0
        while to_fill:
            x, y = to_fill.pop()
            if tiles_to_fill and grid[x][y] not in tiles_to_fill:
                continue
            if not grid[x][y]:
                continue
            grid[x][y] = fill_with
            for nx, ny in self.find_neighbours_direct(x, y):
                if grid[nx][ny] != fill_with:
                    to_fill.add((nx, ny))
            count += 1
            if count > self.width * self.height:
                print('overrun')
                break

    # LEVEL SEARCH FUNCTIONS
             
    def find_empty_space(self, distance):
        """
        Finds the first empty space encountered in the 2D grid that it not surrounding by anything within the given distance
         
        Args:
            distance: integer, the distance from the current x,y point being checked to see if is empty
             
        Returns:
            the x,y indices of the free space or None, None if no space was found
        """
        for x in range(distance, self.width - distance):
            for y in range(distance, self.height - distance):
                touching = 0
                for xi in range(-distance, distance):
                    for yi in range(-distance, distance):
                        if self.grid[x+xi][y+yi]:
                            touching += 1
                if not touching: 
                    return x, y                    
        return None, None
     
    def find_unconnected_areas(self):
        """
        Checks through the grid to find islands/unconnected rooms
        Note, this can be slow for large grids and memory intensive since it needs to create a deep copy of the grid
        in order to use join_unconnected_areas() this needs to be called first and the returned list passed to
        join_unconnected_areas()
         
        Args:
            None
        Returns:
            A list of unconnected cells, where each group of cells is in its own list and each cell index is stored as
            a tuple, ie [[(x1,y1), (x2,y2), (x3,y3)], [(xi1,yi1), (xi2,yi2), (xi3,yi3)]]
        """
        unconnected_areas = []
        area_count = 0
        grid_copy = [[EMPTY for i in range(self.width)] for i in range(self.height)]
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y]:
                    grid_copy[x][y] = 'x'
        for x in range(self.width):
            for y in range(self.height):                
                if grid_copy[x][y] == 'x':
                    unconnected_areas.append([])
                    area_count += 1
                    self.flood_fill(x, y, area_count, None, grid_copy)
        for x in range(self.width):
            for y in range(self.height):
                if grid_copy[x][y]:
                    i = grid_copy[x][y]
                    unconnected_areas[i-1].append((x, y))
        return unconnected_areas
     
    def find_dead_ends(self):
        """
        looks through all the corridors generated by generatePath() and join_unconnected_areas() to identify dead ends
        populates self.dead_ends and is used by prune_dead_ends()
         
        Args:
            none
        Returns:
            none
        """
        self.dead_ends = []
        for x, y in self.corridors:
            touching = 0
            for nx, ny in self.find_neighbours_direct(x, y):
                if self.grid[nx][ny]: touching += 1
            if touching == 1:
                self.dead_ends.append((x, y))
             
     
    # GENERATION FUNCTIONS
     
    def place_room(self, start_x, start_y, room_width, room_height, ignore_overlap=False):
        """
        place a defined quad within the grid and add it to self.rooms
         
        Args:
            x and y: integer, starting corner of the room, grid indicies
            roomWdith and room_height: integer, height and width of the room where room_width > x and room_height > y
            ignore_overlap: boolean, if true the room will be placed irregardless of if it overlaps with any other tile in the grid
                note, if true then it is up to you to ensure the room is within the bounds of the grid
        Returns:
            True if the room was placed
        """
        if self.quad_fits(start_x, start_y, room_width, room_height, 0) or ignore_overlap:
            for x in range(room_width):
                for y in range(room_height):
                    self.grid[start_x+x][start_y+y] = FLOOR
            self.rooms.append(DungeonRoom(start_x, start_y, room_width, room_height))
            return True
         
    def place_random_rooms(self, min_room_size, max_room_size, room_step=1, margin=1, attempts=500):
        """ 
        randomly places quads in the grid
        takes a brute force approach: randomly a generate quad in a random place -> check if fits -> reject if not
        Populates self.rooms
         
        Args:
            min_room_size: integer, smallest size of the quad
            max_room_size: integer, largest the quad can be
            room_step: integer, the amount the room size can grow by, so to get rooms of odd or even numbered sizes set
            roomSize to 2 and the minSize to odd/even number accordingly
            margin: integer, space in grid cells the room needs to be away from other tiles
            attempts: the amount of tries to place rooms, larger values will give denser room placements, but slower
            generation times
        Returns:
            none
        """
        for attempt in range(attempts):
            room_width = randrange(min_room_size, max_room_size, room_step)
            room_height = randrange(min_room_size, max_room_size, room_step)
            start_x = randint(0, self.width)
            start_y = randint(0, self.height)
            if self.quad_fits(start_x, start_y, room_width, room_height, margin):
                for x in range(room_width):
                    for y in range(room_height):
                        self.grid[start_x+x][start_y+y] = FLOOR
                self.rooms.append(DungeonRoom(start_x, start_y, room_width, room_height))
                    
    def generate_caves(self, p=45, smoothing=4):
        """
        Generates more organic shapes using cellular automata
         
        Args:
            p: the probability that a cell will become a cave section, values between 30 and 45 work well
            smoothing: amount of noise reduction, lower values produce more jagged caves, little effect past 4
        Returns:
            None
        """
        for x in range(self.width):
            for y in range(self.height):
                if randint(0, 100) < p:
                    self.grid[x][y] = CAVE
        for i in range(smoothing):
            for x in range(self.width):
                for y in range(self.height):
                    if x == 0 or x == self.width or y == 0 or y == self.height:
                        self.grid[x][y] = EMPTY
                    touching_empty_space = 0
                    for nx, ny in self.find_neighbours(x,y):
                        if self.grid[nx][ny] == CAVE: 
                            touching_empty_space += 1
                    if touching_empty_space >= 5:
                        self.grid[x][y] = CAVE
                    elif touching_empty_space <= 2:
                        self.grid[x][y] = EMPTY
     
    def generate_corridors(self, mode='r', x=None, y=None):
        """
        generates a maze of corridors on the growing tree algorithm, 
        where corridors do not overlap with over tiles, are 1 tile away from anything else and there are no diagonals
        Populates self.corridors
         
        Args:
            mode: char, either 'r', 'f', 'm' or 'l'
                  this controls how the next tile to attempt to move to is determined and affects generated corridors
                  'r' - random selection, produces short straight sections with spine like off-shoots, lots of dead_ends
                  'f' - first cell in the list to check, long straight sections and few diagonal snaking sections
                  'm' - similar to first but more likely to snake
                  'l' - snaking and winding corridor sections
            x and y: integer, grid indices, starting point for the corridor generation,
                     if none is provided a random one will be chosen
            Returns:
                none
        """
        cells = [] 
        if not x and not y:       
            x = randint(1, self.width-2)
            y = randint(1, self.height-2)        
            while not self.can_carve(x, y, 0, 0):
                x = randint(1, self.width-2)
                y = randint(1, self.height-2)
        self.grid[x][y] = CORRIDOR
        self.corridors.append((x, y))
        cells.append((x, y))
        while cells:
            if mode == 'l':
                x, y = cells[-1]
            elif mode == 'r':
                x, y = choice(cells)
            elif mode == 'f':
                x, y = cells[0]
            elif mode == 'm':
                x, y = cells[len(cells)//2]
            possible_moves = self.get_possible_moves(x, y)
            if possible_moves:
                xi, yi = choice(possible_moves)
                self.grid[xi][yi] = CORRIDOR
                self.corridors.append((xi, yi))
                cells.append((xi, yi))
            else:
                cells.remove((x, y))                
     
    def prune_dead_ends(self, amount):
        """
        Removes dead_ends from the corridors/maze
        each iteration will remove all identified dead ends
        it will update self.dead_ends after
         
        Args:
            amount: number of iterations to remove dead ends
        Returns:
            none
        """
        for i in range(amount):
            self.find_dead_ends()
            for x, y in self.dead_ends:
                self.grid[x][y] = EMPTY
                self.corridors.remove((x, y))
        self.find_dead_ends()
                 
    def place_walls(self):
        """
        Places wall tiles around all floor, door and corridor tiles
        As some functions (like flood_fill() and anything that uses it) don't distinguish between tile types it is best
        called later/last
        """
        for x in range(self.width):
            for y in range(self.height):
                if not self.grid[x][y]:
                    for nx, ny in self.find_neighbours(x, y):
                        if self.grid[nx][ny] and self.grid[nx][ny] is not WALL:
                            self.grid[x][y] = WALL
                            break         
                                             
    def connect_all_rooms(self, extra_door_chance=0):
        """
        Joins rooms to the corridors
        This not guaranteed to join everything,
        depending on how rooms are placed and corridors generated it is possible to have unreachable rooms
        in that case join_unconnected_areas() can join them
        Populates self.doors
         
        Args:
            extra_door_chance: integer, where 0 >= extra_door_chance <= 100, the chance a room will have more than one connection to the corridors
        if extra_door_chance >= 100: extra_door_chance = 99
        Returns:
            list of DungeonRoom's that are not connected, this will not include islands, so 2 rooms connected to each other, but not the rest will not be included
        """
        unconnected_rooms = []
        for room in self.rooms:
            connections = []
            for i in range(room.width):
                if self.grid[room.x+i][room.y-2]:
                    connections.append((room.x+i, room.y-1))                
                if room.y+room.height+1 < self.height and self.grid[room.x+i][room.y+room.height+1]:
                    connections.append((room.x+i, room.y+room.height))                
            for i in range(room.height):
                if self.grid[room.x-2][room.y+i]:
                    connections.append((room.x-1, room.y+i))                
                if room.x+room.width+1 < self.width and self.grid[room.x+room.width+1][room.y+i]:
                    connections.append((room.x+room.width, room.y+i))
            if connections:
                chance = -1
                while chance <= extra_door_chance:
                    pick_again = True
                    while pick_again:
                        x, y = choice(connections)
                        pick_again = False
                        for xi, yi in self.find_neighbours(x, y):
                            if self.grid[xi][yi] == DOOR:
                                pick_again = True
                                break
                    chance = randint(0, 100)
                    self.grid[x][y] = DOOR
                    self.doors.append((x, y))
            else:
                unconnected_rooms.append(room)
        return unconnected_rooms
             
    def join_unconnected_areas(self, unconnected_areas):
        """
        Forcibly connect areas not joined together
        This will work nearly every time (I've seen one test case where an area was still un-joined)
        But it will not always produce pretty results - connecting paths may cause diagonal touching
         
        Args:
            unconnected_Areas: the list returned by find_unconnected_areas() - ie [[(x1,y1), (x2,y2), (x3,y3)],
            [(xi1,yi1), (xi2,yi2), (xi3,yi3)]]
        Returns:
            none
        """
        while len(unconnected_areas) >= 2:
            best_distance = self.width + self.height
            c = [None, None]
            to_connect = unconnected_areas.pop()
            for area in unconnected_areas:
                for x, y in area:                    
                    for xi, yi in to_connect:
                        distance = abs(x-xi) + abs(y-yi)
                        if distance < best_distance and (x == xi or y == yi):
                            best_distance = distance
                            c[0] = (x, y)
                            c[1] = (xi, yi)
            c.sort()
            x, y = c[0]
            for x in range(c[0][0]+1, c[1][0]):
                if self.grid[x][y] == EMPTY:
                    self.grid[x][y] = CORRIDOR
            for y in range(c[0][1]+1, c[1][1]):
                if self.grid[x][y] == EMPTY:
                    self.grid[x][y] = CORRIDOR
            self.corridors.append((x, y))

    # PATH FINDING FUNCTIONS
     
    def construct_nav_graph(self):
        """
        builds the navigation graph for path finding
        must be called before find_path()
        Populates self.graph
        """
        for x, y in self.corridors:
            if self.grid[x][y] < WALL:
                break
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x][y] not in [WALL, EMPTY, OBSTACLE]:
                    self.graph[(x, y)] = []
                    for nx, ny in self.find_neighbours_direct(x, y):
                        if self.grid[nx][ny] not in [WALL, EMPTY, OBSTACLE]:
                            self.graph[(x, y)].append((nx, ny))
                     
    def find_path(self, start_x, start_y, end_x, end_y):
        """
        finds a path between 2 points on the grid
        While not part of generating a dungeon/level it was included as I initially thought that
        since the generator had lots of knowledge about the maze it could use that for fast path finding
        however, the overhead of any heuristic was always greater than time saved. But I kept this as its useful
         
        Args:
            start_x, start_y: integers, grid indices to find a path from
            end_y, end_y: integers, grid indices to find a path to
        Returns:
            a list of grid cells (x,y) leading from the end point to the start point
            such that [(end_x, end_y) .... (start_y, end_y)] to support popping of the end as the agent moves
        """
        cells = []
        came_from = {}
        cells.append((start_x, start_y))
        came_from[(start_x, start_y)] = None
        while cells:
            # manhattan distance sort, commented out at slow, but there should you want it
            # cells.sort(key=lambda x: abs(end_x-x[0]) + abs(end_y - x[1]))
            current = cells[0]
            del cells[0]            
            if current == (end_x, end_y):
                break           
            for nx, ny in self.graph[current]:
                if (nx, ny) not in came_from:
                    cells.append((nx, ny))
                    came_from[(nx, ny)] = current
        if (end_x, end_y) in came_from:
            path = []
            current = (end_x, end_y)
            path.append(current)
            while current != (start_x, start_y):
                current = came_from[current]
                path.append(current)
            return path  
