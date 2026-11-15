"""Assemble explicitly adjudicated computing reviews. No model/API/compute calls."""
import json, pathlib, sys, re
from collections import Counter
sys.path.insert(0,str(pathlib.Path('track-1/src').resolve()))
from epistemics_dataset.seeds import digest
BASE=pathlib.Path('/Users/michaelho/.local/share/openresearch/files/epistemics/track-1/global-mmlu-main')
OUT=BASE/'parallel-computing'; REVIEW=pathlib.Path(__file__).resolve().parent
SUBJECTS=['high_school_computer_science','college_computer_science','computer_security']
def read(p):return [json.loads(l) for l in pathlib.Path(p).read_text().splitlines() if l]
def write(name,rows): (OUT/name).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows))
main=[c for c in read(BASE/'selection-v2/main-cases.jsonl') if c['subject'] in SUBJECTS]
evidence={r['sample_id']:r for r in read(BASE/'selection-v2/evidence-candidates.jsonl')}
trans={r['sample_id']:r for r in read(BASE.parent/'pilot-generation/evidence-translation/1da2b7dc55e1fce72c2929fee3e6dfa8facffec4e99cb1c21cfc5f2a05d315e5/translation-candidates.jsonl')}
prior={}
for name in ['hs-computing','college-computing','security']:
 for r in json.loads((REVIEW.parent/('material-review-'+name+'-01.json')).read_text())['rows']:prior[r['sample_id']]=r
