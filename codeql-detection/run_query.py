#!/usr/bin/env python3

import os
import sys

CODEQL_DATABASES_DIR = "./databases"
DATABASES = [
    "apache_hadoop_ee7d178",
    "apache_hbase_e1ad781",
    "apache_hive_e427ce0",
    "apache_cassandra_f0ad7ea",
    "elastic_elasticsearch_7556157",
]

if len(sys.argv) < 2:
    print("Usage: run_query.py PATH_TO_QUERY_FILE") 
    sys.exit(1)

QUERY_FILE = sys.argv[1]

for index, db in enumerate(DATABASES):
    arr = db.split("_") 

    github_org = arr[0]
    app_name = arr[1]
    commit = arr[2]

    path_to_db = os.path.join(CODEQL_DATABASES_DIR, db)

    incl_headers_flag = "--no-titles" if index != 0 else ""

    os.system(f'sed -e "s/%%GITHUB_ORG%%/{github_org}/g" -e "s/%%APP_NAME%%/{app_name}/g" -e "s/%%COMMIT_SHA%%/{commit}/g" {QUERY_FILE} > temp_query.ql')
    os.system(f'codeql query run --database=./{path_to_db} --additional-packs=. --verbosity=errors --output={app_name}.bqrs temp_query.ql')
    os.system(f'codeql bqrs decode {incl_headers_flag} --entities=url --format=csv --verbosity=errors {app_name}.bqrs')
    os.system(f'rm {app_name}.bqrs temp_query.ql')
