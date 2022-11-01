import bpy
import os
from bpy.types import Panel

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
    PointerProperty,
)

from .operators import *
from .functions import *


class AMM_PT_AmmoPipe_Naming_Panel(Panel):
    """Ammonite Pipeline Naming Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AmmoPipe"
    bl_label = "Naming"

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(text="Naming")


classes = (AMM_PT_AmmoPipe_Naming_Panel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