reserves=[r for r in read(BASE/'replacement-review-v1/reserve-cases.jsonl') if r['case']['subject'] in SUBJECTS]
olddec={r['sample_id']:r for r in json.loads((REVIEW.parent/'reserve-decisions-01.json').read_text())['decisions']}
access=json.loads((OUT/'source-access.json').read_text())+json.loads((OUT/'source-access-supplement.json').read_text())
access={r['url']:r for r in access}
AP='https://apcentral.collegeboard.org/media/pdf/ap-computer-science-principles-exam-reference-sheet.pdf'
TOR='https://support.torproject.org/about-tor/onion-services/what-is-a-dot-onion/'
access[AP]={'url':AP,'status':'read_via_web_reader','source_locator':'PDF pages 2-5: assignment/DISPLAY, iteration and one-based list indexing; web reader accessed 2026-11-15'}
access[TOR]={'url':TOR,'status':'read_via_web_reader','source_locator':'Understanding .onion addresses, body lines 51-59; web reader accessed 2026-11-15'}
# Explicit source locators and case-specific reasoning. A regexp only locates a
# passage already read; matching is never the decision rule for approval.
loc={
'high_school_computer_science':{
61:('robustness against failure','RFC1122 section1.1.2: robustness despite failed networks/gateways, using remaining bandwidth. Alternative paths are conditional on remaining connectivity, not a guarantee after every failure.'),
84:('uses numerous hosts','NIST definition explicitly says numerous hosts perform the attack; this uniquely distinguishes attacking sources from targets.'),
63:('compilation proper','GCC Overall Options opening four-stage pipeline. Translation is the offered compiler role; assembly/linking details do not make testing/versioning correct.'),
95:('', 'AP reference PDF page2 assignment and DISPLAY; trace r=1,s=2,t=3; after r<-s and s<-t, display2,3.'),
86:('automatic allocation of reusable','RFC2131 abstract and section1: DHCP supplies network addresses to hosts. Automatic DHCP is one example; static/other configuration remains possible.'),
38:('hex \\(', 'Python hex definition; positional calculation231=14*16+7, so E7.'),
76:('', 'AP PDF page4 iteration: n0-2k preserves parity; least k with n<=0 yields0 for even n and -1 for odd n, so C.'),
15:('str. isupper','Python exact cased-character requirement read. Retain educational shorthand all characters as all characters with a case; no concrete input tests uncased characters. Method uniquely fits among join/len/ljust. Do not restate a universal all-character rule.'),
98:('arbitrary host interoperation','RFC1122 introduction requires general host interoperation across heterogeneous Internet systems. Shared protocol implementation, not manufacturer, enables this.'),
93:('ZeroDivisionError','Python tutorial8.2 explicitly shows runtime zero division. Retain conventional runtime-input arithmetic model; division by variable N is detected upon execution, not simply N entry. This is not a universal promise about every compiler/language.'),
4:('running time|running times|time complexity|asymptotic','MIT recitation sorting analysis is background. Own counterexample: fixed-size nested loop source can do n^2 operations; source-statement count alone does not bound time/memory/storage growth. LEAST qualifier avoids saying code size never matters.'),
3:('255|invert','Pillow inversion rule; independent algebra255-(255-x)=x for each channel, unlike many-to-one averaging or overwritten image regions.'),
77:('static modifier','Oracle class variables section: shared ID allocator belongs to class; each insect keeps its own age,idNum,position.'),
8:('compilation proper','GCC four-stage source-to-executable pipeline. Human readability is a conventional high-level representation comparison; no universal empirical readability claim.'),
87:('15.24. Conditional-Or Operator \\|\\| The','JLS15.24 truth/short-circuit semantics: a<c makes left operand true and guarantees whole OR true. Other alternatives fail for suitable choices of remaining integer.'),
60:('max \\(', 'Python max definition; max([1,2,3,4])=4.'),
34:('testing by sampling','Dijkstra EWD249 surrounding sampling discussion: untested cases can fail. A passing finite suite cannot justify all pre/postconditions or unrestricted reuse.'),
2:('reassembly|reassembled','RFC1122 transport/IP overview and reassembly requirements. Packets/segments reconstructed by receiving protocols; browser does not request sequential individual packets.'),
19:('IP header','RFC1122 IP header/source/destination discussion; routing metadata accompanies data. Header is not an encryption guarantee; translated safety addition must be removed.'),
92:('slice of s from i to j with step k','Python common sequence operations and notes: positive step2 omitted start begins at0, selecting indexes0,2,4 =>[11,15,19].'),
48:('repeatedly dividing the search interval in half','NIST binary-search definition. On random-access sorted sequence halving gives logarithmic comparisons vs up to n for scan; not fewer on every individual input.')},
'college_computer_science':{
53:('Merge sort|merge sort','MIT recitation3 merge-sort section: linear merge at log n levels. Conventional quicksort comparison, excluding modern hybrid introsort.'),
8:('representation error|rounding errors|rounding error','Chinese 关联 is nonstandard for associativity but its repeated arithmetic/rounding contrast corresponds to the same property; Vietnamese uses tính kết hợp. Retain with terminology limitation. Binary-double counterexample (1e16-1e16)+1=1 vs1e16+(-1e16+1)=0; ordinary finite precision cannot restore associativity by roundoff conventions.'),
55:('A new frame is created','JVM is execution-context background only. Own dependence proof: S1 first; S2,S3,S4 second; S5,S6 third. S1->S2->S5 gives lower bound3. Reads at step start/writes at end; initial F nonzero and arithmetic defined. S4 reads old F before S6 overwrite. This is a formal derivation, not an Oracle scheduling theorem.'),
50:('rebuilding compromised hosts','NIST800-83r1 recovery/rebuilding and attacker-tool backdoors. Often rebuild for administrator compromise; no universal assertion disk wipe fixes firmware or stolen credentials.'),
93:('Conflict misses','Cornell cache notes conflict-miss definition and one-location direct mapping. Alternating distinct same-slot blocks evicts each other.'),
34:('uses a stack','OSTEP13 address-space components: stack stores call/local state; heap separate. Heap pointer inside frame is not heap region itself.'),
1:('divisor|greatest common divisor','DLMF27.2 is number-theory background; independent example x=y=6 gives exact signed divisor set C; if6 divides x,y then3 does too. Zero never divides a nonzero number. (0,0) has infinitely many divisors under divisibility definition, so no finite option containing0 fits.'),
5:('binomial|Binomial','DLMF26.3 binomial coefficient background only. Own proof: forest gives10-6=4components; K4 plus6isolates gives7. With8components at most3edges can be packed on10vertices, so7max.'),
24:('Circular wait','OSTEP32 necessary conditions and total ordering. Priority queue alone does not release held resources. Random restart alternative assumes resources released upon restart; otherwise the conventional recovery reading would not hold.'),
63:('A new frame is created','JVM2.6 new frame per invocation. Recursive active calls need distinct state; one static frame per procedure insufficient. Alternative heap continuations are outside supplied stack-vs-static model.'),
51:('Each bit directly controls','Course author COA teaching slides microinstruction-format slide140: direct horizontal control signals, encoded vertical fields. This educational convention supports II alone; horizontal parallelism opposes I; single opcode is not horizontal control format.'),
46:('0.1','Python floating-point representation background. Own positional proof: finite binary rational m/2^k; reduced denominators10,5,10 include5, but1/2 terminates. Exact means finite representation in this finite-machine context.'),
64:('grammar|production','Python expression grammar is notation background only. Own expansion: B=x+, C=x+|y|zy; A=x^{>=2}|x+y|x+zy. xyz impossible; xy,xxzy,xxxxy have direct derivations. Existing evidence states necessary string classes, not that every only-x string is generated.'),
39:('memory mapped|memory-mapped','Linux device-I/O documentation memory-mapped register access vs port I/O. Ordinary address/load-store model; access ordering may differ from RAM.'),
16:('polling seems','OSTEP36 canonical protocol and interrupts discussion: polling wastes CPU when another ready task could run; short wait or no work can favor it.'),
61:('These variables form the root set','Wilson GC survey section2: active globals, stack locals, registers are roots and traversal discovers reachable heap. Whole heap cannot be roots or no garbage would be reclaimed.'),
33:('even bigger.*than physical|bigger.*physical|physical memory itself','OSTEP21 swap-space example supports partial residency and virtual size>physical. Additional OSTEP18 introduction states paging uses fixed-size pages, unlike segmentation; auxiliary source cited in source record.'),
69:('MAP_SHARED','mmap man page MAP_SHARED vs MAP_PRIVATE: shared writes visible, COW private not. Own offset0x77E81234-0x77E80000=0x1234; debugger address0x01001234, shared READ/WRITE needed.'),
62:('Converting Protocol Addresses','RFC826 title/purpose and Ethernet address mapping protocol. IP->hardware, not DNS names.'),
49:('Integer Overflow','CWE190 background for representable bounds. Own signed-magnitude/ones-complement8bit bounds[-127,127], twos[-128,127];109-42=67 inside all.'),
72:('Integer Overflow','CWE190 background. Independent two-complement decoding options sums0,-127,-128,-213; only D outside[-128,127].'),
28:('avoids rebuild cascades','Microsoft pimpl article public pointer to hidden implementation avoids client rebuilds and extra indirection. Conventional representation comparison, with private implementation changes not changing public interface; optimizer may remove some access cost.'),
30:('interrupt','OSTEP36 interrupt-driven completion: hardware can notify OS of completion. Can does not require an interrupt per I/O.'),
90:('write-through','Cornell cache notes write-through immediately propagates every store.256*4=1024data bytes; block-fill reads/metadata excluded.')},
'computer_security':{
56:('proof|origin','NIST non-repudiation definitions provide verified origin evidence; sender cannot successfully deny subject to cryptographic/procedural assumptions.'),
24:('overwhelmingly','Christin2013 original Silk Road measurement paper abstract and introduction identify anonymous Tor marketplace dominated by controlled substances; historical identification only.'),
80:('data holding area','NIST overflow definition identifies buffer as data-holding area. Conventional sequential memory region, not universal physical contiguity of every abstract buffer.'),
7:('The original Freenet','Original project site explicitly identifies original Freenet as Hyphanet and decentralized media/file sharing; distinguish newer Freenet project.'),
64:('previously captured messages','NIST replay definition captured legitimate message reuse; successful acceptance is attack goal, not guarantee all replays succeed.'),
3:('authorized restrictions','NIST confidentiality authorizes parties. Direct three-language inspection: receiver vs sender retained; Modulor undefined English distractor becomes module/modulator, translator becomes converter. Both latter roles remain nonrecipient operations/devices and introduce no authorized recipient alternative. Lexical limitation does not change unique receiver completion in message-delivery context; sender can naturally know original message.'),
32:('forwards the remote client','OKWS sections4.1/4.2 and runtime UID table: okd forwards accepted client descriptors to separately running services, uses nonroot UID, inherits channels. Without descriptor passing that existing connection-transfer path fails; privileged parent can preopen listening socket before exec so nonroot operation remains possible. Counterfactual about given design, not all possible relaying redesigns.'),
67:('test methodology|method of testing','NIST penetration-testing definition is background. Own comparison: specific controlled exploit can be repeated under same preconditions; clean tests do not prove full/compositional security, and neural-network convergence unrelated. Often reproducible is qualitative, not an empirical rate claimed from glossary.'),
83:('ease the setup','CERTVU723755 description defines WPS as simplifying setup/securing home wireless network. Few years back retained as undated historical phrasing, not2026date claim.'),
71:('improper information modification','NIST integrity definition guards against alteration/destruction; exact-as-sent concerns integrity, not confidentiality.'),
86:('A new frame is created','JVM2.6 background plus conventional stack-address derivation: different invocation nesting places frame at runtime-dependent location. Does not say compiler never knows any optimized local address.'),
61:('modification detection codes|modification detection code','HAC9.2 classification of unkeyed MDC vs keyed MAC; a compact hash digest needs additional trust/authentication to protect against adversarial replacement.'),
12:('Forward secrecy after key change','RFC8446E.1 key secrecy discussion. Standard key-compromise interpretation with erased old secrets, not protection for retained plaintext histories on compromised computer.'),
21:('RSA blinding operation','Brumley/Boneh section defenses: random r makes decrypted ciphertext random, fresh each operation. This is input randomization, not prime change or arbitrary delay.'),
69:('ci = mi','HAC6 one-time-pad equations ci=mi XORki. Own cancellation m XORc=m XOR(m XORk)=k, at known positions; ciphertext-only perfect secrecy unaffected.'),
27:('verify|verification','NIST public-key definition/signature verification. Vietnamese mã riêng/công khai is nonstandard code-for-key terminology, but all four sender/receiver x private/public combinations preserve unique signer-public verification contrast. Retain with limitation; evidence uses correct khóa.'),
45:('Wireless LAN','Wireshark manual1.1.3 specifically lists Wireless LAN. Existing generic passage omits decisive wireless capability; edit English and retranslate rather than approve weak evidence.'),
2:('KRB_AP_ERR_TKT_EXPIRED','RFC4120 section3.2.3: server compares endtime/current local time with permitted skew. Rejects new expired authentication, not necessarily terminates established app sessions;24h is given scenario policy.'),
57:('upper layer-functionality','NIST application-proxy gateway definition intermediary with upper-layer functionality. Application among offered layers, even though also lower-layer controls.'),
77:('more input can be placed','NIST overflow capacity violation and code-control consequence. Extra malicious-data wording awkward but identifies overflow uniquely among alternatives; no claim every overflow executes instructions.'),
60:('gain control of the system','NIST control-corruption background. Own classic-stack model: saved return address determines return target; overwrite with code address redirects control. Assumes unprotected executable-stack setting, no assertion bypassing modern defenses.'),
39:('deployed inline','Snort official what-is section rules/alerts/inline blocking. Vietnamese online for inline loses in-path distinction, pending translation correction.'),
38:('Message Authentication Codes|message authentication code','HAC9 MAC background. Own counting proof32possible tags; uniform guess hits any correct5bit tag with probability>=1/32, fixed nonnegligible constant.'),
9:('Previous versions of TLS offered explicitly','RFC8446C.5 unauthenticated key exchange vulnerable to active MITM; own DH substitution explanation, authenticated keys required.'),
25:('', 'Tor official body: onion services only accessible through Tor network. Dark web is ordinary special-access hidden-service category, not all deep-web/nonindexed content; unknown is loose prose, not an empirical universal.'),
31:('WPA3™ offers','Wi-Fi Alliance security section WPA3 stronger authentication/cryptographic strength and legacy protocol exclusion. Among listed generations under comparable implementations, not unconditional comparison of every deployment.')}
}
# Holds stay excluded; no original strings are repaired.
holds={'high_school_computer_science':[67,54,28,22,94,53,70,58,97],'college_computer_science':[82,6,81,83,2,57],'computer_security':[1,66,46,54]}
exclusions=[]
for c in main:
 if int(c['sample_id'].split('/')[-1]) in holds[c['subject']]:exclusions.append({'sample_id':c['sample_id'],'subject':c['subject'],'reviewed_question_hash':digest(c),'decision':'exclude_published_question','reason':prior[c['sample_id']]['finding'],'source_url':evidence[c['sample_id']]['source_url'],'approved_for_experiment':False,'model_outcomes_seen':False})
