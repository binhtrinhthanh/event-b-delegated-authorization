# Thực nghiệm bổ sung: case study, reference monitor và mutation

## Hệ được triển khai

Một user ủy quyền cho agent điều phối; agent này cấp quyền đọc báo cáo cho analyst và quyền tạo bản phát hành cục bộ cho release agent. Hai tool thực sự đọc/ghi SQLite. Các agent chạy theo kịch bản, chưa dùng LLM, nền tảng agent bên ngoài hay dịch vụ phát hành thực tế.

Reference monitor là mã Python/SQLite khác với oracle bất biến thuần Python. Trạng thái được ánh xạ sang biến mô hình; các điều kiện và cập nhật được đối chiếu ở mức event. Đây là kiểm thử conformance hữu hạn, chưa phải chứng minh code refines Event-B.

Contract thực thi: docs/research/STAGED_EXECUTION_CONTRACT.md. Submit không dispatch sang provider; CancelConfirmed là local atomic abort, không kiểm tra một acknowledgement bên ngoài.

## Kết quả đối chiếu

| Cấu hình | Trạng thái đạt được | Lệnh được kiểm tra | Cạnh được chấp nhận | Lệnh bị từ chối |
|---|---:|---:|---:|---:|
| chain_budget1 | 422 | 8,862 | 882 | 7,980 |
| chain_budget2 | 566 | 11,886 | 1,344 | 10,542 |
| star_budget1 | 770 | 16,170 | 1,731 | 14,439 |
| star_budget2 | 1,058 | 22,218 | 2,691 | 19,527 |

Tổng theo bốn cấu hình: 59,136 lượt lệnh, gồm 6,648 lượt chấp nhận và 52,488 lượt từ chối; không có sai lệch enabledness hoặc trạng thái sau thực thi. Các đồ thị có thể chồng lặp hành vi; không cộng để tuyên bố số hành vi toàn cục độc lập.

Mỗi trạng thái được đạt tới bằng replay một prefix hợp lệ. Tại đó mọi lệnh trong miền kiểm tra được thử trên triển khai; trạng thái sau thử được rollback. Miền gồm các đích cấp quyền, scope 0–3, đích thu hồi và các job cho vòng đời, cùng ReleaseUnconfirmed phải bị từ chối.

## Tình huống thực thi và đối chứng lỗi

Bản đúng khớp oracle trong cả 7 kịch bản, gồm luồng thành công và các yêu cầu không hợp lệ. Luồng thành công tạo 2 hiệu ứng tool, trong đó có một bản ghi phát hành; xem case_study.sqlite.

| Lỗi cài chủ động | Vi phạm quan sát được trên prototype | PO mở tương ứng ở M2 |
|---|---|---|
| scope_expansion | scope_attenuation | Delegate/grd5/GRD |
| local_revocation | authorization_at_use, live_chain_authority | Revoke/grd2/GRD |
| cached_authorization | authorization_at_use | Commit/inv25/INV, Commit/grd2/GRD |
| no_shared_budget | shared_budget | Reserve/grd3/GRD |
| early_release | obligation_coverage | ReleaseUnconfirmed/inv20/INV, ReleaseUnconfirmed/used/EQL, ReleaseUnconfirmed/pending/EQL, ReleaseUnconfirmed/VAR |
| replay_commit | at_most_once, effect_count_membership, ledger_conservation | ReplayCommit/inv22a/INV, ReplayCommit/inv23/INV, ReplayCommit/VAR |

Cả 6/6 biến thể triển khai bị phát hiện. Cả 6 biến thể mô hình statically check thành công nhưng còn PO liên quan mở; invariant và các context/M0/M1 được giữ nguyên. Các mutant mô hình là biến thể của refinement M2/M3; số PO của chúng không nằm trong 109 PO của mô hình đúng.

**PO mở không tự chứng minh có lỗi.** Những trace ở đây được quan sát trên prototype và đánh giá với oracle/yêu cầu cố định. Các binding để thử animation Rodin được xuất riêng; chưa được chạy xác nhận bằng ProB. Biến thể mô hình và biến thể triển khai đại diện cùng cơ chế lỗi, chưa có chứng minh tương đương giữa từng cặp.

## Đồng thời và thứ tự thu hồi

| Kiểm tra | Số lần | Kết quả |
|---|---:|---|
| atomic_monitor, 2 yêu cầu / hạn mức 1 | 100 | nhận 1 yêu cầu/lần; 0 lần vi phạm |
| non_atomic_reserve, 2 yêu cầu / hạn mức 1 | 100 | nhận 2 yêu cầu/lần; 100 lần vi phạm |
| Revoke_then_Commit | 50 | 0 Commit được nhận, 0 hiệu ứng |
| Commit_then_Revoke | 50 | 50 Commit được nhận, 50 hiệu ứng |

Các lịch được điều khiển chủ động: bản unsafe để cả hai lần đọc hạn mức hoàn tất trước khi ghi. Đây là minh họa race do kiểm tra ngoài vùng nguyên tử, không phải lấy mẫu tất cả interleaving hoặc đo thông lượng production.

## Lỗi tool và rollback

Một trigger làm lỗi khi ghi tool_effects, sau khi đã ghi thử release_registry. Savepoint rollback cả bản ghi phát hành và trạng thái monitor; snapshot giữ nguyên. Bỏ lỗi và retry chỉ tạo một hiệu ứng. Chỉ kết luận cho tool/database cùng transaction; không suy ra exactly-once cho dịch vụ bên ngoài.

## Cấu hình và tái lập

Python 3.12.14; SQLite 3.53.1. Chạy `python3 implementation/run_experiments.py`. Thời gian trong JSON là wall time của cả harness, bao gồm oracle/snapshot/rollback; không phải latency riêng của monitor.

Native negative controls: `python3 implementation/check_model_mutants.py --rodin PATH --ecj PATH`. Source mutant, log, goal PO và summary có trong implementation/model_mutants.

## Hạn chế còn lại cho bài báo

- Một case study được xây dựng cho nghiên cứu, agent theo kịch bản và tool cục bộ; chưa có benchmark agent độc lập hoặc LLM thật.
- Oracle Python được diễn giải thủ công từ mô hình bởi cùng nhóm tác giả; chưa có đối chiếu native ProB hay chứng minh code-level refinement.
- Sáu lỗi và race baseline đều do tác giả cài, nên tỷ lệ phát hiện không đại diện cho lỗi thực tế.
- Chỉ một monitor process với lock chung; không chứng minh tính sẵn sàng, phân tán, crash recovery hoặc non-bypassability của triển khai.
- Artifact này cung cấp formal development và thực nghiệm hỗ trợ; không khẳng định protocol mới hoặc công trình đầu tiên.
