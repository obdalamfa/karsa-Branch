from .farm import build_farm
from .town import build_town
from .mountain import build_mountain
from .lake import build_lake
from .cemetery import build_cemetery
from .beach import build_beach
from .house import build_house
from .shop import build_shop
from .clinic import build_clinic
from .studio import build_studio
from .smith import build_smith
from .greenhouse import build_greenhouse
from .naga_cave import build_naga_cave
from .dungeon import build_dungeon_placeholder
from .swarga import build_swarga

SCENES = {
    'farm': build_farm(),
    'town': build_town(),
    'mountain': build_mountain(),
    'lake': build_lake(),
    'cemetery': build_cemetery(),
    'beach': build_beach(),
    'house': build_house(),
    'shop': build_shop(),
    'clinic': build_clinic(),
    'studio': build_studio(),
    'smith': build_smith(),
    'greenhouse': build_greenhouse(),
    'naga_cave': build_naga_cave(),
    'dungeon': build_dungeon_placeholder(),
    'swarga': build_swarga(),
}
