# Team

## Thông tin nhóm

- Tên nhóm (`TenNhom`, không dấu, không khoảng trắng): `T100`
- Lớp: `L3B`
- Repo của bàn: `https://github.com/D121104/K5-L3B-DAY10-T100-PoCtoPilotGate1`
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

Trưởng nhóm; Gate Engineer phụ trách đánh giá và giám sát. Trong Phiếu A phụ trách góc đo lường kỹ thuật, đặc biệt metric offline ở A2/Câu 1.3 và cách diễn giải kết quả ở A3. Trong Phase 3 phụ trách đánh giá S8, thiết kế monitor mới và ghi nhận bằng chứng/giới hạn trong Phiếu C, đặc biệt C1, C8, C11 và C12. File liên quan: `lab10/monitors.py`, `templates/form-a-criteria.md`, `templates/form-c-incident.md`.

### Đóng góp cụ thể

- Bổ sung `protected_refund_escalation_rate` vào `MONITORS` để đo tỷ lệ lượt có escalation do approval không hợp lệ hoặc sắp vượt hạn mức hoàn tự động theo khách hàng; không dựa vào nhãn đúng/sai hay nội dung ticket.
- Đối chiếu kết quả base và S8 sau sửa: monitor mới thay đổi từ 0.0 lên 0.04 trên S8 (5/125), trong khi regression đạt 13/13 và các kiểm tra visible, criteria đạt.
- Ghi nhận giới hạn tự chấm: grade `R-S8-grade-20261119-192650-5f5d87` vẫn FAIL integrity do các tệp S1–S7 được khóa không có trong repo; không coi kết quả visible là xác nhận grade toàn phần. Cùng với chi phí phân khúc order không xác minh được 10.200đ/ticket, đây là căn cứ giữ quyết định v2 ở trạng thái “Cải tiến thêm”, chưa mở pilot thật.

### Bằng chứng

Phiếu A A2/Câu 1.3 ghi metric offline cho quyết định `file_carrier_fault` theo từng kiện và A3/Câu 1.5 ghi cách đọc khoảng tin cậy; Phase 3 có commit `f49ef54`, mã lần chạy `R-S8-grade-20261119-192650-5f5d87` và report tại `submission/runs/grade-report.md`. Kết quả monitor được ghi ở C8, checklist chất lượng ở C11 và quyết định ở C12; `protected_refund_escalation_rate` sáng từ 0.0 (base) lên 0.04 (S8 after).

### Exit ticket

Học được rằng metric vận hành hữu ích cần dựa trên sự kiện thực tế của guard, không dựa vào nhãn của bộ kiểm thử, và phải có khả năng phân biệt được sự cố với bộ nền. Chưa chắc monitor hiện tại có phát hiện được việc approval bị thu hồi sau bước kiểm tra nhưng trước lúc ghi; cần cơ chế tiêu thụ approval nguyên tử ở write boundary và kiểm chứng thêm trước Gate 2.

## NguyenMinhNhan-2A202603723

### Phần việc phụ trách

Gate Engineer phụ trách guards: trong Phiếu A phối hợp rà soát các tiêu chí an toàn và ranh giới đầu ra để chuyển thành điều kiện kiểm soát kỹ thuật; trong phần thực thi phụ trách cổng trước thao tác ghi, đặc biệt G1 xác minh nguồn dữ liệu/quyền hoàn và G3 giới hạn dữ liệu gửi hãng. File liên quan: `lab10/guards_round1.py`, `lab10/guards.py`, `config/switches.json`; Phiếu A A4, Phiếu B B7.1–B7.3 và Phiếu C C7.

### Đóng góp cụ thể

- Thiết kế và triển khai cổng G1 để đối chiếu dữ liệu nguồn sự thật, approval và ledger trước khi hoàn tiền hoặc ghi lỗi hãng; dữ liệu thiếu hoặc approval không hợp lệ được chuyển người duyệt.
- Thiết kế và triển khai cổng G3 theo allowlist `order_id`, `parcel_id`, `district`, `delay_days`, loại `customer_note` và `recipient_contact` khỏi payload gửi hãng.
- Trong Phase 3, bổ sung kiểm tra tổng hoàn tự động theo khách hàng trong ngày và chuyển ticket có order không xác minh được cho người xử lý trước LLM; regression đạt 13/13.
- Đối chiếu các giới hạn an toàn ở Phiếu A A4 với nơi thực thi: không hoàn vượt quyền/thiếu approval hợp lệ và không gửi dữ liệu ngoài allowlist cho hãng.

### Bằng chứng

Phiếu A A4 ghi ranh giới hoàn tiền và payload gửi hãng; Phiếu B B7.1–B7.3 ghi các cổng G1/G3 và kiểm thử behavioral; Phiếu C C7 ghi customer-cap và `pre_guard`; report `submission/runs/grade-report.md` ghi regression 13/13, visible S8 đạt và không có hoàn sai/lỗi hãng oan sau sửa. Mã lần chạy: `R-S8-grade-20261119-192650-5f5d87`.

### Exit ticket

