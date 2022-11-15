import bpy
import os

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
    PointerProperty,
)
from bpy.types import (
    Operator,
    PropertyGroup,
)

from .functions import *


class PIPE_OT_Organize_Scene(Operator):
    """Create Collections and Objects with proper naming,
    put Objects into relevant Collections based on the Object type"""

    bl_idname = "pipeline.organzie_scene"
    bl_label = "Organize Scene"
    bl_options = {"REGISTER", "UNDO"}

    asset_name: StringProperty()

    def execute(self, context):
        # Capture visibility
        # I moved this out of function as inside it
        # the viewport hide gone reset for some reason
        hide_dict = {}
        for ob in context.scene.objects:
            hide_dict[ob] = ob.hide_get()

        if self.asset_name == "":
            self.report({"ERROR"}, "Asset Name can't be empty")
            return {"FINISHED"}
        else:

            for coll in context.scene.collection.children_recursive:
                layer_coll = recurLayerCollection(context.view_layer.layer_collection, coll.name)
                coll["exclude"] = layer_coll.exclude
            organize_blocks(context.scene, self.asset_name)
            for coll in context.scene.collection.children_recursive:
                layer_coll = recurLayerCollection(context.view_layer.layer_collection, coll.name)
                if "exclude" in coll.keys():
                    layer_coll.exclude = coll["exclude"]

        # Restore visibility
        for ob in context.scene.objects:
            ob.hide_set(hide_dict[ob])
        # Rename Objects
        rename_objects(context.scene, self.asset_name)

        return {"FINISHED"}


class PIPE_OT_Incremental_Save(Operator):
    """Save current state of the File with incremental naming.
    You continue working in the original file, without switching to the newly saved one"""

    bl_idname = "pipeline.incremental_save"
    bl_label = "Save Version"
    bl_options = {"REGISTER", "UNDO"}

    count: IntProperty()

    def execute(self, context):
        # Save file if it hasn't been saved at all
        if not bpy.data.is_saved:
            bpy.ops.wm.save_as_mainfile("INVOKE_DEFAULT")
            return {"FINISHED"}
        # File name before the extension
        name = os.path.splitext(os.path.basename(directory_files()[2]))[0]
        # Don't forget to bring the extension back
        new_name = next_relative_name(directory_files()[1], name, self.count) + ".blend"
        inc_path = os.path.join(directory_files()[0], new_name)
        bpy.ops.wm.save_as_mainfile(filepath=inc_path, copy=True)  # Save it

        self.report({"INFO"}, "Incremental Saved " + new_name)

        return {"FINISHED"}


class PIPE_OT_Unify_Scenes_Names(Operator):
    """Unify names of the scenes with 'scene_XX' pattern"""

    bl_idname = "pipeline.unify_scenes_names"
    bl_label = "Unify Scenes Names"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        unify_scenes_names(context)

        return {"FINISHED"}


class WM_OT_Add_New_Scene(bpy.types.Operator):
    """Add New Scene with Collections being Linked/Copied (see the "Scenes Collections" sub-panel) from the Source Scene
    \n! Thus some Scene should be marked marked as Source"""

    bl_label = "Add_New_Scene"
    bl_idname = "wm.add_new_scene"
    bl_option = {"REGISTER", "UNDO"}

    name: StringProperty(name="Name", default="")
    suffix: StringProperty(name="Suffix", default="")

    @classmethod
    def poll(cls, context):
        return any(scene for scene in bpy.data.scenes if scene.source_scene)

    def execute(self, context):
        name = self.name
        suffix = self.suffix
        if len(suffix) > 0:
            suffix = "_" + suffix
        source_scene = [scene for scene in bpy.data.scenes if scene.source_scene][0]

        scene_new = bpy.data.scenes.new(name=name + suffix)
        scene_new.ammopipe_scene_name_suffix = self.suffix
        for coll in source_scene.collection.children:
            if coll.ammopipe_collection_share_enum == "Link":
                scene_new.collection.children.link(coll)
        context.window.scene = scene_new

        add_name = "_" + scene_new.name
        colls_and_obs_recursive_dupli(
            source_scene, source_scene.collection, scene_new.collection, add_name, True
        )
        # Copy Actions
        for coll in scene_new.collection.children_recursive:
            for ob_copy in coll.objects:
                if ob_copy.animation_data and ob_copy.animation_data.action:
                    action_copy = ob_copy.animation_data.action.copy()
                    action_copy.name = ob_copy.animation_data.action.name + add_name
                    ob_copy.animation_data.action = action_copy

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class PIPE_OT_Set_Source_Scene(Operator):
    """Set current Scene as the source for creating (duplicating) the new scenes"""

    bl_idname = "pipeline.set_source_scene"
    bl_label = "Set Source Scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        for scene in bpy.data.scenes:
            scene.source_scene = scene == context.scene

        return {"FINISHED"}


class WM_OT_Delete_Current_Scene(Operator):
    """Delete Current Scene \n! Scene marked as Source cannot be deleted from this UI"""

    bl_label = "Delete Current Scene?"
    bl_idname = "wm.delete_current_scene"
    bl_option = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not context.scene.source_scene

    def recursive_orphan_delete(self, data):
        for block in data:
            if block.users == 0:
                data.remove(block)
        if any(block for block in data if block.users == 0):
            self.recursive_orphan_delete(data)

    def execute(self, context):
        datas = [bpy.data.collections, bpy.data.objects, bpy.data.meshes, bpy.data.actions]
        bpy.data.scenes.remove(context.scene, do_unlink=True)
        for data in datas:
            self.recursive_orphan_delete(data)

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class PIPE_OT_Save_Scenes_Separately(Operator):
    """Save each Scene as a Separate Blend File"""

    bl_idname = "pipeline.save_scenes_separately"
    bl_label = "Save Scenes Separately"
    bl_options = {"REGISTER", "UNDO"}

    scene_name: StringProperty()

    def execute(self, context):

        bpy.ops.wm.save_mainfile()
        path_full = context.blend_data.filepath
        name = bpy.path.basename(path_full)
        path = path_full.split(name)[0]

        scene_file_name = (name.split(".blend")[0] + "_" + self.scene_name + ".blend").replace(
            "__", "_"
        )  # reduce underscores just in case
        filepath_new = path + scene_file_name

        scenes_all = list(bpy.data.scenes)
        for scene in scenes_all:
            if scene.name != self.scene_name:
                bpy.data.scenes.remove(scene)
        bpy.ops.wm.save_as_mainfile(filepath=filepath_new, copy=True)
        bpy.ops.wm.open_mainfile(filepath=path_full)

        return {"FINISHED"}


classes = (
    PIPE_OT_Organize_Scene,
    PIPE_OT_Incremental_Save,
    PIPE_OT_Unify_Scenes_Names,
    WM_OT_Add_New_Scene,
    WM_OT_Delete_Current_Scene,
    PIPE_OT_Set_Source_Scene,
    PIPE_OT_Save_Scenes_Separately,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
