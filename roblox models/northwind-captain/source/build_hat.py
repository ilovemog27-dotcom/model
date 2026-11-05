"""Original Northwind Captain hat. Native Roblox primitives and shared mesh geometry.
Coordinates in this generator are Roblox studs, X right, Y up, -Z front.
"""
from pathlib import Path
import numpy as np,math,json,xml.etree.ElementTree as ET,uuid
P=Path(__file__).resolve().parent
P.mkdir(exist_ok=True)
PALETTE={'crown':(22,35,57),'band':(21,82,91),'visor':(20,24,33),'brass':(201,159,77),'steel':(132,160,171),'lining':(79,36,48),'badge':(13,47,61),'gem':(91,202,211)}
parts=[]
def rx(deg):
 a=math.radians(deg);return np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
def ry(deg):
 a=math.radians(deg);return np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
def rz(deg):
 a=math.radians(deg);return np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
def add(name,shape,size,pos,color,R=None,segments=16):
 R=np.eye(3) if R is None else np.asarray(R);assert abs(np.linalg.det(R)-1)<1e-6
 parts.append({'name':name,'shape':shape,'size':list(size),'position':list(pos),'rotation':R.tolist(),'color':color,'segments':segments})
def line(name,start,end,radius,color,segments=10):
 a=np.asarray(start);b=np.asarray(end);x=b-a;length=np.linalg.norm(x);x/=length
 helper=np.array([0,1.,0]) if abs(x[1])<.95 else np.array([0,0,1.])
 z=np.cross(x,helper);z/=np.linalg.norm(z);y=np.cross(z,x);R=np.column_stack((x,y,z))
 add(name,'cylinder',(length,radius*2,radius*2),(a+b)/2,color,R,segments)
def triangle(name,a,b,c,thickness,color):
 pts=[np.asarray(x,dtype=float) for x in [a,b,c]]
 # Longest edge is the base so the altitude falls within it.
 lengths=[np.linalg.norm(pts[1]-pts[2]),np.linalg.norm(pts[0]-pts[2]),np.linalg.norm(pts[0]-pts[1])]
 apex=int(np.argmax(lengths));A=pts[apex];B=pts[(apex+1)%3];C=pts[(apex+2)%3]
 u=C-B;L=np.linalg.norm(u);u/=L;t=np.dot(A-B,u);D=B+t*u;v=A-D;h=np.linalg.norm(v)
 if h<1e-6:return
 v/=h
 for suffix,Q,z,width in [('a',B,u,t),('b',C,-u,L-t)]:
  if width<.001:continue
  R=np.column_stack((np.cross(v,z),v,z))
  add(name+'_'+suffix,'wedge',(thickness,h,width),(A+Q)/2,color,R)
# Slouched, flared crown with a clean top and original asymmetric seam detail.
add('Soft navy crown','sphere',(2.22,.68,1.86),(0,.09,.07),'crown',rx(12),32)
add('Peaked crown top','cylinder',(.10,2.31,1.94),(0,.41,.01),'crown',rx(12)@rz(90),32)
add('Deep teal headband','cylinder',(.27,2.00,1.62),(0,-.205,.07),'band',rz(90),32)
add('Burgundy lower welt','cylinder',(.045,2.025,1.645),(0,-.354,.07),'lining',rz(90),32)
# Swept visor, built from exact native wedge prisms as well as exportable mesh faces.
N=12;thetas=np.linspace(-math.radians(78),math.radians(78),N+1)
inner=[];outer=[]
for t in thetas:
 inner.append(np.array((1.00*math.sin(t),-.307,-.76*math.cos(t)+.03)))
 outer.append(np.array((1.17*math.sin(t),-.44+.045*abs(math.sin(t)),-1.45*math.cos(t)+.01)))
for i in range(N):
 triangle(f'Visor panel {i:02d} I',inner[i],outer[i],outer[i+1],.062,'visor')
 triangle(f'Visor panel {i:02d} II',inner[i],outer[i+1],inner[i+1],.062,'visor')
 line(f'Brass visor edge {i:02d}',outer[i]+[0,.006,0],outer[i+1]+[0,.006,0],.018,'brass',8)
