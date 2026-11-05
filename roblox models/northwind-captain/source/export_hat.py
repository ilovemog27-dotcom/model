import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;data=json.loads((P/'geometry.json').read_text());manifest=json.loads((P/'manifest.json').read_text());palette=manifest['palette_rgb'];keys=list(palette)
bpy.ops.wm.read_factory_settings(use_empty=True)
# Color atlas has generous flat-color cells to survive Roblox texture filtering.
image=bpy.data.images.new('Northwind Captain color atlas',width=512,height=256,alpha=True)
pixels=[]
for y in range(256):
 for x in range(512):
  index=min(7,(y//128)*4+x//128);rgb=palette[keys[index]];pixels.extend([c/255 for c in rgb]+[1])
image.pixels=pixels;image.filepath_raw=str(P/'northwind_palette.png');image.file_format='PNG';image.save();image.pack()
mat=bpy.data.materials.new('Northwind Captain palette');mat.use_nodes=True;nodes=mat.node_tree.nodes;bsdf=nodes.get('Principled BSDF');tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.interpolation='Closest';mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);bsdf.inputs['Roughness'].default_value=.55
objects=[]
for d in data:
 # Roblox Y-up to Blender Z-up, preserving handedness.
 verts=[(v[0],-v[2],v[1]) for v in d['vertices']];mesh=bpy.data.meshes.new(d['name']);mesh.from_pydata(verts,[],d['faces']);mesh.update();bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 uv=mesh.uv_layers.new(name='UVMap');idx=keys.index(d['color']);center=Vector(((idx%4+.5)/4,(idx//4+.5)/2))
 for face in mesh.polygons:
  normal=face.normal;axis=Vector((1,0,0)) if abs(normal.x)<.8 else Vector((0,1,0));u=normal.cross(axis).normalized();v=normal.cross(u).normalized();coords=[Vector(mesh.vertices[mesh.loops[i].vertex_index].co) for i in face.loop_indices];pts=[Vector((co.dot(u),co.dot(v))) for co in coords];lo=Vector((min(p.x for p in pts),min(p.y for p in pts)));hi=Vector((max(p.x for p in pts),max(p.y for p in pts)));extent=max(hi.x-lo.x,hi.y-lo.y,.00001)
  for loop,pt in zip(face.loop_indices,pts):uv.data[loop].uv=center+(pt-(lo+hi)/2)*(.14/extent)
 obj=bpy.data.objects.new(d['name'],mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(mat);objects.append(obj)
bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();hat=bpy.context.object;hat.name='Northwind_Captain';bpy.ops.object.shade_smooth_by_angle(angle=math.radians(45),keep_sharp_edges=True)
bpy.context.scene.unit_settings.system='NONE'
# Triangulate explicitly for a deterministic low-poly game mesh.
tri=hat.modifiers.new('Game mesh triangulation','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
mesh=hat.data;mesh.calc_loop_triangles();triangles=len(mesh.loop_triangles);assert triangles<10000,triangles
# Direct OBJ coordinates use Roblox Y-up axes, for predictable dimensions.
with (P/'northwind_captain.obj').open('w') as f:
 f.write('# Northwind Captain - original model; Roblox studs, Y up, -Z front\nmtllib northwind_captain.mtl\no Northwind_Captain\n')
 for vert in mesh.vertices:x,y,z=vert.co;f.write(f'v {x:.9g} {z:.9g} {-y:.9g}\n')
 for uv in mesh.uv_layers.active.data:f.write(f'vt {uv.uv.x:.9g} {uv.uv.y:.9g}\n')
 f.write('usemtl NorthwindPalette\n')
 for face in mesh.polygons:f.write('f '+' '.join(f'{mesh.loops[i].vertex_index+1}/{i+1}' for i in face.loop_indices)+'\n')
(P/'northwind_captain.mtl').write_text('newmtl NorthwindPalette\nKd 1 1 1\nKa 0.2 0.2 0.2\nKs 0.2 0.2 0.2\nNs 30\nd 1\nillum 2\nmap_Kd northwind_palette.png\n')
bpy.ops.export_scene.fbx(filepath=str(P/'northwind_captain.fbx'),use_selection=True,object_types={'MESH'},global_scale=1.0,apply_unit_scale=True,apply_scale_options='FBX_SCALE_NONE',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_tspace=True,add_leaf_bones=False,bake_anim=False,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True)
# Actual export/import check: FBX contains one mesh, matching triangle count and bounds.
expected_vertices=len(mesh.vertices);expected_dims=list(hat.dimensions);expected_tris=triangles
bpy.ops.wm.save_as_mainfile(filepath=str(P/'northwind_captain.blend'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.fbx(filepath=str(P/'northwind_captain.fbx'))
imported=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(imported)==1
hat=imported[0];hat.data.calc_loop_triangles();assert len(hat.data.loop_triangles)==expected_tris
assert max(abs(a-b) for a,b in zip(hat.dimensions,expected_dims))<.0001,(list(hat.dimensions),expected_dims)
# Check actual OBJ indices, UVs and expected Roblox bounding-box coordinates.
obj_text=(P/'northwind_captain.obj').read_text().splitlines();objv=[list(map(float,x.split()[1:])) for x in obj_text if x.startswith('v ')];objfaces=[x for x in obj_text if x.startswith('f ')];assert len(objfaces)==expected_tris
for face in objfaces:
 for corner in face.split()[1:]:assert 1<=int(corner.split('/')[0])<=len(objv)
lo=[min(v[i] for v in objv) for i in range(3)];hi=[max(v[i] for v in objv) for i in range(3)]
for a,b in zip([hi[i]-lo[i] for i in range(3)],manifest['roblox_bounds_studs']['size']):assert abs(a-b)<.0001
report={'name':'Northwind Captain','mesh_objects':1,'triangles':expected_tris,'vertices':expected_vertices,'uv_atlas_size':[512,256],'fbx_export_reimport_passed':True,'obj_structure_and_bounds_passed':True,'native_part_count':manifest['native_part_count'],'mesh_bounds_roblox_studs':manifest['roblox_bounds_studs']['size'],'roblox_studio_import_tested':False,'wearing_in_roblox_studio_tested':False,'hashes':{name:hashlib.sha256((P/name).read_bytes()).hexdigest() for name in ['northwind_captain.fbx','northwind_captain.obj','northwind_palette.png']}}
(P/'mesh_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('MESH_VALIDATION',report,flush=True)
# Presentation uses workbench materials generated from the UV swatch, with both hero and fit views.
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in data:
 verts=[(v[0],-v[2],v[1]) for v in d['vertices']];me=bpy.data.meshes.new(d['name']);me.from_pydata(verts,[],d['faces']);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();o=bpy.data.objects.new(d['name'],me);bpy.context.collection.objects.link(o);material=bpy.data.materials.get('Preview '+d['color'])
 if not material:material=bpy.data.materials.new('Preview '+d['color']);material.diffuse_color=tuple(x/255 for x in palette[d['color']])+(1,)
 me.materials.append(material)
 for face in me.polygons:face.use_smooth=d['name'] in ['Soft navy crown'] or ('button' in d['name'].lower())
scene=bpy.context.scene;scene.world=bpy.data.worlds.new('World');scene.world.color=(.075,.09,.115);scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD';scene.render.image_settings.file_format='PNG';scene.render.resolution_x=1200;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
bpy.ops.object.camera_add(location=(3.5,6,3.2));cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO'
def render(filename,location,center,scale):
 cam.location=Vector(location);cam.rotation_euler=(Vector(center)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(P/filename);bpy.ops.render.render(write_still=True)
render('preview.png',(3.5,6,3.2),(0,.15,.1),3.6)
render('front_preview.png',(0,7,2),(0,.15,.1),3.5)
# Classic-head fit reference: head top and HatAttachment match the native model's intended placement.
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.625,depth=1.25,location=(0,0,-1.0));head=bpy.context.object;head.name='Classic head fit reference (not exported)';material=bpy.data.materials.new('Mannequin yellow');material.diffuse_color=(.92,.65,.10,1);head.data.materials.append(material)
render('wear_preview.png',(4.5,7,3),(0,.1,-.45),4.1)
render('back_preview.png',(-3.5,-6,2.8),(0,0,-.25),3.9)
