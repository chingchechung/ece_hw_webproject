"""Synthetic-only v2 acceptance and single-choice membership cases."""
from copy import deepcopy
import json
from pathlib import Path


def fixture_v2(name="S01.json"):
    return json.loads((Path(__file__).parent / "fixtures/v2" / name).read_text(encoding="utf-8"))


def v2_contract_cases():
    cases = []

    def add(name, data, valid=False, filename="S01.json"):
        cases.append(dict(name="v2 " + name, data=data, valid=valid, kind="unit", filename=filename))

    def change(name, path, value, valid=False):
        data = fixture_v2()
        target = data
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        add(name, data, valid)

    add("four questions mixed choice counts", fixture_v2(), True)
    add("five questions mixed choice counts", fixture_v2("S02.json"), True, "S02.json")
    for count in (3, 4):
        for accepted in (["A"], ["B"], ["A", "C"], ["C", "B", "A"], ["D"], ["A", "B", "C", "D"]):
            data = fixture_v2()
            q = data["questions"][0]
            q["options"] = [f"Dummy option {label}" for label in "ABCD"[:count]]
            q["correctOptions"] = accepted
            add(f"{count} options {accepted}", data, all(label in "ABCD"[:count] for label in accepted))
    for accepted in ([], None, "A", 0, False, {}, [""], ["a"], [" A"], ["A "], ["AB"], ["E"], [None], [True], [1], [[]], [{}], ["A", "A"], ["B", "C", "B"], ["A", "B", "C", "D", "A"]):
        change(f"invalid accepted {accepted!r}", ["questions", 0, "correctOptions"], accepted)
    for value in (None, True, "2", 0, 1, 3, [], {}, 2.5):
        change(f"unsupported version {value!r}", ["schemaVersion"], value)
    for value in (2, 2.0):
        change(f"numeric version {value!r}", ["schemaVersion"], value, True)
    for key in ("correctOptions", "questionVideoUrl", "explanationVideoUrl", "options", "id"):
        data = fixture_v2()
        del data["questions"][1][key]
        add(f"missing {key}", data)
    for options in ([], ["A"], ["A", "B"], ["a"]*5, "ABC", None, {}, ["a", " ", "c"], ["a", False, "c"]):
        change(f"invalid options {options!r}", ["questions", 0, "options"], options)
    data = fixture_v2()
    data["questions"][0]["correctOption"] = "A"
    add("mixed answer fields", data)
    for name in ("S02.json", "../S01.json", "s01.json"):
        add(f"filename {name}", fixture_v2(), filename=name)
    change("duplicate question ID", ["questions", 1, "id"], "Q01")
    change("missing form URL", ["googleFormUrl"], "")
    change("missing video URL", ["questions", 0, "questionVideoUrl"], "")
    change("bad explanation URL", ["questions", 0, "explanationVideoUrl"], "https://evil.test/video")
    change("Unicode trim preserves option order", ["questions", 0, "options"], [" 第二 ", " 第一 ", " third "], True)
    return cases


def answer_cases():
    cases = []
    for option_count in (3, 4):
        for accepted in (["A"], ["A", "C"], ["A", "B", "C"]):
            question = {"options":["dummy"]*option_count, "correctOptions":accepted}
            for selected in ("A", "B", "C", "D", "E", "", ["A"], ["A", "C"], None, True, 0):
                expected = isinstance(selected, str) and selected in accepted and selected in "ABCD"[:option_count]
                cases.append({"question":deepcopy(question), "selected":selected, "expected":expected})
    legacy = {"options":["dummy"]*4, "correctOption":"B"}
    for selected in ("A", "B", "C", "D", ["B"], None):
        cases.append({"question":legacy, "selected":selected, "expected":selected == "B"})
    for invalid in (
        {"options":["dummy"]*3, "correctOptions":["D"]},
        {"options":["dummy"]*3, "correctOptions":["A", "A"]},
        {"options":["dummy"]*3, "correctOptions":[]},
        {"options":["dummy"]*3, "correctOptions":["A"], "correctOption":"A"},
    ):
        cases.append({"question":invalid, "selected":"A", "expected":False})
    return cases
