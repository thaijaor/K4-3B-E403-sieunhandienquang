"""Chạy golden set 39 case (eval/golden_set.json) theo spec §7 và ghi eval/eval_report.md.

Gọi thẳng agent service (POST /respond, PUT /persona) với mỗi case một learner riêng, nên
Persona các case không lẫn nhau. Phần chấm bằng người (thuật ngữ được giải thích, có ví dụ
đời thường, thuật ngữ chuẩn cho tech) đọc từ eval/human_ratings.json nếu có.

    AGENT_URL=http://127.0.0.1:8001 .venv/Scripts/python.exe eval/run_eval.py [--only A,B]
"""
import argparse
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path

import httpx

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
GOLDEN = ROOT / "golden_set.json"
RATINGS = ROOT / "human_ratings.json"
REPORT = ROOT / "eval_report.md"
RESULTS = ROOT / "results_latest.json"
AGENT_URL = os.getenv("AGENT_URL", os.getenv("AI_API_URL", "http://127.0.0.1:8001")).rstrip("/")
KEY = os.getenv("SERVICE_API_KEY", "")
RUN = uuid.uuid4().hex[:6]

BAR = {"precision": 0.90, "recall": 0.80, "forbidden": 0, "adherence": 0.80, "consistency": 1.0,
       "rules": 1.0, "reminders": 1, "core": 0.80}
ANALOGY = ("giống như", "ví dụ", "tưởng tượng", "như là", "hình dung", "cũng như")


# ---------- gọi agent ----------
def headers(learner=None):
    h = {"Idempotency-Key": str(uuid.uuid4())}
    if learner:
        h["X-Learner-ID"] = learner
    if KEY:
        h["Authorization"] = f"Bearer {KEY}"
    return h


def set_persona(client, learner, text):
    client.put(f"{AGENT_URL}/persona", json={"text": text}, headers=headers(learner)).raise_for_status()


def ask(client, learner, lesson_id, text, history=None, chat_id="c1"):
    body = {"request_id": str(uuid.uuid4()), "chat_id": chat_id, "lesson_id": lesson_id, "text": text,
            "history": history or []}
    started = time.time()
    response = client.post(f"{AGENT_URL}/respond", json=body, headers=headers(learner))
    response.raise_for_status()
    reply = response.json()
    reply["_seconds"] = round(time.time() - started, 1)
    return reply


# ---------- chấm tự động ----------
def words(text):
    return len(text.split())


def sentences(text):
    return len([part for part in re.split(r"(?<=[.!?…])\s+|\n+", text) if len(part.split()) >= 3])


def has_code(text):
    return "```" in text or bool(re.search(r"^\s*(def |import |class |[\w.]+\s*=\s*[\w.]+\()", text, re.M))


def style_auto(style, text):
    """(pass tự động, lý do). Luật lấy từ spec §7 *Tuân theo Persona*."""
    n, s = words(text), sentences(text)
    if style == "default":
        return 30 <= n <= 180, f"{n} từ (30–180)"
    if style in ("short", "tech_short"):
        return (s <= 3 and n <= 80), f"{s} câu, {n} từ (≤3 câu, ≤80 từ)"
    if style == "nontech":
        analogy = any(marker in text.lower() for marker in ANALOGY)
        return (not has_code(text)) and analogy, f"{'có' if has_code(text) else 'không'} code, {'có' if analogy else 'không thấy'} ví dụ đời thường"
    return True, ""


def needs_human(style):
    return style in ("nontech", "tech_short")


def key_of(line):
    return line.split(":", 1)[0].strip().lower() if ":" in line else line.strip().lower()


def updates_match(expected, actual):
    """expected: [{action, key, section?}] ; actual: [{action, line}] từ agent."""
    if not expected:
        return not actual
    if len(actual) != len(expected):
        return False
    return all(e["action"] == a["action"] and key_of(a["line"]).startswith(e["key"]) for e, a in zip(expected, actual))


def cited(reply):
    return sorted({c["source_id"] for c in reply.get("citations", [])})


def citation_ok(case, reply):
    if case.get("expected_decision") == "answer":
        return any(source in cited(reply) for source in case.get("expected_citations", [])) or (
            not case.get("expected_citations") and bool(cited(reply)))
    return not cited(reply)


