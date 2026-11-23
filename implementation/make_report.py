#!/usr/bin/env python3
"""Build user-facing tables and a paper draft only from recorded experiment data."""
from pathlib import Path
import csv,json,xml.etree.ElementTree as E
BASE=Path(__file__).resolve().parents[1];HERE=BASE/'implementation';OUT=HERE/'results'
r=json.loads((OUT/'implementation_results.json').read_text())
native=json.loads((HERE/'model_mutants/native_mutation_summary.json').read_text())
assert len(native['mutants'])==6 and all(x['static_errors']==0 and x['total_open']>0 for x in native['mutants'])
# Use distinct project names for intentionally unsafe negative controls.
for row in native['mutants']:
 p=HERE/'model_mutants'/row['mutant']/'DelegatedAuthorization/.project'
 tree=E.parse(p);tree.getroot().find('name').text='Negative_'+row['mutant'];E.indent(tree);tree.write(p,encoding='UTF-8',xml_declaration=True)
node=['u','a1','a2','a3'];job=['req1','req2','req3'];caps={1:'readCap',2:'writeCap'}
def setexpr(values):return '{'+', '.join(values)+'}' if values else '∅'
def capexpr(mask):return setexpr([name for bit,name in caps.items() if bit&mask])
witnesses=[]
for row in r['implementation_mutants']:
 before=dict(scopes=[3,0,0,0],revoked=[False]*4,phases=[0]*3,pending=[],used=0,effects=[0]*3,auth=[3,0,0,0]);steps=[]
 for step in row['trace']:
  op,*args=step['command'];bindings={};label=op;after=step['actual']
  if op=='Delegate':bindings.update(a=node[args[0]],S=capexpr(args[1]))
  if op=='Revoke':bindings['a']=node[args[0]]
  if op in ('Delegate','Revoke'):
   bindings['P']=setexpr([node[a]+' ↦ '+name for a,mask in enumerate(after['auth']) for bit,name in caps.items() if mask&bit])
  if op in ('Reserve','Submit','Commit','CancelConfirmed','ReleaseUnconfirmed'):
   j=args[0];bindings['j']=job[j]
   if op=='Submit':bindings['T']=setexpr([job[k] for k in before['pending'] if before['phases'][k]!=2 and k!=j])
   if op in ('Commit','CancelConfirmed'):bindings['R']=setexpr([job[k] for k in before['pending'] if k!=j])
   if op=='Commit' and before['phases'][j]==3:label='ReplayCommit';bindings={'j':job[j]}
  steps.append(dict(native_event=label,bindings=bindings,implementation_command=step['command'],prototype_accepted=step['actual_accept'],requirements_violated=step['requirements_violated']))
  before=after
 witnesses.append(dict(mutant=row['variant'],status='CANDIDATE_NATIVE_ANIMATION_TRACE; observed prototype witness, not a ProB trace',steps=steps))
