# CodeQL Detection Scripts

Tools to run various CodeQL queries and output as csv. The following queries are included:

 - `query_files/retry_loop_locations.ql`: list of "retry loops" based on heuristics 
 - `query_files/retry_loop_methods_and_exceptions.ql`: list of retried methods (inside retry loops), declared exception, and whether exception appears is retried (used for fault injection)
 - `query_files/error_policy_outliers.ql`: list of exception types # locations retried, # locations not retried, and "coherence" of these values 
    * Results are used to find IF bugs. E.g. Exceptions with 100% coherence - i.e. always retried or not retried - are not flagged, and exceptions around 50% not flagged (i.e. XX is retried half the time), but those with coherence between, e.g. 66-99% should be flagged.


### How to run
1. Install the CodeQL CLI on your system (see https://codeql.github.com)
2. Download CodeQL Databases: `python3 download_codeql_databases.py`  
3. Run script using the command: `python3 run_query.py PATH_TO_QUERY_FILE`

Script output is printed to the console. You can choose to redirect output to a file (`... > output.csv`)
