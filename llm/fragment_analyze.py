#!/usr/bin/env python3

import os
import time
import random
import openai
import sys
import subprocess
from tqdm import tqdm

LOOP_DIR="./fragments/cassandra_methods/"
BASE_PROMPT="Does the following method resubmit a task to a queue on failure? (yes/no)?"

with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key

#output_file=open(OUTPUT_FILE, "x")

print(BASE_PROMPT)

for file in tqdm(sorted(os.listdir(LOOP_DIR))):
    with open(os.path.join(LOOP_DIR,file)) as f: 
        lines=f.readlines()
    prompt_string=BASE_PROMPT+"\n\n"+"".join(lines[3:])
    messages=[
      {"role": "user", "content": prompt_string}
    ]
    response=None
    while response == None:
        try:
            response=openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages) 
        except openai.error.InvalidRequestError as e:
            break
        except:
            time.sleep(3)

    if response == None:
        continue
    content=response["choices"][0]["message"]["content"]
    classification="?"
    if content.lower().startswith("yes"):
        classification="Y"
    elif content.lower().startswith("no"):
        classification="N"
    
    output_line=";;;".join([file,lines[0],lines[1],lines[2],content,classification])
    print(output_line.encode("unicode_escape").decode("utf-8"), file=sys.stdout) 
    sys.stdout.flush()
    #output_file.flush()

#output_file.close()
