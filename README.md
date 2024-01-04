# Retry issue detection

This repo contains scripts that detect retry related information and issues.

## CodeQL Retry Detection Scripts

The `codeql-detection-scripts` folder contains the following scripts related to retry issue detection:
 - `retry_loop_locations.ql`: return list of "retry loops" based on heuristics ("for" or "while" loops only)
 - `retry_loop_methods_and_exceptions.ql`: return list of retried methods (inside retry loops), declared exception, and whether exception appears is retried (used for fault injection)
 - `error_policy_outliers.ql`: returns a list of exception types # locations retried, # locations not retried, and "coherence" of these values 
    * Results are used to find IF bugs. E.g. Exceptions with 100% coherence - i.e. always retried or not retried - are not flagged, and exceptions around 50% not flagged (i.e. XX is retried half the time), but those with coherence between, e.g. 66-99% should be flagged.

### How to run
1. Install the CodeQL CLI on your system (see https://codeql.github.com)
2. Download or generate CodeQL databases for apps (a pre-built set of databases for apps in retry paper is available)
3. Run the script using the command: `python3 run_query.py [SCRIPT_FILE]`, where [SCRIPT\_FILE] is one of the files listed above

Script output is printed to the console. You can choose to redirect output to a file (`python3 run_query.py [SCRIPT_FILE] > output.csv`)

# LLM Retry Detection Scripts 
The `llm-detection-script` folder contains a script to analyze retry-related behavior of Java source files using OpenAI LLM

Given a path to the source code root directory, it recursively analyzes all files in the directory, returning the following information for each file (as "Yes" or "No"):
- `has_retry_gpt` : If the file performs retry

If the answer to the above is "Yes"
- `has_sleep_gpt`: whether code sleeps between retries
- `has_cap_gpt`: whether code has a cap (timeout or num attempts) on retries
- `method_names_gpt`: what methods may contain retry logic
- `has_compare_or_poll_gpt`: whether the methods perform atomic-var-setting or polling behavior (so we can exclude these non-retry cases)

If the file does not have retry, it returns "N/A" for these columns.

Also note: if the file is above user-set or GPT limit, it returns "TOO\_LONG"

The output is formatted as a CSV


*CAUTION*: this script sends every file to the LLM (excl test files), so please consider cost before running (as of Dec 2023, cost was ~$100 for 4000 files)

## How to run 
1. Put your OpenAI key in a file named "openai.key"
2. Run the script: `python3 analyze_files.py PATH_TO_SOURCE_DIR`
 - The output is written to "output\_[timestamp].csv"

Note: the script by default only analyzes files with extensions ".java" or ".scala"; and does not analyze files in "test" directories

