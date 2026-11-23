# Thay đổi để hỗ trợ chứng minh tự động

## 1. Quan hệ quyền thay cho hàm trả về tập quyền

V1 dùng scope ∈ issued → ℙ(CAP). V2 dùng scope ⊆ NODE×CAP, dom(scope)=issued. Quyền của a được đọc bằng scope[{a}].

Ánh xạ biểu diễn: scope_relation = {a,k · a∈issued ∧ k∈scope_function(a) ∣ a↦k}. Chiều ngược là scope_function(a)=scope_relation[{a}] trên issued. Mỗi node đã cấp quyền có scope không rỗng, nên dom(scope_relation)=issued. Hai dạng biểu diễn có cùng phạm vi quyền; việc thêm {a}×S thay cho mở rộng hàm tránh các PO khó về hàm chứa powerset.

Auth được định nghĩa bằng giao giữa scope và các cặp agent/capability có đường tổ tiên không chứa nút bị thu hồi. Ancestor closure của issued vẫn được giữ. Các invariant attenuation và scope[{a}]⊆rootScope vẫn có proof; không chỉ kiểm tra ở pilot.

## 2. Tập còn lại được đặt tên trong event

Commit/CancelConfirmed có tham số R=pending∖{j}; Submit có T=(pending∖submitted)∖{j}. Mỗi giá trị được định nghĩa duy nhất từ trạng thái và j, không tạo lựa chọn nghiệp vụ mới.

Các đẳng thức phân hoạch, tính hữu hạn và cardinality hỗ trợ được ghi là **theorem guards**, không phải axiom hay giả thiết bổ sung. Ví dụ:

- pending = R∪{j}, j∉R;
- pending∖submitted = T∪{j}, j∉T;
- card(pending∖submitted)=card(T)+1.

Rodin sinh và đóng các PO THM/WD cho chúng. Những theorem này xuất hiện trong tổng 109 PO. Không chuyển một yêu cầu an toàn chưa chứng minh thành guard giả định để làm PO khác đóng được.

Hai guard tường minh a∈NODE∖{root} và S⊆CAP là điều kiện kiểu đã suy ra từ a∉issued/root∈issued và S⊆scope của cha; không làm giảm các bước ủy quyền hợp lệ của V1.

## 3. Đặc tả bộ đếm thành hai trường hợp

V1 dùng effectCount(j)=card({j}∩committed). V2 dùng j∈committed⇒effectCount(j)=1 và j∈JOB∖committed⇒effectCount(j)=0. Vì committed⊆JOB, hai cách viết tương đương. Commit vẫn thực hiện effectCount(j)≔effectCount(j)+1; invariant effectCount(j)≤1 vẫn có PO riêng, không gán trực tiếp bộ đếm bằng 1.

## 4. Sự kiện Submit vẫn convergent

Variant vẫn là card(pending∖submitted). Submit/VAR có mặt trong inventory và đã được đóng tự động. Không đổi Submit thành anticipated/ordinary để loại bỏ PO khó.

## 5. Cấu hình prover cũng thay đổi

V1 có 64/84 PO được script đóng qua IUserSupport, đánh dấu manual trong metadata. V2 dùng native AutoProver, profile DelegatedAuto, native core tactics và Atelier B Provers; mọi proof có psManual=false.

Do cả cách biểu diễn và cấu hình prover cùng thay đổi, không dùng 64/84→109/109 làm thí nghiệm đối chứng để khẳng định riêng tác dụng của việc mô hình lại. Tỷ lệ 100% là bằng chứng tái chạy của đúng phiên bản/cấu hình này.

Diễn giải Python đi kèm kiểm tra thêm quan hệ quyền, các phân hoạch R/T và mô phỏng hữu hạn. Chưa có một chứng minh bisimulation riêng giữa hai phiên bản Rodin V1/V2; phần đối chiếu biểu diễn ở trên là lập luận toán học, không phải một PO đã sinh cho việc chuyển phiên bản.