Học được rằng kiểm tra riêng từng khoản hoàn không bảo đảm an toàn nếu giới hạn được tính theo tổng nhiều order của cùng khách; guard phải kiểm tra ngay tại ranh giới trước khi ghi. Rủi ro còn lại là approval có thể bị thu hồi sau bước kiểm tra nhưng trước lúc ghi nếu hệ thống không hỗ trợ tiêu thụ nguyên tử.

## BuiNgocHung-2A202603770

### Phần việc phụ trách

Sản phẩm và kinh doanh, người cầm bút chính Phiếu A: điều phối mục tiêu cấp hệ thống, chốt tiêu chí/ngưỡng tiền, chi phí/ROI, phạm vi pilot và ký quyết định Gate 1. File liên quan: `templates/form-a-criteria.md`, `config/acceptance_criteria.json`, `config/operating_gates.json`; Phiếu A mục A1, A4–A5, Phiếu B mục B8 và Phiếu C mục C12.

### Đóng góp cụ thể

- Đặt các ngưỡng kinh doanh và an toàn đã ký: chi phí tối đa 7.000đ/ticket, ROI tối thiểu 0,4, không chấp nhận hoàn sai/lỗi hãng/PII; giới hạn phạm vi tự động ở HN/HCM.
- Điều phối mục tiêu kinh doanh và rà soát tiêu chí theo các bên chịu ảnh hưởng; chốt hành động tương ứng khi ngưỡng an toàn, chất lượng hoặc vận hành không đạt.
- Đối chiếu kết quả theo phân khúc thay vì chỉ nhìn trung bình: phân khúc `?` còn 10.200đ/ticket, cao hơn mức làm tay 10.000đ, dù tổng chi phí bộ nền sau sửa là 5.538đ/ticket và ROI 0,81.
- Ghi nhận quyết định v1 “Thu hẹp” và v2 “Cải tiến thêm/hold”; không mở pilot thật khi còn vướng chi phí phân khúc và kết quả tự kiểm tra integrity.

### Bằng chứng

Phiếu A A1 ghi mục tiêu hệ thống và các bên liên quan; A4–A5 ghi tiêu chí cùng người ký `BuiNgocHung-2A202603770`; Phiếu B B8 ghi quyết định v1 và Phiếu C C12 ghi quyết định v2. Report `submission/runs/grade-report.md` ghi chi phí bộ nền 5.538đ/ROI 0,81 và phân khúc `?` 10.200đ/ticket. Mã lần chạy: `R-S8-grade-20261119-192650-5f5d87`.

### Exit ticket

Học được rằng kết quả trung bình đạt ngưỡng không đủ để quyết định mở rộng nếu một phân khúc cụ thể vẫn đắt hơn làm tay. Chưa thể kết luận cho pilot khi tự kiểm tra integrity còn FAIL và chưa có hidden suite; cần xử lý hai khoảng trống này trước Gate 2.

## TranCanhHung-2A202603759

### Phần việc phụ trách

Vận hành và pháp lý: trong Phiếu A phụ trách góc nhìn mục tiêu của stakeholder và telemetry production; đồng thời phụ trách PIC/runbook, năng lực người duyệt, SLA, điều kiện dừng và bảo vệ dữ liệu bên thứ ba. File liên quan: `templates/form-a-criteria.md`, `config/operating_gates.json`, `config/switches.json`; Phiếu A A1/Câu 1.2 và A2/Câu 1.4, Phiếu B B7.5–B7.6 và Phiếu C C11.

### Đóng góp cụ thể

- Ghi quy trình vận hành với PIC `NV-TUNG`, người duyệt `NV-HANH`, một reviewer với công suất 6 ca/giờ, SLA tối đa 60 phút, kênh cảnh báo và điều kiện dừng.
- Đặt yêu cầu pháp lý chặn `customer_note` và `recipient_contact` gửi cho bên thứ ba, đồng thời chỉ cho phép ghi lỗi hãng khi tracking có nguyên nhân đã ghi nhận.
- Bổ sung runbook xử lý sự cố/tuần đầu trong C11; ghi rõ các việc còn thiếu trước khi chạy thật: fallback LLM vẫn fail-open, cảnh báo Slack thủ công và chưa định danh reviewer dự phòng.
- Đóng góp góc nhìn của kế toán đối soát và trưởng ca trong A1/Câu 1.2; xác định telemetry production ở A2/Câu 1.4 dựa trên khiếu nại/đối soát, không dùng gold label.

### Bằng chứng

Phiếu A A1/Câu 1.2 ghi nhu cầu của kế toán và trưởng ca; A2/Câu 1.4 ghi telemetry theo ca khiếu nại/đối soát. Bằng chứng vận hành nằm trong `config/operating_gates.json` mục `operations`/`legal`, Phiếu B B7.5–B7.6 và Phiếu C C11; report `submission/runs/grade-report.md` ghi thời gian chờ tối đa S8 là 1 phút, không có hàng đợi ùn sau sửa. Mã lần chạy: `R-S8-grade-20261119-192650-5f5d87`.

### Exit ticket

Học được rằng có ngưỡng SLA và kênh cảnh báo trong cấu hình chưa đồng nghĩa vận hành đã sẵn sàng nếu cảnh báo vẫn thủ công và chưa có người dự phòng cụ thể. Trước pilot thật cần chỉ định reviewer dự phòng, xác nhận quy trình dừng và chuyển fallback của LLM sang fail-closed.
