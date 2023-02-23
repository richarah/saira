import os
import re
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up authentication with the Hugging Face Inference API
hf_api_key = os.getenv("HF_API_KEY")
hf_api_url = os.getenv("HF_API_URL")
headers = {"Authorization": f"Bearer {hf_api_key}"}

def query_hf(payload):
    data = json.dumps(payload)
    response = requests.request("POST", hf_api_url, headers=headers, data=data)
    return json.loads(response.content.decode("utf-8"))


def read_prompt_file(filename):
    with open(filename, 'r') as file:
        text = file.read()
    name = filename.split('.')[0].title()
    return text, name

INIT_CONTEXT, AI_NAME = read_prompt_file(input("Prompt file name: "))

# Chatbot name, terminator string and personality
STR_END="|"

# Min length of responses
SOFT_MIN_RESPONSE_LENGTH=20
HARD_MIN_RESPONSE_LENGTH=3

# Max iterations before switching from soft to hard
SOFT_MAX_ITERATIONS = 3
HARD_MAX_ITERATIONS = 10

# Generates a bit of text
def generate_snippet(context):
    data = query_hf({
    "inputs": context,
    "options": {"wait_for_model": True},
    "parameters": {
        "max_length": 400,
        "temperature": 0.9,
        "top_p": 0.67,
        "repetition_penalty": 1,
        "presence_penalty": 1,
        "frequency_penalty": 1,
        "num_return_sequences": 1,
    }
    })
    # snippet = data[0]['generated_text'].replace(init_prompt, "")
    snippet = data[0]['generated_text']
    return snippet

# Due to strip() and rstrip() not working properly in certain cases
def strip_response(string, terminator):
    index = repr(string).find(terminator)
    return string[:index]

def rstrip_response(string, terminator):
    index = repr(string).rfind(terminator)
    return string[:index]

# Generate response from snippets, extract
def generate_response(context, prompt, max_len=800):
    original_context = context + "\n" + prompt + "\n Me:"
    response_context = generate_snippet(original_context)
    while True:
        # Generate next snippet
        response_context = generate_snippet(response_context)
        response = response_context.replace(original_context, "").strip()

        # Terminator string detected
        if STR_END in response:
            # Strip everything right of terminator
            response = strip_response(response, STR_END)
        # This is not supposed to happen but it does
        elif "Anon" in response:
            # Strip everything right of training character
            response = strip_response(response, "Anon")
        elif "\n" in repr(response):
            # Strip everything right of newline
            response = strip_response(response, "\n")
        elif len(response) > max_len:
            response = rstrip_response(response, ".") + "."
        return response.replace(STR_END, "")

# Main loop
convo = INIT_CONTEXT
name = input("Enter your name: ")
while True:
    prompt = (name + ": " + input(name + ": ") + STR_END)
    #Generate response. Regenerate if too short
    i = 0
    while True:
        generated = generate_response(convo, prompt)
        i += 1
        response = AI_NAME + ": " + generated
        if i >= HARD_MAX_ITERATIONS:
            # Blank response if we give up. Also DO NOT log to convo
            response = AI_NAME + ": " + "..."
            break
        elif (len(generated) >= SOFT_MIN_RESPONSE_LENGTH) or ((len(generated) >= HARD_MIN_RESPONSE_LENGTH) and i >= SOFT_MAX_ITERATIONS):
            # Disable logging
            # convo = convo + prompt + STR_END + response + STR_END
            break
    print(response)

# print(generate_response(context, "Anon: Saira, tell me a little about yourself."))
