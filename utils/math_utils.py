import numpy as np
from scipy.ndimage.measurements import label


class Graph:
    """Program to perform depth first search according to value in a boolean 2D matrix."""

    def __init__(self, row, col, g):
        self.rows = row
        self.columns = col
        self.graph = g
        self.visited = np.full((self.rows, self.columns), False)

    # A function to check if a given cell (row, col) can be included in depth first search.
    def isSafe(self, i, j):
        # Row number is in range, column number is in range and value is 1 and not yet visited.
        return (i >= 0 and i < self.rows and
                j >= 0 and j < self.columns and
                not self.visited[i][j] and self.graph[i][j])

    # A utility function to do DFS for a 2D boolean matrix. It only considers the 8 neighbours as adjacent vertices.
    def depth_first_search(self, i, j):
        # These arrays are used to get row and column numbers of 8 neighbours of a given cell
        rowNbr = [-1, -1, -1, 0, 0, 1, 1, 1]
        colNbr = [-1, 0, 1, -1, 1, -1, 0, 1]

        # Mark this cell as visited
        self.visited[i][j] = True

        # Recur for all connected neighbours
        for k in range(8):
            if self.isSafe(i + rowNbr[k], j + colNbr[k]):
                self.depth_first_search(i + rowNbr[k], j + colNbr[k])

    def find_connected_area(self, i, j):
        """Function to find all connected tiles"""
        structure = np.ones((3, 3), dtype=np.bool)
        labeled, ncomponents = label(self.graph, structure)
        island_value = labeled[i][j]

        island_arr = np.full((self.rows, self.columns), False)
        for x in range(self.rows):
            for y in range(self.columns):
                if labeled[x][y] == island_value:
                    island_arr[x][y] = True
                else:
                    island_arr[x][y] = False
        return island_arr


def find_neighbours(width: int, height: int, x: int, y: int):
    xi = (0, -1, 1) if 0 < x < width - 1 else ((0, -1) if x > 0 else (0, 1))
    yi = (0, -1, 1) if 0 < y < height - 1 else ((0, -1) if y > 0 else (0, 1))
    for a in xi:
        for b in yi:
            if a == b == 0:
                continue
            yield (x + a, y + b)


def crop_array(array: np.ndarray):
    """Crop an array to its content"""
    # argwhere will give you the coordinates of every non-zero point
    true_points = np.argwhere(array=True)
    # take the smallest points and use them as the top left of your crop
    top_left = true_points.min(axis=0)
    # take the largest points and use them as the bottom right of your crop
    bottom_right = true_points.max(axis=0)
    out = array[top_left[0]:bottom_right[0] + 1,  # plus 1 because slice isn't
          top_left[1]:bottom_right[1] + 1]  # inclusive

    return out