(OUT/'mutation_witness_bindings.json').write_text(json.dumps(witnesses,indent=2,ensure_ascii=False)+'\n')
lines=['# Thực nghiệm bổ sung: case study, reference monitor và mutation','', '## Hệ được triển khai','', 'Một user ủy quyền cho agent điều phối; agent này cấp quyền đọc báo cáo cho analyst và quyền tạo bản phát hành cục bộ cho release agent. Hai tool thực sự đọc/ghi SQLite. Các agent chạy theo kịch bản, chưa dùng LLM, nền tảng agent bên ngoài hay dịch vụ phát hành thực tế.','', 'Reference monitor là mã Python/SQLite khác với oracle bất biến thuần Python. Trạng thái được ánh xạ sang biến mô hình; các điều kiện và cập nhật được đối chiếu ở mức event. Đây là kiểm thử conformance hữu hạn, chưa phải chứng minh code refines Event-B.','', 'Contract thực thi: docs/research/STAGED_EXECUTION_CONTRACT.md. Submit không dispatch sang provider; CancelConfirmed là local atomic abort, không kiểm tra một acknowledgement bên ngoài.','', '## Kết quả đối chiếu','', '| Cấu hình | Trạng thái đạt được | Lệnh được kiểm tra | Cạnh được chấp nhận | Lệnh bị từ chối |','|---|---:|---:|---:|---:|']
for x in r['bounded_conformance']:lines.append(f"| {x['configuration']} | {x['states']:,} | {x['checked_commands']:,} | {x['enabled_edges']:,} | {x['rejected_inputs']:,} |")
checks=sum(x['checked_commands'] for x in r['bounded_conformance']);edges=sum(x['enabled_edges'] for x in r['bounded_conformance']);denials=sum(x['rejected_inputs'] for x in r['bounded_conformance'])
lines+=['',f'Tổng theo bốn cấu hình: {checks:,} lượt lệnh, gồm {edges:,} lượt chấp nhận và {denials:,} lượt từ chối; không có sai lệch enabledness hoặc trạng thái sau thực thi. Các đồ thị có thể chồng lặp hành vi; không cộng để tuyên bố số hành vi toàn cục độc lập.','', 'Mỗi trạng thái được đạt tới bằng replay một prefix hợp lệ. Tại đó mọi lệnh trong miền kiểm tra được thử trên triển khai; trạng thái sau thử được rollback. Miền gồm các đích cấp quyền, scope 0–3, đích thu hồi và các job cho vòng đời, cùng ReleaseUnconfirmed phải bị từ chối.','', '## Tình huống thực thi và đối chứng lỗi','', f"Bản đúng khớp oracle trong cả {len(r['correct_scenarios'])} kịch bản, gồm luồng thành công và các yêu cầu không hợp lệ. Luồng thành công tạo {len(r['correct_scenarios'][0]['tool_effects'])} hiệu ứng tool, trong đó có một bản ghi phát hành; xem case_study.sqlite.",'', '| Lỗi cài chủ động | Vi phạm quan sát được trên prototype | PO mở tương ứng ở M2 |','|---|---|---|']
lookup={x['mutant']:x for x in native['mutants']}
for x in r['implementation_mutants']:
 po=lookup[x['variant']];names=[p['po'] for p in po['open_pos'] if p['component']=='M2_SubmittedObligations']
 lines.append('| '+x['variant']+' | '+', '.join(x['violations'])+' | '+', '.join(names)+' |')
lines+=['','Cả 6/6 biến thể triển khai bị phát hiện. Cả 6 biến thể mô hình statically check thành công nhưng còn PO liên quan mở; invariant và các context/M0/M1 được giữ nguyên. Các mutant mô hình là biến thể của refinement M2/M3; số PO của chúng không nằm trong 109 PO của mô hình đúng.','', '**PO mở không tự chứng minh có lỗi.** Những trace ở đây được quan sát trên prototype và đánh giá với oracle/yêu cầu cố định. Các binding để thử animation Rodin được xuất riêng; chưa được chạy xác nhận bằng ProB. Biến thể mô hình và biến thể triển khai đại diện cùng cơ chế lỗi, chưa có chứng minh tương đương giữa từng cặp.','', '## Đồng thời và thứ tự thu hồi','', '| Kiểm tra | Số lần | Kết quả |','|---|---:|---|']
for x in r['concurrency']:lines.append(f"| {x['variant']}, 2 yêu cầu / hạn mức 1 | {x['trials']} | nhận {x['accepted_per_trial']} yêu cầu/lần; {x['requirement_violations']} lần vi phạm |")
for x in r['revocation_linearizations']:lines.append(f"| {x['order']} | {x['trials']} | {x['commits_accepted']} Commit được nhận, {x['tool_effects']} hiệu ứng |")
lines+=['','Các lịch được điều khiển chủ động: bản unsafe để cả hai lần đọc hạn mức hoàn tất trước khi ghi. Đây là minh họa race do kiểm tra ngoài vùng nguyên tử, không phải lấy mẫu tất cả interleaving hoặc đo thông lượng production.','', '## Lỗi tool và rollback','', 'Một trigger làm lỗi khi ghi tool_effects, sau khi đã ghi thử release_registry. Savepoint rollback cả bản ghi phát hành và trạng thái monitor; snapshot giữ nguyên. Bỏ lỗi và retry chỉ tạo một hiệu ứng. Chỉ kết luận cho tool/database cùng transaction; không suy ra exactly-once cho dịch vụ bên ngoài.','', '## Cấu hình và tái lập','', f"Python {r['environment']['python']}; SQLite {r['environment']['sqlite']}. Chạy `python3 implementation/run_experiments.py`. Thời gian trong JSON là wall time của cả harness, bao gồm oracle/snapshot/rollback; không phải latency riêng của monitor.",'', 'Native negative controls: `python3 implementation/check_model_mutants.py --rodin PATH --ecj PATH`. Source mutant, log, goal PO và summary có trong implementation/model_mutants.','', '## Hạn chế còn lại cho bài báo','', '- Một case study được xây dựng cho nghiên cứu, agent theo kịch bản và tool cục bộ; chưa có benchmark agent độc lập hoặc LLM thật.','- Oracle Python được diễn giải thủ công từ mô hình bởi cùng nhóm tác giả; chưa có đối chiếu native ProB hay chứng minh code-level refinement.','- Sáu lỗi và race baseline đều do tác giả cài, nên tỷ lệ phát hiện không đại diện cho lỗi thực tế.','- Chỉ một monitor process với lock chung; không chứng minh tính sẵn sàng, phân tán, crash recovery hoặc non-bypassability của triển khai.','- Artifact này cung cấp formal development và thực nghiệm hỗ trợ; không khẳng định protocol mới hoặc công trình đầu tiên.']
(BASE/'docs/IMPLEMENTATION_RESULTS_VI.md').write_text('\n'.join(lines)+'\n')
# Compact LaTeX draft with measured values, deliberately limited claims.
latex=r'''\section{Prototype Evaluation}
\label{sec:prototype-evaluation}
We implemented a Python/SQLite reference monitor for a release-preparation workflow comprising a user, a coordinator, an analyst, and a release agent. The analyst reads a local report, while the release agent creates a local release record. Agents are scripted actors; the experiment does not use an LLM or an external deployment service. The allowance counts both outstanding reservations and previously executed tool calls. Authorization checking, ledger updates, and local tool effects occur within a single monitor transaction.

\paragraph{Execution contract.}
Submit updates staging/control metadata and does not dispatch an independently executing provider operation. Commit is the protected-effect transition. CancelConfirmed is an atomic local abort in this prototype; its pending-membership guard does not validate a provider acknowledgement. Authentication, trusted control-plane inputs, protected monitor state and complete mediation are assumptions. The code is not a sandbox and the model does not cover distributed recovery or uncertain external outcomes.

\paragraph{Bounded conformance.}
An independent, immutable Python interpretation of the Event-B model supplies the reference decisions and post-states. For every reachable state in each finite configuration, we replay an accepted prefix against the implementation and test all commands in the declared input domain, including rejected requests. This procedure checks conformance to the Python interpretation; it is not a mechanically proved refinement of the implementation to Event-B.
\begin{table}[t]
\centering
\caption{Bounded implementation conformance. All checked commands matched the oracle.}
\begin{tabular}{lrrrr}
\hline
Configuration & States & Commands & Accepted & Rejected\\
\hline
'''
for x in r['bounded_conformance']:
 latex+=f"{x['configuration'].replace('_',r'\_')} & {x['states']} & {x['checked_commands']} & {x['enabled_edges']} & {x['rejected_inputs']}\\\\\n"
