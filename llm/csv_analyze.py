#!/usr/bin/env python3
import os
import time
import random
import openai
import sys
import subprocess
from tqdm import tqdm



INPUT_CSV="state_machine_classes.csv"

with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key

with open(INPUT_CSV, "r") as f:
    lines=f.read().splitlines()



BASE_PATH = "./hbase-3.0.0-alpha3/hbase-server/src/main/java/"
PROMPT = "Does the following code contain retry-related bugs (yes/no)? If yes, please list the bugs\n\n"

OUTPUT_FILE_PATH="state_machine_retry_related_bug2.out"
SEPARATOR=";;;"

output_file=open(OUTPUT_FILE_PATH, "x")
print("Writing results to "+OUTPUT_FILE_PATH)

for line in tqdm(lines):
    cols=line.split(";;;")

    filename=cols[0]
    file_path=BASE_PATH+filename
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            code=f.read()
        prompt_string=PROMPT+"\n\n"+code
        messages=[
          {"role": "user", "content": prompt_string}
        ]
        response=None
        while response==None:
            try:
                response=openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages) 
            except openai.error.InvalidRequestError as e:
                break
            except:
                time.sleep(3)
        if response==None:
            continue
        content=response["choices"][0]["message"]["content"]

        classification="?"
        if content.lower().startswith("yes"):
            classification="Y"
        elif content.lower().startswith("no"):
            classification="N"
        print(filename+SEPARATOR+content+SEPARATOR+classification, file=output_file)
        output_file.flush()

output_file.close()
