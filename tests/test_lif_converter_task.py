import shutil
from pathlib import Path

import pytest
from devtools import debug
from fractal_tasks_core.channels import ChannelInputModel

from lif_converters.lif_plate_converter_init_task import lif_plate_converter_task
