"""Small harvestable plants with a visible silhouette on the mountain path."""
from ursina import Entity, color
from .config import GROUND_H
from .meshes import low_cone_mesh, creature_body_mesh
from .smooth_shader import apply_smooth


def build_wild(kind, position):
    root = Entity(position=position)

    def part(model, pos, size, tint, rotation=(0, 0, 0)):
        e = Entity(parent=root, model=model, position=pos, scale=size,
                   color=color.rgb(*tint), rotation=rotation)
        apply_smooth(e)
        return e

    if kind == 'running_mushroom':
        part('cube', (0, .23, 0), (.15, .45, .15), (208, 190, 149))
        part(low_cone_mesh(), (0, .5, 0), (.72, .34, .72), (168, 81, 66))
        for x, z in ((-.12, .1), (.14, .04), (0, -.13)):
            part(creature_body_mesh(), (x, .61, z), (.09, .05, .09), (228, 207, 157))
    else:
        if kind == 'mandrake':
            part(creature_body_mesh(), (0, .16, 0), (.3, .35, .24), (161, 127, 80))
        for angle in (0, 72, 144, 216, 288):
            leaf = part(low_cone_mesh(), (0, .23, 0), (.19, .63, .11),
                        (86, 140, 78), (0, angle, 40))
        if kind == 'wild_berry':
            for x, z in ((-.13, .1), (.12, .04), (.02, -.13)):
                part(creature_body_mesh(), (x, .38, z), (.16, .16, .16), (163, 64, 82))
    return root
