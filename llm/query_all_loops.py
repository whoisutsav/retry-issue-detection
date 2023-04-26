import os
import time
import random
import openai
import sys
import subprocess
from tqdm import tqdm


BASE_PROMPT="Does the following loop perform retry of a request? (yes/no)"


with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key

process = subprocess.Popen(['jar', 'tf', JAR_FILE],
                     stdout=subprocess.PIPE, 
                     stderr=subprocess.PIPE)
stdout, stderr = process.communicate()

classes=stdout.decode('UTF-8').splitlines()

for class_file in tqdm(classes):
    if class_file.endswith(".class"):
        class_file_short=class_file.replace(".class", "")
        javap_process = subprocess.Popen(['javap','-protected', '-classpath', JAR_FILE, class_file_short],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        stdout,stderr = javap_process.communicate()

        prompt_string=BASE_PROMPT+"\n\n"+class_sig
        messages=[
          {"role": "user", "content": prompt_string}
        ]
        response=None
        while response == None:
            try:
                response=openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages) 
            except:
                raise
                #time.sleep(3)
        content=response["choices"][0]["message"]["content"]
        classification="?"
        secondary_classification="?"
        if content.lower().startswith("yes"):
            classification="Y"
            secondary_classification="N"
        elif content.lower().startswith("no"):
            classification="N"
    
        
        output_line=class_file+SEPARATOR+class_sig+SEPARATOR+content+SEPARATOR+classification+SEPARATOR+content2+SEPARATOR+secondary_classification
        print(output_line.encode("unicode_escape").decode("utf-8"), file=output_file) 
        output_file.flush()

output_file.close()
