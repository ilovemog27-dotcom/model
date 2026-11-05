"""R6-style six-body-part articulated display figure, units mm.
Requires numpy and manifold3d. Prints separately; assemble using the printed pins.
"""
from pathlib import Path
import sys,json,struct,hashlib,zipfile
import numpy as np
try: import manifold3d as m
except ImportError:
 sys.path.insert(0,'/tmp/dominus-tools');import manifold3d as m
P=Path(__file__).resolve().parent
P.mkdir(exist_ok=True)
SEGMENTS=64

def box(size,center):return m.Manifold.cube(size,center=True).translate(center)
def cz(h,r,center):return m.Manifold.cylinder(h,r,circular_segments=SEGMENTS,center=True).translate(center)
def cx(h,r,center):return m.Manifold.cylinder(h,r,circular_segments=SEGMENTS,center=True).rotate((0,90,0)).translate(center)
def union(parts):return m.Manifold.batch_boolean(parts,m.OpType.Add)
def cut(base,tools):return m.Manifold.batch_boolean([base]+tools,m.OpType.Subtract)
# R6 block proportions: torso 2x2x1, arms 1x2x1, legs approximately 1x2x1.
torso=box((60,30,60),(0,0,91))
tabs=[]
for x in [-15.25,15.25]:tabs += [cx(10,8,(x,0,45)),box((10,12,17),(x,0,53.5))]
torso=union([torso]+tabs)
tools=[cz(12.2,3,(0,0,115))]
for side in [-1,1]:tools += [cx(13.2,3,(side*24.4,0,106)),cx(10.4,3,(side*15.25,0,45))]
torso=cut(torso,tools)
left_arm=cut(box((30,30,60),(46,0,91)),[cx(30.4,3.3,(46,0,106))])
right_arm=left_arm.mirror((1,0,0))
left_leg=union([box((29.5,30,45),(15.25,0,22.5)),cx(29.5,15,(15.25,0,45))])
left_leg=cut(left_leg,[cx(10.8,18.3,(15.25,0,45)),cx(29.9,3.3,(15.25,0,45))])
right_leg=left_leg.mirror((1,0,0))
head=union([m.Manifold.cylinder(1,20,21,circular_segments=SEGMENTS).translate((0,0,125)),cz(33,21,(0,0,142.5)),m.Manifold.cylinder(1,21,20,circular_segments=SEGMENTS).translate((0,0,159))])
head=cut(head,[cz(13.2,3.3,(0,0,131.5)),cz(3,3.7,(0,0,136))])

def hinge_pin(length,split_length):
 flange=cz(2.2,5,(0,0,1.1))
 shaft=cz(length-1.5,3.1,(0,0,2.2+(length-1.5)/2))
 lead=m.Manifold.cylinder(1.5,3.1,2.6,circular_segments=SEGMENTS).translate((0,0,2.2+length-1.5))
 base=union([flange,shaft,lead])
 return cut(base,[box((1.05,8,split_length+.4),(0,0,2.2+length-split_length/2+.1))])
shoulder_pin=hinge_pin(43,14)
hip_pin=hinge_pin(29.5,24)
neck_pin=union([m.Manifold.cylinder(1.5,2.6,3.1,circular_segments=SEGMENTS),cz(10.5,3.1,(0,0,6.75)),cz(4,5,(0,0,14)),cz(10,3.1,(0,0,21)),cz(1.2,3.45,(0,0,26.6)),m.Manifold.cylinder(.8,3.45,2.9,circular_segments=SEGMENTS).translate((0,0,27.2))])
neck_pin=cut(neck_pin,[box((1.05,8,10.4),(0,0,4.9)),box((1.05,8,10.4),(0,0,23.1))])
coupon=box((70,16,8),(0,0,4))
coupon=cut(coupon,[cz(8.4,d/2,(x,0,4)) for x,d in zip([-24,-8,8,24],[6,6.2,6.4,6.6])]+[box((3,4,8.4),(-35,0,4))])
fit_pin=hinge_pin(12,8)

