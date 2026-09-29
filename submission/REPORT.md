# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.jpg`.

## 1. Thông tin học viên

- **Họ và tên:** Trương Thị Lan Anh
- **MSSV:** 2A202602451
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/SxAinsworth/K4-L3A-Day13-TruongThiLanAnh-2A202602451Monitoring-LLMOps
- **Commit SHA cuối:** `PENDING_FINAL_COMMIT` — cập nhật sau khi commit toàn bộ source, report và evidence.
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602451`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | [01-pytest.jpg](evidence/01-pytest.jpg) |
| Log validator | [02-log-validator.jpg](evidence/02-log-validator.jpg) |
| Dashboard validator | [03-dashboard-validator.jpg](evidence/03-dashboard-validator.jpg) |
| Structured log | [04-structured-log.jpg](evidence/04-structured-log.jpg) |
| PII redaction | [05-pii-redaction.jpg](evidence/05-pii-redaction.jpg) |
| Trace list | [06-trace-list.jpg](evidence/06-trace-list.jpg) |
| Trace waterfall | [07-trace-waterfall.jpg](evidence/07-trace-waterfall.jpg) |
| Trace metadata | [08-trace-metadata.jpg](evidence/08-trace-metadata.jpg) |
| Prompt versions | [09-prompt-versions.jpg](evidence/09-prompt-versions.jpg) |
| Prompt rollback | [10-prompt-rollback.jpg](evidence/10-prompt-rollback.jpg) |
| Dashboard runtime | [11-dashboard-overview.jpg](evidence/11-dashboard-overview.jpg) |
| Incident metric | [12-incident-metric.jpg](evidence/12-incident-metric.jpg) |
| Incident log | [13-incident-log.jpg](evidence/13-incident-log.jpg) |
| Incident trace | [14-incident-trace.jpg](evidence/14-incident-trace.jpg) |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | Không lưu output baseline trước khi sửa | `100/100` | 91 records hợp lệ, 43 correlation IDs |
| `validate_dashboard.py` | `6/6` contract có sẵn | `6/6` | Có thêm dashboard runtime tại `/dashboard` |
| `pytest` | Không lưu riêng | `24 passed` | Chạy trên working tree sau CP3 |
| Số traces hợp lệ | `0` trong project cá nhân | `≥11` cây trace hoàn chỉnh | Có root, retriever và generation |
| Số PII leak | Chưa đo | `0` | Validator quét toàn bộ `data/logs.jsonl` |
| Latency P95 / TTFT P95 | Không lưu riêng | Sau mitigation: `≤154 ms / 50 ms` | Trong incident: `3897 ms / 50 ms` |
| Retrieval success rate | Chưa đo | `100%` | Challenge có 5/5 retrieval thành công dù bị chậm |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** `CorrelationIdMiddleware` xóa contextvars ở đầu mỗi request, nhận `x-request-id` nếu có hoặc sinh `req-<8-hex>`, bind ID vào structlog, lưu vào `request.state`, rồi trả lại qua header `x-request-id`. Header `x-response-time-ms` ghi thời gian xử lý HTTP.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash`, `session_id`, `feature`, `model`, `env`, timestamp, level và event. Event `response_sent` còn có latency, TTFT, token, cost, quality và trạng thái retrieval.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` được đăng ký trước `JsonlFileProcessor` và `JSONRenderer`. Processor duyệt đệ quy mọi string trong dict/list/tuple; `user_id` được SHA-256 và rút gọn còn 12 ký tự trước khi bind.
- **Cách kiểm chứng kết quả:** test bao phủ email, điện thoại Việt Nam, CCCD và ba định dạng thẻ; workload chứa PII giả được ghi thành `[REDACTED_*]`. Validator cuối phát hiện `0` PII leak và đạt `100/100`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** dùng key trong `.env` cục bộ của project `day13-k4-l3a-2A202602451`, tự chạy `load_test.py` và truy vấn observation trong chính project. Kết quả có ít nhất 11 trace tree hoàn chỉnh.
- **Cấu trúc root/retrieval/generation observations:** root agent `lab-agent-run`; child retriever `knowledge-retrieval`; child generation `fake-llm-generation`. Generation ghi model, managed prompt, input/output/total token và total cost nhưng đặt raw input/output là `None`.
- **Cách nối trace với log:** cùng `correlation_id` được bind vào log context và trace metadata. Ví dụ incident dùng `req-5b00f9eb` để tìm trace `8a0afeeb5f8272441f0dfbdbb8474b83`.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** version 1, labels `baseline` và `production` sau rollback.
- **Version/label candidate:** version 2, label `candidate`.
- **Trace ID của mỗi version:** baseline v1 `f1ae608e43059b73313194de04608484`; candidate v2 `5fdb425094252433520f50fe7e47a364`.
- **Cách promote và rollback `production`:** bỏ label `production` khỏi v1 và gắn vào v2, chạy request kiểm chứng, sau đó bỏ label khỏi v2 và gắn lại vào v1. Trạng thái cuối đã kiểm tra: `production` trỏ về version 1.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** dashboard local tại `/dashboard`, đọc `data/logs.jsonl` trong 60 phút gần nhất và refresh mỗi 30 giây. Sáu panel gồm latency/TTFT, traffic, error/retrieval success, cost, token và quality; mỗi panel có đơn vị và threshold. Contract validator đạt `6/6`.
- **SLO và lý do chọn:** 99.5% request phải có `response_sent` trong tối đa 3000 ms trên cửa sổ 28 ngày. Ngưỡng này đo trực tiếp trải nghiệm người dùng và vẫn cho phép một error budget nhỏ để vận hành/thay đổi hệ thống.
- **Cách tính error budget:** `total_requests × (1 - 99.5/100)`. Với 10.000 request, budget là 50 request xấu trong 28 ngày, tương đương 0.5%.
- **Ba alert và runbook tương ứng:** error rate >2% trong 5 phút (`critical`, `api-oncall`); latency P95 >3000 ms trong 10 phút (`warning`, `api-oncall`); quality trung bình <0.75 trong 15 phút (`warning`, `llm-oncall`). Cả ba gửi Slack `#llmops-alerts` và có hướng dẫn metric → log → trace cùng mitigation tại [`docs/alerts.md`](../docs/alerts.md).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** `2026-09-29 09:06:12–09:06:27 UTC` (`16:06:12–16:06:27 Asia/Ho_Chi_Minh`).
- **Triệu chứng từ metrics:** panel Latency ghi nhận P50 `2654 ms`, P95/P99 `3897 ms`, vượt SLO P95 `3000 ms`. TTFT P95 vẫn `50 ms`, error breakdown rỗng và cả 5 request đều trả HTTP 200, nên sự cố nằm trước bước sinh token chứ không phải lỗi LLM.
- **Log line và correlation ID liên quan:** request `req-5b00f9eb` nhận lúc `09:06:12.523700Z`, trả `response_sent` lúc `09:06:16.871191Z` với `latency_ms=3897`, `ttft_ms=50`, `tool_name=retrieval`, `tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** trace `8a0afeeb5f8272441f0dfbdbb8474b83`. Root `lab-agent-run` mất `3900 ms`; child `knowledge-retrieval` mất `2503 ms`, trong khi `fake-llm-generation` chỉ mất `152 ms`. Cả ba observation có status `DEFAULT/ok` và hai child cùng trỏ về root.
- **Root cause:** retrieval bị tăng độ trễ (`rag_slow`). Retrieval vẫn thành công nhưng chiếm phần lớn thời gian xử lý, làm tail latency vượt SLO; generation và TTFT không bất thường.
- **Fix action:** tắt incident/fault injection để khôi phục retrieval rồi chạy lại cùng workload. Năm request sau mitigation có app latency `[152, 152, 154, 152, 152] ms`; giá trị lớn nhất `154 ms`, thấp hơn SLO `3000 ms`.
- **Preventive measure:** duy trì alert `latency_p95_ms > 3000` trong 10 phút; theo dõi riêng duration của retriever và generation; dùng timeout/circuit breaker cùng retrieval fallback; chạy regression load test trước khi phát hành thay đổi retrieval.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** không capture raw prompt/output trong observation. Trace chỉ giữ preview đã scrub, metadata vận hành, prompt version, usage và cost. Quyết định này vẫn đủ để debug nhưng giảm nguy cơ đưa PII lên dịch vụ quan sát bên ngoài.
- **Một lỗi/blocker đã gặp:** Langfuse Cloud đôi lúc timeout khi fetch prompt hoặc export span; khi prompt chưa tồn tại, metadata hiển thị `local-fallback` thay vì version managed.
- **Cách tìm nguyên nhân và xử lý:** kiểm tra `tracing_enabled`, `prompt_source`, name/label và API observation; tạo đúng `day13-chat` v1/v2, dùng cache prompt, flush client và truy vấn lại trace tree. Các batch timeout được chạy bổ sung, sau đó xác nhận có trên 10 cây trace hoàn chỉnh.
- **Cách hiểu luồng Metrics → Logs → Traces:** metrics phát hiện loại triệu chứng và time range; log thu hẹp xuống request qua `correlation_id`; trace cùng ID so sánh duration/status của từng child span; chênh lệch giữa retrieval và generation đưa ra root cause có bằng chứng.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** version/label giúp truy xuất chính xác thay đổi và rollback không cần sửa code; token/cost phát hiện tăng chi phí; SLO định nghĩa mức trải nghiệm chấp nhận được và error budget quyết định tốc độ thay đổi an toàn.
- **Điều quan trọng nhất đã học:** một metric bất thường chưa đủ kết luận nguyên nhân. Cần correlation ID và trace waterfall để phân biệt retrieval, LLM hay lớp HTTP gây ảnh hưởng.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** baseline CP0 không được lưu riêng trước khi sửa nên report ghi rõ là không có thay vì ước lượng. Fake LLM và local JSONL dashboard phù hợp phạm vi lab nhưng chưa đại diện đầy đủ cho throughput, sampling và retention của hệ thống production. Evidence `10` cần được thay bằng ảnh thể hiện trạng thái promote `production` sang v2 trước khi rollback về v1. Commit SHA sẽ được cập nhật sau khi tạo commit nộp bài cuối cùng.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thật hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
