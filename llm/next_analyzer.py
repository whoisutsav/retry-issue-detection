import os
import time
import random
import openai
import sys
import subprocess
from tqdm import tqdm



INPUT_CSV="output.csv"

with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key

with open(INPUT_CSV, "r") as f:
    lines=f.read().splitlines()



BASE_PATH = "./hbase/hbase-server/src/main/java/"
PROMPT = "Does the following java code contain retry functionality (yes/no)? If yes, please list in which methods a retry is performed, and which errors trigger retry"

OUTPUT_FILE_PATH="code_analysis2.out"
SEPARATOR=";;;"

output_file=open(OUTPUT_FILE_PATH, "x")
print("Writing results to "+OUTPUT_FILE_PATH)

for line in tqdm(lines):
    cols=line.split(";;;")
    if cols[2]=="Y":
        filename=cols[0].replace(".class",".java")
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
            print(filename+SEPARATOR+content, file=output_file)
            output_file.flush()

output_file.close()
