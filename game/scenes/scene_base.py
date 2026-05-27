class Scene:
    def __init__(self, name, display, tiles, portals=None, indoor=False, builder=None, has_horizon=True):
        if builder is None:
            from .props import default_prop_builder
            self.builder = lambda world: default_prop_builder(world, self)
        else:
            self.builder = builder
        self.name    = name
        self.display = display
        self.tiles   = tiles
        self.w       = len(tiles[0]) if tiles else 0
        self.h       = len(tiles) if tiles else 0
        self.portals = portals or []
        self.indoor  = indoor
        self.has_horizon = has_horizon

def _build_indoor_room(name, display, objects, portal_exit):
    from game.config import WL, FL, DR
    w, h = 15, 6
    tiles = []
    for y in range(h):
        row = []
        for x in range(w):
            if x == 0 or x == w - 1 or y == 0 or y == h - 1:
                row.append(WL)
            else:
                row.append(FL)
        tiles.append(row)
    
    tiles[5][7] = DR
    
    for ox, oy, ot in objects:
        if 0 <= oy < h and 0 <= ox < w:
            tiles[oy][ox] = ot
        
    portals = [(7, 5, portal_exit[0], portal_exit[1], portal_exit[2])]
    return Scene(name, display, tiles, portals, indoor=True)
