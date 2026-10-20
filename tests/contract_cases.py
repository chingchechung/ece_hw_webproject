"""Shared complete synthetic fixtures and mutation corpus. Never deploy these."""
from copy import deepcopy
import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name="S01.json"):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def contract_cases():
    cases = []

    def add(name, data, valid=False, kind="unit", filename="S01.json"):
        cases.append(dict(name=name, data=data, valid=valid, kind=kind, filename=filename))

    def change(name, path, value, valid=False):
        data = fixture()
        target = data
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        add(name, data, valid)

    add("four questions", fixture(), True)
    add("five questions", fixture("S02.json"), True, filename="S02.json")
    for unit_number in range(1, 13):
        data = fixture()
        data["unitId"] = f"S{unit_number:02}"
        add(f"unit {unit_number}", data, True, filename=f"S{unit_number:02}.json")
    for key in fixture():
        data = fixture()
        del data[key]
        add(f"missing {key}", data)
    for key in fixture()["questions"][0]:
        data = fixture()
        del data["questions"][0][key]
        add(f"missing question {key}", data, key in ("title", "prompt", "explanationText"))
    for field in ("title", "prompt", "explanationText"):
        for value in ("", " \n ", "測試 <b>literal text</b>", None, [], {}, False, 7):
            change(f"optional {field}={value!r}", ["questions", 0, field], value, isinstance(value, str))
    for value in (None, False, 1, "unit", [], [fixture()]):
        add(f"root type {value!r}", value)
    for value in (None, True, False, "1", 0, 2, 1.5, {}, [], 1.0):
        change(f"version {value!r}", ["schemaVersion"], value, type(value) in (int, float) and value == 1)
    for value in ("S00", "S13", "s01", "S1", " S01", "S01\n", None, 1, {}, []):
        change(f"unit ID {value!r}", ["unitId"], value)
    for name in ("S02.json", "s01.json", "S01.JSON", "../S01.json", "/tmp/S01.json", "S01.json?x", ""):
        add(f"filename {name!r}", fixture(), filename=name)
    for value in ("", " \n\ufeff", None, 5, [], {}, False):
        change(f"unit title {value!r}", ["title"], value)
    for value in (None, {}, "questions", False, [], [fixture()["questions"][0]], fixture()["questions"]*2):
        change(f"question array {value!r}", ["questions"], value)
    for value in (None, False, [], "question", 7):
        change(f"question object {value!r}", ["questions", 0], value)
    for value in ("Q01", "Q03", "q02", "Q2", "Q02\n", "", None, False, 2, []):
        change(f"duplicate/sequential ID {value!r}", ["questions", 1, "id"], value)
    for value in (None, "ABCD", {}, [], ["a"]*3, ["a"]*5, ["a", "", "c", "d"], ["a", " \ufeff", "c", "d"], ["a", None, "c", "d"], ["a", 1, "c", "d"]):
        change(f"options {value!r}", ["questions", 0, "options"], value)
    for value in ("A", "B", "C", "D", "a", " B ", "AB", "", None, 0, True, [], {}):
        change(f"answer {value!r}", ["questions", 0, "correctOption"], value, isinstance(value, str) and value in ("A", "B", "C", "D"))

    good_video = [
        "https://www.youtube.com/watch?v=xDARFvArIpc",
        "https://youtube.com/watch?v=ChtmE09BSy0&t=30s",
        "https://youtube.com/watch?si=abc_DEF-12&v=ChtmE09BSy0&t=30#t=20",
        "https://youtu.be/xDARFvArIpc",
        "https://youtu.be/xDARFvArIpc?si=abc&t=20",
        " https://youtu.be/xDARFvArIpc \n",
        "https://www.youtube.com/watch?v=xDARFvArIpc&list=PL_abc&feature=share",
    ]
    bad_video = [
        None, False, [], {}, 1, "", "  ", "javascript:alert(1)",
        "http://youtube.com/watch?v=xDARFvArIpc",
        "https://youtube.com.evil.test/watch?v=xDARFvArIpc",
        "https://www.youtube.com@evil.test/watch?v=xDARFvArIpc",
        "https://user@youtube.com/watch?v=xDARFvArIpc",
        "https://youtube.com:443/watch?v=xDARFvArIpc",
        "https://youtube.com./watch?v=xDARFvArIpc",
        "https://youtube.com/watch", "https://youtube.com/watch?v=short",
        "https://youtube.com/watch?v=xDARFvArIpcA",
        "https://youtube.com/watch?v=XXXXXXXXXXX",
        "https://youtu.be/YYYYYYYYYYY", "https://youtu.be/00000000000",
        "https://youtube.com/watch?v=YOUR_VIDEO_ID",
        "https://youtube.com/watch?v=xDARFvArIpc&v=ChtmE09BSy0",
        "https://youtu.be/xDARFvArIpc?v=ChtmE09BSy0",
        "https://youtube.com/watch?v=xDARFvArIpc&si=%ZZ",
        "https://youtube.com/watch?v=xDARFvArIpc\n&si=abc",
        "https://youtube.com/shorts/xDARFvArIpc",
        "https://youtube.com/embed/xDARFvArIpc",
        "https://youtu.be/xDARFvArIpc/extra",
        "//youtu.be/xDARFvArIpc", "https:\\youtu.be\\xDARFvArIpc",
        "https://youtu.be/%78DARFvArIpc",
        "https://youtube.com/watch?v=xDARFvArIpc\" onclick=\"alert(1)",
    ]
    for field in ("questionVideoUrl", "explanationVideoUrl"):
        for valid, values in ((True, good_video), (False, bad_video)):
            for value in values:
                change(f"{field} {value!r}", ["questions", 0, field], value, valid)
    good_form = [
        "https://forms.gle/AbCdEf1234567890",
        " https://forms.gle/AbCdEf1234567890 \n",
        "https://forms.gle/AbCdEf1234567890?usp=sharing",
        "https://docs.google.com/forms/d/e/1FAIpQLSc0123456789/viewform",
        "https://docs.google.com/forms/d/1AbCdEF/edit?usp=sharing",
        "https://docs.google.com/forms/u/0/d/e/1FAIpQLSc0123456789/viewform?entry.12=yes#responses",
    ]
    bad_form = [
        None, False, {}, [], 1, "", " \n", "http://forms.gle/AbCdEf1234567890",
        "https://forms.gle/XXXXXXXXXXXX", "https://forms.gle/YOUR_FORM_ID",
        "https://forms.gle/placeholder", "https://forms.gle/example",
        "https://forms.gle/", "https://forms.gle/AbCdEf/extra",
        "https://forms.gle.evil.test/AbCdEf", "https://forms.gle@evil.test/AbCdEf",
        "https://docs.google.com/form/d/e/1FAIpQLSc/viewform",
        "https://docs.google.com/forms/", "https://docs.google.com/forms/d/e/XXXX/viewform",
        "https://docs.google.com/spreadsheets/d/1abc/edit",
        "https://docs.google.com.evil.test/forms/d/e/1FAIpQLSc/viewform",
        "https://docs.google.com/forms/../spreadsheets/d/1abc/edit",
        "https://forms.gle:443/AbCdEf", "https://user@forms.gle/AbCdEf",
        "https://forms.gle/AbCdEf?usp=%x1", "javascript:alert(1)",
    ]
    for valid, values in ((True, good_form), (False, bad_form)):
        for value in values:
            change(f"form {value!r}", ["googleFormUrl"], value, valid)
    data = fixture()
    data["title"] = "\ufeff 日本語 中文 <b>literal</b> \u3000"
    data["questions"][0]["options"] = [" B ", " A ", " D ", " C "]
    add("normalization preserves order and Unicode", data, True)
    for location in ([], ["questions", 0]):
        data = fixture()
        target = data
        for key in location:
            target = target[key]
        target["allowPlay"] = True
        add(f"private metadata {location}", data)

    add("complete manifest", fixture("manifest.json"), True, "manifest")
    add("empty public allowlist", {"schemaVersion":1, "units":[]}, True, "manifest")
    for value in (None, False, [], "manifest", 1):
        add(f"manifest root {value!r}", value, kind="manifest")
    for key in ("schemaVersion", "units"):
        data = fixture("manifest.json")
        del data[key]
        add(f"manifest missing {key}", data, kind="manifest")
    for key in ("unitId", "title", "file"):
        data = fixture("manifest.json")
        del data["units"][0][key]
        add(f"entry missing {key}", data, kind="manifest")
    for field, values in (
        ("schemaVersion", [True, "1", 2]), ("units", [None, {}, "", [None], fixture("manifest.json")["units"]*7]),
    ):
        for value in values:
            data = fixture("manifest.json")
            data[field] = value
            add(f"manifest {field}={value!r}", data, kind="manifest")
    for field, values in (
        ("unitId", [None, False, [], "S13", "S00", "s01", "S01\n"]),
        ("title", [None, [], "", " \ufeff"]),
        ("file", [None, 1, [], "", "S02.json", "../S01.json", "/S01.json", "S01.JSON", "https://evil.test/S01.json", "S01.json?x", "S01.json#x", "sub/S01.json"]),
        ("allowPlay", [True]), ("correctOption", ["A"]),
    ):
        for value in values:
            data = fixture("manifest.json")
            data["units"][0][field] = value
            add(f"manifest entry {field}={value!r}", data, kind="manifest")
    data = fixture("manifest.json")
    data["units"].append(deepcopy(data["units"][0]))
    add("duplicate manifest unit", data, kind="manifest")
    data = fixture("manifest.json")
    data["units"][1] = dict(data["units"][0], title="Other title")
    add("duplicate unit with other title", data, kind="manifest")
    from tests.contract_cases_v2 import v2_contract_cases
    return cases + v2_contract_cases()
