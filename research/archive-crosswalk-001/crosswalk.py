"""Bounded saved-file crosswalk, not a general Archive parser or write admission."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import struct,json,hashlib,importlib.util
ROOT=Path(__file__).resolve().parent
GROUP=ROOT.parent/'group-color'
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
base=load('crosswalk_base',GROUP/'type3-clipboard-base-serialize-003/walk_base.py')
check=load('crosswalk_predictions',GROUP/'type3-clipboard-independent-prediction-006/prediction_check.py')
class Unsupported(ValueError):pass
class Reader:
    def __init__(self,data):self.data=data;self.pos=6;self.next_id=1;self.classes={};self.events=[];self.colors=[];self.properties=[]
    def take(self,n):
        if n<0 or self.pos+n>len(self.data):raise Unsupported('truncated at '+str(self.pos))
        a=self.pos;self.pos+=n;return self.data[a:self.pos]
    def u32(self):return struct.unpack('<I',self.take(4))[0]
    def bounded(self,n):
        if n>100:raise Unsupported('unreviewed count/length')
        return n
    def property_body(self,start):
        # Maude 603ac..605ce: sequential writes; meanings remain raw members.
        self.take(40);ni=self.bounded(self.u32());self.take(4*ni)
        self.take(16);nd=self.bounded(self.u32());self.take(8*nd)
        self.take(32)
        n1=self.bounded(self.u32());self.take(n1)
        if self.u32()!=0:raise Unsupported('optional property child1')
        n2=self.bounded(self.u32());self.take(n2)
        if self.u32()!=0:raise Unsupported('optional property child2')
        self.properties.append({'body':[start,self.pos],'int_count':ni,'double_count':nd,'string_lengths':[n1,n2]})
    def obj(self,depth=0):
        if depth>8:raise Unsupported('depth limit')
        start=self.pos;tag=struct.unpack('<H',self.take(2))[0]
        if tag==0xffff:
            schema,size=struct.unpack('<HH',self.take(4));name=self.take(self.bounded(size)).decode('ascii')
            if name not in ('CZone','CCourbe','CContour','CPropertyExtend'):raise Unsupported('class '+name)
            wanted={'CZone':1,'CCourbe':1,'CContour':2,'CPropertyExtend':5}
            if schema!=wanted[name]:raise Unsupported('unreviewed schema')
            cid=self.next_id;self.next_id+=1;self.classes[cid]=name
            self.events.append({'kind':'new_class','span':[start,self.pos],'class_id':cid,'class':name,'schema':schema})
        elif 0x8000<tag<0xffff:
            cid=tag&0x7fff
            if cid not in self.classes:raise Unsupported('unknown class reference '+str(cid))
            name=self.classes[cid]
            self.events.append({'kind':'class_reference','span':[start,self.pos],'class_id':cid,'class':name,'tag':hex(tag)})
        else:raise Unsupported('object/null/extended reference branch not supported')
        oid=self.next_id;self.next_id+=1;body=self.pos
        node={'class':name,'class_id':cid,'object_id_archive_scope_only':oid,'tag_span':[start,body],'body_start':body,'children':[]}
        if name=='CPropertyExtend':self.property_body(body)
        else:
            walked=base.walk(self.data,self.pos);self.pos=walked['base_end'];node['base_span']=[body,self.pos]
            if name in ('CZone','CCourbe'):
                if self.u32()!=3:raise Unsupported('container version')
                count=self.bounded(self.u32());node['helper_count']=count
                for _ in range(count):node['children'].append(self.obj(depth+1))
                # Conditional scope: reviewed samples have no extra direct Serialize-list bytes.
                node['additional_virtual_list']='not independently proven; zero contribution assumed for this crosswalk'
                if name=='CCourbe':
                    a=self.pos;raw=self.take(24);values=struct.unpack('<6I',raw)
                    self.colors.append({'curve_body':body,'suffix_span':[a,self.pos],
                        'b8_range':[a+8,a+12],'c4_range':[a+20,a+24],
                        'b8_hex':raw[8:12].hex(),'c4_hex':raw[20:24].hex(),'raw_dwords':list(values)})
            elif name=='CContour':
                node['raw_member_130']=self.u32();count=self.bounded(self.u32())
                a=self.pos;self.take(count*36);node['point_records']={'count':count,'span':[a,self.pos],'record_width':36}
                prop=self.obj(depth+1)
                if prop['class']!='CPropertyExtend':raise Unsupported('contour property class')
                node['children'].append(prop)
        node['body_end']=self.pos
        self.events.append({'kind':'object_end','class':name,'object_id_archive_scope_only':oid,'end':self.pos})
        return node

def diagnose(data):
    if data[:6]!=bytes.fromhex('000000000100'):raise Unsupported('unreviewed Type3 prefix')
    reader=Reader(data);tree=reader.obj()
    predicted=check.predict_bytes(data)['locator_result']
    if predicted['status']!='CANDIDATE_ONLY':raise Unsupported('locator rejects family')
    ranges=[m['color_pair_ranges_candidate'] for m in predicted['members']]
    actual=[[c['b8_range'],c['c4_range']] for c in reader.colors]
    if ranges!=actual:raise Unsupported('native-order suffix differs from locator')
    return {'sha256':hashlib.sha256(data).hexdigest(),'verdict':'ARCHIVE_CROSSWALK_PARTIAL',
        'archive_start_hypothesis':6,'initial_map_count_hypothesis':1,
        'assumptions':['Fresh unseeded archive context at byte6; prefix producer not proven',
            'No additional virtual direct-Serialize-list data or hidden MapObject in reviewed object bodies'],
        'events':reader.events,'tree':tree,'properties':reader.properties,'curve_colors':reader.colors,
        'class_table_conditional':reader.classes,'parsed_end':reader.pos,'trailing_bytes':len(data)-reader.pos,
        'trailing_bytes_meaning':'UNKNOWN; not parsed as padding or more objects',
        'class8_conditional':reader.classes.get(8),'color_ranges_equal_locator':True,'change_allowed':False}

def main():
    paths={'G1':GROUP/'type3-clipboard-member-color-003/samples/G1/typeeditzone.bin',
        'H0-A':GROUP/'type3-clipboard-independent-prediction-006/samples/H0-A/typeeditzone.bin',
        'H1':GROUP/'type3-clipboard-independent-prediction-006/samples/H1/typeeditzone.bin'}
    out={name:diagnose(p.read_bytes()) for name,p in paths.items()}
    (ROOT/'crosswalk.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name,r in out.items():print(name,r['class8_conditional'],r['parsed_end'],r['color_ranges_equal_locator'])
    return out
if __name__=='__main__':main()
