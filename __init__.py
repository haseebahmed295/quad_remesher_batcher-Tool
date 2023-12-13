# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Quad Remesher Batch Tool",
    "author": "haseebahmed295",
    "version": (0, 5),
    "blender": (2, 80, 0),
    "location": "N panel-->Quad Remesher ",
    "description": "Allow you batch remesh objects using Quad Remesher",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}

import textwrap
import bpy
import time
from bpy.props import (
    PointerProperty,
    FloatProperty
)


class Quad_Remesher_BatcherPanel_operator(bpy.types.Operator):
    bl_idname = "qremesher.remesh_selected"
    bl_label = "Remesh Selected Objects"
    bl_description = "Quad Remesh all selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects is not None

    def modal(self, context, event):
        if event.type == 'TIMER':
            if len (bpy.data.objects) != self.objs or self.First_time:
                self.objs = len(bpy.data.objects)
                self.First_time = False
                if self.object_index > 0 and bpy.context.scene.after_script is not None:
                    bpy.ops.script.run_script()
                if self.object_index >= len(self.selected_objects):
                    self.cancel(context)
                    return {'FINISHED'}

                # Get the next object
                obj = self.selected_objects[self.object_index]

                # Deselect all
                bpy.ops.object.select_all(action='DESELECT')
                # Set as active object
                obj.select_set(True)
                context.view_layer.objects.active = obj

                try:
                    bpy.ops.qremesher.remesh()
                except:
                    # open this link https://exoside.com/
                    if not 'quad_remesher_1_2' in bpy.context.preferences.addons:
                        # open a window showing the button to open link https://exoside.com/
                        bpy.ops.wm.call_menu('INVOKE_DEFAULT' ,name=No_MT_Remesher.bl_idname)
                        return {'FINISHED'}
                # time.sleep(context.scene.sleep_time)
                # Move on to the next object
                self.object_index += 1

        return {'PASS_THROUGH'}

    def execute(self, context):
        self.objs = len(bpy.data.objects)
        self.First_time = True
        self.selected_objects = context.selected_objects
        self.object_index = 0

        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(.01, window=context.window)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)

class No_MT_Remesher(bpy.types.Menu):
   bl_label = "Custom Menu"
   bl_idname = "No_MT_Remesher"

   def draw(self, context):
       layout = self.layout
       layout.label(text="Quad Remesher is not available.", icon='ERROR')
       layout.separator()
       layout.label(text="You can download it from : Exoside.com")
       layout.operator('wm.url_open' ,text="Open Link" , depress=True).url = "https://exoside.com/"

class SCRIPT_OT_RunScript(bpy.types.Operator):
    bl_idname = "script.run_script"
    bl_label = "Run Script"


    def execute(self, context):
        try:
            if context.scene.after_script is None:
                return {'FINISHED'}
            script_content = context.scene.after_script.as_string()
            exec(script_content, {'bpy': bpy})
        except Exception as e:
            self.report({'ERROR'}, f"Error executing script: {str(e)}")

        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

class SCRIPT_OT_SetTimer(bpy.types.Operator):
    bl_idname = "qremesher.set_timer"
    bl_label = "Set Timer"
    bl_description = 'Set the sleep time by remeshing selected object'
    _timer = None
    _objects_len = 0
    ran = False

    def modal(self, context, event):
        if event.type == 'TIMER':
            # If the number of objects has increased, a new object has been added
            if len(bpy.data.objects) > self._objects_len:
                
                # Get the current time after the operation
                end_time = time.time()

                time_taken = end_time - self.start_time

                print(f"Time taken by the operation: {time_taken} seconds")
                context.scene.sleep_time = time_taken
                self.ran = True
        if self.ran:
            return {'FINISHED'}
        else:
            return {'PASS_THROUGH'}

    def execute(self, context):
        self.start_time = time.time()
        bpy.ops.qremesher.remesh()
        self._objects_len = len(bpy.data.objects)
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)

class Quad_PT_Remesher_BatcherPanel(bpy.types.Panel):
    """Docstring of Quad_Remesher_BatcherPanel"""
    bl_idname = "VIEW3D_PT_quad_remesher_batcher_panel"
    bl_label = "Quad_Remesher_Batcher Panel"
    #bl_options =  {'DEFAULT_CLOSED'}
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Quad Remesh'
    

    def draw(self, context):
        layout = self.layout
        if not 'quad_remesher_1_2' in bpy.context.preferences.addons:
            layout.label(text="Quad Remesher is not available.", icon='ERROR')
        layout.label(text=f'Selected Mesh Count: {len(list(x for x in context.selected_objects if x.type == "MESH"))}')
        row = layout.row()
        row.label(text=f'Sleep Time')
        row.prop(context.scene, "sleep_time" , text='')
        row.operator(SCRIPT_OT_SetTimer.bl_idname, text = "", icon = 'RECOVER_LAST')
        # put script prop in box with info as lable 
        box = layout.box()
        textTowrap = "Set Script to execute after remeshing. Leave it empty if you don't want to run any script."
        wrapp = textwrap.TextWrapper(width=30)
        wList = wrapp.wrap(text=textTowrap)
        for text in wList: 
            row = box.row(align = True)
            row.alignment = 'EXPAND'
            row.scale_y = 0.6
            row.label(text=text)
        box.prop(context.scene, "after_script", text="Script")
        layout.operator(Quad_Remesher_BatcherPanel_operator.bl_idname, text = "<<<Batch Remesh>>>")




classes = (
    SCRIPT_OT_RunScript,
    Quad_PT_Remesher_BatcherPanel,
    Quad_Remesher_BatcherPanel_operator,
    No_MT_Remesher ,
    SCRIPT_OT_SetTimer
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.after_script = PointerProperty(type=bpy.types.Text , name="After Script" , description='Script to execute after remeshing each object ')
    bpy.types.Scene.sleep_time = FloatProperty(min=0.1, default=1 , description='Waited time before remeshing next object')
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.after_script


if __name__ == "__main__":
    register()
