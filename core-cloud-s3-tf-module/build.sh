#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GENERATED_DIR="$SCRIPT_DIR/generated"
PLAN_FILE="$GENERATED_DIR/terraform.plan"
PLAN_TEXT_FILE="$GENERATED_DIR/terraform-plan.txt"
INIT_LOG_FILE="$GENERATED_DIR/terraform-init.txt"
TEST_RESULTS_FILE="$GENERATED_DIR/terraform-test-results.txt"
PLAN_VARS_FILE="$GENERATED_DIR/plan.auto.tfvars"
TEST_DIR="tests"
PLAN_PROVIDER_OVERRIDE_FILE="$SCRIPT_DIR/build-plan-provider-override.tf"

mkdir -p "$GENERATED_DIR"
touch "$GENERATED_DIR/.gitkeep"

cd "$SCRIPT_DIR"

# Provide non-sensitive local defaults so provider initialization works during CI/local tests.
export AWS_ACCESS_KEY_ID="mock_access_key"
export AWS_SECRET_ACCESS_KEY="mock_secret_key"
export AWS_SESSION_TOKEN="mock_session_token"
export AWS_DEFAULT_REGION="eu-west-2"
export AWS_REGION="eu-west-2"
export AWS_EC2_METADATA_DISABLED="true"

cat > "$PLAN_VARS_FILE" <<'EOF'
account_id  = "100000000000"
bucket_name = "testbucket"
kms_alias   = "test-kms-key"
project_name = "testproject"
environment = "test"
region = "eu-west-2"
encryption_type = "aws:kms"
email_address = "test@test"

tags = {
  Environment      = "test"
  Project          = "test"
  cost-centre      = "CC1000"
  account-code     = "AC1000"
  portfolio-id     = "PF1000"
  project-id       = "PR1000"
  service-id       = "SV1000"
  environment-type = "test"
  owner-business   = "test"
  budget-holder    = "testteam"
  source-repo      = "UKHomeOffice/core-cloud-s3-tf-module"
}
EOF

echo "Running build in $(pwd)"

echo "Running terraform init..."
terraform init -input=false -no-color | tee "$INIT_LOG_FILE"

cat > "$PLAN_PROVIDER_OVERRIDE_FILE" <<'EOF'
provider "aws" {
  region                      = "eu-west-2"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
}
EOF

echo "Running terraform plan..."
set +e
terraform plan -input=false -no-color -refresh=false -var-file="$PLAN_VARS_FILE" -out="$PLAN_FILE" | tee "$PLAN_TEXT_FILE"
PLAN_EXIT_CODE=${PIPESTATUS[0]}
set -e

rm -f "$PLAN_PROVIDER_OVERRIDE_FILE"

if [[ $PLAN_EXIT_CODE -ne 0 ]]; then
  echo "Terraform plan failed. See $PLAN_TEXT_FILE for details."
  exit "$PLAN_EXIT_CODE"
fi

echo "Running terraform tests from $TEST_DIR directory..."

shopt -s nullglob
TEST_FILES=("$TEST_DIR"/*.tftest.hcl)
shopt -u nullglob

if [[ ${#TEST_FILES[@]} -eq 0 ]]; then
  echo "No Terraform test files found in $TEST_DIR" | tee "$TEST_RESULTS_FILE"
  exit 1
fi

FAILED_TESTS=0
{
  echo "Terraform test run started at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "Found ${#TEST_FILES[@]} test files"
} > "$TEST_RESULTS_FILE"

for test_file in "${TEST_FILES[@]}"; do
  test_name="$(basename "$test_file")"
  per_test_log="$GENERATED_DIR/${test_name%.tftest.hcl}.test.txt"
  per_test_junit_xml="$GENERATED_DIR/${test_name%.tftest.hcl}.junit.xml"

  echo "Running terraform test for $test_name"
  {
    echo
    echo "===== $test_name ====="
  } | tee -a "$TEST_RESULTS_FILE"

  set +e
  terraform test -no-color -test-directory="$TEST_DIR" -filter="$test_file" -junit-xml="$per_test_junit_xml" | tee "$per_test_log"
  test_exit_code=${PIPESTATUS[0]}
  set -e

  cat "$per_test_log" >> "$TEST_RESULTS_FILE"
  echo "JUnit XML: $per_test_junit_xml" | tee -a "$TEST_RESULTS_FILE"

  if [[ $test_exit_code -ne 0 ]]; then
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "Result: FAIL ($test_name)" | tee -a "$TEST_RESULTS_FILE"
  else
    echo "Result: PASS ($test_name)" | tee -a "$TEST_RESULTS_FILE"
  fi
done

if [[ $FAILED_TESTS -ne 0 ]]; then
  echo "Terraform tests failed for $FAILED_TESTS file(s). See $TEST_RESULTS_FILE for details."
  exit 1
fi

echo "Terraform plan and tests completed successfully."
echo "Generated files are in: $GENERATED_DIR"
