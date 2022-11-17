from contextvars import Context
from typing import Dict, Tuple
import bpy
import os


def recurLayerCollection(layerColl, collName):
    """Recursively transverse layer_collection for a particular name"""
    found = None
    if layerColl.name == collName:
        return layerColl
    for layer in layerColl.children:
        found = recurLayerCollection(layer, collName)
        if found:
            return found


def remove_collections(coll, prefixes, asset_name):
    """Remove all Scene Collections that don't pass the naming convention
    and don't have any Objects"""

    for collection in coll.children_recursive:
        if not any(collection.name.startswith(prefix + asset_name) for prefix in prefixes):
            if len(collection.objects) == 0:
                bpy.data.collections.remove(collection)


def create_collections(scene, asset_name) -> Dict:
    """Create Collections according to selected Asset's contents"""
    # Mandatory minimun of Collections
    coll_prefixes = ["COLL-", "GEO-"]
    # List of Collections to create
    if scene.ammopipe_naming_use_rigs:
        coll_prefixes.append("RIG-")
    if scene.ammopipe_naming_use_lights:
        coll_prefixes.append("LIGHT-")
    if scene.ammopipe_naming_use_cameras:
        coll_prefixes.append("CAM-")
    if scene.ammopipe_naming_use_refs:
        coll_prefixes.append("REF-")

    coll_dict = {}
    children_all = [coll.name for coll in scene.collection.children_recursive]

    # Create Collections from the Prefix List, link them to the Scene Collection
    for prefix in coll_prefixes:
        name = prefix + asset_name
        if (name not in children_all) and not bpy.data.collections.get(name):
            coll_new = bpy.data.collections.new(name)
        else:
            coll_new = bpy.data.collections.get(name)
        if not scene.collection.children.get(name):
            scene.collection.children.link(coll_new)
        coll_dict[prefix] = coll_new
        for coll in scene.collection.children_recursive:
            if coll_new.name in coll.children:
                coll.children.unlink(coll_new)

    # Link GEO- and RIG- to the COLL- Collection
    coll_dict["COLL-"].color_tag = "COLOR_05"
    coll_dict["COLL-"].children.link(coll_dict["GEO-"])
    coll_dict["GEO-"].color_tag = "COLOR_03"
    scene.collection.children.unlink(coll_dict["GEO-"])
    if scene.ammopipe_naming_use_rigs:
        coll_dict["COLL-"].children.link(coll_dict["RIG-"])
        coll_dict["RIG-"].color_tag = "COLOR_01"
        scene.collection.children.unlink(coll_dict["RIG-"])

    # Silly hack to place CAM-, LIGHT- & REF- below the COLL- in the Outliner list
    add_colls_usage = {
        "CAM-": scene.ammopipe_naming_link_cameras,
        "LIGHT-": scene.ammopipe_naming_link_lights,
        "REF-": scene.ammopipe_naming_link_refs,
    }
    for pref in add_colls_usage.keys():
        if add_colls_usage[pref]:
            if coll_dict[pref].name in scene.collection.children:
                scene.collection.children.unlink(coll_dict[pref])
            if add_colls_usage[pref] and not coll_dict[pref].name in coll_dict["COLL-"].children:
                coll_dict["COLL-"].children.link(coll_dict[pref])
            else:
                scene.collection.children.link(coll_dict[pref])

    # List of objects types to associate with Collections
    objects_types = {
        "OTHERS": coll_dict["GEO-"],
    }

    if scene.ammopipe_naming_use_rigs:
        objects_types["ARMATURE"] = coll_dict["RIG-"]
    if scene.ammopipe_naming_use_lights:
        objects_types["LIGHT"] = coll_dict["LIGHT-"]
    if scene.ammopipe_naming_use_cameras:
        objects_types["CAMERA"] = coll_dict["CAM-"]
        objects_types["SPEAKER"] = coll_dict["CAM-"]
    if scene.ammopipe_naming_use_refs:
        objects_types["EMPTY"] = coll_dict["REF-"]

    collections_all = list(scene.collection.children_recursive)
    collections_all.append(scene.collection)

    # Additional Sub-Collections for GEO- & RIG-
    main_colls = [objects_types["OTHERS"]]
    if scene.ammopipe_naming_use_rigs:
        main_colls.append(objects_types["ARMATURE"])
    add_colls = ["_main", "_helpers"]

    for main_coll in main_colls:
        for add_coll in add_colls:
            find_coll = None
            for coll in collections_all:
                if (main_coll.name + add_coll) == coll.name:
                    find_coll = coll
            if not find_coll:
                find_coll = bpy.data.collections.new(main_coll.name + add_coll)
            for c in collections_all:
                if find_coll.name in c.children:
                    c.children.unlink(find_coll)
            if not find_coll.name in main_coll.children:
                main_coll.children.link(find_coll)
            find_coll.color_tag = main_coll.color_tag

    geo_add = [c for c in objects_types["OTHERS"].children if "_helpers" in c.name][0]
    geo_main = [c for c in objects_types["OTHERS"].children if "_main" in c.name][0]
    rig_add = None
    rig_main = None
    if scene.ammopipe_naming_use_rigs:
        rig_add = [c for c in objects_types["ARMATURE"].children if "_helpers" in c.name][0]
        rig_main = [c for c in objects_types["ARMATURE"].children if "_main" in c.name][0]

    scene_dict = {
        "objects_types": objects_types,
        "geo_add": geo_add,
        "geo_main": geo_main,
        "rig_add": rig_add,
        "rig_main": rig_main,
        "coll_prefixes": coll_prefixes,
    }
    return scene_dict


