# SonarQube Generic Test Execution & Coverage Demo

This project demonstrates how to use SonarQube's **Generic Test Data** and **Generic Coverage** formats to import results from languages or tools that aren't natively supported (e.g., Terraform compliance tests) alongside standard languages like Python.

## Quickstart

From the repository root:

```bash
brew install python
brew install uv
brew tap hashicorp/tap
brew install hashicorp/tap/terraform awscli

uv venv .venv
uv pip install --python .venv/bin/python pytest

uv run --python .venv/bin/python pytest
uv run --python .venv/bin/python generate_reports.py

./build.sh
```

You also need either docker  or podman to be installed
If its Docker, you also need Docker-Desktop to be running.

Then bring up the SonarQube Server with
```
docker compose up -d
```

and submit the generated results with 
```
./submit_results_d.sh
```
or for podman
```
./submit_results_p.sh
```


Note: `./build.sh` returns a non-zero exit code when any Terraform test file fails (expected if `s3_basic_failing.tftest.hcl` is enabled).

## Project Structure

- `src/`: Python source code.
- `tests/`: Python unit tests.
- `terraform/`: Terraform configuration (`main.tf`).
- `terraform/tests/`: Terraform compliance tests (`compliance_test.tf`).
- `reports/`: Generated XML reports for SonarQube ingestion.
- `generate_reports.py`: Python script to generate SonarQube-compatible XML.
- `sonar-project.properties`: Configuration for the SonarQube scanner.
- `scanner_debug.log`: Full verbose output from the SonarQube scanner for deep analysis.
- `docker-compose.yml`: Spins up a local SonarQube and PostgreSQL instance.
- `screenshots/`: Visual evidence of the SonarQube UI and results.

## Tooling

