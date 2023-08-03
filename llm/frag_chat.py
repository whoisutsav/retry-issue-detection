#!/usr/bin/env python3

import os
import time
import random
import openai
import sys
import subprocess
import tiktoken
from tqdm import tqdm

FRAGMENT_DIR="./fragments/hadoop_common_methods/"
SOURCE_DIR="./repos/hadoop_ee7d178/"

with open("./hadoop_common_stream_read",'r') as f:
    checkpoint_data=f.read()

PROMPTS=[
        {
            "prompt":"Does the following code retry a stream read on failure? Please answer yes or no.",
            "model":"gpt-3.5-turbo",
        },
        {
            "prompt":"Here is the full class code. Is it possible for a stream read failure in the method above to be retried WITHOUT the stream being re-opened or reset? Assume all other code works correctly.",
            "model":"gpt-4",
            "append_file_contents":True
        }
    ]

def get_token_count(messages):
    content=""
    for message in messages:
        content+=message["content"]

    encoding=tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(content))

def query(messages,model):
    if get_token_count(messages) > 8192:
        return "TOO_LONG"

    for i in range(2):
        try:
            response=openai.ChatCompletion.create(model=model, messages=messages) 
            return response["choices"][0]["message"]["content"]
        except openai.error.InvalidRequestError as e:
            sys.stderr.write("Invalid request error: " + str(e))
            sys.stderr.flush()
            return "TOO_LONG" 
        except Exception as e:
            sys.stderr.write("Error: "+str(e))
            sys.stderr.flush()
            time.sleep(60 if model=="gpt-4" else 3)

    return "FAILED"


with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key

print(PROMPTS)

for file in tqdm(sorted(os.listdir(FRAGMENT_DIR))):
    with open(os.path.join(FRAGMENT_DIR,file)) as f: 
        lines=f.readlines()

    messages=[]
    responses=[]
    keep_querying=True

    if file in checkpoint_data:
        continue
    
    for i in range(len(PROMPTS)):
        if i==0:
            messages=[
              {"role": "user", "content": PROMPTS[0]["prompt"]+"\n\n"+"".join(lines[3:])
}
            ]
        else:
            if PROMPTS[i]["append_file_contents"]:
                with open(SOURCE_DIR+lines[0].strip()) as f:
                    code=f.read()
                content=PROMPTS[i]["prompt"]+"\n\n"+code
            else:
                content=PROMPTS[i]["prompt"]

            messages += [{"role":"user", "content":content}]

        if keep_querying:
            response=query(messages, PROMPTS[i]["model"])
        else:
            response="NA"

        if not "yes" in response.lower():
           keep_querying=False 

        responses.append(response)
        messages += [{"role":"assistant","content":response}] 

    
    output_line=";;;".join([file,lines[0],lines[1],lines[2]]+responses)
    print(output_line.encode("unicode_escape").decode("utf-8"), file=sys.stdout) 
    sys.stdout.flush()

