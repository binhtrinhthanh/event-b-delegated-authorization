# Thực nghiệm thăm dò: Delegated Authorization

Đã chạy thực tế bằng bộ duyệt trạng thái BFS tự viết bằng Python. Chưa chạy Rodin/ProB; chưa có bằng chứng chứng minh Event-B.

## Cấu hình và kết quả

n tính cả nút gốc đại diện người dùng. Mỗi yêu cầu tiêu thụ 1 đơn vị tài nguyên; B là hạn mức dùng chung. Mỗi dòng là một đồ thị trạng thái được duyệt hết.

| Nút | Yêu cầu | B | Cấu trúc | Trạng thái | Chuyển trạng thái | Giây |
|---:|---:|---:|---|---:|---:|---:|
| 3 | 2 | 1 | chain | 150 | 312 | 0.0013 |
| 3 | 2 | 1 | star | 170 | 365 | 0.0015 |
| 3 | 2 | 2 | chain | 222 | 543 | 0.0021 |
| 3 | 2 | 2 | star | 242 | 605 | 0.0023 |
| 4 | 3 | 2 | chain | 1,790 | 5,576 | 0.0237 |
| 4 | 3 | 2 | star | 2,230 | 7,265 | 0.0299 |
| 4 | 3 | 3 | chain | 2,222 | 7,493 | 0.0300 |
| 4 | 3 | 3 | star | 2,662 | 9,317 | 0.0379 |
| 5 | 3 | 2 | chain | 4,926 | 17,258 | 0.0724 |
| 5 | 3 | 2 | star | 6,690 | 25,140 | 0.1044 |
| 6 | 4 | 2 | chain | 33,278 | 134,950 | 0.5912 |
| 6 | 4 | 2 | star | 54,150 | 238,350 | 1.1901 |

Không phát hiện vi phạm trên 12 cấu hình hữu hạn này. Thời gian là một lần chạy, không phải thống kê hiệu năng; các cấu hình có thể chồng lặp hành vi nên không cộng để tuyên bố số hành vi độc lập.

## Cài lỗi và phản ví dụ

| Lỗi | Thuộc tính bị vi phạm đầu tiên | Độ dài phản ví dụ |
|---|---|---:|
| scope_expansion | scope_attenuation | 1 |
| local_revocation | live_chain_at_use | 3 |
| cached_authorization | live_chain_at_use | 5 |
| no_shared_budget | shared_budget | 4 |
| early_release | outstanding_obligation_covered | 4 |
| replay_commit | shared_budget, at_most_once | 5 |

### scope_expansion

Delegate(0->1,scope=2)

### local_revocation

Delegate(0->1,scope=1) → Revoke(0) → Reserve(job=0,agent=1)

### cached_authorization

Delegate(0->1,scope=1) → Reserve(job=0,agent=1) → Submit(job=0) → Revoke(0) → Commit(job=0,agent=1)

### no_shared_budget

Delegate(0->1,scope=1) → Delegate(1->2,scope=1) → Reserve(job=0,agent=1) → Reserve(job=1,agent=2)

### early_release

Delegate(0->1,scope=1) → Reserve(job=0,agent=1) → Submit(job=0) → ReleaseBeforeCancel(job=0)

### replay_commit

Delegate(0->1,scope=1) → Reserve(job=0,agent=1) → Submit(job=0) → Commit(job=0,agent=1) → ReplayCommit(job=0)

## Ý nghĩa cho bài báo

Kết quả cho thấy bộ kiểm tra phân biệt được phiên bản có bảo vệ và sáu biến thể cố ý bỏ bảo vệ. Tình huống đáng tập trung là thu hồi quyền xen giữa Submit và Commit: kết quả kiểm tra trước đó không đủ để cho phép thực thi sau thu hồi. Chính sách ở đây chặn mọi Commit mới sau thu hồi, kể cả yêu cầu đã Submit; nghĩa vụ vẫn được giữ cho tới CancelConfirmed. Đây là lựa chọn ngữ nghĩa cần nêu rõ trong bài.

Phần tổng quát là ủy quyền nhiều cấp, giảm phạm vi quyền, kiểm tra chuỗi quyền tại lúc sử dụng và giới hạn tài nguyên chung. Procurement/payment có thể là một case study; không cần giới hạn tiêu đề vào thanh toán.

## Chưa đủ để viết kết quả formal verification hoàn chỉnh

1. Cần xây dựng mô hình Event-B nhập được vào Rodin, sinh và chứng minh proof obligations; hiện chỉ có đặc tả toán học và kế hoạch refinement trong MODEL.md.
2. Cần kiểm tra đối chiếu Python–Event-B/ProB để giảm nguy cơ sai khác mô hình.
3. Cần triển khai reference monitor cho một hệ agent thực tế và chạy lại các trace; hiện chưa có tích hợp này.
4. Cần mở rộng scope theo action/resource/audience, hạn mức từng nhánh, thời hạn quyền, credential renewal, truyền thu hồi bất đồng bộ và reconciliation sau lỗi. Hiện các nội dung này chưa được thực nghiệm.
5. Chỉ kiểm tra safety/at-most-once; chưa kiểm tra liveness, fairness, exactly-once hay deadlock freedom. Trạng thái kết thúc và trạng thái không còn quyền có thể không có event sử dụng hợp lệ.
6. Các mutant do tác giả tạo và oracle do cùng tác giả viết; 6/6 không phải bằng chứng hiệu quả trên lỗi thực tế.

## Khung thực nghiệm chính thức đề xuất

RQ1: Các invariant nào được chứng minh tại từng refinement và còn PO nào cần xử lý tương tác?
RQ2: Cơ chế nào ngăn privilege escalation, ancestor-revocation bypass và authorization race?
RQ3: Kết quả mô hình có tái hiện trên reference monitor và tool adapter thực tế không?
RQ4: Chi phí kiểm chứng tăng thế nào theo số agent, chiều sâu delegation, số yêu cầu và độ rộng scope?

Bộ thăm dò hiện cung cấp dữ liệu ban đầu cho RQ2 và quy mô nhỏ của RQ4; chưa trả lời RQ1/RQ3.
