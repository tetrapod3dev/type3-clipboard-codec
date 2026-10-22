"""Verify saved, approved one-Paste output. No Clipboard or Host operations."""
from prepare_patch import HERE,PRIOR,INPUT_SHA,OUTPUT_SHA,CHANGED,sha,Decoder,geometry,colors
import json

root=HERE/'runtime-001'
original=(PRIOR/'samples/G1/typeeditzone.bin').read_bytes()
candidate=(HERE/'candidate/typeeditzone.bin').read_bytes()
recopy=(root/'recopy/typeeditzone.bin').read_bytes()
version=(HERE/'candidate/typeeditzone_version.bin').read_bytes()
recopy_version=(root/'recopy/typeeditzone_version.bin').read_bytes()
if sha(original)!=INPUT_SHA or sha(candidate)!=OUTPUT_SHA:
    raise ValueError('Frozen input/candidate SHA mismatch')
if candidate!=recopy or version!=recopy_version:
    raise ValueError('Actual recopy differed; investigate before runtime verdict')
before,after=Decoder().decode_bytes(original),Decoder().decode_bytes(recopy)
if geometry(before)!=geometry(after):raise ValueError('Geometry differs')
if not after.is_grouped or after.declared_object_count!=1 or len(after.object_chains)!=2:
    raise ValueError('Unexpected decoded group structure')
if [c['name'] for c in colors(after)]!=['Navy Blue','Army Green']:
    raise ValueError('Unexpected member colors')
actual=[i for i,(a,b) in enumerate(zip(original,recopy)) if a!=b]
if actual!=list(CHANGED):raise ValueError('Unexpected source-to-recopy differences')
result={'verdict':'GROUP_PATCH_RUNTIME_VERIFIED','scope':'Exact approved G1 candidate only',
    'input_G1_sha256':sha(original),'candidate_sha256':sha(candidate),'recopy_sha256':sha(recopy),
    'zone_lengths':[len(original),len(candidate),len(recopy)],
    'version_sha256':sha(version),'recopy_version_sha256':sha(recopy_version),'version_lengths':[len(version),len(recopy_version)],
    'candidate_recopy_byte_equal':True,'version_recopy_byte_equal':True,
    'source_G1_to_recopy_changed_offsets':actual,'candidate_to_recopy_differences':[],
    'geometry_identical':True,'geometry':geometry(after),'member_colors':colors(after),
    'observed_ui':{'original_host_pid':34968,'test_host_pid':17188,
        'test_window_before':'Blank Type31 in a separately launched instance',
        'actual_paste_count':1,'selected_top_level_group_count':1,
        'visible_shapes':'Two separated rectangles, small blue and large green; no extra shape observed',
        'group_width_height_mm_rounded':[416.124,104.092],
        'group_center_mm_rounded':[368.728,349.039],
        'import_or_confirmation_dialogs_after_paste':0,'warning_or_error_observed':False,
        'evidence':['test-empty.png','after-single-paste.png','restored-colors-visible.png']},
    'normalization_observation':'No byte normalization observed in this recopy. Not a general guarantee.',
    'member_serialize_boundary':'UNKNOWN','general_member_ownership':'NOT_ESTABLISHED',
    'original_document':'No document command, save, close, discard or selection edits sent to original host',
    'runtime_approval':'Explicit user approval before execution',
    'final_clipboard':'Copy of the restored patched group; exact candidate bytes',
    'mode':'OFF','programs':'Both hosts left running; documents unsaved'}
(root/'runtime-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(result['verdict'])
print('One Paste; group=1; R1 Navy Blue / R2 Army Green; exact Zone+Version recopy; geometry unchanged.')