# Front cord follows the band, lifted slightly at the sides. No copied insignia.
cord=[]
for t in np.linspace(-1.24,1.24,11):cord.append(np.array((.96*math.sin(t),-.13+.095*abs(math.sin(t)),-.815*math.cos(t)-.013)))
for i in range(len(cord)-1):line(f'Front brass cord {i:02d}',cord[i],cord[i+1],.025,'brass',8)
for side in [-1,1]:
 add(f'Side compass button {side}','cylinder',(.055,.18,.18),(side*.99,-.10,-.22),'brass',segments=16)
 add(f'Side button inset {side}','cylinder',(.063,.105,.105),(side*1.004,-.10,-.22),'steel',segments=12)
 # Short original chevron-like epaulet stripes, inset on the crown shoulders.
 add(f'Crown teal slash {side}','block',(.035,.28,.045),(side*.80,.26,-.51),'band',rz(-side*35))
# Compass badge on the high front crown. Ring and rays are separate, native geometry.
badge_center=np.array((0,.265,-.902))
# Local cylinder X axis points toward the front (-Z).
badge_R=ry(90)
add('Compass badge backing','cylinder',(.060,.37,.37),badge_center,'badge',badge_R,24)
add('Compass badge metal rim','cylinder',(.018,.407,.407),badge_center+[0,0,.008],'brass',badge_R,24)
add('Compass badge face','cylinder',(.027,.354,.354),badge_center+[0,0,-.033],'badge',badge_R,24)
# Four long and four short rays create a new eight-point compass motif.
for i in range(8):
 a=i*math.pi/4;radius=.155 if i%2==0 else .112
 direction=np.array((math.sin(a),math.cos(a),0.));perp=np.array((math.cos(a),-math.sin(a),0.))
 origin=badge_center+np.array((0,0,-.057))
 tip=origin+radius*direction;base=origin-.022*direction
 triangle(f'Compass ray {i}',tip,base+.029*perp,base-.029*perp,.018,'brass')
add('Compass center enamel','sphere',(.071,.071,.035),badge_center+[0,0,-.075],'gem',segments=16)
# Short stepped wings, visually distinct from the inspiration's badge.
for side in [-1,1]:
 for j in range(3):add(f'Badge wing {side} {j}','block',(.11,.025,.023),(side*(.255+j*.07),.245-j*.035,-.855+j*.012),'brass',rz(side*12))
# Two restrained steel seam stitches on the top/front.
for side in [-1,1]:
 for j in range(2):add(f'Top stitch {side} {j}','block',(.12,.013,.018),(side*(.52+j*.15),.485+j*.009,-.30),'steel',rx(12)@ry(side*12))

