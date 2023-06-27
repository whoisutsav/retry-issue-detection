#!/usr/bin/env python3

import os
import time
import random
import openai
import sys
import subprocess
from tqdm import tqdm
# Import the xml module
import xml.etree.ElementTree as ET

def get_config_params():
    params=[]
    # Read the hadoop core-default.xml file as a string
    with open('tmp.xml', 'r') as f:
        xml_string = f.read()
    
    # Strip the comments and spaces from the xml string
    xml_string = ET.tostring(ET.fromstring(xml_string), encoding='unicode')
    
    # Parse the xml string
    tree = ET.ElementTree(ET.fromstring(xml_string))
    
    # Get the root element
    root = tree.getroot()
    
    # Iterate through all the property elements
    for prop in root.findall('property'):
        # Get the name and description elements
        name = prop.find('name')
        description = prop.find('description')
    
        if name != None and description != None:
            params.append({'name':name.text.strip(),'description':description.text.strip()})

    return params


BASE_PROMPT="Does the following configuration parameter specify a maximum number of attempts or retries (yes/no)?"

with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key

#output_file=open(OUTPUT_FILE, "x")

print(BASE_PROMPT)

for param in tqdm(get_config_params()):
    prompt_string=BASE_PROMPT+"\n\n"+"Name: "+param['name']+"\nDescription: "+param['description']
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
    
    output_line=";;;".join([param['name'],param['description'].replace('\n', ' '),content,classification])
    print(output_line.encode("unicode_escape").decode("utf-8"), file=sys.stdout) 
    sys.stdout.flush()
    #output_file.flush()

#output_file.close()