def organize_blocks(scene, asset_name):
    """Create Collections and Objects with proper naming,
    put Objects into relevant Collections based on the Object type"""

    # Place Objects into correct Collections
    collections_all = list(scene.collection.children_recursive)
    collections_all.append(scene.collection)
    scene_dict = create_collections(scene, asset_name)
    objects_types = scene_dict["objects_types"]
    geo_add = scene_dict["geo_add"]
    geo_main = scene_dict["geo_main"]
    rig_add = scene_dict["rig_add"]
    rig_main = scene_dict["rig_main"]
    coll_prefixes = scene_dict["coll_prefixes"]

    # If Keep Collections is on
    if scene.ammopipe_naming_keep_geo_collections:
        exclude_list = []
        for coll in collections_all:
            if coll is scene.collection:
                continue
            for ob in coll.objects:
                if ob.type == "MESH":
                    if coll.name not in scene_dict["objects_types"]["OTHERS"].children_recursive:
                        # Link to GEO- collection
                        if coll.name not in scene_dict["objects_types"]["OTHERS"].children:
                            scene_dict["objects_types"]["OTHERS"].children.link(coll)
                        coll.color_tag = scene_dict["objects_types"]["OTHERS"].color_tag
                        if not coll.name.startswith(scene_dict["objects_types"]["OTHERS"].name):
                            coll.name = scene_dict["objects_types"]["OTHERS"].name + "_" + coll.name
                        exclude_list.append(coll.name)
                    break
        print(exclude_list)
        for coll in collections_all:
            if (
                coll is not scene_dict["objects_types"]["OTHERS"]
                and coll.name not in scene_dict["objects_types"]["OTHERS"].children_recursive
            ):
                for child in coll.children:
                    if child.name in exclude_list:
                        coll.children.unlink(child)

    for coll in collections_all:
        if "WGTS" in coll.name:
            continue
        else:
            for ob in coll.objects:
                if ob.type in objects_types.keys():
                    if ob.type == "ARMATURE":
                        if "META" in ob.name:
                            continue
                        else:
                            if rig_main:
                                if not ob.name in scene_dict["rig_main"].objects:
                                    scene_dict["rig_main"].objects.link(ob)
                                ob_coll_new = scene_dict["rig_main"]
                            else:
                                if not ob.name in scene.collection.objects:
                                    scene.collection.objects.link(ob)
                                ob_coll_new = scene.collection
                    else:
                        if ob.type == "EMPTY":  # Speical treatment for Empties
                            if ob.empty_display_type == "IMAGE":
                                if scene.ammopipe_naming_use_refs:
                                    if ob.name not in objects_types[ob.type].objects:
                                        objects_types[ob.type].objects.link(ob)
                                        ob_coll_new = objects_types[ob.type]
                                else:
                                    if ob.name not in scene.collection.objects:
                                        objects_types[ob.type].objects.link(ob)
                                    ob_coll_new = scene.collection
                            elif ob.instance_type == "COLLECTION":
                                if scene.ammopipe_naming_use_refs:
                                    if ob.name not in objects_types[ob.type].objects:
                                        objects_types[ob.type].objects.link(ob)
                                        ob_coll_new = objects_types[ob.type]
                                else:
                                    if ob.name not in geo_add.objects:
                                        geo_add.objects.link(ob)
                                    ob_coll_new = geo_add
                            else:
                                if ob.name not in geo_add.objects:
                                    geo_add.objects.link(ob)
                                ob_coll_new = geo_add
                        if ob.name not in objects_types[ob.type].objects:
                            objects_types[ob.type].objects.link(ob)
                        ob_coll_new = objects_types[ob.type]
                else:
                    if ob.type == "LATTICE":
                        if not ob.name in geo_add.objects:
                            geo_add.objects.link(ob)
                        ob_coll_new = geo_add
                    elif ob.type == "MESH":
                        if scene.ammopipe_naming_keep_geo_collections:
                            keep_colls = [
                                coll
                                for coll in ob.users_collection
                                if scene_dict["objects_types"]["OTHERS"].name in coll.name
                            ]
                            if len(keep_colls) > 0:
                                ob_coll_new = keep_colls[0]
                            else:
                                if not ob.name in geo_main.objects:
                                    geo_main.objects.link(ob)
                                ob_coll_new = geo_main
                        else:
                            if not ob.name in geo_main.objects:
                                geo_main.objects.link(ob)
                            ob_coll_new = geo_main
                    else:
                        if not ob.name in scene_dict["objects_types"]["OTHERS"].objects:
                            scene_dict["objects_types"]["OTHERS"].objects.link(ob)
                        ob_coll_new = scene_dict["objects_types"]["OTHERS"]
                if coll is not ob_coll_new:
                    coll.objects.unlink(ob)

    # Exception: WGTS Colletction
    collections_all = scene.collection.children_recursive
    collections_all_extended = collections_all
    collections_all_extended.extend([scene.collection])
    wgts = [coll for coll in collections_all_extended if "WGTS" in coll.name]
    for coll in collections_all_extended:
        for wgt in wgts:
            if wgt.name in coll.children:
                coll.children.unlink(wgt)
    for wgt in wgts:
        if rig_add:
            if not wgt.name in rig_add.children:
                rig_add.children.link(wgt)
        else:
            if not wgt.name in geo_add.children:
                geo_add.children.link(wgt)
    # Exception: META Armatures
    meta_obs = [
        [ob for ob in collection.objects if (ob.type == "ARMATURE" and "META" in ob.name)]
        for collection in collections_all_extended
    ]
    meta_obs_flat = [item for sublist in meta_obs for item in sublist]
    for ob in meta_obs_flat:
        for coll in ob.users_collection:
            coll.objects.unlink(ob)
    for ob in meta_obs_flat:
        if rig_add:
            if not ob.name in rig_add.objects:
                rig_add.objects.link(ob)
        else:
            if not ob.name in scene.collection.objects:
                scene.collection.objects.link(ob)

    # Remove Collections
    remove_collections(scene.collection, coll_prefixes, asset_name)


