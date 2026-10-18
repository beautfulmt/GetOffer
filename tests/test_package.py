"""Validate that the distributable skill is complete and portable."""
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/get-offer"


def links(path):
    visible, fence = [], None
    for line in path.read_text().splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            kind = marker.group(1)[0]
            fence = None if fence == kind else kind if fence is None else fence
        elif fence is None:
            visible.append(line)
    for match in re.finditer(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", "\n".join(visible)):
        target = match.group(1).split(' "')[0].strip("<>")
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:|^#", target):
            yield unquote(target.split("#")[0])


def broken_links(root):
    return [f"{path.relative_to(root)}: {target}" for path in root.rglob("*.md")
            if ".git" not in path.parts for target in links(path)
            if target and not (path.parent / target).exists()]


class PackageTest(unittest.TestCase):
    def test_repository_links_resolve(self):
        self.assertEqual(broken_links(ROOT), [])

    def test_skill_can_be_copied_without_the_repository(self):
        with tempfile.TemporaryDirectory() as area:
            target = Path(area) / "get-offer"
            shutil.copytree(SKILL, target)
            self.assertEqual(broken_links(target), [])
            for path in target.rglob("*.md"):
                self.assertNotIn("/Users/", path.read_text())

    def test_every_reference_and_template_is_discoverable(self):
        seen, todo = set(), [SKILL / "SKILL.md"]
        while todo:
            path = todo.pop().resolve()
            if path in seen:
                continue
            seen.add(path)
            for target in links(path):
                child = (path.parent / target).resolve()
                if child.suffix == ".md" and child.is_file():
                    todo.append(child)
        resources = {p.resolve() for folder in ["references", "assets"] for p in (SKILL / folder).glob("*.md")}
        self.assertTrue(resources <= seen, str(resources - seen))

    def test_metadata_names_the_skill_and_uses_quoted_interface_strings(self):
        text = (SKILL / "SKILL.md").read_text()
        self.assertTrue(text.startswith("---\nname: get-offer\n"))
        self.assertRegex(text, r'(?m)^description: ".+"$')
        interface = (SKILL / "agents/openai.yaml").read_text()
        for field in ["display_name", "short_description", "default_prompt"]:
            value = re.search(rf'(?m)^  {field}: (".*")$', interface)
            self.assertIsNotNone(value)
            self.assertTrue(json.loads(value.group(1)))
        self.assertIn("$get-offer", interface)

    def test_eval_ids_and_fixture_are_self_contained_simulations(self):
        cases = json.loads((ROOT / "tests/evals/cases.json").read_text())["cases"]
        self.assertEqual(len({c["id"] for c in cases}), len(cases))
        for case in cases:
            self.assertTrue(case["prompt"])
            self.assertTrue(case["expect"])
            self.assertTrue(case["anti_patterns"])
        fixture = json.loads((ROOT / "tests/fixtures/candidate.json").read_text())
        self.assertTrue(fixture["simulation"])
        self.assertTrue(fixture["facts"])
