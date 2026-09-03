import unittest
from pathlib import Path

from whiteboard_app.project import load_project


class MultiJobExamplePackTests(unittest.TestCase):
    def test_five_projects_are_valid_and_independent(self) -> None:
        pack = Path(__file__).resolve().parents[1] / "examples" / "multi-job-5-pack"
        manifests = sorted(pack.glob("*/project.json"))
        self.assertEqual(len(manifests), 5)

        projects = [load_project(manifest) for manifest in manifests]
        try:
            self.assertEqual(len({project.title for project in projects}), 5)
            for project in projects:
                self.assertEqual(len(project.scenes), 1)
                self.assertEqual(len(project.narration_cues), 4)
                self.assertTrue(all(len(cue.element_ids) == 1 for cue in project.narration_cues))
                self.assertTrue(project.script_text)
                self.assertEqual(
                    {cue.element_ids[0] for cue in project.narration_cues},
                    {
                        element_id
                        for cue in project.narration_cues
                        for element_id in cue.element_ids
                    },
                )
        finally:
            for project in projects:
                project.close()

    def test_five_zip_packages_load_from_one_folder(self) -> None:
        pack = Path(__file__).resolve().parents[1] / "examples" / "multi-job-5-pack" / "zips"
        archives = sorted(pack.glob("*.zip"))
        self.assertEqual(len(archives), 5)

        projects = [load_project(archive) for archive in archives]
        try:
            self.assertEqual(len({project.title for project in projects}), 5)
            self.assertTrue(all(len(project.narration_cues) == 4 for project in projects))
        finally:
            for project in projects:
                project.close()


if __name__ == "__main__":
    unittest.main()