# Generate matching polygon meshes from the native primitive specifications.
def primitive(part):
 shape=part['shape'];sx,sy,sz=part['size'];v=[];f=[]
 if shape=='block':
  v=[(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)]
  f=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]
 elif shape=='wedge':
  v=[(-.5,-.5,-.5),(.5,-.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(-.5,.5,.5),(.5,.5,.5)]
  f=[(0,2,3,1),(2,4,5,3),(0,1,5,4),(0,4,2),(1,3,5)]
 elif shape=='cylinder':
  n=part['segments']
  for x in [-.5,.5]:
   for i in range(n):a=2*math.pi*i/n;v.append((x,.5*math.cos(a),.5*math.sin(a)))
  f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
  for i in range(n):j=(i+1)%n;f.append((i,j,n+j,n+i))
 elif shape=='sphere':
  n=part['segments'];rings=max(8,n//2);v=[(0,.5,0)]
  for j in range(1,rings):
   a=math.pi*j/rings
   for i in range(n):b=2*math.pi*i/n;v.append((.5*math.sin(a)*math.cos(b),.5*math.cos(a),.5*math.sin(a)*math.sin(b)))
  v.append((0,-.5,0));bottom=len(v)-1
  for i in range(n):f.append((0,1+(i+1)%n,1+i))
  for j in range(rings-2):
   for i in range(n):a=1+j*n+i;b=1+j*n+(i+1)%n;f.append((a,b,b+n,a+n))
  for i in range(n):f.append((bottom,1+(rings-2)*n+i,1+(rings-2)*n+(i+1)%n))
 else:raise ValueError(shape)
 v=np.array(v)*np.array((sx,sy,sz));v=v@np.array(part['rotation']).T+np.array(part['position'])
 return {'name':part['name'],'vertices':v.tolist(),'faces':[list(x) for x in f],'color':part['color']}
meshes=[primitive(part) for part in parts];(P/'primitive_parts.json').write_text(json.dumps(parts,indent=2));(P/'geometry.json').write_text(json.dumps(meshes));allv=np.vstack([x['vertices'] for x in meshes]);lo=allv.min(0);hi=allv.max(0)
manifest={'name':'Northwind Captain','description':'Original peaked officer cap inspired by the Team Captain silhouette; new shape, palette and compass insignia.','native_part_count':len(parts),'palette_rgb':PALETTE,'roblox_bounds_studs':{'min':lo.tolist(),'max':hi.tolist(),'size':(hi-lo).tolist(),'center':((lo+hi)/2).tolist()},'handle_hat_attachment_position':[0,-.4,0],'mesh_handle_hat_attachment_position':(np.array((0,-.4,0))-(lo+hi)/2).tolist(),'roblox_front':'-Z','native_requires_mesh_upload':False,'mesh_import_requires_roblox_asset_creation':True,'roblox_studio_runtime_tested':False,'notes':['Original geometry created from scratch; no Valve or TF2 meshes/textures used.','Native Studio accessory uses built-in primitives joined by Weld instances; optimized mesh exports share the design geometry.','STL is not included because this deliverable is for Roblox Studio rather than 3D printing.']}
(P/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
# Canonical Roblox XML accessory, with references entirely internal to this file.
root=ET.Element('roblox',{'version':'4'});ET.SubElement(root,'External').text='null';ET.SubElement(root,'External').text='nil'
def ref(name):return 'RBX'+uuid.uuid5(uuid.NAMESPACE_URL,'northwind-captain/'+name).hex.upper()
def item(parent,cls,name):
 obj=ET.SubElement(parent,'Item',{'class':cls,'referent':ref(name)});props=ET.SubElement(obj,'Properties');ET.SubElement(props,'string',{'name':'Name'}).text=name;return obj,props
def boolprop(props,name,value):ET.SubElement(props,'bool',{'name':name}).text='true' if value else 'false'
def vec(props,name,value):
 e=ET.SubElement(props,'Vector3',{'name':name})
 for k,x in zip(['X','Y','Z'],value):ET.SubElement(e,k).text=format(float(x),'.9g')
def frame(props,name,pos,R):
 e=ET.SubElement(props,'CoordinateFrame',{'name':name})
 for k,x in zip(['X','Y','Z'],pos):ET.SubElement(e,k).text=format(float(x),'.9g')
 for i in range(3):
  for j in range(3):ET.SubElement(e,f'R{i}{j}').text=format(float(R[i][j]),'.9g')
def part(parent,name,shape,size,pos,R,color,transparent=False):
 obj,pr=item(parent,'WedgePart' if shape=='wedge' else 'Part',name);vec(pr,'size',size);frame(pr,'CFrame',pos,R)
 for key,value in [('Anchored',False),('CanCollide',False),('CanTouch',False),('CanQuery',False),('Massless',True)]:boolprop(pr,key,value)
 ET.SubElement(pr,'float',{'name':'Transparency'}).text='1' if transparent else '0'
 rgb=PALETTE[color];ET.SubElement(pr,'Color3uint8',{'name':'Color3uint8'}).text=str((255<<24)|(rgb[0]<<16)|(rgb[1]<<8)|rgb[2])
 ET.SubElement(pr,'token',{'name':'Material'}).text=str(1088 if color in ['brass','steel'] else 272)
 ET.SubElement(pr,'token',{'name':'TopSurface'}).text='0';ET.SubElement(pr,'token',{'name':'BottomSurface'}).text='0'
 if shape!='wedge':ET.SubElement(pr,'token',{'name':'shape'}).text=str({'block':1,'cylinder':2,'sphere':0}[shape])
 return obj
accessory,pr=item(root,'Accessory','Northwind Captain');ET.SubElement(pr,'token',{'name':'AccessoryType'}).text='1'
handle=part(accessory,'Handle','block',(.2,.2,.2),(0,0,0),np.eye(3),'visor',True)
attachment,pr=item(handle,'Attachment','HatAttachment');frame(pr,'CFrame',(0,-.4,0),np.eye(3))
for p in parts:
 obj=part(accessory,p['name'],p['shape'],p['size'],p['position'],p['rotation'],p['color'])
 weld,wp=item(obj,'Weld','Joint '+p['name']);ET.SubElement(wp,'Ref',{'name':'Part0'}).text=ref('Handle');ET.SubElement(wp,'Ref',{'name':'Part1'}).text=ref(p['name']);frame(wp,'C0',p['position'],p['rotation']);frame(wp,'C1',(0,0,0),np.eye(3));boolprop(wp,'Enabled',True)
ET.indent(root,space='  ');(P/'northwind_captain.rbxmx').write_text(ET.tostring(root,encoding='unicode'))
print('Original hat generated:',len(parts),'visible primitives; bounds(studs)',hi-lo)
