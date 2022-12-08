import bpy
import os
from pathlib import Path

from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty
from bpy.types import (
    Operator,
    PropertyGroup,
)

from .functions import *


class Project_Scenes(PropertyGroup):
    name: StringProperty(name="Scene Name", default="")


class Project_Properties(PropertyGroup):
    project_name: StringProperty(name="Project Name", default="")
    project_path: StringProperty(
        name="Project's Parent Folder",
        description="A place to create a Project folders structure. \nIn most cases should be set to 'Ammonite-Documents\Projects'",
        subtype="DIR_PATH",
        default="",
    )
    use_animatic: BoolProperty(
        name="Animatic", description="Project has Animatic", default=True
    )
    use_assets: BoolProperty(
        name="Assets", description="Project has Assets", default=True
    )
    use_references: BoolProperty(
        name="References", description="Project has References", default=True
    )
    use_scenes: BoolProperty(
        name="Scenes", description="Project has Scenes", default=True
    )
    use_exports: BoolProperty(
        name="Exports", description="Project has Exports", default=True
    )
    use_utilities: BoolProperty(
        name="Utilities", description="Project has Utilities", default=True
    )
    project_scenes: CollectionProperty(type=Project_Scenes)
    project_scenes_list_show: BoolProperty(name="Show Scenes List", default=True)


class PIPE_OT_Project_Add(Operator):
    """Add Project Properties"""

    bl_idname = "pipeline.project_add"
    bl_label = "Add Project Properties"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        context.scene.ammopipe_project_properties.add()
        return {"FINISHED"}


class PIPE_OT_Project_Remove(Operator):
    """Remove Project Properties"""

    bl_idname = "pipeline.project_remove"
    bl_label = "Remove Project Properties"
    bl_options = {"REGISTER", "UNDO"}

    i: IntProperty()

    def execute(self, context):
        context.scene.ammopipe_project_properties.remove(self.i)
        return {"FINISHED"}


class PIPE_OT_Project_Scene_Add(Operator):
    """Add Project Scene"""

    bl_idname = "pipeline.project_scene_add"
    bl_label = "Add Project Scene"
    bl_options = {"REGISTER", "UNDO"}

    i: IntProperty()

    def execute(self, context):
        context.scene.ammopipe_project_properties[self.i].project_scenes.add()
        return {"FINISHED"}


class PIPE_OT_Project_Scene_Remove(Operator):
    """Remove Project Scene"""

    bl_idname = "pipeline.project_scene_remove"
    bl_label = "Remove Project Scene"
    bl_options = {"REGISTER", "UNDO"}

    i: IntProperty()
    j: IntProperty()

    def execute(self, context):
        context.scene.ammopipe_project_properties[self.i].project_scenes.remove(self.j)
        return {"FINISHED"}


class PIPE_OT_Organize_Scene(Operator):
    """Create Collections and Objects with proper naming,
    put Objects into relevant Collections based on the Object type"""

    bl_idname = "pipeline.organzie_scene"
    bl_label = "Organize Scene"
    bl_options = {"REGISTER", "UNDO"}

    asset_name: StringProperty()

    def execute(self, context):
        # Capture visibility
        # I moved this out of function because when inside
        # the "viewport hide" is reset for some reason
        hide_dict = {}
        for ob in context.scene.objects:
            hide_dict[ob] = ob.hide_get()

        if self.asset_name == "":
            self.report({"ERROR"}, "Asset Name can't be empty")
            return {"FINISHED"}
        else:

            for coll in context.scene.collection.children_recursive:
                layer_coll = recurLayerCollection(
                    context.view_layer.layer_collection, coll.name
                )
                coll["exclude"] = layer_coll.exclude
            organize_blocks(context.scene, self.asset_name)
            for coll in context.scene.collection.children_recursive:
                layer_coll = recurLayerCollection(
                    context.view_layer.layer_collection, coll.name
                )
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


