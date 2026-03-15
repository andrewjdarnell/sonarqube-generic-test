import os
import xml.etree.ElementTree as ET

def generate_test_execution_report(output_file):
    root = ET.Element("testExecutions", version="1")
    
    # 1. Python Standard Tests
    for test_file in ["tests/test_math_ops.py", "tests/test_utils.py", "tests/test_advanced.py"]:
        file_el = ET.SubElement(root, "file", path=test_file)
        classname = test_file.replace("/", ".").replace(".py", "")
        ET.SubElement(file_el, "testCase", name="test_success", duration="100", classname=classname)
        fail_tc = ET.SubElement(file_el, "testCase", name="test_failure", duration="200", classname=classname)
        ET.SubElement(fail_tc, "failure", message="Assertion failed").text = "Traceback detail..."
        ET.SubElement(file_el, "testCase", name="test_skipped", duration="50", classname=classname)

    # 2. Terraform Compliance Tests (Mapped to the actual .tf file)
    tf_test_file = "terraform/tests/compliance_test.tf"
    file_el = ET.SubElement(root, "file", path=tf_test_file)
    tf_classname = "Terraform.ComplianceTests"
    ET.SubElement(file_el, "testCase", name="bucket_is_private", duration="150", classname=tf_classname)
    ET.SubElement(file_el, "testCase", name="versioning_is_enabled", duration="150", classname=tf_classname)
    fail_tc1 = ET.SubElement(file_el, "testCase", name="encryption_is_enabled", duration="300", classname=tf_classname)
    ET.SubElement(fail_tc1, "failure", message="Encryption missing").text = "Error detail..."
    fail_tc2 = ET.SubElement(file_el, "testCase", name="tags_are_present", duration="200", classname=tf_classname)
    ET.SubElement(fail_tc2, "failure", message="Tags missing").text = "Error detail..."

    # 3. Parallel Dummy Python Mapping (just in case)
    dummy_file = "tests/test_terraform_dummy.py"
    file_el_dummy = ET.SubElement(root, "file", path=dummy_file)
    ET.SubElement(file_el_dummy, "testCase", name="mapped_tf_test_success", duration="100", classname="DummyMapping")
    fail_tc_dummy = ET.SubElement(file_el_dummy, "testCase", name="mapped_tf_test_failure", duration="200", classname="DummyMapping")
    ET.SubElement(fail_tc_dummy, "failure", message="Mapped failure").text = "Mapped detail..."

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Generated All-inclusive Test Execution Report: {output_file}")

def generate_coverage_report(source_files, output_file):
    root = ET.Element("coverage", version="1")
    for file_path in source_files:
        if not os.path.exists(file_path): continue
        file_el = ET.SubElement(root, "file", path=file_path)
        with open(file_path, "r") as f:
            num_lines = len(f.readlines())
        for i in range(1, num_lines + 1):
            is_covered = "true" if i <= max(1, num_lines - 2) else "false"
            ET.SubElement(file_el, "lineToCover", lineNumber=str(i), covered=is_covered)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)
    print(f"Generated Coverage Report: {output_file}")

if __name__ == "__main__":
    generate_test_execution_report("reports/test-results.xml")
    generate_coverage_report(["src/math_ops.py", "src/utils.py", "terraform/main.tf"], "reports/coverage.xml")
