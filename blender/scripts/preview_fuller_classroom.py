"""渲染实际构建环境的概览与椅架细节，不修改运行时资产。"""
import bpy,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'blender/build/classroom-fuller'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'story_classroom.blend'))
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('PreviewWorld');scene.world.use_nodes=True
background=next((n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND'),None)
if not background:
 background=scene.world.node_tree.nodes.new('ShaderNodeBackground');output=scene.world.node_tree.nodes.new('ShaderNodeOutputWorld');scene.world.node_tree.links.new(background.outputs[0],output.inputs['Surface'])
background.inputs['Color'].default_value=(.67,.75,.86,1);background.inputs['Strength'].default_value=.35
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.3
def xyz(p):return Vector((p[0],-p[2],p[1]))
for pos,power,size in [((-5.6,3.6,0),1800,5),((3,3.8,1),900,4),((0,3.8,5),700,3)]:
 bpy.ops.object.light_add(type='AREA',location=xyz(pos));light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(xyz((0,.5,1))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=xyz((-5.2,2.65,-2.35)));camera=bpy.context.object;camera.data.lens=22;scene.camera=camera
camera.rotation_euler=(xyz((.4,.95,2.1))-camera.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(OUT/'overview.png');bpy.ops.render.render(write_still=True)
camera.location=xyz((1.45,1.05,2.95));camera.rotation_euler=(xyz((.38,.48,2.38))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=48
scene.render.filepath=str(OUT/'chair-detail.png');bpy.ops.render.render(write_still=True)