bodies={'head':head,'torso':torso,'left_arm':left_arm,'right_arm':right_arm,'left_leg':left_leg,'right_leg':right_leg}
hardware={'shoulder_pin':shoulder_pin,'hip_pin':hip_pin,'neck_pin':neck_pin,'fit_test_block':coupon,'fit_test_pin':fit_pin}
world={**bodies,'shoulder_pin_left':shoulder_pin.rotate((0,-90,0)).translate((63.2,0,106)),'shoulder_pin_right':shoulder_pin.rotate((0,90,0)).translate((-63.2,0,106)),'hip_pin_left':hip_pin.rotate((0,-90,0)).translate((32.2,0,45)),'hip_pin_right':hip_pin.rotate((0,90,0)).translate((-32.2,0,45)),'neck_pin':neck_pin.translate((0,0,109))}

# Validate geometry, designed motion, and nominal fit clearances before export.
checks=[]
for key,angles,pivot in [('left_arm',[-120,-60,0,60,120],106),('right_arm',[-120,-60,0,60,120],106),('left_leg',[-90,-45,0,45,90],45),('right_leg',[-90,-45,0,45,90],45)]:
 for angle in angles:
  moving=bodies[key].translate((0,0,-pivot)).rotate((angle,0,0)).translate((0,0,pivot))
  volume=(moving^torso).volume()
  checks.append({'part':key,'rotation_degrees':angle,'torso_intersection_mm3':volume})
  assert volume<.001,(key,angle,volume)
for angle in [0,90,180,270]:
 moving=head.translate((0,0,-125)).rotate((0,0,angle)).translate((0,0,125))
 assert (moving^torso).volume()<.001

# Each individual STL is in a usable printing orientation, bottom at Z=0.
print_models={}
for key,solid in {**bodies,**hardware}.items():
 assert solid.status()==m.Error.NoError,(key,solid.status())
 assert len(solid.decompose())==1,(key,'not one solid',len(solid.decompose()))
 if key in ['head','torso']:solid=solid.rotate((180,0,0))
 me=solid.to_mesh();v=np.asarray(me.vert_properties[:,:3]);lo=v.min(0);hi=v.max(0)
 solid=solid.translate((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))
 print_models[key]=solid

def mesh_json(solid):
 me=solid.to_mesh();return {'vertices':np.asarray(me.vert_properties[:,:3]).tolist(),'faces':np.asarray(me.tri_verts).tolist()}
(P/'parts_geometry.json').write_text(json.dumps({key:mesh_json(value) for key,value in print_models.items()}))
(P/'assembly_geometry.json').write_text(json.dumps({key:mesh_json(value) for key,value in world.items()}))
posed={**world}
for key,angle,pivot in [('left_arm',-35,106),('right_arm',35,106),('left_leg',25,45),('right_leg',-15,45)]:posed[key]=bodies[key].translate((0,0,-pivot)).rotate((angle,0,0)).translate((0,0,pivot))
(P/'posed_geometry.json').write_text(json.dumps({key:mesh_json(value) for key,value in posed.items()}))
manifest={'design':'R6-style articulated block avatar','main_body_parts':list(bodies),'main_body_part_count':6,'assembled_height_mm':160,'units':'millimeters','joints':{'neck':'swivel, snap-retained split pin','shoulders':'two friction-retained printed axle hinges','hips':'two friction-retained printed axle hinges; no knees'},'hardware_quantities':{'shoulder_pin.stl':2,'hip_pin.stl':2,'neck_pin.stl':1},'fit_test_quantities':{'fit_test_block.stl':1,'fit_test_pin.stl':1},'nominal_fit':{'axle_diameter_mm':6.2,'moving_bore_diameter_mm':6.6,'anchor_bore_diameter_mm':6.0,'hip_fork_clearance_each_side_mm':.4,'neck_snap_bead_diameter_mm':6.9,'neck_snap_groove_diameter_mm':7.4},'collision_checks':checks,'neck_rotation_samples_degrees':[0,90,180,270],'physical_joint_fit_tested':False,'bambu_studio_slicing_tested':False,'notes':['Custom CAD model based on classic R6 block proportions; not a converted official Roblox avatar mesh.','Six main body parts plus five separately printed joint pins. No elbows or knees.','STLs are separate parts for assembly. Do not fuse the body parts together.','Print the fit test first; printer calibration and material affect pin fit.','Nominal 0.2 mm diameter interference at split pin anchors; the split tip supplies compliance.']}
(P/'design_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('R6 design generated:',len(bodies),'body parts;',len(hardware),'unique hardware/test models;',len(checks),'limb clearance checks passed.')
