#!/usr/bin/env python3

import os
import sys
import openai
import time
from tqdm import tqdm

BASE_PROMPT="Does the following code contain a cancel-related bug?"
DIRECTORY="./repos/hbase-3.0.0-alpha3/hbase-server/"
#OUTPUT_FILE="analyze_all_files.out"

with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key

#if os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) == 0:
#    os.remove(OUTPUT_FILE)

#output_f = open(OUTPUT_FILE, "x")

print(BASE_PROMPT, file=sys.stdout)

for subdir, dirs, files in tqdm(list(os.walk(DIRECTORY))):
    for file in files:
        if not file.endswith(".java"):
            continue

        full_path = os.path.join(subdir, file)
        with open(full_path) as f:
            code=f.read()

        prompt_str = BASE_PROMPT+"\n\n"+code
        messages=[
          {"role": "user", "content": prompt_str}
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
            content="### INVALID REQUEST ERROR ###" 
        else:
            content=response["choices"][0]["message"]["content"]

        if content.lower().startswith("yes"):
            classification="Y"
        elif content.lower().startswith("no"):
            classification="N"
        else:
            classification="?"
        
        output_line=";;;".join([full_path, content, classification])
        print(output_line.encode("unicode_escape").decode("utf-8"), file=sys.stdout) 
        #output_f.flush()

#output_f.close()