def rename_objects(scene, asset_name):
    """Rename Objects due to their Collection name"""
    for ob in scene.objects:
        if "META" in ob.name:
            continue
        ob_coll = ob.users_collection[0]
        if ob.users_collection[0] is scene.collection:
            if ob.type == "ARMATURE":
                prefix = "RIG" + "-" + asset_name
            elif ob.type == "MESH":
                prefix = "GEO" + "-" + asset_name
            else:
                prefix = ob.type[:3] + "-" + asset_name
        else:
            if ob.type == "ARMATURE" and ("_main" in ob_coll.name or "_helpers" in ob_coll.name):
                prefix = [
                    coll
                    for coll in scene.collection.children_recursive
                    if ob_coll.name in coll.children
                ][0].name
            else:
                prefix = ob_coll.name

        if not ob.name.startswith(prefix):
            ob.name = prefix + "_" + ob.name
        elif not ob.name.split(prefix)[1].startswith("_"):
            ob.name = ob.name.replace(prefix, (prefix + "_"))
        else:
            pass
        if ob.type != "EMPTY":
            ob.data.name = "DATA_" + ob.name


def seperate_string_number(string) -> Tuple:
    """Split the current file name to digits and letters parts"""
    previous_character = string[0]
    groups = []
    newword = string[0]
    for x, i in enumerate(string[1:]):
        if i.isalpha() and previous_character.isalpha():
            newword += i
        elif i.isnumeric() and previous_character.isnumeric():
            newword += i
        else:
            groups.append(newword)
            newword = i

        previous_character = i

        if x == len(string) - 2:
            groups.append(newword)
            newword = ""

        state = False
        for item in groups:
            if item.isdigit():
                state = True
    return (groups, state)


