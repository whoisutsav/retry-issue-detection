#!/usr/bin/env python3

import os
import sys
import openai
import time
from tqdm import tqdm
from methods import METHODS

BASE_PROMPT="Define a task as a runnable or message class that encapsulates work to be performed. Define a task queue as a queue or executor object which holds tasks to be executed. \n\nDoes the following java code contain a task queue anywhere (yes/no)?"

FOLLOWUP_PROMPTS = [
    "Does the java code contain logic that checks if a task failed or catches exceptions from a task (yes/no)?",
    "Does the java code contain logic that resubmits the failed task to the task queue (yes/no)?",
    "Please give the line numbers where (1) the task queue is defined, (2) task failures or exceptions are caught and (3) the task is resubmitted to a task queue"
]
DIRECTORY="./repos/cassandra_f0ad7ea/src/java/org/apache/cassandra/db/"

with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key

#with open("cassandra_queue_retry") as f:
#    analyzed=f.read()

print(BASE_PROMPT, file=sys.stdout)

def classify(content_str):
    if content_str.lower().startswith("yes"):
        return "Y"
    elif content_str.lower().startswith("no"):
        return "N"
    else:
        return "?"


for subdir, dirs, files in tqdm(list(os.walk(DIRECTORY))):
    for file in files:
        if not file.endswith(".java"):
            continue

        
        full_path = os.path.join(subdir, file)

#        if full_path in analyzed:
#            continue


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

        if classify(content) != "Y":
            followup_contents=["N/A","N/A","N/A"]
        else:
            followup_contents=[]
            latest_content=content
            for followup_prompt in FOLLOWUP_PROMPTS:
                messages+=[{"role":"assistant","content":latest_content}]

                messages+=[
                  {"role": "user", "content": followup_prompt}
                ]
                response2=None
                while response2 == None:
                    try:
                        response2=openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages) 
                    except openai.error.InvalidRequestError as e:
                        break
                    except:
                        time.sleep(3)

                if response2 == None:
                    latest_content="### INVALID REQUEST ERROR ###" 
                else:
                    latest_content=response2["choices"][0]["message"]["content"]

                followup_contents.append(latest_content)

            
        output_line=";;;".join([full_path, content, classify(content)] + followup_contents + [classify(followup_contents[0]), classify(followup_contents[1]), classify(followup_contents[2])])
        print(output_line.encode("unicode_escape").decode("utf-8"), file=sys.stdout) 


#FILES=[
#    "src/main/java/org/apache/hadoop/hbase/regionserver/ServerNonceManager.java",
#    "src/main/java/org/apache/hadoop/hbase/master/MasterWalManager.java",
#    "src/main/java/org/apache/hadoop/hbase/master/procedure/SplitWALProcedure.java",
#    "src/main/java/org/apache/hadoop/hbase/master/procedure/InitMetaProcedure.java",
#    "src/main/java/org/apache/hadoop/hbase/master/procedure/SwitchRpcThrottleProcedure.java",
#    "src/main/java/org/apache/hadoop/hbase/master/procedure/ReopenTableRegionsProcedure.java",
#    "src/main/java/org/apache/hadoop/hbase/master/replication/ModifyPeerProcedure.java",
#    "src/main/java/org/apache/hadoop/hbase/master/replication/SyncReplicationReplayWALRemoteProcedure.java",
#]

#arr=[0]
#for i in arr:
#    for method in METHODS:
#        full_path=method["file"]
#        code=method["content"]

#        check=False
#        for myf in FILES:
#            if myf in full_path:
#                check=True
#
#        if check==False:
#            continue
