#!/bin/bash

#USAGE ./run_queries.sh QL_FILE [APP_NAME]

OUTPUT_DIR=output
#APPS=(cassandra hadoop hbase hive spark zookeeper kafka) 
APPS=(apache_hadoop_ee7d178)


if [ "$#" -eq 2 ]; then
	APPS=($2) 
fi

for app_name in "${APPS[@]}" 
do
  mkdir -p $OUTPUT_DIR 
  #echo "Running query ${QUERY_FILE} on app ${app_name}"
  #codeql database analyze ./databases/$app_name --format=csv --output=$OUTPUT_DIR/$1.$app_name.csv --rerun $1 
  codeql query run --database=./databases/$app_name --additional-packs=. --verbosity=errors --output=$1.$app_name.bqrs $1 
  codeql bqrs decode --no-titles --entities=url --format=csv --verbosity=errors $1.$app_name.bqrs
  rm $1.$app_name.bqrs
done