class PIPE_OT_Set_Workflow_Asset(Operator):
    """Use this Workflow type when you create Assets"""

    bl_idname = "pipeline.set_workflow_asset"
    bl_label = "Set Workflow: Asset"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        for scene in bpy.data.scenes:
            scene.ammopipe_workflow = "Asset"
        self.report({"INFO"}, "Current workflow: ASSET")
        return {"FINISHED"}


class PIPE_OT_Set_Workflow_Layout(Operator):
    """Use this Workflow type when you work with Layouts (e.g. with Linked Libraries)"""

    bl_idname = "pipeline.set_workflow_layout"
    bl_label = "Set Workflow: Layout"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        for scene in bpy.data.scenes:
            scene.ammopipe_workflow = "Layout"
        self.report({"INFO"}, "Current workflow: LAYOUT")
        return {"FINISHED"}


class PIPE_OT_Set_Workflow_Project(Operator):
    """Use this Workflow type when you set up the Project's folders structure"""

    bl_idname = "pipeline.set_workflow_project"
    bl_label = "Set Workflow: Project"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        for scene in bpy.data.scenes:
            scene.ammopipe_workflow = "Project"
        self.report({"INFO"}, "Current workflow: PROJECT")
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
        return any(scene for scene in bpy.data.scenes if scene.ammopipe_source_scene)

    def execute(self, context):
        suffix = self.suffix
        if len(suffix) > 0:
            suffix = "_" + suffix
        # Ensure all the blocks have info about themselves
        # They will be copied in a new scene thus we'll have
        # a method to connect a copied block with its original
        source_scene = [
            scene for scene in bpy.data.scenes if scene.ammopipe_source_scene
        ][0]
        blocks_recursive_property(source_scene, source_scene.collection)

        # Create a copy Scene
        bpy.ops.scene.new(type="FULL_COPY")
        scene_new = context.window.scene
        scene_new.name = self.name + suffix
        scene_new.ammopipe_workflow = source_scene.ammopipe_workflow
        scene_new.ammopipe_scene_name_suffix = self.suffix
        scene_new.ammopipe_source_scene = False

        add_name = "_" + scene_new.name
        # Unlink and delete the Collections that should have been shared instead
        for coll_new in scene_new.collection.children:
            if (
                bpy.data.collections[
                    coll_new.ammopipe_source_collection
                ].ammopipe_collection_share_enum
                == "Link"
            ):
                for child_coll_new in coll_new.children_recursive:
                    for ob_new in child_coll_new.objects:
                        if ob_new.animation_data and ob_new.animation_data.action:
                            bpy.data.actions.remove(ob_new.animation_data.action)
                        bpy.data.objects.remove(ob_new)
                    bpy.data.collections.remove(child_coll_new)
                bpy.data.collections.remove(coll_new)
        # Link them in a copied Scene
        for coll_old in source_scene.collection.children:
            if coll_old.ammopipe_collection_share_enum == "Link":
                scene_new.collection.children.link(coll_old)
        # Return correct names for the copied Collections, Objects and Actions
        for coll_new in scene_new.collection.children_recursive:
            coll_source = bpy.data.collections[coll_new.ammopipe_source_collection]
            if coll_source.ammopipe_collection_share_enum == "Copy":
                for ob_new in coll_new.objects:
                    if ob_new.animation_data and ob_new.animation_data.action:
                        action = ob_new.animation_data.action
                        action_source = bpy.data.actions[action.ammopipe_source_action]
                        ob_new.animation_data.action.name = (
                            action_source.name + add_name
                        )
                    ob_source = bpy.data.objects[ob_new.ammopipe_source_object]
                    ob_new.name = ob_source.name + add_name
                coll_new.name = coll_source.name + add_name

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
            scene.ammopipe_source_scene = scene == context.scene

        return {"FINISHED"}


