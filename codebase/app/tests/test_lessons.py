"""Content structure and source mapping, not live model quality evaluation."""
import json
import re
import unittest
from collections import Counter
from pathlib import Path

from lessons import load_lessons

ROOT = Path(__file__).resolve().parents[1]


class LessonContentTests(unittest.TestCase):
    def setUp(self):
        self.lessons = load_lessons(ROOT / "lessons.sample.json")

    def test_six_substantial_lessons_in_three_days(self):
        self.assertEqual(len(self.lessons), 6)
        self.assertEqual(sorted(Counter(x["day"] for x in self.lessons).values()), [2, 2, 2])
        self.assertEqual(len({x["id"] for x in self.lessons}), 6)
        for lesson in self.lessons:
            with self.subTest(lesson=lesson["id"]):
                words = sum(len(s["text"].split()) for s in lesson["sources"])
                self.assertTrue(600 <= words <= 900, words)
                self.assertTrue(lesson["sample"])
                self.assertIn("Không phải học liệu chính thức VLearn", lesson["subtitle"])
                self.assertGreaterEqual(len(lesson["sources"]), 6)
                body = "\n".join(s["title"] + "\n" + s["text"] for s in lesson["sources"]).lower()
                self.assertIn("ví dụ", body)
                self.assertIn("tóm tắt", body)
                self.assertTrue(any("thực hành" in s["title"].lower() for s in lesson["sources"]))

    def test_sources_have_unique_stable_anchors_and_supported_markdown(self):
        ids = set()
        for lesson in self.lessons:
            markdown = (ROOT / lesson["markdown"]).read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r"^# ", markdown, re.M)), 1)
            self.assertNotRegex(markdown, r"(?m)^(###|```|\|)|<script")
            for source in lesson["sources"]:
                self.assertNotIn(source["id"], ids)
                ids.add(source["id"])
                self.assertTrue(source["text"].strip())
                self.assertIn("{#" + source["anchor"] + "}", markdown)
                self.assertEqual(source["locator"], lesson["markdown"] + "#" + source["anchor"])
        by_id = {x["id"]: x for x in self.lessons}
        self.assertTrue({"kiem-chung", "thieu-can-cu"} <= {s["anchor"] for s in by_id["demo-grounding"]["sources"]})
        self.assertTrue({"hoi-tiep", "kiem-tra"} <= {s["anchor"] for s in by_id["demo-dialogue"]["sources"]})

    def test_twelve_scenarios_reference_real_lesson_sources(self):
        cases = json.loads((ROOT / "lesson-scenarios.json").read_text(encoding="utf-8"))
        by_id = {x["id"]: x for x in self.lessons}
        self.assertEqual([c["id"] for c in cases], [f"L{i:02}" for i in range(1, 13)])
        self.assertEqual({c["lesson_id"] for c in cases[:6]}, set(by_id))
        self.assertEqual(Counter(c["decision"] for c in cases), {"answer": 8, "clarify": 1, "abstain": 3})
        for case in cases:
            self.assertTrue(case["question"] and case["persona"] and case["criteria"])
            anchors = {s["anchor"] for s in by_id[case["lesson_id"]]["sources"]}
            self.assertTrue(set(case["anchors"]) <= anchors)
            if case["decision"] == "answer":
                self.assertTrue(case["anchors"])
        self.assertEqual(cases[6]["question"], cases[7]["question"])
        self.assertNotEqual(cases[6]["persona"], cases[7]["persona"])