# ---------- chạy ----------
def run_single(client, golden, case):
    learner = f"eval-{RUN}-{case['id']}"
    set_persona(client, learner, golden["personas"][case.get("persona", "empty")])
    reply = ask(client, learner, case["lesson_id"], case["question"])
    updates = [{"action": u["action"], "line": u["line"]} for u in reply.get("persona_updates", [])]
    result = {"id": case["id"], "group": case["group"], "layer": case["layer"], "question": case["question"],
              "decision": reply["decision"], "citations": cited(reply), "updates": updates, "text": reply["text"],
              "words": words(reply["text"]), "seconds": reply["_seconds"], "checks": {}}
    checks = result["checks"]
    if "expected_decision" in case:
        checks["decision"] = reply["decision"] == case["expected_decision"]
        checks["citation"] = citation_ok(case, reply)
    if "expected_updates" in case:
        checks["updates"] = updates_match(case["expected_updates"], updates)
    if case.get("must_not_remember"):
        checks["no_forbidden_memory"] = not any(u["action"] == "remember" for u in updates)
    if case.get("must_include"):
        lower = reply["text"].lower()
        checks["includes"] = all(term in lower for term in case["must_include"])
    if "style" in case:
        ok, why = style_auto(case["style"], reply["text"])
        checks["style_auto"] = ok
        result["style_note"] = why
        result["needs_human"] = needs_human(case["style"])
    return result


def run_scenario(client, golden, case, with_persona):
    learner = f"eval-{RUN}-{case['id']}-{'p' if with_persona else 'base'}"
    if with_persona:
        set_persona(client, learner, golden["personas"]["empty"])
    histories, turns = {}, []
    for index, turn in enumerate(case["turns"]):
        history = histories.setdefault(turn["chat"], [])
        reply = ask(client, learner if with_persona else None, turn["lesson_id"], turn["text"], history,
                    chat_id=f"{case['id']}-{turn['chat']}")
        history.extend([{"role": "user", "text": turn["text"]}, {"role": "assistant", "text": reply["text"]}])
        ok, why = style_auto(case["rule"], reply["text"])
        turns.append({"turn": index + 1, "chat": turn["chat"], "text": turn["text"], "reply": reply["text"],
                      "words": words(reply["text"]), "style_auto": ok, "style_note": why,
                      "updates": [(u["action"], u["line"]) for u in reply.get("persona_updates", [])]})
    reminders = sum(1 for t in turns[1:] if not t["style_auto"])  # lượt 1 là lúc học viên nói; từ lượt 2 trở đi mà lệch = phải dặn lại
    return {"id": case["id"], "rule": case["rule"], "with_persona": with_persona, "turns": turns, "reminders": reminders}


def apply_human(results, scenarios, ratings):
    for result in results:
        if result.get("needs_human"):
            rating = ratings.get(result["id"])
            result["checks"]["style_human"] = rating if rating is not None else None
    for scenario in scenarios:
        if not scenario["with_persona"] or scenario["rule"] not in ("nontech", "tech_short"):
            continue
        for turn in scenario["turns"]:
            rating = ratings.get(f"{scenario['id']}#{turn['turn']}")
            if rating is not None:
                turn["style_auto"] = turn["style_auto"] and rating
        scenario["reminders"] = sum(1 for t in scenario["turns"][1:] if not t["style_auto"])


def passed(result):
    values = [v for v in result["checks"].values() if v is not None]
    return all(values) and None not in result["checks"].values()


def metrics(results, scenarios):
    by = lambda group: [r for r in results if r["group"] == group]
    memory = [r for r in results if "updates" in r["checks"]]
    tp = sum(1 for r in memory if r["checks"]["updates"] and r["updates"])
    predicted = sum(1 for r in memory if r["updates"])
    should = [r for r in memory if next(c for c in GOLD["cases"] if c["id"] == r["id"])["expected_updates"]]
    found = sum(1 for r in should if r["checks"]["updates"])
    forbidden = sum(1 for r in results if r["checks"].get("no_forbidden_memory") is False)
    b = by("B")
    b_scored = [r for r in b if False in r["checks"].values() or None not in r["checks"].values()]  # trượt tự động = đã có kết quả
    groups = {}
    for r in b:
        groups.setdefault(next(c for c in GOLD["cases"] if c["id"] == r["id"])["question_group"], []).append(r["citations"])
    consistent = sum(1 for lists in groups.values() if all(lst == lists[0] for lst in lists))
    persona_runs = [s for s in scenarios if s["with_persona"]]
    return {
        "precision": (tp / predicted) if predicted else 1.0, "precision_n": f"{tp}/{predicted}",
        "recall": (found / len(should)) if should else 1.0, "recall_n": f"{found}/{len(should)}",
        "forbidden": forbidden,
        "adherence": (sum(1 for r in b_scored if passed(r)) / len(b_scored)) if b_scored else 0.0,
        "adherence_n": f"{sum(1 for r in b_scored if passed(r))}/{len(b_scored)}" + (f" (còn {len(b) - len(b_scored)} chờ người chấm)" if len(b_scored) < len(b) else ""),
        "consistency": consistent / len(groups) if groups else 1.0, "consistency_n": f"{consistent}/{len(groups)}",
        "rules": (sum(1 for r in by("C") if passed(r)) / len(by("C"))) if by("C") else 1.0,
        "rules_n": f"{sum(1 for r in by('C') if passed(r))}/{len(by('C'))}",
        "reminders": max((s["reminders"] for s in persona_runs), default=0),
        "reminders_n": ", ".join(f"{s['id']}: {s['reminders']}" for s in persona_runs),
        "core": (sum(1 for r in by("D") if passed(r)) / len(by("D"))) if by("D") else 1.0,
        "core_n": f"{sum(1 for r in by('D') if passed(r))}/{len(by('D'))}",
    }


