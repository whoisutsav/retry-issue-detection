import openai
import random
import time
import util
import re
import sys
from string import Template

# Experiment parameters
# ENGINE_NAME = "text-davinci-001"
# ENGINE_NAME = "code-davinci-002"

TEMP = 0.7
NUM_COMPLETIONS = 1
NUM_SHOTS = 5
APP_NAME = "commons-math3-3.6.1"
# Replace indexed-arguments with named arguments
REPLACE_ARGS = True
# Algorithm for choosing context examples
# Options: "arg_count", "mitigation", "mitigation2", "none"
CONTEXT_SELECTION = "mitigation2"
START_TEXT = "Summarize in code"
SHOT_TEMPLATE = "Comment: $comment\nSignature: $signature\nOutput: $condition"
DRY_RUN = False

# Load API key
with open("openai.key") as f:
    key = f.readline().strip()
    openai.api_key = key


# Preprocess examples
def preprocess_example(example):
    condition_new = example["condition"]

    # Convert positional args (e.g. args[0]) to arg names (e.g. "myVal")
    if REPLACE_ARGS:
        for idx, name in enumerate(example["arg_names"]):
            condition_new = condition_new.replace("args[" + str(idx) + "]", name)

    example["condition"] = condition_new
    return example


# Select context examples based on our query ("test_example")
def get_context_examples(count, test_example, context_bank):
    if count > len(context_bank):
        raise IndexError

    # choose context examples with same number of arguments
    if CONTEXT_SELECTION == "arg_count":
        filtered = list(filter(lambda x: len(x["arg_names"]) == len(test_example["arg_names"]), context_bank))
        return random.sample(filtered, min(count, len(filtered)))
    elif CONTEXT_SELECTION == "mitigation":
        examples = list()
        # include 1-2 untranslatable examples
        examples += random.sample(list(filter(lambda x: x["condition"] == "", context_bank)), 1)
        # include in-array examples
        examples += random.sample(list(filter(lambda x: "array" in x["comment"], context_bank)), 1)

        # include portion-argument examples
        def uses_only_portion_args(example):
            for arg_name in example["arg_names"]:
                if arg_name not in example["condition"]:
                    return True
            return False

        examples += random.sample(list(filter(uses_only_portion_args, context_bank)), 1)
        # remainder arg-count
        remainder = list(filter(lambda x: len(x["arg_names"]) == len(test_example["arg_names"]), context_bank))
        examples += random.sample(remainder, min(2, len(remainder)))
        return examples
    elif CONTEXT_SELECTION == "mitigation2":
        examples = list()
        # include 1-2 untranslatable examples
        # examples += random.sample(list(filter(lambda x: x["condition"]=="", context_bank)), 1)
        # include in-array examples
        examples += random.sample(list(filter(lambda x: "array" in x["comment"], context_bank)), 2)

        # include portion-argument examples
        def uses_only_portion_args(example):
            for arg_name in example["arg_names"]:
                if arg_name not in example["condition"]:
                    return True
            return False

        examples += random.sample(list(filter(uses_only_portion_args, context_bank)), 2)
        # remainder arg-count
        remainder = list(filter(lambda x: len(x["arg_names"]) == len(test_example["arg_names"]), context_bank))
        examples += random.sample(remainder, min(2, len(remainder)))
        return examples
    else:
        return random.sample(context_bank, count)


def generate_prompt(test_example, context_bank, num_shots):
    prompt = START_TEXT + "\n\n"

    t = Template(SHOT_TEMPLATE)

    for context_example in get_context_examples(num_shots, test_example, context_bank):
        prompt += t.substitute(comment=context_example["comment"], signature=context_example["signature"],
                               condition=context_example["condition"]) + "\n\n"
    prompt += t.substitute(comment=context_example["comment"], signature=context_example["signature"], condition="")

    return prompt


def query_model(prompt_text, engine, top_k):
    temp = 0
    response = openai.Completion.create(
        engine=engine,
        prompt=prompt_text,
        temperature=temp,
        max_tokens=30,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        n=1,
        best_of=top_k
    )
    return response


def print_headers():
    print(
        f'Experiment parameters: engine:{ENGINE_NAME},temp:{TEMP},start_text:{START_TEXT},num_shots:{NUM_SHOTS},num_completions:{NUM_COMPLETIONS},app_name:{APP_NAME},replace_args:{REPLACE_ARGS},context_selection:{CONTEXT_SELECTION},shot_template:{SHOT_TEMPLATE}')
    print("prompt;;;query;;;output_expected;;;output_actual;;;top_correct;;;any_correct")


def print_result(result):
    top_correct = re.sub(r'\s+', '', result["outputs"][0]) == re.sub(r'\s+', '', result["test_example"]["condition"])
    any_correct = re.sub(r'\s+', '', result["test_example"]["condition"]) in list(
        map(lambda x: re.sub(r'\s+', '', x), result["outputs"]))
    # print(
    #         repr(result["prompt"])+";;;"+
    #         repr(result["test_example"]["comment"])+";;;"+
    #         repr(result["test_example"]["condition"])+";;;"+
    #         repr(','.join(result["outputs"]))+";;;"+
    #         repr(top_correct)+";;;"+
    #         repr(any_correct))
    print("*** start of prompt ***")
    print(result["prompt"])
    print("*** end of prompt ***")

    print("")

    print("*** start of test_example - comment")
    print(result["test_example"]["comment"])
    print("*** end of test_example - comment")

    print("")

    print("*** start of test_example - conditon")
    print(result["test_example"]["condition"])
    print("*** end of test_example - conditon")

    print("")

    print("*** start of output ***")
    print(','.join(result["outputs"]))
    print("*** end of output ***")

    print("")

    # print("*** start of top_correct ***")
    # print(top_correct)
    # print("*** end of top_correct ***")
    #
    # print("")
    #
    # print("*** start of any_correct ***")
    # print(any_correct)
    # print("*** end of any_correct ***")


def run_experiment(test_example, context_bank, num_shots):
    prompt = generate_prompt(test_example, context_bank, num_shots)

    outputs = ["dry_run"]
    if not DRY_RUN:
        response = query_model(prompt)
        outputs = list(map(lambda x: x["text"], response["choices"]))

    return {
        "prompt": prompt,
        "test_example": test_example,
        "outputs": outputs,
        "response": response
    }


def run_and_print(context_bank, num_shots, test_examples):
    print_headers()

    results = list()
    count = 0
    for example in test_examples:
        try:
            result = run_experiment(example, context_bank, num_shots)
            print(f"**************** EXAMPLE {count} ****************")
            print_result(result)
        except Exception as e:
            print("Exception: " + str(e), file=sys.stderr)

        time.sleep(0.5 if ENGINE_NAME == "text-davinci-001" else 3.5)  # greater throttling if using codex
        print(f"**************** END OF EXAMPLE {count} ****************")
        count += 1

