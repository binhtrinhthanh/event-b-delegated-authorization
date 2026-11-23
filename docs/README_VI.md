# DelegatedAuthorization — 100% automatic proof configuration

**Kết quả đã chạy trực tiếp: 109/109 proof obligations được native AutoProver của Rodin đóng; 0 PO mở; 0 proof có cờ manual.** Đây là kết quả với profile `DelegatedAuto` đi kèm và Atelier B Provers, không phải cam kết cho cấu hình Auto mặc định của mọi bản Rodin.

| Thành phần | PO | Tự động đóng |
|---|---:|---:|
| C_Delegation | 4 | 4 |
| M0_AuthorityLedger | 36 | 36 |
| M1_DelegationChain | 33 | 33 |
| M2_SubmittedObligations | 36 | 36 |
| C_Pilot, M3_Pilot | 0 | 0 |
| Tổng | 109 | 109 |

Các proof của M0/M1/M2 dùng miền hữu hạn tham số hóa, không cố định số agent/yêu cầu bằng cấu hình pilot. M3 chỉ ràng buộc một instance để animation; 0 PO của M3 không phải kết quả model checking.

## Thực nghiệm triển khai đã bổ sung

`implementation/` chứa case study các agent theo kịch bản, reference monitor SQLite và hai tool cục bộ. Đã chạy 59.136 lượt đối chiếu trên bốn cấu hình, phát hiện sáu lỗi triển khai cài chủ động, kiểm tra sáu negative-control model trực tiếp trong Rodin, các lịch đồng thời và rollback/retry.

- Báo cáo: `docs/IMPLEMENTATION_RESULTS_VI.md`.
- Chạy: `python3 implementation/run_experiments.py`.
- Chi tiết phương pháp/giới hạn: `implementation/README.md`.

Các dự án `Negative_*` trong `implementation/model_mutants/` cố ý không chứng minh được toàn bộ PO. Kết quả 109/109 phía trên chỉ áp dụng dự án gốc `DelegatedAuthorization`. Khi import, chọn đúng thư mục dự án gốc.

## Mở trong Rodin

1. Dùng một workspace mới để tránh trùng tên dự án cũ.
2. Cài **Atelier B Provers** từ update site chính thức: https://www.atelierb.eu/update_site/atelierb_provers/
3. Để tái tạo chiến lược Auto, chép `plugins/delegated.batch_1.0.0.jar` của gói vào thư mục `dropins` của bản Rodin đang dùng, rồi khởi động lại. JAR này được biên dịch từ mã Java đi kèm, không chứa binary Atelier B của bên thứ ba.
4. **File → Import → General → Existing Projects into Workspace**; chọn thư mục `DelegatedAuthorization` có `.project`.
5. Dự án chứa `.settings/org.eventb.core.prefs` chọn profile `DelegatedAuto`. Kiểm tra profile trong preferences của dự án trước khi chạy Auto.
6. Mở Proof Obligation Explorer: các proof đã lưu nằm trong `.bpr`, trạng thái nằm trong `.bps`. Khi đổi phiên bản Rodin/prover, cần kiểm tra lại proof và chạy Auto lại.

Không cần Camille hoặc Theory plugin. Cấu hình được kiểm tra: Rodin 3.8.0.202304051545-af2f57e1e, Java 17.0.20, Atelier B core 1.7.1.r16756 và Linux fragment 2.4.0.r16756. Chạy UI/Windows chưa được thực nghiệm trong gói này; số 109/109 là kết quả native Linux nói trên.

## Những gì được giữ lại

- Giảm phạm vi quyền qua từng bước ủy quyền, không vượt quyền gốc.
- Thu hồi một nút vô hiệu hóa quyền sử dụng mới trong toàn bộ cây con.
- Kiểm tra quyền hiện tại tại Reserve, Submit và Commit.
- Nghĩa vụ tiếp tục chiếm tài nguyên sau thu hồi; chỉ CancelConfirmed được giải phóng nó.
- `used = card(pending) + card(committed)` và `used ≤ budget` vẫn là invariant.
- Commit tăng effectCount; mỗi yêu cầu có nhiều nhất một hiệu ứng.
- Submit vẫn là event convergent và PO VAR đã được đóng.

Chi tiết thay đổi biểu diễn và giải thích không làm yếu yêu cầu: `docs/CHANGES_FROM_V1.md`.

## Tái chạy từ đầu trên Linux

```bash
python3 tools/run_rodin.py --rodin /absolute/path/to/rodin --work /absolute/path/to/new-work
python3 tools/collect_evidence.py --workspace-project /absolute/path/to/new-work/workspace/DelegatedAuthorization --native-log /absolute/path/to/new-work/rodin_native.log
```

Cần bản Rodin có Atelier B Provers và JDK phù hợp; nếu thiếu javac, thêm `--ecj /absolute/path/to/ecj.jar`. Script luôn nhập chỉ `.bum/.buc`, không nhập các proof đã lưu, nên workspace mới tái chứng minh từ đầu. Native AutoProver được gọi sau static checking/POG và chọn profile có một chiến lược chung cho tất cả PO; không có nhánh chọn theo tên PO hoặc thao tác interactive.

`collect_evidence.py` kiểm tra nguồn trùng khớp, cả 6 component `accurate=true`, mọi PO confidence=1000 và `psManual=false`; không chấp nhận proof được Review để đạt tỷ lệ này.

## Kiểm tra bổ sung

```bash
python3 tools/check_sources.py
python3 tools/check_context.py
python3 tools/check_finite.py
```

Đây lần lượt là kiểm tra cấu trúc, witness hữu hạn cho context và diễn giải hữu hạn độc lập của các event/refinement. Chúng bổ sung cho native proof, không thay thế Rodin hoặc ProB. Chưa chạy ProB. Có prototype SQLite với agent theo kịch bản ở implementation/; chưa tích hợp LLM hoặc một hệ agent triển khai thực tế.

## Nội dung gói

- `DelegatedAuthorization/`: context, machine, proof và preferences.
- `docs/MODELS.eventb.txt`: công thức đọc được.
- `docs/SEMANTICS.md`: ngữ nghĩa, ranh giới tin cậy và giới hạn.
- `docs/RESULTS_VI.md`: kết quả và cách dùng số liệu trong bài.
- `validation/`: log native, thống kê PO, nguồn chứng cứ và kiểm tra bổ sung.
- `tools/`: generator và mã chiến lược/ứng dụng kiểm tra.
- `plugins/`: JAR của chiến lược tự động do gói này cung cấp.

Nếu sửa mô hình, phải chạy lại kiểm chứng; 109/109 chỉ gắn với nguồn và cấu hình có SHA256 trong gói.
