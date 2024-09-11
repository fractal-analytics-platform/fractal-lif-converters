import json
from pathlib import Path

import lif_converters

PACKAGE = "lif_converters"
PACKAGE_DIR = Path(lif_converters.__file__).parent
MANIFEST_FILE = PACKAGE_DIR / "__FRACTAL_MANIFEST__.json"
with MANIFEST_FILE.open("r") as f:
    MANIFEST = json.load(f)
    TASK_LIST = MANIFEST["task_list"]