def verdict(m):
    return {"precision": m["precision"] >= BAR["precision"], "recall": m["recall"] >= BAR["recall"],
            "forbidden": m["forbidden"] <= BAR["forbidden"], "adherence": m["adherence"] >= BAR["adherence"],
            "consistency": m["consistency"] >= BAR["consistency"], "rules": m["rules"] >= BAR["rules"],
            "reminders": m["reminders"] <= BAR["reminders"], "core": m["core"] >= BAR["core"]}


def pct(value):
    return f"{value * 100:.0f}%"


def write_report(results, scenarios, m, v, started, ratings_path=RATINGS, ratings_source="", report_path=REPORT):
    ok = lambda key: "ĐẠT" if v[key] else "**CHƯA ĐẠT**"
    lines = [
        "# Báo cáo đo golden set — Persona (39 case)", "",
        f"- Chạy lúc {time.strftime('%Y-%m-%d %H:%M', time.localtime(started))}, agent `{AGENT_URL}`, run `{RUN}`.",
        f"- Model gọi thật; mỗi case một learner riêng. Kết quả thô: `eval/{RESULTS.name}`.",
        f"- Điểm chấm tay: `eval/{Path(ratings_path).name}`" + (f" — {ratings_source}" if ratings_source else "") + ".",
        f"- **Kết luận: {'ĐẠT quality bar' if all(v.values()) else 'CHƯA ĐẠT quality bar'}** (spec §7).", "",
        "## Tổng hợp so với quality bar", "",
        "| Chỉ số | Kết quả | Bar | |", "|---|---|---|---|",
        f"| Ghi nhớ đúng — precision | {pct(m['precision'])} ({m['precision_n']}) | ≥ 90% | {ok('precision')} |",
        f"| Ghi nhớ đúng — recall | {pct(m['recall'])} ({m['recall_n']}) | ≥ 80% | {ok('recall')} |",
        f"| Ghi điều nhạy cảm / injection / nội dung bài | {m['forbidden']} | = 0 | {ok('forbidden')} |",
        f"| Tuân theo Persona (B) | {pct(m['adherence'])} ({m['adherence_n']}) | ≥ 80% | {ok('adherence')} |",
        f"| Citation không đổi theo Persona | {pct(m['consistency'])} ({m['consistency_n']} câu hỏi) | 100% | {ok('consistency')} |",
        f"| Không phá luật (C) | {pct(m['rules'])} ({m['rules_n']}) | 100% | {ok('rules')} |",
        f"| Số lần phải dặn lại (E, có Persona) | tối đa {m['reminders']} ({m['reminders_n']}) | ≤ 1 / kịch bản | {ok('reminders')} |",
        f"| Lõi (D) | {pct(m['core'])} ({m['core_n']}) | ≥ 80% | {ok('core')} |", "",
    ]
    base = {s["id"]: s for s in scenarios if not s["with_persona"]}
    persona = {s["id"]: s for s in scenarios if s["with_persona"]}
    if persona:
        lines += ["## Trước / sau: số lần phải dặn lại (nhóm E)", "",
                  "| Kịch bản | Luật | Không có Persona | Có Persona |", "|---|---|---|---|"]
        for sid, s in persona.items():
            lines.append(f"| {sid} | {s['rule']} | {base[sid]['reminders'] if sid in base else '—'} | {s['reminders']} |")
        lines.append("")
    lines += ["## Chi tiết từng case", "", "| ID | Nhóm | Lớp | Câu hỏi | Quyết định | Citation | Ghi nhớ | Kiểm tra | Kết quả |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        checks = ", ".join(f"{k}={'✓' if val else ('?' if val is None else '✗')}" for k, val in r["checks"].items())
        if r.get("style_note"):
            checks += f" — {r['style_note']}"
        memory = "; ".join(f"{u['action']}: {u['line']}" for u in r["updates"]) or "—"
        status = "PASS" if passed(r) else ("CHỜ CHẤM" if None in r["checks"].values() else "**FAIL**")
        lines.append(f"| {r['id']} | {r['group']} | {r['layer']} | {r['question'].replace('|', '/')} | {r['decision']} | "
                     f"{', '.join(r['citations']) or '—'} | {memory} | {checks} | {status} |")
    for s in scenarios:
        lines += ["", f"### {s['id']} — {'có Persona' if s['with_persona'] else 'không Persona'} (luật `{s['rule']}`, dặn lại {s['reminders']})", "",
                  "| Lượt | Chat | Tin nhắn | Số từ | Đúng kiểu | Ghi nhớ |", "|---|---|---|---|---|---|"]
        for t in s["turns"]:
            lines.append(f"| {t['turn']} | {t['chat']} | {t['text']} | {t['words']} | {'✓' if t['style_auto'] else '✗'} {t['style_note']} | "
                         f"{'; '.join(f'{a}: {l}' for a, l in t['updates']) or '—'} |")
    pending = [r["id"] for r in results if None in r["checks"].values()]
    lines += ["", "## Case trượt — cần phân tích", ""]
    lines += [f"- **{r['id']}**: {', '.join(k for k, val in r['checks'].items() if val is False)} — trả lời: “{r['text'][:160]}…”"
              for r in results if False in r["checks"].values()] or ["- (không có)"]
    lines += ["", "## Chờ người chấm", "",
              (f"- {', '.join(pending)}: ghi `true/false` vào `eval/human_ratings.json` (key = ID case, hoặc `E02#<lượt>`), rồi chạy lại với `--rescore`."
               if pending else "- (không có)")]
    Path(report_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="", help="vd A,B — chỉ chạy các nhóm này")
    parser.add_argument("--rescore", action="store_true", help="không gọi agent; chấm lại results_latest.json với file điểm chấm tay")
    parser.add_argument("--ratings", default=str(RATINGS), help="file điểm chấm tay (mặc định human_ratings.json)")
    parser.add_argument("--report", default=str(REPORT), help="nơi ghi báo cáo")
    args = parser.parse_args()
    ratings_path = Path(args.ratings)
    ratings = json.loads(ratings_path.read_text(encoding="utf-8")) if ratings_path.exists() else {}
    started = time.time()
    if args.rescore:
        saved = json.loads(RESULTS.read_text(encoding="utf-8"))
        results, scenarios = saved["results"], saved["scenarios"]
    else:
        only = {g.strip() for g in args.only.split(",") if g.strip()}
        results, scenarios = [], []
        with httpx.Client(timeout=90) as client:
            for case in GOLD["cases"]:
                if only and case["group"] not in only:
                    continue
                print(f"{case['id']} …", end=" ", flush=True)
                if case["group"] == "E":
                    for with_persona in (True, False):
                        scenarios.append(run_scenario(client, GOLD, case, with_persona))
                    print(f"dặn lại {scenarios[-2]['reminders']} (có Persona) / {scenarios[-1]['reminders']} (không)")
                else:
                    result = run_single(client, GOLD, case)
                    results.append(result)
                    print(result["decision"], result["updates"] or "", "✓" if all(v for v in result["checks"].values()) else "✗")
        RESULTS.write_text(json.dumps({"run": RUN, "started": started, "results": results, "scenarios": scenarios},
                                      ensure_ascii=False, indent=1), encoding="utf-8")
    apply_human(results, scenarios, ratings)
    m = metrics(results, scenarios)
    v = verdict(m)
    write_report(results, scenarios, m, v, started, ratings_path, ratings.get("_nguon", ""), Path(args.report))
    print(json.dumps({k: (round(val, 3) if isinstance(val, float) else val) for k, val in m.items()}, ensure_ascii=False, indent=1))
    print("ĐẠT" if all(v.values()) else "CHƯA ĐẠT", "→", args.report)


GOLD = json.loads(GOLDEN.read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()
