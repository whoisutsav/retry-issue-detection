import os
import sys

CODEQL_DATABASES_DIR = "./databases"
DATABASES = [
#    "apache_cassandra_f0ad7ea",
    "apache_hadoop_ee7d178",
#    "apache_hbase_e1ad781",
#    "apache_hive_e427ce0",
#    "apache_kafka_c6590ee",
#    "apache_spark_1979169",
#    "apache_zookeeper_ab1bdad",
#    "elastic_elasticsearch_7556157"
]

if len(sys.argv) < 2:
    print("Usage: query.py QL_FILE") 
    sys.exit(1)

QUERY_FILE = sys.argv[1]

#for db in os.listdir(CODEQL_DATABASES_DIR):
for db in DATABASES:
    arr = db.split("_") 

    github_org = arr[0]
    app_name = arr[1]
    commit = arr[2]


    os.system(f'sed -e "s/%%GITHUB_NAMESPACE%%/{github_org}\/{app_name}/g" -e "s/%%COMMIT_SHA%%/{commit}/g" {QUERY_FILE} > temp_query.ql')
    os.system(f'codeql query run --database=./databases/{db} --additional-packs=. --verbosity=errors --output={app_name}.bqrs temp_query.ql')
    os.system(f'codeql bqrs decode --no-titles --entities=url --format=csv --verbosity=errors {app_name}.bqrs')
    os.system(f'rm {app_name}.bqrs temp_query.ql')

