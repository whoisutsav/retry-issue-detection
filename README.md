# SOSP 24 Artifact

Repo with static scripts and other artifacts for the retry issue project.

## 1. Retry issues dataset (Table 2)

Contained in file `retry_issue_set_artifact.xlsx`

This dataset is used to create **Table 1** (# issues per app) and **Table 2** (category breakdown)

The issues themselves are discussed in **Section 2**, *"Understanding Retry Issues."*

## 2. Static IF bug detection script (Sec. 3.2.2 & 4.1)

The script is described in **Section 3.2.2**, and is used to generate results in **Section 4.1**, *"Wasabi Static Checking"*: "Wasabi finds **9** outlier cases.."

The script can be found in `codeql-if-detection/error_policy_outliers.ql`

### Steps to reproduce

To make re-running easier, we have packaged the script and dependencies into a docker image. To reproduce results, run the following commands (requires docker):

```
docker run -it --rm whoisutsav/sosp-retry-if-bugs
cd /usr/local/repro-scripts
./repro.sh
```
(The script should take no more than 60 minutes to run, likely less. Note, it requires internet access to download CodeQL databases from an external repo.)

The output should match the following:

| AppName | ExceptionType | LocationsRetried | LocationsNotRetried | Coherence |
| --- | --- | --- | --- | --- |
|hbase | org.apache.zookeeper.KeeperException | 17 | **(3)** | .85 |
| hadoop | java.lang.IllegalArgumentException | **(1)** | 5 | .83 |
| hadoop | java.io.FileNotFoundException| **(1)**| 3| .75 |
|hadoop|org.apache.hadoop.util.ExitUtil$ExitException|**(1)**|2|.67|
|hive|java.lang.IllegalArgumentException|**(1)**|2|.67|
|hive|org.apache.thrift.transport.TTransportException|2|**(1)**|.67|
|cassandra|java.lang.IllegalStateException|**(1)**|2|.67|

The outliers (in bold) add up to the 9 cases mentioned.

Users that wish to run the script on other applications should install the CodeQL CLI and pass the script as a parameter to `codeql query run`.

## 3. Static WHEN bug detection results (Table 4)

These results are used to generate **Table 4**, *"Retry bugs reported by Wasabi GPT-4 detector"*

The raw results are included in the file `wasabi_gpt_detection_results--table4.xlsx`

### Steps to reproduce

They were generated by the included script `gpt-when-detection/find_when_bugs_gpt.py`, using the gpt-4-turbo model; however using this model on full files via the chat API (as we do) requires a billing account with OpenAI at very large cost.

As an alternative, to enable reviewers to confirm that these values are reproducible, we used OpenAI's free web-browser-based chat (with the same prompts to generate Table 4) on a sample of 20 of these bugs. The browser chat uses a GPT-4-class model that is similar to the API model. To verify the reproduced bugs:

1. Navigate to the `GPT Results - ARTIFACT SAMPLE` tab of the spreadsheet
2. Under the `reproduce-link` column, find the link to the OpenAI chat used to reproduce that bug (same prompts as our script)
3. Confirm the the chat responses are the exact same as our results (columns F, G, H, and J). Note, answers starting with 'Yes'=Y, 'No'=N).

