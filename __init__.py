bl_info = {
    "name": "Ammonite Pipeline",
    "author": "Arthur Shapriro",
    "version": (0, 1),
    "blender": (3, 3, 1),
    "location": "View3D > N-Panel",
    "description": "Ammonite Animation Stiduio Pipeline",
    "warning": "In Development",
    "doc_url": "",
}


import bpy
import os

from . import functions
from . import operators
from . import panels

##################################
########## REGISTRATION ##########
##################################
def register():
    # operators.register()
    panels.register()


def unregister():
    # operators.unregister()
    panels.unregister()


if __name__ == "__main__":
    register()
