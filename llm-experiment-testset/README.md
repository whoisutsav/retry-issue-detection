# LLM experiment testset

Contains a labeled test set of retry-related files and experiment script that can be used to fine-tune an LLM prompt.

Current labeling includes:
* Whether file contains retry
* (If yes) whether retry includes delay
* (If yes) the retry has a cap or timeout

## How to use

1. Put your OpenAI key in a file named `openai.key`
2. `python3 run_experiment.py` 

**Note:** this should not be submitted as part of the artifact. 