class WM_OT_Delete_Current_Scene(Operator):
    """Delete Current Scene \n! Scene marked as Source cannot be deleted from this UI"""

    bl_label = "Delete Current Scene?"
    bl_idname = "wm.delete_current_scene"
    bl_option = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return not context.scene.ammopipe_source_scene

    def recursive_orphan_delete(self, data):
        for block in data:
            if block.users == 0:
                data.remove(block)
        if any(block for block in data if block.users == 0):
            self.recursive_orphan_delete(data)

    def execute(self, context):
        datas = [
            bpy.data.collections,
            bpy.data.objects,
            bpy.data.meshes,
            bpy.data.actions,
        ]

        for coll_del in context.scene.collection.children_recursive:
            del_state = True
            if any(
                scene
                for scene in bpy.data.scenes
                if coll_del in scene.collection.children_recursive
                and scene is not context.scene
            ):
                del_state = False
            if del_state:
                for ob_del in coll_del.objects:
                    if ob_del.animation_data and ob_del.animation_data.action:
                        bpy.data.actions.remove(ob_del.animation_data.action)
                    bpy.data.objects.remove(ob_del)
                bpy.data.collections.remove(coll_del)

        bpy.data.scenes.remove(context.scene, do_unlink=True)
        for data in datas:
            self.recursive_orphan_delete(data)

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class PIPE_OT_Set_Filepath_From_Current(Operator):
    """Set Scene Save Path equal to the Path of the Current File"""

    bl_idname = "pipeline.set_filepath_from_current"
    bl_label = "Set Filepath from Current"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bpy.data.is_saved

    def execute(self, context):
        path_full = context.blend_data.filepath
        name = bpy.path.basename(path_full)
        path = path_full.split(name)[0]
        bpy.data.window_managers["WinMan"].ammopipe_scene_save_path = path
        return {"FINISHED"}


class PIPE_OT_Save_Scenes_Separately(Operator):
    """Save each Scene as a Separate Blend File"""

    bl_idname = "pipeline.save_scenes_separately"
    bl_label = "Save Scenes Separately"
    bl_options = {"REGISTER", "UNDO"}

    filepath_new: StringProperty()
    scene_name: StringProperty()

    @classmethod
    def poll(cls, context):
        return bpy.data.window_managers["WinMan"].ammopipe_scene_save_path.strip()

    def execute(self, context):
        save_path = bpy.data.window_managers["WinMan"].ammopipe_scene_save_path
        bpy.ops.wm.save_mainfile()
        path_full = context.blend_data.filepath
        name = bpy.path.basename(path_full)

        scene_file_name = (
            name.split(".blend")[0] + "_" + self.scene_name + ".blend"
        ).replace(
            "__", "_"
        )  # reduce underscores just in case
        filepath_new = self.filepath_new + scene_file_name

        scenes_all = list(bpy.data.scenes)
        for scene in scenes_all:
            if scene.name != self.scene_name:
                bpy.data.scenes.remove(scene)
        bpy.ops.wm.save_as_mainfile(filepath=filepath_new, copy=True)
        bpy.ops.wm.open_mainfile(filepath=path_full)
        bpy.data.window_managers["WinMan"].ammopipe_scene_save_path = save_path

        return {"FINISHED"}


class PIPE_OT_Fix_Name(Operator):
    """Fix Name of the Block"""

    bl_idname = "pipeline.fix_name"
    bl_label = "Fix Name of the Block"
    bl_options = {"REGISTER", "UNDO"}

    block: StringProperty()
    collection: StringProperty()

    def execute(self, context):

        block = eval(self.block)
        collection = eval(self.collection)
        block.name = naming_ussues(context.scene, block, collection)

        return {"FINISHED"}


class PIPE_OT_Fix_Names_All(Operator):
    """Fix Names of All the Blocks"""

    bl_idname = "pipeline.fix_names_all"
    bl_label = "Fix Names of All the Blocks"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        collections = [
            bpy.data.objects,
            bpy.data.meshes,
            bpy.data.images,
            bpy.data.materials,
            bpy.data.armatures,
            bpy.data.lattices,
            bpy.data.cameras,
            bpy.data.lights,
        ]

        for block_collection in collections:
            for block in block_collection:
                block.name = naming_ussues(context.scene, block, block_collection)

        return {"FINISHED"}


