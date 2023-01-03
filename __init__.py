bl_info = {
    "name": "Ammonite Pipeline",
    "author": "Arthur Shapriro",
    "version": (0, 2, 0),
    "blender": (3, 3, 1),
    "location": "View3D > N-Panel",
    "description": "Ammonite Animation Stiduio Pipeline",
    "warning": "In Development",
    "doc_url": "",
}

import bpy
from . import functions
from . import operators
from . import panels
from bpy.app.handlers import persistent

"""
@persistent
def load_handler(dummy):
    print("Load Handler:", bpy.data.filepath)
"""


##################################
########## REGISTRATION ##########
##################################
def register():
    # bpy.app.handlers.load_post.append(load_handler)
    operators.register()
    panels.register()


def unregister():
    operators.unregister()
    panels.unregister()


if __name__ == "__main__":
    register()
