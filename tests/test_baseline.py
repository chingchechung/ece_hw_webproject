"""Dependency-free checks that the runnable baseline remains the supplied v1.2."""
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class BaselinePreservationTests(unittest.TestCase):
    def test_extracted_prototype_matches_original_archive(self):
        with zipfile.ZipFile(ROOT / "emi_maze_dualview_v1.2.zip") as archive:
            for name in archive.namelist():
                if not name.endswith("/"):
                    with self.subTest(file=name):
                        self.assertEqual((ROOT / name).read_bytes(), archive.read(name))


if __name__ == "__main__":
    unittest.main()