- **Python environment**: [`uv`](https://github.com/astral-sh/uv) using a local `.venv` in the repository root.
- **Python test framework**: `pytest`.
- **Terraform testing**: `terraform test` with per-file JUnit XML output from `build.sh`.
- **JUnit to Sonar conversion**: `junit_to_sonar.py` converts JUnit XML to SonarQube generic `testExecutions` XML.
- **Infrastructure tooling**: Terraform and AWS CLI.
- **Analysis tooling**: SonarQube scanner via Docker/Podman.

## Getting Started

### 0. Install Required Tooling

```bash
brew install uv
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
brew install awscli
```

Check versions:

```bash
python --version
uv --version
terraform --version
aws --version
```

### 1. Create the Python Virtual Environment (uv)

From the repository root:

```bash
uv venv .venv
uv pip install --python .venv/bin/python pytest
```

Optional activation:

```bash
source .venv/bin/activate
```

If you do not activate the environment, run commands with `uv run`:

```bash
uv run --python .venv/bin/python pytest -q
```

### 2. Start SonarQube
Ensure Docker Desktop or Podman is running, then start the environment:

**With Docker Compose:**
```bash
docker compose up -d
```

**With Podman Compose:**
```bash
podman-compose up -d
```

Login at [http://localhost:9000](http://localhost:9000) (Default: `admin`/`admin`).

### 3. Generate a Security Token Via the API
(the scanner. You can also generate one via the UI. If one is already created the command will fail. Check at http://localhost:9000/account/security


**Extract and save the token to .env using jq:**
```bash
curl -u admin -X POST "http://localhost:9000/api/user_tokens/generate?name=scanner-token" | jq -r '.token' | xargs -I{} sh -c 'echo SONAR_TOKEN={} > .env'
```
*Note: This command uses jq to cleanly extract the token from the JSON response and writes it to the .env file. if you then include  '--env-file .env' in your docker command, you can then reference SONAR_TOKEN in your sonar-project.properties.* with sonar.token=${SONAR_TOKEN}


Then apply the minimum recommended baseline hardening of:

```bash
chmod 600 .env
```

Why this is reasonable: `.env` is already ignored by `.gitignore`, and `chmod 600` limits read/write access to your user account only.

See the bottom of the Readme for an alternative solution

**Via UI:**
1. Go to **My Account** (top right) -> **Security**.
2. Under **Generate Token**, give it a name and click **Generate**.

### Update Admin Password (defaults are admin/admin)

### Create Local Project
sonar.projectKey=sonarqube-generic-test (Project Key)
sonar.projectName=sonarqube-generic-test (Display Name)
sonar.projectVersion=1.0
Main Branch Name -  main


### 4. Run Python Tests (pytest)

```bash
uv run --python .venv/bin/python pytest
```

### 5. Generate Reports
Run the generator script to create the `testExecutions` and `coverage` XML files:
```bash
uv run --python .venv/bin/python generate_reports.py
```

### 6. Run Terraform Module Build and Test Reports

The module build script runs:

- `terraform init`
- `terraform plan`
- `terraform test` for each `.tftest.hcl` file
- JUnit XML generation per test file
- Sonar generic test execution XML conversion per test file

```bash
./build.sh
```

Generated outputs are written to `generated/`.

#### build.sh details

- Script path: `build.sh`.
- Test discovery pattern: `core-cloud-s3-tf-module/tests/*.tftest.hcl`.
- Per-test execution: each discovered test file is run individually using Terraform `-filter`.
- JUnit output per test file: `*.junit.xml`.
- Sonar generic execution output per test file: `*.sonar.xml` (via `junit_to_sonar.py`).
- Aggregate test log: `terraform-test-results.txt`.
- Plan artifacts: `terraform.plan` and `terraform-plan.txt`.

Typical generated files:

- `generated/kms_policy.junit.xml`
- `generated/kms_policy.sonar.xml`
- `generated/s3_basic.junit.xml`
- `generated/s3_basic.sonar.xml`
- `generated/terraform-test-results.txt`

Exit behavior:

- `0`: plan succeeds and all discovered test files pass.
- Non-zero: plan fails, or at least one test file fails (for example `s3_basic_failing.tftest.hcl`).

### 7. Run Analysis
Use the SonarQube Scanner to submit the results:

*Note: In the Docker command, `--rm` removes the container automatically when it exits, and `-v "$(pwd):/usr/src"` mounts your current project directory into the container so the scanner can read your source files and report XML files.*

Recommended helper scripts:

- Docker: `./submit_results_d.sh`
- Podman: `./submit_results_p.sh`

Both scripts forward extra scanner arguments, for example:

```bash
./submit_results_d.sh -Dsonar.log.level=DEBUG
```

**With Docker:**
```bash
./submit_results_d.sh
```

**With Podman:**
```bash
./submit_results_p.sh
```
*Note: Podman uses `host.containers.internal` instead of `host.docker.internal` for host communication.*

---

## Visual Results & Observations

### 1. Test Results Submitted
![Test Results Submitted](screenshots/Screenshot_01_testresults_submitted.png)
*Evidence of the successful submission and ingestion of generic test data into the SonarQube dashboard.*

### 2. Python Test Results Detail
![Python Tests Detail](screenshots/Screenshot_02_py_tests_whichonespassed.png)
*Detailed view of Python test components.*

### 3. Terraform Test Results Detail
![Terraform Tests Detail](screenshots/Screenshot_03_tf_tests_whichonespassed.png)
*Detailed view of Terraform test components.*

### Conclusion
**What we see is that SonarQube is not showing the unit test results per unit test, only at an overall file level.**

---

## Implementation History: The Path to Success

To achieve a successful generic test submission, we followed these key architectural steps:

1.  **Environment Isolation**: Established a reliable local SonarQube instance using Docker Compose with an external PostgreSQL database for persistence.
2.  **Generic XML Generation**: Developed a Python script (`generate_reports.py`) to map diverse test results (Python `unittest` and Terraform `compliance`) into the [SonarQube Generic Test Execution](https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/test-coverage/generic-test-data/#generic-test-execution) XML format.
3.  **Dynamic Coverage Mapping**: Implemented a dynamic line-coverage generator that calculates file lengths to ensure the `coverage.xml` always matches the physical source files, preventing sensor parsing errors.
4.  **Strict Source vs. Test Classification**: Refined `sonar-project.properties` to explicitly separate `sonar.sources` from `sonar.tests`. This was critical for ensuring that:
    - **Source files** (like `main.tf`) show **Coverage** (green/red bars).
    - **Test files** (like `compliance_test.tf`) show **Execution Results** (pass/fail counts).
5.  **UI Optimization**: Enhanced the XML report with `classname` attributes and explicitly included test patterns in `sonar.test.inclusions` to ensure the SonarQube UI correctly attributed results to the appropriate components.
6.  **Scanner-to-Host Communication**: Configured the Docker-based scanner to communicate with the host-bound SonarQube instance using `host.docker.internal`, allowing for a seamless local development loop.

## Bonus points: Keychain-based token storage (macOS)

If you want to avoid storing the token in `.env`, you can store it in macOS Keychain and inject it at runtime.

1. Save token in Keychain once:

```bash
security add-generic-password -a "$USER" -s sonar_token -w "<your-sonar-token>" -U
```

2. Export token into your shell for the current session:

```bash
export SONAR_TOKEN="$(security find-generic-password -a "$USER" -s sonar_token -w)"
```

3. Use scanner commands with environment passthrough instead of `--env-file .env`:

```bash
docker run --rm \
  -e SONAR_TOKEN \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli \
  -Dsonar.host.url=http://host.docker.internal:9000
```

```bash
podman run --rm \
  -e SONAR_TOKEN \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli \
  -Dsonar.host.url=http://host.containers.internal:9000
```
