from bioio import BioImage


class PlateScene:
    """Utility class to extract the scene information from the image."""

    def __init__(self, scene_name: str, image: BioImage):
        """Extract the scene information from the image."""
        tile_to_acquisition_id = {}
        id_counter = 0

        for scene in image.scenes:
            scene_elements = scene.split("/")
            if len(scene_elements) != 3:
                raise ValueError(
                    "Scene name is not in the expected format,"
                    f"expected: 'Tile/Row/Column' got {scene}"
                )

            tile_name, row, column = scene_elements
            if tile_name not in tile_to_acquisition_id:
                tile_to_acquisition_id[tile_name] = id_counter
                id_counter += 1

            if scene == scene_name:
                self.tile_name = tile_name
                self.row = row
                self.column = column
                self.acquisition_id = tile_to_acquisition_id[tile_name]
                self.scene = scene
                break
        else:
            raise ValueError(f"Scene {scene_name} not found in the image.")


def scene_plate_iterate(image: BioImage):
    """Iterate over the scenes in the image and yield the tile_name, row and column"""
    for scene in image.scenes:
        yield PlateScene(scene, image)
