import sys
import os
import getpass
import openai
import datetime
import random

models = {
    "llama":    "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    "mistral":  "mistralai/Mistral-7B-Instruct-v0.3",
    "qwen":     "Qwen/Qwen2.5-7B-Instruct-Turbo"
}
query_config = {
    "temperature": 0.7,
    "max_tokens": 512,
    "seed": 42
}
API_ENDPOINT = "https://api.together.xyz/v1"
DRY_RUN = True

def retrieve_api_key():
    """ Prompt user for API key or read it from file """
    base_dir = os.path.split(os.path.dirname(__file__))[0]
    key_file = os.path.join(base_dir, "api_key.txt")
    if os.path.isfile(key_file):
        with open(key_file, "r") as f:
            key = f.read()
    else:
        print(f"Please enter API key (will be stored in {key_file})")
        key = getpass.getpass("API key: ")
        with open(key_file, "w") as f:
            f.write(key)
    if len(key) != 64 or not key.isalnum():
        print("Invalid API key. Please delete", key_file)
        sys.exit(1)
    return key


class Wrapper:
    """ Wrapper around model object for bookkeeping """
    def __init__(self, model, system_prompt = None):
        self.model = models[model]
        self.client = None if DRY_RUN else openai.OpenAI(api_key=retrieve_api_key(), base_url=API_ENDPOINT)
        self.messages = []
        if system_prompt is not None:
            self.add_message("system", system_prompt)
    
    def add_message(self, role, content):
        """ Add message to conversation history """
        self.messages.append({
            "role": role,
            "content": content
        })

    def query(self, prompt):
        """ Prompt the model """
        self.add_message("user", prompt)
        return self._do_query()

    def _do_query(self):
        """ Actually query the model """
        assert self.messages[-1]["role"] == "user"

        if DRY_RUN:
            response = "random response " + str(random.randint(1000,9999))
            self.add_message("assistant", response)
            result = dict()
            result["model_response"] = response
            result["completion_tokens"] = 42
            result["timestamp"] = datetime.datetime.now().isoformat()
            result["latency_ms"] = 1234
            return result

        t0 = datetime.datetime.now()
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            max_tokens=query_config["max_tokens"],
            temperature=query_config["temperature"],
            seed=query_config["seed"]
        )
        t1 = datetime.datetime.now()

        response = completion.choices[0].message.content
        self.add_message("assistant", response)
        result = dict()
        result["model_response"] = response
        result["completion_tokens"] = completion.usage.completion_tokens
        result["timestamp"] = datetime.datetime.fromtimestamp(completion.created).isoformat()
        result["latency_ms"] = int((t1-t0).total_seconds()*1000)

        return result
