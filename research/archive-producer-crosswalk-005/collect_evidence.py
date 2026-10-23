import json,hashlib,re,subprocess
from pathlib import Path
import pefile,capstone
ROOT=Path('C:/work/develop/type3-clipboard-codec')
OUT=ROOT/'research/archive-producer-crosswalk-005'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=False)
 source=ROOT/'research/archive-copy-runtime-004'
 old=json.loads((source/'incident-closeout-evidence.json').read_text(encoding='utf-8-sig'))
 protected=[{'path':x['Path'],'sha256':sha(Path(x['Path'])),'expected':x['SHA256'].lower()} for x in old['ProtectedFiles']]
 assert all(x['sha256']==x['expected'] for x in protected)
 p=Path('C:/TypeEdit_2009/EXE/Pltf.exe');pe=pefile.PE(str(p));base=pe.OPTIONAL_HEADER.ImageBase
 assert sha(p)=='f679f2641e60a41f62326e1c68c5e2c64d2415498bb1b92019c5f2d64245e662'
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 expected={0xc350e:('call 0x64c516','e803901800'),0xc352d:('call 0x64bd7e','e84c881800'),0xc3532:('mov byte ptr [ebp-4],1','c645fc01'),0xc3536:('call [0x70b868]','ff1568b87000'),0xc354c:('call [0x70b86c]','ff156cb87000'),0xc3564:('call eax','ffd0'),0xc3566:('call [0x70b870]','ff1570b87000')}
 rows=[]
 for r,(text,enc) in expected.items():
  n=len(bytes.fromhex(enc));s=next(s for s in pe.sections if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData))
  rows.append({'rva':hex(r),'file_offset':hex(pe.get_offset_from_rva(r)),'section':s.Name.rstrip(b'\0').decode(),'runtime_text':text,'runtime_encoding_inferred_not_captured':enc,'disk_bytes':pe.get_data(r,n).hex(),'encoding_matches':pe.get_data(r,n).hex()==enc,'disk_decode_candidate':[{'rva':hex(i.address-base),'bytes':i.bytes.hex(),'asm':i.mnemonic+' '+i.op_str} for i in md.disasm(pe.get_data(r,12),base+r)]})
 obs=json.loads((source/'runtime-001/debugger-observations.json').read_text(encoding='utf-8-sig'))
 excerpt=[x for x in obs if 'disassemble --start-address 0x004c34f0' in x['commands']]
 (OUT/'runtime-instruction-excerpt.json').write_text(json.dumps(excerpt,ensure_ascii=False,indent=2),encoding='utf-8')
 rel=[{'rva':hex(e.rva),'type':e.type} for block in getattr(pe,'DIRECTORY_ENTRY_BASERELOC',[]) for e in block.entries if 0xc34e0<=e.rva<0xc35b0]
 result={'verdict':'PLTF_ARCHIVE_CROSSWALK_BLOCKED','publication':'UNKNOWN / PRODUCER_NOT_FULLY_LINKED','Pltf':{'path':str(p),'sha256':sha(p),'size':p.stat().st_size,'preferred_base':hex(base),'machine':hex(pe.FILE_HEADER.Machine)},'comparisons':rows,'relocations_in_target_range':rel,'runtime_raw_instruction_bytes_available':False,'comparison_limit':'Runtime mnemonic evidence only; encodings reconstructed for comparison, not historical memory bytes. Disk opcodes independently incompatible with recorded instructions.','protected_originals':protected,'git_head':subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()}
 (OUT/'static-evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'verdict':result['verdict'],'comparisons':len(rows),'matches':sum(x['encoding_matches'] for x in rows),'protected':len(protected),'relocations':rel}))
if __name__=='__main__':main()
