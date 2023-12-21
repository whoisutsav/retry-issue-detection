#!/usr/bin/env python3

import os
import sys
import openai
import time
import tiktoken
import csv
import pandas as pd
from tqdm import tqdm

MODEL_NAME="gpt-4-1106-preview"
SYSTEM_PROMPT="You are a Java expert software engineer. \
A user will ask questions about source code. \
The source code is included in initial prompt. \
For every question, the user specifies the \
format or potential answers that you need to choose from."
CHAT_PROMPTS=[
    
"Here's the source code, starting and ending with triple quotes.\n\n'''%%FILE_CONTENTS%%'''\n\n \
Here is the question with notes:\n \
1. Does the following code perform retry anywhere? Answer (Yes) or (No).\n \
- Say NO if the file only _defines_ or _creates_ retry policies, or only passes retry parameters to other builders/constructors.\n \
- Say NO if the file does not check for exception or errors before retry. \n \
- Say NO if the file only retries polling or setting of atomic variables (e.g. \"compareAndSet\"). \n \
**Remember that retry mechanisms can be implemented through \"for\" or \"while\" loops or data structures like state machines and queues.**",
    
"2. Does the code sleep before retrying or resubmitting the request? Answer (Yes) or (No).\n**Remember that delay might be implemented through scheduling after an interval or some other mechanism.**",
    
"3. Does the code have a cap OR time limit on the number times a request is retried or resubmitted? Answer (Yes) or (No).\n**Remember that timeouts or caps should be specifically applied to retry and not other behaviors**",

"4. What methods implement retry logic? Provide a comma separated list of the method name(s) only",
]

SOURCES_DIR="./testset_combined/"
LABEL_CSV="./testset_combined.csv"

def print_acc_stats(header_str, matched_df, base_df):
    if(len(base_df.index) == 0):
        print(header_str+" N/A - DATAFRAME EMPTY")
    else:
        print("{}: {}/{} ({}%)".format(header_str, len(matched_df.index), len(base_df.index), int(100*len(matched_df.index)/len(base_df.index))))

def compare_results(merged_df):

    print_acc_stats("Has retry [yes] accuracy: ", merged_df.query('has_retry_gpt==True and has_retry==True'), merged_df.query('has_retry_gpt==True'))
    print_acc_stats("Has retry [all] accuracy: ", merged_df.query('(has_retry_gpt==True and has_retry==True) or (has_retry_gpt==False and has_retry==False)'), merged_df)
    print_acc_stats("Has sleep [no] accuracy: ", merged_df.query('has_sleep_gpt==False and has_sleep==False'), merged_df.query('has_sleep_gpt==False'))
    print_acc_stats("Has cap [no] accuracy: ", merged_df.query('has_cap_gpt==False and has_cap==False and has_timeout==False'), merged_df.query('has_cap_gpt==False and not (has_retry == True and has_timeout == "N/A")'))
    
    #print("Has retry [yes] FP:\n" + merged_df.query('has_retry_gpt==True and has_retry==False').to_string())
    #print("Has retry [all] FP:\n" + merged_df.query('has_retry_gpt==False and has_retry==True').to_string())
    #print("Has sleep [no] FP:\n" + merged_df.query('has_sleep_gpt==False and has_sleep != False').to_string())
    print("Has cap [no] FP:\n" + merged_df.query('has_cap_gpt==False and (has_cap == True or has_timeout == True or has_retry==False)').to_string())


with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key

def booleanize_df(df, columns):
    def convert(x):
        if "yes" in str(x).lower():
            return True
        elif "no" in str(x).lower():
            return False
        else:
            return x

    columns=list(set(columns).intersection(df.columns))
    booleanized_df = df.copy()
    booleanized_df[columns]=booleanized_df[columns].map(convert)
    return booleanized_df

def get_ground_truth_labels(file_path):
    dict_array = []

    with open(file_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            dict_array.append(dict(row))

    return dict_array

def get_token_count(messages):
    content=""
    for message in messages:
        content+=message["content"]

    encoding=tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(content))

def query(messages,model):
    token_count = get_token_count(messages)

    if 8192 < token_count:
        return "TOO_LONG"

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
            time.sleep(3)

    return "FAILED"



print(CHAT_PROMPTS, file=sys.stdout)
structured_output=[]

file_labels_df=pd.read_csv(LABEL_CSV).fillna("N/A")
file_labels_df=booleanize_df(file_labels_df,["has_retry", "has_sleep", "has_cap", "has_timeout"])

#temporarily only look at timeout ones
#file_labels_df=file_labels_df[file_labels_df["has_timeout"] != "N/A"]

for source_file in tqdm(file_labels_df["file_name"]):
   #if not (source_file.endswith(".java") or source_file.endswith(".scala")) or "/test/" in subdir:
   #    continue

   full_path = os.path.join(SOURCES_DIR, source_file)

   #if full_path not in checkpoint_data:
   #    continue

   with open(full_path) as f:
       code=f.read()
   
   messages=[{"role":"system", "content":SYSTEM_PROMPT}]
   responses=[]
   keep_querying=True

   for i,prompt in enumerate(CHAT_PROMPTS):
       messages += [{"role":"user","content":prompt.replace("%%FILE_CONTENTS%%",code)}]
       
       if keep_querying==False:
           content="N/A"
       else:
           content=query(messages, MODEL_NAME)

       if i==0 and not "yes" in content.lower():
           keep_querying=False

       #if "yes" in content.lower():
       #    content="Yes"
       #else:
       #    content="No"

       responses.append(content)
       messages+=[{"role":"assistant","content":content}]

       #if i==1:
       #    print(content)


   output_line=";;;".join([full_path]+responses)
   structured_output+=[{
       "file_name":source_file, 
       "has_retry_gpt":responses[0], 
       "has_sleep_gpt":responses[1],
       "has_cap_gpt":responses[2],
       "method_names":responses[3],
       }]
   #print(structured_output)
   #print(output_line.encode("unicode_escape").decode("utf-8"), file=sys.stdout) 
   sys.stdout.flush()


result_df=pd.DataFrame(structured_output)
result_df=booleanize_df(result_df, ["has_retry_gpt", "has_sleep_gpt", "has_cap_gpt"])

merged_df=pd.merge(result_df, file_labels_df, on='file_name', how='left')
merged_df.to_csv('output_temp.csv', sep=";", index=False)

compare_results(merged_df)

