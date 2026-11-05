import bpy,bmesh,json,hashlib,sys,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;OUT=P/'stl';OUT.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);data=json.loads((P/'parts_geometry.json').read_text());validation=[];clean={}
for name,d in data.items():
 me=bpy.data.meshes.new(name);me.from_pydata(d['vertices'],[],d['faces']);me.update();obj=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(obj)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0002);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0002);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;path=OUT/(name+'.stl');bpy.ops.wm.stl_export(filepath=str(path),export_selected_objects=True,ascii_format=False)
 bpy.data.objects.remove(obj,do_unlink=True);bpy.ops.wm.stl_import(filepath=str(path));obj=bpy.context.object;bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
 unseen=set(bm.verts);count=0
 while unseen:
  count+=1;todo=[unseen.pop()]
  while todo:
   v=todo.pop()
   for e in v.link_edges:
    o=e.other_vert(v)
    if o in unseen:unseen.remove(o);todo.append(o)
 r={'file':path.name,'triangles':len(bm.faces),'vertices':len(bm.verts),'components':count,'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-9 for f in bm.faces),'volume_mm3':bm.calc_volume(signed=True),'dimensions_mm':list(obj.dimensions),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 assert r['components']==1 and r['boundary_edges']==r['nonmanifold_edges']==r['degenerate_faces']==0 and r['volume_mm3']>0,r
 bm.verts.ensure_lookup_table();index={v:i for i,v in enumerate(bm.verts)};clean[name]={'vertices':[v.co[:] for v in bm.verts],'faces':[[index[v] for v in f.verts] for f in bm.faces]};bm.free();validation.append(r);bpy.data.objects.remove(obj,do_unlink=True)
(P/'validation.json').write_text(json.dumps({'units':'mm','parts':validation,'actual_stl_reimport_checks_passed':True,'physical_joint_fit_tested':False,'bambu_studio_slicing_tested':False,'motion_checks':'20 sampled hinge rotations plus four neck rotations were checked for intersection with the torso in generate_r6.py.'},indent=2)+'\n')
# Arrange thirteen actual printed pieces on a plate inside a 170 mm square.
quantities={'head':1,'torso':1,'left_arm':1,'right_arm':1,'left_leg':1,'right_leg':1,'shoulder_pin':2,'hip_pin':2,'neck_pin':1,'fit_test_block':1,'fit_test_pin':1}
plate={};x=y=5.;rowheight=0.
for name in ['head','torso','left_arm','right_arm','left_leg','right_leg','fit_test_block','shoulder_pin','hip_pin','neck_pin','fit_test_pin']:
 d=clean[name];vs=[Vector(v) for v in d['vertices']];lo=Vector(tuple(min(v[i] for v in vs) for i in range(3)));hi=Vector(tuple(max(v[i] for v in vs) for i in range(3)));width=hi.x-lo.x;height=hi.y-lo.y
 for q in range(quantities[name]):
  if x+width>165:x=5.;y+=rowheight+8.;rowheight=0.
  assert y+height<170
  offset=Vector((x-lo.x,y-lo.y,-lo.z));plate[f'{name}_{q+1}']={'vertices':[list(v+offset) for v in vs],'faces':d['faces']};x+=width+8.;rowheight=max(rowheight,height)
(P/'plate_geometry.json').write_text(json.dumps(plate))
ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
def tag(t):return '{'+ns+'}'+t
model=ET.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'});ET.SubElement(model,tag('metadata'),{'name':'Title'}).text='R6 articulated avatar - separate parts print plate';resources=ET.SubElement(model,tag('resources'));build=ET.SubElement(model,tag('build'))
for i,(name,d) in enumerate(plate.items(),1):
 o=ET.SubElement(resources,tag('object'),{'id':str(i),'type':'model','name':name});mesh=ET.SubElement(o,tag('mesh'));verts=ET.SubElement(mesh,tag('vertices'));tri=ET.SubElement(mesh,tag('triangles'))
 for v in d['vertices']:ET.SubElement(verts,tag('vertex'),dict(zip(['x','y','z'],[format(n,'.9g') for n in v])))
 for f in d['faces']:ET.SubElement(tri,tag('triangle'),dict(zip(['v1','v2','v3'],map(str,f))))
 ET.SubElement(build,tag('item'),{'objectid':str(i)})
with zipfile.ZipFile(P/'r6_print_plate.3mf','w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
 z.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
 z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
# Re-read the package and assert all thirteen printable objects survived serialization.
with zipfile.ZipFile(P/'r6_print_plate.3mf') as z:
 root=ET.fromstring(z.read('3D/3dmodel.model'));assert len(root.find(tag('build')))==13
print('R6 exported:',len(validation),'unique closed STL models, 13 pieces on a 3MF plate.',flush=True)
# Render neutral, posed, and separate-parts previews using CAD geometry.
colors={'head':(.95,.69,.05,1),'torso':(.04,.28,.75,1),'left_arm':(.95,.69,.05,1),'right_arm':(.95,.69,.05,1),'left_leg':(.15,.48,.10,1),'right_leg':(.15,.48,.10,1)}
for source,filename in [('assembly_geometry.json','assembly_preview.png'),('posed_geometry.json','posed_preview.png'),('plate_geometry.json','print_plate_preview.png')]:
 bpy.ops.wm.read_factory_settings(use_empty=True);j=json.loads((P/source).read_text())
 for name,d in j.items():
  me=bpy.data.meshes.new(name);me.from_pydata(d['vertices'],[],d['faces']);me.update();obj=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(obj);mat=bpy.data.materials.new(name+' material');key=next((k for k in colors if name==k or name.startswith(k+'_')),None);mat.diffuse_color=colors.get(key,(.40,.40,.42,1));obj.data.materials.append(mat)
 scene=bpy.context.scene;scene.world=bpy.data.worlds.new('World');scene.world.color=(.16,.16,.16);scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.studio_light='paint.sl';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.background_type='WORLD'
 if source=='plate_geometry.json':center=Vector((80,55,25));location=center+Vector((160,-240,220));ortho=240
 else:center=Vector((0,0,80));location=Vector((220,-320,220));ortho=235
 bpy.ops.object.camera_add(location=location);camera=bpy.context.object;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=ortho;scene.camera=camera;scene.render.resolution_x=1000;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(P/filename);bpy.ops.render.render(write_still=True)
 if source=='assembly_geometry.json':bpy.ops.wm.save_as_mainfile(filepath=str(P/'r6_assembly_reference.blend'))