def next_name(filename, count) -> str:
    """Define what the digits should the next name consist of"""
    if not seperate_string_number(filename)[1]:
        # E.g. add "1" if the current name has no digits at all
        if count < 10:
            zero = "0"
        else:
            zero = ""
        if "_ver_" not in filename:
            return filename + "_ver_" + zero + str(count)
        else:
            return filename + str(count)
    else:
        filename_list = seperate_string_number(filename)[0]
        # We want to take only the last digital part of the name
        filename_list.reverse()
        for i in range(len(filename_list)):
            if filename_list[i].isdigit():
                last_number = int(filename_list[i])
                next_number = last_number + count
                if len(str(next_number)) > len(str(last_number)):  # 09 -> 10 instead of 09 -> 010
                    base = filename_list[i].split(str(last_number))[0][:-1]
                else:
                    base = filename_list[i].split(str(last_number))[0]
                # Add floating zeroes and have 000 -> 001 instead of 000 -> 1
                if int(filename_list[i]) == 0:
                    if "_ver_" not in filename:
                        filename_list[i] = (
                            base + "_ver_" + str(next_number).zfill(len(filename_list[i]))
                        )
                    else:
                        filename_list[i] = base + str(next_number).zfill(len(filename_list[i]))
                else:
                    if "_ver_" not in filename:
                        filename_list[i] = base + "_ver_" + str(next_number)
                    else:
                        filename_list[i] = base + str(next_number)
                break
        filename_list.reverse()
        return "".join(filename_list)


def next_relative_name(directory_files, current_name, count) -> str:
    """Compare the name that we want to take as the next one
    with all the exeisting names in the directory,
    and if there is a match then add 1 to the count parameter until we have
    the number that makes file name unique again (Make Name Unique Again!)"""
    while next_name(current_name, count) in directory_files:
        count += 1
        next_relative_name(directory_files, current_name, count)
    return next_name(current_name, count)


def directory_files() -> Tuple:
    current_file = bpy.data.filepath
    directory_name = os.path.dirname(current_file)
    # Collect all the files in the directory
    directory_files = []
    for item in sorted(os.listdir(directory_name)):
        if item.endswith(".blend"):
            directory_files.append(os.path.splitext(item)[0])
    return (directory_name, directory_files, current_file)


