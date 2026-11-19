# Team

## Thông tin nhóm

- Tên nhóm (`TenNhom`, không dấu, không khoảng trắng): `T100`
- Lớp: `L3B`
- Repo của bàn: `K5-L3B-DAY10-T100-PoCtoPilotGate1`
- Thẻ sự cố đã bốc (S1–S8): `S8` (commit nhận thẻ: `68aae9f`)

## Thành viên

Họ tên đầy đủ và MSSV của **mọi** thành viên; thêm dòng nếu cần. Vai: Kỹ sư cổng · Sản phẩm và kinh doanh · Vận hành và pháp lý (README mục 3, phút 0–15).

| STT | Họ và tên | MSSV | Vai | Trưởng nhóm |
| --: | --------- | ---- | --- | :---------: |
|   1 |  Đào Đức Duy        |   2A202603900   |  Gate Engineer – Evaluation & Monitoring   |     x       |
|   2 |    Nguyễn Minh Nhân       |  2A202603723    |  Gate Engineer – Guards   |             |
|   3 |    Bùi Ngọc Hùng       |  2A202603770    |  	Product & Business   |             |
|   4 |    Trần Cảnh Hưng       |  2A202603759    |  Operations & Legal   |             |

Ghi `members` trong `submission/submission.json` theo dạng `"HoVaTen-MSSV"`, khớp bảng trên.

## Cá nhân

Mỗi thành viên tự viết một mục bên dưới (chép mẫu, đổi tiêu đề thành họ tên không dấu và MSSV, ví dụ `## NguyenVanAn-20241234`).

## DaoDucDuy-2A202603900

### Phần việc phụ trách

Trưởng nhóm; Gate Engineer phụ trách đánh giá và giám sát. Phụ trách đánh giá kết quả Phase 3 của thẻ S8, thiết kế chỉ số theo dõi mới và ghi nhận bằng chứng/giới hạn của kết quả trong Phiếu C, đặc biệt C1, C8, C11 và C12. File liên quan: `lab10/monitors.py`, `templates/form-c-incident.md`.

### Đóng góp cụ thể

- Bổ sung `protected_refund_escalation_rate` vào `MONITORS` để đo tỷ lệ lượt có escalation do approval không hợp lệ hoặc sắp vượt hạn mức hoàn tự động theo khách hàng; không dựa vào nhãn đúng/sai hay nội dung ticket.
- Đối chiếu kết quả base và S8 sau sửa: monitor mới thay đổi từ 0.0 lên 0.04 trên S8 (5/125), trong khi regression đạt 13/13 và các kiểm tra visible, criteria đạt.
- Ghi nhận giới hạn tự chấm: grade `R-S8-grade-20261119-192650-5f5d87` vẫn FAIL integrity do các tệp S1–S7 được khóa không có trong repo; không coi kết quả visible là xác nhận grade toàn phần. Cùng với chi phí phân khúc order không xác minh được 10.200đ/ticket, đây là căn cứ giữ quyết định v2 ở trạng thái “Cải tiến thêm”, chưa mở pilot thật.

### Bằng chứng

Commit `f49ef54` (`LAB 10: submit S8 Phase 3 evaluation`); mã lần chạy `R-S8-grade-20261119-192650-5f5d87` và report tại `submission/runs/grade-report.md`; kết quả monitor ở mục C8, checklist nhóm 1 ở C11 và quyết định ở C12. Trong report, `protected_refund_escalation_rate` sáng từ 0.0 (base) lên 0.04 (S8 after).

### Exit ticket

Học được rằng metric vận hành hữu ích cần dựa trên sự kiện thực tế của guard, không dựa vào nhãn của bộ kiểm thử, và phải có khả năng phân biệt được sự cố với bộ nền. Chưa chắc monitor hiện tại có phát hiện được việc approval bị thu hồi sau bước kiểm tra nhưng trước lúc ghi; cần cơ chế tiêu thụ approval nguyên tử ở write boundary và kiểm chứng thêm trước Gate 2.
