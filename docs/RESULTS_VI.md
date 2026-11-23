# Kết quả mô hình lại và chứng minh tự động

**109/109 PO được chứng minh tự động; 0 PO mở; 0 proof manual.**

| Thành phần | Tổng PO | Tự động đóng | Mở |
|---|---:|---:|---:|
| C_Delegation | 4 | 4 | 0 |
| C_Pilot | 0 | 0 | 0 |
| M0_AuthorityLedger | 36 | 36 | 0 |
| M1_DelegationChain | 33 | 33 | 0 |
| M2_SubmittedObligations | 36 | 36 | 0 |
| M3_Pilot | 0 | 0 | 0 |

## Bằng chứng kiểm tra

- Static checking: 0 lỗi; cả sáu component accurate=true.
- Native AutoProver được chạy với profile DelegatedAuto từ workspace sạch; chỉ nhập .bum/.buc, không nhập .bpr cũ.
- Từng dòng .bps có confidence=1000 và psManual=false. Không dùng Review hoặc thao tác interactive.
- Lượt thành công đầu và lượt kiểm tra sạch cuối đều đóng 109/109 PO của cùng nguồn mô hình.
- Các PO THM/WD của theorem guards được tính đầy đủ trong tổng, không bị loại khỏi mẫu số.

| Loại PO | Số lượng |
|---|---:|
| INV | 68 |
| NAT | 1 |
| THM | 12 |
| VAR | 1 |
| VWD | 1 |
| WD | 26 |

## Phạm vi kết luận

Các invariant và các refinement của đúng mô hình Event-B này đã có proof với cấu hình ghi nhận. M0/M1/M2 dùng các miền hữu hạn có kích thước tham số hóa; kết quả không chỉ là duyệt một instance nhỏ. C_Pilot/M3_Pilot có 0 PO mới; không dùng chúng để tuyên bố đã model-check hệ agent thực tế.

100% auto ở đây là **tỷ lệ của cấu hình DelegatedAuto đi kèm**, có core tactics và Atelier B Provers. Không gọi đây là tỷ lệ của cấu hình Auto mặc định hoặc cam kết trên mọi phiên bản/phần cứng. Native Linux đã được thử; Windows/UI chưa được thử.

Việc chuyển biểu diễn đi kèm các theorem hỗ trợ đã chứng minh; những yêu cầu an toàn ban đầu vẫn hiện diện. Xem CHANGES_FROM_V1.md để đối chiếu phạm vi quyền, thu hồi, ngân sách, at-most-once và variant. Tăng số PO từ 84 lên 109 phản ánh thay đổi biểu diễn và các theorem/WD bổ sung, không phải tăng số lỗi thực tế đã phát hiện.

## Cấu hình

- Rodin 3.8.0.202304051545-af2f57e1e; Java 17.0.20.
- Atelier B Provers: core 1.7.1.r16756, Linux fragment 2.4.0.r16756.
- Profile: tối đa ba lượt; biến đổi native, chọn giả thiết, rewriting theo đẳng thức, built-in PP, các tactic ML/P1/PP của Atelier B; ML bổ sung timeout 2.000 ms, forces=3.
- Chiến lược chung không kiểm tra tên PO để chọn cách chứng minh. Mã nguồn và JAR của chiến lược có trong gói.

## Kiểm tra hữu hạn bổ sung

| Nút | Yêu cầu | Hạn mức | Cấu trúc | Trạng thái | Chuyển trạng thái |
|---:|---:|---:|---|---:|---:|
| 3 | 2 | 1 | chain | 422 | 882 |
| 3 | 2 | 2 | chain | 566 | 1,344 |
| 3 | 2 | 1 | star | 770 | 1,731 |
| 4 | 3 | 2 | chain | 5,382 | 16,483 |
| 4 | 3 | 2 | star | 20,878 | 70,340 |
| 5 | 3 | 2 | chain | 21,286 | 75,012 |

Tất cả cấu hình được duyệt hết, kiểm tra thêm biểu diễn quan hệ quyền, phân hoạch R/T, invariant và mô phỏng giữa các mức. Đây là Python độc lập; chưa có đối chiếu trace bằng ProB hoặc triển khai agent thực tế.

## Cách báo cáo trong paper

Có thể viết: “All 109 generated proof obligations were discharged automatically using Rodin 3.8 with the supplied DelegatedAuto strategy and Atelier B Provers. No interactive proof steps were required.”

Cần giữ các giả thiết trusted atomic monitor và ngữ nghĩa Submit/Commit trong phần mô hình; chứng minh không bao phủ việc một nhà cung cấp bên ngoài tự hoàn tất yêu cầu sau thu hồi, lỗi triển khai, mật mã hay hành vi nội bộ của LLM.