def unify_scenes_names(context):
    scenes = [scene.name for scene in bpy.data.scenes if not scene.ammopipe_source_scene]
    scenes.sort()
    for name in scenes:
        index = str(scenes.index(name) + 1)
        if len(index) == 1:
            zero = "0" + index
        else:
            zero = index
        bpy.data.scenes[name].name = (
            "scene_"
            + zero
            + ("_" + bpy.data.scenes[name].ammopipe_scene_name_suffix)
            * bool(len(bpy.data.scenes[name].ammopipe_scene_name_suffix))
        )
    for scene in bpy.data.scenes:
        if scene.ammopipe_source_scene:
            scene.name = "_scene_source" + ("_" + scene.ammopipe_scene_name_suffix) * bool(
                len(scene.ammopipe_scene_name_suffix)
            )


def blocks_recursive_property(scene, coll):
    for source_coll in coll.children:
        source_coll.ammopipe_source_collection = source_coll.name
        if coll is not scene.collection:
            source_coll.ammopipe_collection_share_enum = coll.ammopipe_collection_share_enum
        for source_obj in source_coll.objects:
            source_obj.ammopipe_source_object = source_obj.name
            if source_obj.animation_data and source_obj.animation_data.action:
                source_obj.animation_data.action.ammopipe_source_action = (
                    source_obj.animation_data.action.name
                )
        if len(source_coll.children) > 0:
            blocks_recursive_property(scene, source_coll)


"""
def colls_and_obs_recursive_dupli(scene, collection, collection_dst, add_name, check_copy):
    for coll in collection.children:
        # Pass the "Link" collections if we expect them here
        if check_copy and coll.ammopipe_collection_share_enum == "Link":
            continue
        # Duplicate Collection if it's Local
        # Create new if it's overridden
        # (as we cannot (un)link to an overridden one)
        if not coll.override_library:
            coll_copy = coll.copy()
            coll_copy.name = coll.name + add_name
        else:
            coll_copy = bpy.data.collections.new(coll.name + add_name)
            coll_copy.color_tag = coll.color_tag
            original_parents = list(
                [
                    scene_collection
                    for scene_collection in scene.collection.children_recursive
                    if coll.name in scene_collection.children
                ]
            )
            copy_parents = list([coll.name + add_name for coll in original_parents])
            for scene_collection in scene.collection.children_recursive:
                if scene_collection.name in copy_parents:
                    scene_collection.children.link(coll_copy)
        # Unlink the original children if we are not inside the LO collection
        coll_copy_children = list(
            [child for child in coll_copy.children if not coll_copy.override_library]
        )
        for child in coll_copy_children:
            if child.name in coll.children:
                coll_copy.children.unlink(child)
        # Duplicate objects
        for ob in list(coll.objects):
            ob_copy = ob.copy()
            ob_copy.name = ob.name + add_name
            # Duplicate object data if exists
            # Object data should be duplicated for the non-LO collections only
            if not coll.override_library:
                if ob.data:
                    data = ob.data.copy()
                    data.name = ob_copy.name
                    ob_copy.data = data
            # Link copied object to a copied collection
            if not ob_copy.name in coll_copy.objects:
                coll_copy.objects.link(ob_copy)
            # Unlink the original objects from a copied collection
            if ob.name in coll_copy.objects:
                coll_copy.objects.unlink(ob)
        # Unlink the copied collection from the original parent
        if coll_copy.name in collection.children and collection is not scene.collection:
            collection.children.unlink(coll_copy)
        # Link the copied collection to a destination collection
        if coll_copy.name not in collection_dst.children:
            collection_dst.children.link(coll_copy)
        # Recursion with new parameters
        # if not coll.override_library:
        if len(coll.children) > 0:
            colls_and_obs_recursive_dupli(scene, coll, coll_copy, add_name, False)
"""