class PIPE_OT_Override_And_Snap_Rigged(Operator):
    """Override Rigged asset and move Rig to the current Empty's position"""

    bl_idname = "pipeline.override_and_snap_rigged"
    bl_label = "Override Rigged asset and move Rig to the current Empty's position"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object
            and context.active_object.type == "EMPTY"
            and context.active_object.instance_type == "COLLECTION"
        )

    def execute(self, context):

        empty = context.active_object
        transforms = (
            empty.location.copy(),
            empty.rotation_euler.copy(),
            empty.scale.copy(),
        )
        print(transforms)
        collection = empty.instance_collection
        reference = None
        for coll in collection.children_recursive:
            for ob in coll.objects:
                if ob.type == "ARMATURE" and ob.name == "RIG-" + collection.name:
                    reference = ob
        if not reference:
            self.report({"ERROR"}, "No rig with proper naming found!")
        else:
            bpy.ops.object.make_override_library()
            for ob in bpy.data.objects:
                if ob.override_library and ob.override_library.reference == reference:
                    ob.location = transforms[0]
                    ob.rotation_euler = transforms[1]
                    ob.scale = transforms[2]

        return {"FINISHED"}


class PIPE_OT_Create_Folders(Operator):
    """Create Project Folders"""

    bl_idname = "pipeline.create_project_folders"
    bl_label = "Create Project Folders"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        state = False
        projects = context.scene.ammopipe_project_properties
        for project in projects:
            if project.project_name.strip() and project.project_path.strip():
                ids = [
                    prop.identifier
                    for prop in project.bl_rna.properties
                    if "use" in prop.identifier
                ]
                for key in ids:
                    if getattr(project, key):
                        state = True
                        break
        return len(projects) > 0 and state

    def execute(self, context):
        paths = list(
            [
                project.project_path
                for project in context.scene.ammopipe_project_properties
            ]
        )
        projects_names = list(
            [
                project.project_name
                for project in context.scene.ammopipe_project_properties
            ]
        )
        for i in range(len(paths)):
            # Root Project Folder
            project = context.scene.ammopipe_project_properties[i]
            master_path = bpy.path.abspath(paths[i])
            project_name = projects_names[i]
            master_path = os.path.join(master_path, project_name)
            Path(master_path).mkdir(parents=True, exist_ok=True)
            self.report(
                {"INFO"}, f"'{projects_names}' Project folder created at {paths}"
            )
            # Subfolders
            subfolders = [
                (prop.identifier, prop.name)
                for prop in project.bl_rna.properties
                if ("use" in prop.identifier and getattr(project, prop.identifier))
            ]
            for subfolder in subfolders:
                Path(os.path.join(master_path, subfolder[1])).mkdir(
                    parents=True, exist_ok=True
                )
                # Create Scenes
                if subfolder[1] == "Animatic" or subfolder[1] == "Scenes":
                    if len(project.project_scenes) > 0:
                        for s in range(len(project.project_scenes)):
                            count = "%02d" % s
                            scene_name = "scene_" + count
                            if project.project_scenes[s].name.strip():
                                scene_name = (
                                    scene_name + "_" + project.project_scenes[s].name
                                )
                            Path(
                                os.path.join(master_path, subfolder[1], scene_name)
                            ).mkdir(parents=True, exist_ok=True)
        return {"FINISHED"}


classes = (
    Project_Scenes,
    Project_Properties,
    PIPE_OT_Project_Add,
    PIPE_OT_Project_Remove,
    PIPE_OT_Project_Scene_Add,
    PIPE_OT_Project_Scene_Remove,
    PIPE_OT_Organize_Scene,
    PIPE_OT_Incremental_Save,
    PIPE_OT_Unify_Scenes_Names,
    WM_OT_Add_New_Scene,
    WM_OT_Delete_Current_Scene,
    PIPE_OT_Set_Source_Scene,
    PIPE_OT_Set_Filepath_From_Current,
    PIPE_OT_Save_Scenes_Separately,
    PIPE_OT_Set_Workflow_Asset,
    PIPE_OT_Set_Workflow_Layout,
    PIPE_OT_Set_Workflow_Project,
    PIPE_OT_Fix_Name,
    PIPE_OT_Fix_Names_All,
    PIPE_OT_Override_And_Snap_Rigged,
    PIPE_OT_Create_Folders,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
