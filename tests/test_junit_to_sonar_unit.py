import unittest
import xml.etree.ElementTree as ET

from junit_to_sonar import junit_root_to_sonar_test_executions


class TestJunitToSonarUnit(unittest.TestCase):
    def test_converts_statuses_and_duration(self):
        junit_xml = """
        <testsuites>
          <testsuite name="tests/example.tftest.hcl">
            <testcase name="passing" classname="tests/example.tftest.hcl" time="0.1" />
            <testcase name="failing" classname="tests/example.tftest.hcl" time="0.2">
              <failure message="failed assertion">details text</failure>
            </testcase>
            <testcase name="errored" classname="tests/example.tftest.hcl" time="0.3">
              <error message="runtime error">stack trace</error>
            </testcase>
            <testcase name="skipped" classname="tests/example.tftest.hcl" time="0.0">
              <skipped message="not applicable" />
            </testcase>
          </testsuite>
        </testsuites>
        """
        root = ET.fromstring(junit_xml)

        out_root = junit_root_to_sonar_test_executions(root)
        files = out_root.findall("file")
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].attrib["path"], "tests/example.tftest.hcl")

        test_cases = files[0].findall("testCase")
        self.assertEqual(len(test_cases), 4)

        self.assertEqual(test_cases[0].attrib["name"], "passing")
        self.assertEqual(test_cases[0].attrib["duration"], "100")

        self.assertIsNotNone(test_cases[1].find("failure"))
        self.assertIn("failed assertion", (test_cases[1].find("failure").text or ""))
        self.assertIn("details text", (test_cases[1].find("failure").text or ""))

        self.assertIsNotNone(test_cases[2].find("error"))
        self.assertIsNotNone(test_cases[3].find("skipped"))

    def test_uses_testsuite_name_when_classname_missing(self):
        junit_xml = """
        <testsuite name="tests/fallback.tftest.hcl">
          <testcase name="case1" time="1.0" />
        </testsuite>
        """
        root = ET.fromstring(junit_xml)
        out_root = junit_root_to_sonar_test_executions(root)

        file_node = out_root.find("file")
        self.assertIsNotNone(file_node)
        self.assertEqual(file_node.attrib["path"], "tests/fallback.tftest.hcl")

    def test_uses_explicit_fallback_when_missing_metadata(self):
        junit_xml = """
        <testsuite>
          <testcase name="case1" time="0.01" />
        </testsuite>
        """
        root = ET.fromstring(junit_xml)
        out_root = junit_root_to_sonar_test_executions(root, fallback_test_file_path="from-input.xml")

        file_node = out_root.find("file")
        self.assertIsNotNone(file_node)
        self.assertEqual(file_node.attrib["path"], "from-input.xml")


if __name__ == "__main__":
    unittest.main()
