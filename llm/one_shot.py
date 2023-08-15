#!/usr/bin/env python3

import os
import time
import random
import openai
import sys
import subprocess
from tqdm import tqdm

MODEL="gpt-4-32k"
BASE_PROMPT="Does the following code contain a retry counter variable?"

if len(sys.argv) < 2:
    print("Usage: one_shot.py SOURCE_FILE")
    sys.exit(1)

data_file = sys.argv[1]

with open(data_file, "r") as f:
    java_code=f.read()

with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key


print(BASE_PROMPT + "\n[contents of "+data_file+"]")
prompt_string=BASE_PROMPT+"\n\n"+java_code
messages=[
  {"role": "user", "content": prompt_string}
]
response=openai.ChatCompletion.create(model=MODEL, messages=messages) 
content=response["choices"][0]["message"]["content"]
print(content+"\n")
