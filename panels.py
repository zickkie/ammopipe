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

from .functions import *
from .operators import *


class PIPE_PT_AmmoPipe_Naming_Panel(Panel):
    """Ammonite Pipeline Naming Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AmmoPipe"
    bl_label = "Naming"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(text="Asset Name")
        row = col.row(align=True)
        row.prop(scene, "ammopipe_naming_asset_name", text="")
        col = layout.column(align=True)
        row = col.row()
        row.prop(
            scene,
            "ammopipe_naming_keep_geo_collections",
            text="Keep Collections",
            icon="OUTLINER_COLLECTION",
        )
        col = layout.column(align=True)
        col_split = col.split()
        col1 = col_split.column(align=True)
        row = col1.row(align=True)
        row.prop(scene, "ammopipe_naming_use_rigs", text="Rigs", icon="ARMATURE_DATA")
        row = col1.row(align=True)
        row.prop(scene, "ammopipe_naming_use_lights", text="Lights", icon="LIGHT_DATA")
        row.prop(scene, "ammopipe_naming_link_lights", text="", icon="EVENT_L")
        col2 = col_split.column(align=True)
        row = col2.row(align=True)
        row.prop(scene, "ammopipe_naming_use_cameras", text="Camera", icon="CAMERA_DATA")
        row.prop(scene, "ammopipe_naming_link_cameras", text="", icon="EVENT_L")
        row = col2.row(align=True)
        row.prop(scene, "ammopipe_naming_use_refs", text="Refs", icon="IMAGE_DATA")
        row.prop(scene, "ammopipe_naming_link_refs", text="", icon="EVENT_L")

        row = col.row()
        org = row.operator(PIPE_OT_Organize_Scene.bl_idname, text="Organize Scene")
        org.asset_name = scene.ammopipe_naming_asset_name


class PIPE_PT_AmmoPipe_Versioning_Panel(Panel):
    """Ammonite Pipeline Versioning Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AmmoPipe"
    bl_label = "Versioning"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align=True)
        row = col.row(align=True)
        vers = row.operator(PIPE_OT_Incremental_Save.bl_idname, text="Save Current Version")
        vers.count = scene.ammopipe_version_step
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(text="Version Step")
        row.prop(scene, "ammopipe_version_step", text="")
        row = col.row(align=True)
        row.label(text="Next version is:")
        row = col.row(align=True)
        row.alert = True
        name = os.path.splitext(os.path.basename(directory_files()[2]))[0]
        new_name = (
            next_relative_name(directory_files()[1], name, scene.ammopipe_version_step) + ".blend"
        )
        row.label(text=new_name)


class PIPE_PT_AmmoPipe_Scenes_Management_Panel(Panel):
    """Ammonite Pipeline Scenes Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AmmoPipe"
    bl_label = "Scenes Management"
    bl_idname = "PIPE_PT_AmmoPipe_Scenes_Management_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        window = context.window

        col = layout.column()
        sc_col_split = col.split(factor=0.3)
        sc_col_1 = sc_col_split.column(align=True)
        row = sc_col_1.row(align=True)
        row.label(text="Current Scene")
        sc_col_2 = sc_col_split.column(align=True)
        row = sc_col_2.row(align=True)
        if context.scene.source_scene:
            icon = "PINNED"
        else:
            icon = "UNPINNED"
        row.template_ID(window, "scene")
        row.operator(PIPE_OT_Set_Source_Scene.bl_idname, text="", icon=icon)

        row = col.row(align=True)
        row.operator(WM_OT_Add_New_Scene.bl_idname, text="New from Source", icon="ADD")
        row.operator(WM_OT_Delete_Current_Scene.bl_idname, text="Delete Scene", icon="TRASH")


class PIPE_PT_AmmoPipe_Scenes_Naming_Panel(Panel):
    """Ammonite Pipeline Scenes Naming Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AmmoPipe"
    bl_label = "Scenes Naming"
    bl_order = 0
    bl_parent_id = "PIPE_PT_AmmoPipe_Scenes_Management_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align=True)
        for scene in bpy.data.scenes:
            row = col.row()
            row.label(text=scene.name)
            row.prop(scene, "ammopipe_scene_name_suffix", text="Suffix")
        row = col.row(align=True)
        row.operator(PIPE_OT_Unify_Scenes_Names.bl_idname, text="Unify Names", icon="SORTALPHA")


