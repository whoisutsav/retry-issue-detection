import json
import os

BASE_DIR = "./goal-output/"

def load(path_to_file):
    toradocu_json = None
    with open(path_to_file) as fp: 
        toradocu_json = json.load(fp)

    examples = list()
    for obj in toradocu_json:
        arg_names = list(map(lambda x: x["name"], obj["parameters"]))
        for tag in obj["paramTags"]:
            examples.append({
                "signature": obj["signature"],
                "comment_full": "@param " + tag["parameter"]["name"] + "  " + tag["comment"],
                "comment": tag["comment"],
                "condition": tag["condition"],
                "kind": tag["kind"],
                "arg_names": arg_names})

        for tag in obj["throwsTags"]:
            examples.append({
                "signature": obj["signature"],
                "comment_full": "@throws " + tag["exceptionType"]["name"] + "  " + tag["comment"],
                "comment": tag["comment"],
                "condition": tag["condition"],
                "kind": tag["kind"],
                "arg_names": arg_names})

        if "returnTag" in obj:
            tag = obj["returnTag"]
            examples.append({
                "signature": obj["signature"],
                "comment_full": "@returns " + tag["comment"],
                "comment": tag["comment"],
                "condition": tag["condition"],
                "kind": tag["kind"],
                "arg_names": arg_names})

    return examples


def load_all(app_dir):
    examples = list()
    for toradocu_file in os.listdir(os.path.join(BASE_DIR, app_dir)):
        examples += load(os.path.join(BASE_DIR, app_dir, toradocu_file))
    return examples
