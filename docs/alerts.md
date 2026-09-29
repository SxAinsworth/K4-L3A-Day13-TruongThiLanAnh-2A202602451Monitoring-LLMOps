# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: High user-visible error rate
- Severity: critical
- Duration: 5 phút
- Kênh thông báo: Slack `#llmops-alerts`
- SLI/SLO liên quan: tỷ lệ request thành công của SLO 99.5%.
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` liên tục 5 phút.
- Ảnh hưởng tới người dùng: request `/chat` thất bại hoặc không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên: xác nhận time range/error breakdown trên dashboard; lọc `request_failed` trong log và lấy `correlation_id`; mở trace cùng ID để tìm child observation lỗi.
- Mitigation tạm thời: rollback prompt/config mới nhất, tắt incident flag và giảm tải nếu lỗi vẫn tiếp diễn.
- Owner: `api-oncall`

## Alert 2

- Tên: Slow response tail latency
- Severity: warning
- Duration: 10 phút
- Kênh thông báo: Slack `#llmops-alerts`
- SLI/SLO liên quan: request tốt phải hoàn tất trong 3000 ms.
- Điều kiện và thời gian duy trì: `latency_p95_ms > 3000` liên tục 10 phút.
- Ảnh hưởng tới người dùng: ít nhất 5% request có trải nghiệm phản hồi chậm.
- Ba bước kiểm tra đầu tiên: kiểm tra P95/P99 và TTFT; lấy correlation ID của request chậm; so sánh thời lượng retriever và generation trong waterfall.
- Mitigation tạm thời: giảm concurrency, dùng fallback retrieval/prompt ổn định hoặc rollback thay đổi làm tăng latency.
- Owner: `api-oncall`

## Alert 3

- Tên: Low answer quality
- Severity: warning
- Duration: 15 phút
- Kênh thông báo: Slack `#llmops-alerts`
- SLI/SLO liên quan: quality proxy trung bình tối thiểu 0.75.
- Điều kiện và thời gian duy trì: `quality_score_avg < 0.75` liên tục 15 phút.
- Ảnh hưởng tới người dùng: câu trả lời thiếu ngữ cảnh hoặc không đáp ứng câu hỏi.
- Ba bước kiểm tra đầu tiên: xác nhận quality giảm trên cùng time range; kiểm tra retrieval success; đối chiếu prompt name/version/label trong trace.
- Mitigation tạm thời: rollback label `production` về prompt version ổn định và kiểm tra lại retrieval corpus.
- Owner: `llm-oncall`
