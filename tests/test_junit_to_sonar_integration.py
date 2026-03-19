import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from junit_to_sonar import convert_junit_file_to_sonar_generic


class TestJunitToSonarIntegration(unittest.TestCase):
    def test_converts_generated_s3_basic_failing_junit_file(self):
        repo_root = Path(__file__).resolve().parents[1]
        junit_input = repo_root / "generated" / "s3_basic_failing.junit.xml"

        if not junit_input.exists():
            self.skipTest(
                "Integration fixture not found at generated/s3_basic_failing.junit.xml. "
                "Run ./build.sh from repository root first."
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sonar-test-executions.xml"
            convert_junit_file_to_sonar_generic(junit_input, output_path)

            self.assertTrue(output_path.exists())

            root = ET.parse(output_path).getroot()
            self.assertEqual(root.tag, "testExecutions")
            self.assertEqual(root.attrib.get("version"), "1")

            file_nodes = root.findall("file")
            self.assertEqual(len(file_nodes), 1)
            self.assertEqual(file_nodes[0].attrib.get("path"), "tests/s3_basic_failing.tftest.hcl")

            test_cases = file_nodes[0].findall("testCase")
            self.assertEqual(len(test_cases), 5)

            failure_count = sum(1 for tc in test_cases if tc.find("failure") is not None)
            self.assertEqual(failure_count, 3)

            case_names = {tc.attrib.get("name") for tc in test_cases}
            self.assertIn("validate_bucket_creation", case_names)
            self.assertIn("validate_kms_key_creation", case_names)
            self.assertIn("validate_versioning_enabled", case_names)


if __name__ == "__main__":
    unittest.main()
