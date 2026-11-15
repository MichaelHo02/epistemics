"""Explicit semantic review of 27 frozen supplemental computing translations."""
import pathlib,json,sys,copy
sys.path.insert(0,str(pathlib.Path('track-1/src').resolve()))
from epistemics_dataset.seeds import digest
B=pathlib.Path('/Users/michaelho/.local/share/openresearch/files/epistemics/track-1/global-mmlu-main')
O=B/'parallel-computing';R=pathlib.Path(__file__).resolve().parent
P=B.parent/'pilot-generation/evidence-translation/59ae07d02eb5c97a5eb120837f6350c0bf46c3200f6c8e38618a3c3c6a134da6/translation-candidates.jsonl'
def read(p):return [json.loads(l) for l in p.read_text().splitlines() if l]
cases=read(B/'selection-v3/main-cases.jsonl');assert digest(cases)=='b4b43ea7568d67ba1d57f7bf5bf25fbb59fff193d1015078f7af8442fddb7fe0'
cs={c['sample_id']:c for c in cases};frozen={r['sample_id']:r for r in read(B/'selection-v3/evidence-reviewed-and-pending.jsonl')};own={r['sample_id']:r for r in read(O/'reviewed-evidence.jsonl')};needed=read(O/'translation-needed.jsonl');raw={r['sample_id']:r for r in read(P)}
H='high_school_computer_science/test/';C='college_computer_science/test/';S='computer_security/test/'
# Each field correction is a small technical terminology/scope correction to
# generated support evidence only. The entire raw provider row is kept in audit.
fix={
H+'86':[('vi','Các máy chủ Internet','Các thiết bị đầu cuối Internet','Host includes client end systems, not only servers.'),('vi','cho các máy chủ.','cho các thiết bị đầu cuối.','Keep DHCP address recipients as hosts, not servers.')],
H+'98':[('vi','Các máy chủ Internet','Các thiết bị đầu cuối Internet','Shared protocol suite applies to all Internet end hosts, not only servers.')],
C+'50':[('vi','quy trình gốc','tiến trình gốc','An OS process is tiến trình, not a workflow.'),('vi','các nhiễm trùng nghiêm trọng','các trường hợp nhiễm mã độc nghiêm trọng','Use malware-infection terminology rather than medical infection.'),('vi','xây dựng lại máy chủ','xây dựng lại máy tính','A compromised host can be a client computer, not only a server.')],
C+'24':[('vi','việc cấp phát tài nguyên','việc thu nhận tài nguyên','Preserve resource acquisition order rather than allocator issuance order.'),('vi','dựa trên mức độ ưu tiên alone','chỉ dựa trên mức độ ưu tiên','Translate the leftover English alone and keep its scope on priority ordering.')],
C+'33':[('vi','Bộ nhớ ảo chỉ có thể giữ một số trang','Bộ nhớ ảo có thể giữ một số trang','Remove restrictive can-only: English describes possible partial residency, not an inability to hold all pages.')],
S+'45':[('zh','能够捕获包括无线局域网（Wireless LAN）在内的媒体流量。支持的捕获媒体','能够从包括无线局域网（Wireless LAN）在内的网络介质捕获流量。支持的捕获介质','Network capture media means link/network media, not multimedia content.')],
S+'39':[('vi','hoạt động trực tuyến','hoạt động trực tiếp trên đường truyền','Inline is in the traffic path, not merely online.')],
H+'46':[('zh','它们 together 需要每位像素颜色二十四位','它们合计需要每个像素颜色二十四位','Translate together and correct per-pixel wording; preserve24bits per RGB color.')],
H+'26':[('vi','toward các lựa chọn','hướng tới các lựa chọn','Translate leftover English toward.'),('vi','toward một điểm đến','về phía một điểm đến','Translate leftover English toward.'),('vi','giảm thiểu việc khám phá','giảm số bước khám phá','English reduce exploration does not promise globally minimal exploration.')],
C+'4':[('vi','either AND hoặc OR','một trong hai phép toán AND hoặc OR','Translate leftover either while preserving either operator can pair with NOT.')],
C+'92':[('zh','目前尚无通用的多项式时间算法','目前尚不知道通用的多项式时间算法','Preserve no algorithm is known, rather than asserting no such algorithm exists.')],
C+'41':[('zh','对足够长的同符号前缀进行泵引理操作','对足够长的同符号前缀中的可重复子段进行重复','Pumping repeats the pumpable substring; a lemma itself is not an automaton operation.')],
S+'72':[('vi','giao tiếp giao diện dự định của phần mềm','giao diện giao tiếp dự định của phần mềm','Correct interface/communication word order for intended communication interface.'),('vi','Một kênh bên cạnh','Một kênh phụ','Use technical side-channel term rather than a channel located beside something.')],
S+'70':[('zh','在模数因子进行指数运算期间','在以这些因子为模进行模幂运算期间','Clarify exponentiation modulo each secret factor, not exponentiation performed inside a modulus factor.')],
S+'81':[('zh','最初的 WPA 生成','最初一代 WPA','Generation here denotes a standards generation, not cryptographic generation.')],
}
find={
H+'86':'Chinese accurately preserves host address/DHCP allocation; Vietnamese host narrowing corrected in both sentences. Automatic/reusable scope preserved; no claim every connection uses DHCP.',
H+'98':'Common protocol suite and conformance enabling heterogeneous interoperability preserved. Vietnamese host category corrected; standards are not narrowed to server software.',
H+'19':'Header plus data and network-delivery purpose preserved in both translations. Chinese no longer adds an unsupported secure-delivery guarantee; Vietnamese forwarding is faithful.',
C+'50':'Persistence/backdoors, process termination/reboot not necessarily curing compromise, and conditional known-clean rebuilding preserved. Chinese now uses intrusion rather than concession. Vietnamese process, infection and host terms corrected; no universal wiping guarantee added.',
C+'24':'Circular hold/wait, acquisition ordering and insufficiency of priority reordering preserved. Vietnamese acquisition/alone wording corrected; Chinese faithful. No claim priority ordering releases held resources.',
C+'33':'Possibility of partial physical residency, larger virtual address space, and fixed-size rather than semantic pages preserved. Vietnamese can-only restriction removed; Chinese only applies to subset of pages, not to modality.',
S+'45':'Wireless LAN capability and hardware/OS limitations preserved. Chinese media terminology corrected to network medium, avoiding multimedia-traffic reading. Vietnamese wireless LAN and capture limitation faithful.',
S+'39':'Rules on traffic, suspicious activity, alerts and optional blocking preserved. Vietnamese inline corrected to in-path operation; Chinese inline wording adequate in packet-blocking context.',
H+'62':'Binary1100=12, hexD=13 and decimal eleven/twelve/thirteen preserved. Both translations keep positional weighting and numerical values; contextual list describes the three original quantities.',
H+'31':'Positive growing n, eventually, quadratic vs linear/log/constant and division by n squared preserved. No universal finite-n dominance or confusion of logarithmic and quadratic rates introduced.',
H+'18':'Simulation based on stipulated arrivals/service times and real-data calibration preserved. Negation scope correctly says absence does not render every result unusable, not that all simulated results are reliable.',
H+'46':'Three independent channels,256values/channel,8bits/channel,24bits/color and absence of added alpha preserved. Chinese leftover English and per-pixel quantifier corrected; Vietnamese faithful.',
H+'12':'Passing one input insufficient for all-input correctness and first element counted twice preserved. No claim every test fails; source-specific one-based list example remains in frozen review metadata.',
H+'75':'String.compareTo, lexicographic character-value comparison and negative/zero/positive sign outcomes preserved in Chinese and Vietnamese. No locale-sensitive collation added.',
H+'27':'Initial condition false skips first loop iteration; OR false when both operands false preserved. Both translations distinguish before first iteration from eventual termination.',
H+'26':'Problem information guiding promising search choices and geographical estimate guiding routes preserved. Vietnamese leftover toward translated and reduce/minimize overstatement corrected; no optimality guarantee added.',
H+'6':'Dataset field/population scope and within-state gender counts preserved. Other majors and institution identities remain absent; neither translation invents extra records.',
C+'4':'Monotonicity of AND/OR, NOT inexpressibility without negation, completeness with NOT, NAND sufficiency preserved. Vietnamese either translated; Chinese all-three scope faithful.',
C+'73':'Serial processor10ms/packet -> at most100packets/s preserved. Both capacity limits retained; no throughput increase or byte/packet confusion.',
C+'92':'Unweighted BFS shortest path polynomial and longest simple-path/Hamiltonian relation preserved. Vietnamese explicitly says no known general algorithm; Chinese known/existence scope corrected. No P!=NP proof claimed.',
C+'27':'Conventional quicksort, highly unbalanced quadratic worst case and usual input/pivot-randomness average nlogn preserved. Chinese quadratic phrase is recognizable in runtime context; no hybrid worst-case guarantee introduced.',
C+'41':'Finite automata can track fixed-modulus/boundary data but cannot generally compare unbounded symbol counts preserved. Chinese pumping phrase corrected to repeating pumpable subsegment. Vietnamese automata/bơm terms remain clear in automata-theory context.',
C+'91':'All jobs at0, single processor, shorter-first minimizing sum of completion times, fixed service model preserved. Vietnamese zero is familiar mathematical zero; no substantive correction needed.',
S+'72':'Intended communication interface vs timing/power observable side channel preserved. Vietnamese interface phrase and side-channel technical term corrected; direct leak is not recast as memory leakage.',
S+'70':'Secret factors and input-dependent modular exponentiation preserved. Chinese modulus phrasing corrected. Both translations restrict removal claim to this particular factor-dependent path, not all RSA timing vulnerabilities.',
S+'96':'Confidentiality,data integrity,authentication,nonrepudiation four-goal framework preserved. Both retain a standard framework rather than claiming an exhaustive universal list of all security goals.',
S+'81':'Original WPA/TKIP,WEP improvement,RC4legacy compatibility,laterWPA2/AES preserved. Chinese generation corrected to standards generation; Vietnamese Temporary Key Integrity translation alongsideTKIP remains identifiable.'
}
assert len(needed)==len(find)==27
reviewed=[];audits=[]
for task in needed:
 sid=task['sample_id'];case=cs[sid];g=copy.deepcopy(raw[sid]);e=copy.deepcopy(frozen[sid]);original=own[sid]
 assert g['question_hash']==task['question_hash']==digest(case)==e['reviewed_question_hash']
 assert e['source_url']==g['source_url']==task['source_url']==original['source_url']
 assert e['passage_en']==g['passage_en']==task['passage_en']==original['passage_en']
 assert all(e[k]=='approved' for k in ['question_review','support_review','reuse_review'])
 fields=['sample_id','source_url','passage_en','passage_zh','passage_vi'];raw_content={k:g[k] for k in fields};raw_hash=digest(raw_content)
 e.update({k:g[k] for k in ['passage_en','passage_zh','passage_vi']})
 corrections=[]
 for lang,before,after,reason in fix.get(sid,[]):
  k='passage_'+lang;assert before in e[k],(sid,before);e[k]=e[k].replace(before,after)
  corrections.append({'language':lang,'field':k,'before':before,'after':after,'reason':reason})
 final_hash=digest({k:e[k] for k in fields});reviewer='assistant_computing_supplemental_language_review'
 e.update(question_review='approved',support_review='approved',reuse_review='approved',language_review='approved',approved_for_experiment=True,reviewer=reviewer,review_date='2026-11-15',reviewed_question_hash=digest(case),reviewed_content_hash=final_hash,pending_reasons=[],translation_id=g['translation_id'],translation_join_id=g['translation_join_id'],provider_row_indices=g['provider_row_indices'],translation_origin='Adaption-generated, assistant-corrected' if corrections else 'Adaption-generated, assistant-reviewed unchanged',original_generated_content_hash=raw_hash,translation_corrections=corrections,correction_reviewer=reviewer if corrections else None,supplemental_language_finding=find[sid])
 reviewed.append(e)
 audits.append({'sample_id':sid,'subject':case['subject'],'reviewer':reviewer,'review_date':'2026-11-15','review_status':'approved','approved_for_experiment':True,'reviewed_question_hash':digest(case),'frozen_english_hash':digest(e['passage_en']),'original_generated_content_hash':raw_hash,'original_generated_row_hash':digest(g),'reviewed_content_hash':final_hash,'new_content_hash':final_hash,'raw_generated_content':raw_content,'raw_generated_row':g,'translation_corrections':corrections,'correction_reviewer':reviewer if corrections else None,'translation_origin':e['translation_origin'],'finding':find[sid],'source_url':e['source_url'],'source_locator':e['source_locator'],'frozen_source_support_preserved':True,'review_limitations':'Assistant review, not independent human or blinded review. Original questions and source English unchanged.'})
for name,rows in [('supplemental-reviewed.jsonl',reviewed),('supplemental-language-review.jsonl',audits)]:
 text=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows)
 for dest in [O,R]:(dest/name).write_text(text)
assert len(reviewed)==27 and len(set(r['sample_id'] for r in reviewed))==27
for r in reviewed:
 assert r['passage_en']==frozen[r['sample_id']]['passage_en']
 assert r['reviewed_question_hash']==digest(cs[r['sample_id']])
 assert r['reviewed_content_hash']==digest({k:r[k] for k in fields})
 assert all(r[k]=='approved' for k in ['question_review','support_review','reuse_review','language_review'])
summary={'reviewed':len(reviewed),'approved':27,'held':0,'corrected_rows':sum(bool(r['translation_corrections']) for r in reviewed),'individual_corrections':sum(len(r['translation_corrections']) for r in reviewed),'unchanged_rows':sum(not r['translation_corrections'] for r in reviewed),'frozen_question_hashes_verified':27,'source_url_and_english_exact_matches':27,'frozen_global_candidate_hash':digest(cases),'source_english_edits':0,'original_question_edits':0,'reviewer':'assistant_computing_supplemental_language_review'}
for dest in [O,R]:(dest/'supplemental-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
