# SOSP 24 Artifact

Repo with static scripts and other artifacts for the retry issue project.

## 1. Retry issues dataset 

Contained in file `retry_issue_set.xlsx`

This dataset is used to create **Table 1** (# issues per app) and **Table 2** (category breakdown)

The issues themselves are discussed in **Section 2**, *"Understanding Retry Issues."*

## 2. Static IF bug detection script

The script is described in **Section 3.2.2**, and results are described in **Section 4.1**, *"Wasabi Static Checking"*: "Wasabi finds **9** outlier cases.."

To generate results:

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

## 3. Static WHEN bug detection results (Table 4)

These results are used to generate **Table 4**, *"Retry bugs reported by Wasabi GPT-4 detector"*

The raw results are included in the file `wasabi_gpt_detection_results--table4.xlsx`

They were generated by the included script `llm-detection/analyze_files.py`, using the gpt-4-turbo model; however using this model on full files via the API (as we do) is costly and requires a billing account with OpenAI.

We hope artifact reviewers will review the script+raw results and find them sufficient. If not, any ideas on how to perform this review within an appropriate budget are welcome. We will do whatever we can to accomodate these requests.

