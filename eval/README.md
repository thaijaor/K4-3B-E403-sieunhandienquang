# Eval — golden set Persona (39 case)

- `golden_set.json` — 39 case theo spec §7: A ghi nhớ (12) · B tuân theo Persona (9) · C không phá luật (5) · E kịch bản dặn lại (3) · D lõi (10). Mỗi case ghi nhóm, lớp chỗ khó, nguồn (`turn_id` chatlog hoặc "tự viết").
- `run_eval.py` — gọi agent thật (`POST /respond`, `PUT /persona`), mỗi case một learner riêng; ghi `eval_report.md` và `results_latest.json`.
- `human_ratings.json` — điểm người chấm cho phần không tự động được (B non-tech / tech, E02, E03): `{"B02": true, "E02#3": false, …}`. Chấm xong chạy `--rescore`, không gọi lại model.
- `eval_report_run<N>.md`, `results_run<N>.json` — bản lưu từng lượt. `*_cp3.*` — bộ 20 case và kết quả CP3 (trước Persona).
- `trace.jsonl` — trace từng lượt agent khi chạy thật.

```powershell
# agent đang chạy ở 8001 (hoặc đổi AGENT_URL)
$env:AGENT_URL="http://127.0.0.1:8001"; .\.venv\Scripts\python.exe eval\run_eval.py
.\.venv\Scripts\python.exe eval\run_eval.py --only A,C      # chạy một số nhóm
.\.venv\Scripts\python.exe eval\run_eval.py --rescore       # chấm lại với human_ratings.json
```