selected=[c for c in main if c['sample_id'] not in {r['sample_id'] for r in exclusions}]
new={}
def add(subject,n,url,en,note,pat):new[f'{subject}/test/{n}']={'source_url':url,'passage_en':en,'review_note':note,'pattern':pat}
H='high_school_computer_science';C='college_computer_science';S='computer_security'
add(H,62,'https://docs.python.org/3.9/library/functions.html#hex','Positional notation weights successive digits by powers of its base. Binary 1100 is twelve in decimal; hexadecimal D is thirteen, so the decimal values are eleven, twelve, and thirteen.','Direct en/zh/vi review: all bases, digits, order instruction and choices preserved. Own calculation1*8+1*4=12;D=13;11<12<13. Python hex is background, not a worked solution.','hex \\(')
add(H,31,'https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/1869dbf640ded6b31f1bd369d2001ef5_MIT6_006S20_r03.pdf','For increasing positive n, quadratic growth eventually exceeds linear, logarithmic, and constant growth. The respective growth rates can be compared by dividing each slower rate by n squared.','All symbolic alternatives identical across languages. Conventional educational shorthand compares representative asymptotic growth classes, not claims a particular big-O bound is a tight cost. Ratios1/n^2,1/n,log(n)/n^2 tend to0.','log n')
add(H,18,'https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-sched.pdf','A simulation can compare waiting-line policies using stated assumptions about arrivals and service times. Real customer records can improve calibration, but their absence does not make every simulation result unusable.','All alternatives and NOT preserved. Own constructive example: stipulated arrivals0,0, service times1,2 produce computable waits for one or two tellers; changing teller count/policy yields valid conditional results without observed bank records. OSTEP scheduling/turnaround is background, not validation of any particular real-bank prediction.','turnaround')
add(H,46,'https://www.w3.org/TR/PNG/','Three independent color channels with 256 possible values each require eight bits per channel in a direct representation. Together they require twenty-four bits per pixel color, without an additional alpha channel.','All numeric inputs/options preserved. Own count256^3=2^24; direct full RGB color representation, not file compression or memory alignment. PNG truecolor channel specification is background.','Truecolour|truecolor|truecolour')
add(H,12,AP,'A test that passes on one input need not establish correctness for every input. Initializing a sum to the first list element before adding every list element counts that first element twice.','All pseudocode identifiers/operations/options match; CRLF harmless. AP one-based indexing: initial first element0 masks bug for[0,1,4,5]. Counterexample[1,2] produces4 instead of3. Assume FOR EACH body is sum update, DISPLAY after loop as intended plain-text layout.','')
add(H,75,'https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/String.html','Java String.compareTo compares strings lexicographically using character values. Its result is negative, zero, or positive according to the relative order of the two strings.','All code strings and comparisons identical en/zh/vi. CARROT<Carrot at second char A<a; Carrot<car at first char C<c. Hence strB<strC and strB>strA.','lexicographically')
add(H,27,'https://docs.oracle.com/javase/specs/jls/se25/html/jls-15.html#jls-15.24','A while-loop body is skipped when its condition is false before the first iteration. An OR condition is false when both of its operands are false.','Vietnamese translates while keyword as trong khi but preserves all identifiers, operators, condition and options; recognizable control-flow pseudocode rather than mismatched executable identifiers. num1<num2 and num1<num3 makes both > tests false; only D sufficient. No code execution/compilation is asked.','15.24. Conditional-Or Operator \\|\\| The')
add(H,26,'https://xlinux.nist.gov/dads/HTML/heuristic.html','A heuristic uses information about a problem to guide a search toward promising choices. Geographical estimates can guide a route search toward a destination and reduce exploration.','en/zh/vi preserve all four tasks. Grade formula, encryption, ordinary sorting have direct standard computations; among offered tasks route search most naturally benefits from location-based search guidance. This does not claim shortest path is NP-hard or heuristics always improve runtime.','heuristic')
add(H,6,'https://docs.python.org/3.9/library/stdtypes.html#common-sequence-operations','A data set can answer questions based on the fields and population it contains. Grouping computer-science students by state and gender permits within-state counts and comparisons; it does not supply other majors or college identities.','All three fields and alternatives preserved. Own identifiability proof: count female/male per state and compare; other-major grades, all-student denominators and college identifiers absent. Python data aggregation is only background; exact proof uses given fields, not demographic claims.','s.count')
add(C,4,AP,'AND and OR preserve monotonicity, so expressions built from them alone cannot express NOT. Adding NOT to either AND or OR is functionally complete, and NAND alone can express all three operations.','All logical operator sets and NOT target identical. Formal constructions via De Morgan; NOTp=p NANDp and ANDp,q=(p NANDq)NAND(p NANDq). AP Boolean truth semantics are background only; completeness proven independently by disjunctive normal form and these constructions.','')
add(C,73,'https://www.rfc-editor.org/rfc/rfc1122.html','When a serial sending processor spends ten milliseconds processing each packet, it can process at most one hundred packets per second. The achievable rate is bounded by both processor service capacity and network capacity.','All counts/units/options preserved. Own resource bound min(1/.010,1000)*1000=100000bytes/s. Conventional single serial sender CPU, no unspecified parallel offload. RFC networking is background only.','Efficient use')
add(C,92,'https://vjs.ac.vn/jcc/article/download/12935/382910/389571','In an unweighted graph, breadth-first search finds a shortest path in polynomial time. A general longest simple path includes the Hamiltonian-path problem, and no general polynomial-time algorithm is known.','All graph premises, shortest/longest, simple, known-vs-unknown alternatives preserved. Own reduction: add designated endpoints linked to all original vertices; a simple path visiting original vertices all once witnesses Hamiltonian path. Assumes ordinary unweighted graph as given, not negative weighted cycles.','NP-hard|NP hard')
add(C,27,'https://xlinux.nist.gov/dads/HTML/quicksort.html','Conventional quicksort has quadratic worst-case running time when partitions are highly unbalanced. Its average running time is proportional to n log n under the usual input or pivot-randomness model.','All theta expressions/options unchanged en/zh/vi. Worst recurrenceT(n)=T(n-1)+Theta(n); balanced/expected split yieldsTheta(nlogn). Not an introsort hybrid.','quadratic|worst|average')
add(C,41,'https://sites.radford.edu/~itec420/2019fall-nokie/pumpRegular.html','Finite automata can track a count modulo a fixed integer or remember fixed boundary conditions. They cannot in general compare two unbounded symbol counts; pumping a sufficiently long same-symbol prefix defeats such a comparison.','All count/boundary conditions and CANNOT preserved. Own pumping proof for more1than0: take0^p1^(p+1); any pumpable nonempty segment inside first p zeros can be repeated until zeros>=ones. Other options regular: track zeros modulo5, initial0/final1, or modulo2. Formal regular expressions, not extended regex backreferences.','pumping|Pumping')
add(C,91,'https://pages.cs.wisc.edu/~remzi/OSTEP/cpu-sched.pdf','When all jobs are available at time zero on a single processor, executing shorter jobs before longer ones minimizes the sum of completion times in the usual fixed-service-time model.','All service times,time0,mean and alternatives preserved. Adjacent-swap argument: exchanging inverted lengths a>b lowers sum by a-b. Order2,3,5,15,25 completes at2,5,10,25,50;total92,mean92/5. No setup costs or release constraints given.','Shortest Job First')
add(S,72,'https://crypto.stanford.edu/~dabo/papers/ssl-timing.pdf','A direct disclosure uses the software’s intended communication interface. A side channel instead reveals information through other observable features of computation, such as timing or power consumption.','Vietnamese leak=lỗ hổng is loose, but keyed definition explicitly preserves intended interface vs timing/power/space observations, and distractors still distinguish memory leak/intention/no difference. No valid alternative introduced. Original paper section1 classifies timing/power/electromagnetic side channels; direct-interface contrast independently reasoned.','side-channel attacks')
add(S,70,'https://crypto.stanford.edu/~dabo/papers/ssl-timing.pdf','The described RSA timing attack extracts secret factors through input-dependent behavior during exponentiation modulo those factors. Removing Chinese-remainder exponentiation removes that particular factor-dependent attack path.','All four optimization names and two propositions preserved. Original paper sections2.1-3 uses CRT exponentiations modp/modq. Disabling CR removes the stated channel in both1and2, so True,True. This is case-specific reasoning, not proof non-CRT RSA is immune to all timing attacks; original Kocher attack may apply elsewhere.','with CRT uses the factors')
add(S,96,'https://cacr.uwaterloo.ca/hac/about/chap1.pdf','A standard cryptographic framework groups confidentiality, data integrity, authentication, and non-repudiation as four central goals for protecting information and messages.','All four lists preserve meanings across en/zh/vi. HAC1.2 explicitly selects these four as its framework. Retain ordinary cryptographic-message classification, not a universal claim availability/access control are unimportant security properties.','following four form')
add(S,81,'https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-48r1.pdf','The original WPA generation used the Temporal Key Integrity Protocol, TKIP, to improve on WEP while retaining RC4-based compatibility with legacy equipment. Later WPA2 introduced AES-based protection.','All choices and WPA target preserved; Vietnamese shared-key distractor Chìa khóa chung uses physical-key word but remains shared vs named protocols, no valid alternative. Conventional WPA means original WPA1, as distinguished from WPA2/AES. NIST800-48r1 section6.3.1.','TKIP and MIC')
# Fixed-order reserve decisions, including all previous excludes.
skips={H:{32:'Vietnamese keyed aab becomes abb, changing literal concatenation result.',33:'Vietnamese translates input Chemistry to Hóa học but keyed result Hoá học differs as a literal string; also a becomes Một.',36:'Python3 print tuple[0] lacks required print parentheses and raises SyntaxError, contradicting key B; Vietnamese also changes abcd to A B C D.',37:'Published stem references upgraded system without providing its description; cannot derive benefit comparison.'},C:{35:'Vietnamese drops circuit from circuit switching; general switching is true for many Ethernet networks. Original bus/collision model also needs legacy assumption.',37:'Vietnamese computationally intractable distractor becomes not computable, changing mathematical meaning.',38:'English Enigma transposition distractor becomes Chinese shift cipher; different historical cipher classification, do not repair distractors.',39:'Vietnamese NOT sign becomes euro symbol and even-number-of-true becomes even-numbered variables; Chinese omits exactly in II.'},S:{46:'A identify live systems and B locate live systems are substantively duplicate correct purposes of ping sweep; key not unique.'}}
maxrank={H:44,C:40,S:49}
decisions=[]
selected_ids={c['sample_id'] for c in selected}
for r in reserves:
 c=r['case'];s=c['subject'];sid=c['sample_id'];rank=r['rank_within_subject']
 if rank>maxrank[s]:continue
 if sid in olddec:
  d=dict(olddec[sid]);d['prior_decision_preserved']=True
  # A prior reserve may now be excluded by direct multilingual review.
  if sid in {e['sample_id'] for e in exclusions}:d['current_selection_decision']='exclude_after_direct_multilingual_review';d['current_reason']=prior[sid]['finding']
  else:d['current_selection_decision']='already_selected' if sid in selected_ids else 'prior_exclusion_preserved'
 elif sid in new:
  d={'sample_id':sid,'rank_within_subject':rank,'decision':'retain_candidate','reason':new[sid]['review_note'],'current_selection_decision':'new_replacement'};selected.append(c);selected_ids.add(sid)
 else:
  assert rank in skips[s],(s,rank,sid)
  d={'sample_id':sid,'rank_within_subject':rank,'decision':'exclude_candidate','reason':skips[s][rank],'current_selection_decision':'exclude'}
 d.update(subject=s,model_outcomes_seen=False,approved_for_experiment=False);decisions.append(d)
