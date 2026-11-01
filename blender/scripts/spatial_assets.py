"""共享的实物细节与支撑面审计；坐标单位为米，Web Y 为竖直轴。"""
import bpy,math,json,re
from mathutils import Vector
def cup(name,bottom,radius,height,material,liquid_material,parts=None):
 x,y,z=bottom;n=24;t=.007;verts=[]
 for r,h in [(radius,0),(radius,height),(radius-t,height),(radius-t,t)]:
  for i in range(n):a=i*math.tau/n;verts.append((x+r*math.cos(a),-(z+r*math.sin(a)),y+h))
 faces=[]
 for ring in range(3):
  for i in range(n):j=(i+1)%n;faces.append((ring*n+i,ring*n+j,(ring+1)*n+j,(ring+1)*n+i))
 faces.extend([tuple(reversed(range(n))),tuple(range(3*n,4*n))]);mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.data.materials.append(material)
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 # 杯体具有开口、内壁和底，不以实心球体替代。
 if parts is not None:parts.append(o)
 vertices=[(x,-z,y+height*.78)]+[(x+(radius-t-.002)*math.cos(i*math.tau/n),-(z+(radius-t-.002)*math.sin(i*math.tau/n)),y+height*.78) for i in range(n)]
 liquid=bpy.data.meshes.new(name+'_Liquid');liquid.from_pydata(vertices,[],[(0,i+1,(i+1)%n+1) for i in range(n)]);obj=bpy.data.objects.new(name+'_Liquid',liquid);bpy.context.collection.objects.link(obj);obj.data.materials.append(liquid_material)
 if parts is not None:parts.append(obj)
 return o
def capture_parts(path):
 result=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  pts=[o.matrix_world@Vector(v) for v in o.bound_box];lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
  result.append({'name':o.name,'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]})
 # 仅测试应当放在平面上的实物；墙面装饰、灯具、蝴蝶、树叶不当作悬空道具。
 pattern=r'^(Library_Book|Shelf_Book|Back_Cabinet_Book|Cabinet_Book|Notebook|Pencil|Desk_Book|Desk_Nameplate|Book_Cover|Paper|Desk_Stack|Bread|Basket|Planter|Plant_Pot|Tea_Cup|Coaster)(?:\.\d+)?$'
 checks=[]
 for item in result:
  if not re.match(pattern,item['name']):continue
  a,b=item['min'],item['max'];matches=[]
  if abs(a[1])<.004:matches.append('ground')
  for other in result:
   if other is item:continue
   c,d=other['min'],other['max'];delta=a[1]-d[1]
   overlap=max(0,min(b[0],d[0])-max(a[0],c[0]))*max(0,min(b[2],d[2])-max(a[2],c[2]));area=max(.000001,(b[0]-a[0])*(b[2]-a[2]))
   if abs(delta)<.004 and overlap/area>.65:matches.append(other['name'])
  checks.append({'name':item['name'],'bottom':a[1],'supported_by':matches})
 path.write_text(json.dumps({'parts':result,'support_checks':checks,'unsupported':[c for c in checks if not c['supported_by']]},ensure_ascii=False,indent=2),encoding='utf-8')