class PIPE_PT_AmmoPipe_Scenes_Collections_Panel(Panel):
    """Ammonite Pipeline Scenes Collections Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AmmoPipe"
    bl_label = "Scenes Collections"
    bl_order = 1
    bl_parent_id = "PIPE_PT_AmmoPipe_Scenes_Management_Panel"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Scene Collections:", icon="OUTLINER_COLLECTION")

        source_scene = None
        for scene in bpy.data.scenes:
            if scene.source_scene:
                source_scene = scene
        if source_scene:
            for coll in source_scene.collection.children_recursive:
                if not coll.override_library and coll.name in source_scene.collection.children:
                    split = col.split(factor=0.6)
                    col1 = split.column()
                    row = col1.row()
                    row.label(text=coll.name)
                    col2 = split.column()
                    row = col2.row()
                    row.prop(coll, "ammopipe_collection_share_enum", expand=True)
        else:
            row = layout.row()
            row.label(text="Set the Source Scene first!", icon="ERROR")


class PIPE_PT_AmmoPipe_Scenes_Save_Panel(Panel):
    """Ammonite Pipeline Scenes Save Panel"""

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AmmoPipe"
    bl_label = "Scenes Save"
    bl_order = 2
    bl_parent_id = "PIPE_PT_AmmoPipe_Scenes_Management_Panel"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        split = col.split(factor=0.6)
        col1 = split.column(align=True)
        col2 = split.column(align=True)

        files = directory_files()[1]
        path_full = context.blend_data.filepath
        name = bpy.path.basename(path_full)

        for scene in bpy.data.scenes:
            if not scene.source_scene:
                scene_file_name = (name.split(".blend")[0] + "_" + scene.name + ".blend").replace(
                    "__", "_"
                )
                row_name = col1.row()
                row_name.label(text=scene.name, icon="SCENE_DATA")
                row_name = col1.row()
                row_name.separator(factor=0.5)
                row_save = col2.row()
                if scene_file_name.replace(".blend", "") in files:
                    text = "Saved!"
                    icon = "CHECKMARK"
                else:
                    text = "Save Scene"
                    icon = "FILE_BLEND"
                save = row_save.operator(
                    PIPE_OT_Save_Scenes_Separately.bl_idname, text=text, icon=icon
                )
                save.scene_name = scene.name
                row_save = col2.row()
                row_save.separator(factor=0.5)


ammopipe_collection_share_items = [
    ("Link", "Link", "Share this Collection with the newly created Scene", "LINKED", 0),
    (
        "Copy",
        "Copy",
        "Copy and Localize this Collection into the newly created Scene",
        "COPYDOWN",
        1,
    ),
]


classes = (
    PIPE_PT_AmmoPipe_Naming_Panel,
    PIPE_PT_AmmoPipe_Versioning_Panel,
    PIPE_PT_AmmoPipe_Scenes_Management_Panel,
    PIPE_PT_AmmoPipe_Scenes_Naming_Panel,
    PIPE_PT_AmmoPipe_Scenes_Collections_Panel,
    PIPE_PT_AmmoPipe_Scenes_Save_Panel,
)


def register():

    bpy.types.Scene.ammopipe_naming_asset_name = StringProperty(
        name="Asset Name",
        description="This name will be applied to the Collections, Objects and Objects Data names",
        default="",
    )
    bpy.types.Scene.ammopipe_naming_keep_geo_collections = BoolProperty(
        name="Keep Current Collections",
        description="When enabled the Collections won't be replaced with the newly created ones but instead will be renamed and places as children. \nWorks only for GEO, others will be pushed to the relevant collections anyway",
        default=True,
    )
    bpy.types.Scene.ammopipe_naming_use_rigs = BoolProperty(
        name="Use Rigs",
        description="Will this Asset contain Armatures",
        default=True,
    )
    bpy.types.Scene.ammopipe_naming_use_cameras = BoolProperty(
        name="Use Cameras",
        description="Will this Asset contain Cameras",
        default=True,
    )
    bpy.types.Scene.ammopipe_naming_link_cameras = BoolProperty(
        name="Make Cameras Collection linkable",
        description="Put CAM- collection in the main LINK- Collection",
        default=False,
    )
    bpy.types.Scene.ammopipe_naming_use_lights = BoolProperty(
        name="Use Lights",
        description="Will this Asset contain Lights",
        default=True,
    )
    bpy.types.Scene.ammopipe_naming_link_lights = BoolProperty(
        name="Make Lights Collection linkable",
        description="Put LIGHT- collection in the main LINK- Collection",
        default=False,
    )
    bpy.types.Scene.ammopipe_naming_use_refs = BoolProperty(
        name="Use Refs",
        description="Will this Asset contain References (Empties with assigned Images)",
        default=True,
    )
    bpy.types.Scene.ammopipe_naming_link_refs = BoolProperty(
        name="Make Refs Collection linkable",
        description="Put REF- collection in the main LINK- Collection",
        default=False,
    )
    bpy.types.Scene.ammopipe_version_step = IntProperty(
        name="Version Step",
        description="The name of the next version will be increased on this amount",
        default=1,
        min=1,
        max=99,
    )
    bpy.types.Collection.ammopipe_collection_share_enum = EnumProperty(
        name="Share Collection",
        items=ammopipe_collection_share_items,
        description="Share or Copy this Collection among the other Scenes",
        default="Link",
    )
    bpy.types.Scene.ammopipe_scene_name_suffix = StringProperty(
        name="Name Suffix",
        description="Scene Name Custom Suffix",
        default="",
    )
    bpy.types.Scene.source_scene = BoolProperty(
        name="Source Scene",
        description="Use This Scene as Source",
        default=False,
    )
    bpy.types.Scene.marked_delete = BoolProperty(
        name="Marked for Delete",
        description="Delete this Scene later",
        default=False,
    )

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.ammopipe_naming_asset_name
    del bpy.types.Scene.ammopipe_naming_use_rigs
    del bpy.types.Scene.ammopipe_naming_use_cameras
    del bpy.types.Scene.ammopipe_naming_use_lights
    del bpy.types.Scene.ammopipe_naming_use_refs
    del bpy.types.Scene.ammopipe_version_step
    del bpy.types.Collection.ammopipe_collection_share_enum
    del bpy.types.Scene.ammopipe_scene_name_suffix
    del bpy.types.Scene.source_scene
    del bpy.types.Scene.marked_delete