latex+=r'''\hline
\end{tabular}
\end{table}
'''
latex+=f'Across the four configurations, all {checks:,} command trials matched both enabledness and the projected post-state. These totals include {edges:,} accepted and {denials:,} rejected trials. Counts are summed per configuration and need not represent globally distinct behaviors.\n\n'
latex+=r'''\paragraph{Negative controls.}
We seeded six implementation faults: capability expansion, ignoring ancestor revocation, stale authorization at commit, omission of the shared-limit check, premature release of an obligation, and replayed execution. Each variant produced an observed violation of the unchanged requirements. Corresponding concrete-model variants retained the original invariants and abstract levels: all passed static checking, but relevant Rodin obligations remained open. An open obligation alone is not treated as a counterexample. Prototype traces and candidate native-animation bindings are supplied separately; ProB validation of those traces has not yet been performed.

\paragraph{Controlled schedules and tool failures.}
With two requests and allowance one, the atomic monitor accepted one request in each of 100 trials. A deliberately unsafe baseline, with the capacity read outside the atomic update, accepted both requests and exceeded the allowance in all 100 forced schedules. In 50 executions of each selected revocation order, revocation before commit prevented every effect, whereas commit before revocation produced one effect per execution. An injected database failure rolled back the local release insertion together with monitor state; retry produced one effect. These results rely on effects sharing the database transaction and do not establish exactly-once execution against external providers.

\paragraph{Threats to validity.}
The case study, mutants, and executable oracle were constructed by the authors. The finite configurations and controlled schedules do not cover all deployments or interleavings. Scripted actors and local tools do not establish LLM-agent or distributed-service correctness. The results provide bounded empirical conformance and negative-control evidence in addition to the formal model proofs; they do not establish the novelty of the authorization protocol or a code-level refinement theorem.
'''
(BASE/'docs/PROTOTYPE_EVALUATION_DRAFT.tex').write_text(latex)
print('Report, native-animation candidate bindings and LaTeX evaluation draft generated from recorded data.')
