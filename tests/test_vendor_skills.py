import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


def git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    payload = f"blob {len(content)}\0".encode("utf-8") + content
    return hashlib.sha1(payload).hexdigest()


class VendoredSkillTests(unittest.TestCase):
    def test_airtable_skills_match_pinned_upstream_blobs(self):
        manifest = json.loads((ROOT / "skills" / "UPSTREAM.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_commit"], "295ab93b7d765912ee1a0dc7f1abb0ecaf73f138")
        self.assertEqual(len(manifest["skills"]), 2)

        for skill in manifest["skills"]:
            path = ROOT / skill["local_path"]
            self.assertTrue(path.exists(), skill["local_path"])
            self.assertEqual(git_blob_sha(path), skill["upstream_blob_sha"])
            text = path.read_text(encoding="utf-8")
            self.assertIn(f"name: {skill['name']}", text)
            self.assertIn(f"version: '{skill['version']}'", text)
            self.assertIn("license: MIT", text)


if __name__ == "__main__":
    unittest.main()
