#!/usr/bin/env python3
import os
import sys
import subprocess
from tqdm import tqdm

#format: file,start_line,end_line
FRAGMENT_LOCATIONS = "hbase_tests_named_retry"
OUTPUT_DIR = "./fragments/hbase_retry_tests/"
SOURCE_DIR = "./repos/hbase_e1ad781/"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
elif len(os.listdir(OUTPUT_DIR)) != 0:
    print("Output directory is not empty. Exiting")
    sys.exit(1)

with open(FRAGMENT_LOCATIONS, "r") as f:
    lines = f.readlines()
    for line in tqdm(lines):
        cols = line.split(',')
        if len(cols) < 3:
            continue

        relative_path=cols[0][1:-1]
        source_file=SOURCE_DIR+relative_path
        start_line=int(cols[1])
        end_line=int(cols[2])

        if not relative_path.startswith("src/java/org/apache/cassandra/db") or start_line==end_line:
            continue

        output_file=OUTPUT_DIR+relative_path.replace(".", "_").replace("/","_")+"_"+str(start_line)+"_"+str(end_line)
        with open(output_file, "w") as f2:
            print(relative_path, file=f2)
            print(start_line, file=f2)
            print(end_line, file=f2)
        cmd = f"sed -n '{start_line},{end_line}p;{end_line+1}q' {source_file} | clang-format --assume-filename='.java' >> {output_file}"
        subprocess.run(cmd,shell=True)
        
