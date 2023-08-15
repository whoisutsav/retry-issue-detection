#!/usr/bin/env python3

import os
import sys
import openai
import time
import tiktoken
from tqdm import tqdm

PROMPTS=[
        "Does the following code perform retry anywhere? Please answer yes or no.",
        "In which method is retry performed?"
        ]
DIRECTORY="./repos/kafka_c6590ee/"

with open("./kafka_has_retry_checkpoint",'r') as f:
    checkpoint_data=f.read()

def get_token_count(messages):
    content=""
    for message in messages:
        content+=message["content"]

    encoding=tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(content))

def query(messages,model):
    token_count = get_token_count(messages)

    if model=="gpt-4":
        if  8192 < token_count < 32678:
            model="gpt-4-32k" 
        elif token_count > 32678:
            return "FAILED"

    for i in range(2):
        try:
            response=openai.ChatCompletion.create(model=model, messages=messages) 
            return response["choices"][0]["message"]["content"]
        except openai.error.InvalidRequestError as e:
            sys.stderr.write("Invalid request error: " + str(e))
            sys.stderr.flush()
            return "FAILED"
        except Exception as e:
            sys.stderr.write("Error: "+str(e))
            sys.stderr.flush()
            time.sleep(60 if "gpt-4" in model else 3)

    return "FAILED"

with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key


print(PROMPTS, file=sys.stdout)

for subdir, dirs, files in tqdm(list(os.walk(DIRECTORY))):
    for file in files:
        if not (file.endswith(".java") or file.endswith(".scala")) or "/test/" in subdir:
            continue

        full_path = os.path.join(subdir, file)
        if full_path in checkpoint_data:
            continue


        with open(full_path) as f:
            code=f.read()
        
        responses=[]
        keep_querying=True

        for i,prompt in enumerate(PROMPTS):
            if i==0:
                messages=[{"role": "user", "content": prompt+"\n\n"+code}]
            else:
                messages += [{"role":"user","content":prompt}]
            
            if keep_querying==False:
                content="NA"
            else:
                content=query(messages, "gpt-4")

            if not "yes" in content.lower():
                keep_querying=False

            responses.append(content)
            messages+=[{"role":"assistant","content":content}]


        output_line=";;;".join([full_path]+responses)
        print(output_line.encode("unicode_escape").decode("utf-8"), file=sys.stdout) 
        sys.stdout.flush()