assert Counter(c['subject'] for c in selected)==Counter({s:30 for s in SUBJECTS}),Counter(c['subject'] for c in selected)
# Evidence edits requiring approved supplementary translations, never invented here.
edits={
f'{S}/test/45':('Wireshark is a network packet analyzer that can capture traffic from media including Wireless LAN. Supported capture media depend on the hardware and operating system.','Existing English lacks the decisive wireless capability; official manual1.1.3 explicitly supplies it.')}
translation_defects={sid:r['finding'] for sid,r in prior.items() if r['evidence_language_review']=='edit_required'}
# Extra non-source assumptions are recorded explicitly above rather than changing originals.
rows=[];reviews=[];need=[];approved=[];source_records=[]
for c in selected:
 sid=c['sample_id'];s=c['subject'];n=int(sid.split('/')[-1]);isnew=sid in new
 if isnew:
  v=new[sid];e={'sample_id':sid,'subject':s,'question':c['languages']['en']['question'],'answer_code':c['answer'],'answer_text':c['languages']['en']['option_'+c['answer'].lower()],'source_url':v['source_url'],'passage_en':v['passage_en'],'passage_zh':None,'passage_vi':None,'passage_kind':'researcher_paraphrase_or_formal_derivation','review_note':v['review_note']};pattern=v['pattern'];reason=v['review_note']
 else:
  e=dict(evidence[sid]);pattern,reason=loc[s][n];t=trans[sid]
  assert t['question_hash']==digest(c),(sid,'translation question mismatch')
  assert t['source_url']==e['source_url'] and t['passage_en']==e['passage_en'],(sid,'translation source/content mismatch')
  e.update(passage_zh=t['passage_zh'],passage_vi=t['passage_vi'],translation_id=t['translation_id'])
 if sid in edits:
  e['passage_en'],editwhy=edits[sid];e.update(passage_zh=None,passage_vi=None)
 a=access[e['source_url']];assert a['status']!='failed',(sid,e['source_url'])
 locator=a.get('source_locator','')
 if 'text_file' in a:
  text=(OUT/a['text_file']).read_text();m=re.search(pattern,text,re.I) if pattern else None
  if not m:raise ValueError(('locator did not match; do not auto-approve',sid,pattern))
  # Exact offsets are reproducible locators, not copyright-heavy saved quotations.
  locator=f"{a['text_file']}, character {m.start()}; "+reason.split('.')[0]
 sr={'sample_id':sid,'source_url':e['source_url'],'source_locator':locator,'access_status':'matched_passage_read_and_case_adjudicated','source_role':'See per-family adjudication: direct definition or explicit formal derivation with background citation','adjudication':reason}
 if sid==f'{C}/test/33':sr['additional_source_url']='https://pages.cs.wisc.edu/~remzi/OSTEP/vm-paging.pdf';sr['additional_locator']='Chapter18 opening: fixed-size pages vs variable-size segmentation'
 source_records.append(sr)
 pending=[]
 if isnew:pending.append('New English evidence has no existing source/question/content-bound provider translations; supplemental translation and review required.')
 if sid in translation_defects:pending.append(translation_defects[sid])
 if sid in edits:pending.append(edits[sid][1]+' English changed; supplemental translation required.')
 ok=not pending
 e.update(question_review='approved',support_review='approved',reuse_review='approved',language_review='approved' if ok else 'pending',approved_for_experiment=ok,reviewer='assistant_computing_final_material_review',review_date='2026-11-15',source_access='read_online_or_formal_derivation_with_read_background',source_locator=locator,reviewed_question_hash=digest(c),review_note=(e.get('review_note','')+' '+reason).strip(),pending_reasons=pending)
 content={k:e.get(k) for k in ('sample_id','source_url','passage_en','passage_zh','passage_vi')};e['reviewed_content_hash']=digest(content)
 rows.append(e)
 fr={'sample_id':sid,'subject':s,'reviewed_question_hash':digest(c),'reviewed_content_hash':e['reviewed_content_hash'],'reviewer':e['reviewer'],'question_review':'approved','support_review':'approved','reuse_review':'approved','language_review':e['language_review'],'approved_for_experiment':ok,'source_url':e['source_url'],'source_locator':locator,'case_adjudication':reason,'translation_review': 'Existing en/zh/vi evidence directly compared; meanings preserved with recorded conventional qualifications.' if ok else pending,'prior_multilingual_finding':prior.get(sid,{}).get('finding'),'review_limitations':['Assistant review; not independent human or blinded review.','Source presence and aligned keys were not used as automatic approval.']}
 reviews.append(fr)
 if ok:approved.append(e)
 else:need.append({'sample_id':sid,'subject':s,'question_hash':digest(c),'source_url':e['source_url'],'passage_en':e['passage_en'],'translation_reason':pending,'approved_for_experiment':False,'passage_zh':None,'passage_vi':None,'instruction':'Translate exact English passage; preserve technical meaning. Bind to exact question hash and source URL; review output before approval.'})
write('proposed-cases.jsonl',selected);write('reviewed-evidence.jsonl',rows);write('approved-trilingual-evidence.jsonl',approved);write('translation-needed.jsonl',need);write('family-review.jsonl',reviews);write('question-exclusions.jsonl',exclusions);write('reserve-decisions.jsonl',decisions);write('source-adjudications.jsonl',source_records)
summary={'status':'90_proposed_cases_not_all_materials_ready','counts':dict(Counter(c['subject'] for c in selected)),'replacements':len(new),'excluded_current_questions':len(exclusions),'approved_trilingual_evidence':len(approved),'translation_needed':len(need),'pending_source_support':0,'question_strings_modified':0,'model_calls':0,'reserve_prefix_last_rank':maxrank,'remaining_shortage':0,'reviewer':'assistant_computing_final_material_review','review_limitations':'Assistant review, not independent human or blinded review. Pending translated evidence blocks final use of affected rows.'}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(REVIEW/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
