import openai # TODO : pull in the LLM wrappers from one of the vibe coded projects
import os
from typing import Optional

def get_client():
    client = None
    if client is not None:
        return client
    client = openai.OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
    return client

def complete(
        text_in: str,
        sys_prompt: str,
        client = None,
        ai_is_called = "AI",
        human_is_called = "HUMAN",
):
    if client is None:
        client = get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini", # TODO, try other models
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": text_in}, # I hope this is the right slot for this
            ],
        temperature=0.9,
        max_tokens=650,
    )
    raw_response = response.choices[0].message.content.strip()
    after_last_ai_response = raw_response.split(f"[{ai_is_called}]")[-1]
    last_ai_response = after_last_ai_response.split(f"[{human_is_called}]")[0]
    return last_ai_response

class Convo:
    def __init__(
            self,
            system_prompt: str,
            first_ai_message: str = "Hello!",
            ai_is_called = "AI",
            human_is_called = "HUMAN",
    ):
        self.client = get_client()
        self.said = []
        self.last_ai_message = first_ai_message
        self.last_human_message = ""
        self.system_prompt = system_prompt
        self.ai_is_called = ai_is_called
        self.human_is_called = human_is_called

    def get_said(self):
        result = ""
        for p in self.said:
            result += f"[{self.ai_is_called}]{p[0]}\n"
            result += f"[{self.human_is_called}]{p[1]}\n"
        return result + f"[{self.ai_is_called}]{self.last_ai_message}"

    def process_human(self, human_msg):
        self.last_human_message = human_msg
        self.said.append((
            self.last_ai_message,
            human_msg,
        ))
        self.last_ai_message = ""
        prompt = "\n".join([
            "What follows is a conversation between yourself, and a",
            f" being, {self.human_is_called}.",
            "Your lines in the coversation are preceded by the string ",
            f"'[{self.ai_is_called}]',",
            " while your human partner's lines are preceded by the string ",
            f"[{self.human_is_called}]."
            " Your task is to complete any unfinished lines assigned ",
            f"via the last occuring '[{self.ai_is_called}]' prefix.",
            "", "", "", self.get_said(),
        ])
        self.last_ai_message = complete(
            prompt,
            sys_prompt=self.system_prompt,
            client=self.client,
        )
        return self.last_ai_message

if __name__ == '__main__':
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--human-is-called', '-u',
        default="HUMAN",
        help="What you want to be referred to in the dialog",
    )
    parser.add_argument(
        '--ai-is-called', '-a',
        default="AI",
        help="What you want the AI to think its name is in the dialog",
    )
    parser.add_argument(
        '--system-prompt-file',
        '-s',
        type=Path,
        default=None,
        help="File containing system prompt",
    )
    args = parser.parse_args()

    system_prompt = "You are role-playing as an angry toaster from dimension X"

    if args.system_prompt_file is not None:
        with open(args.system_prompt_file) as infile:
            system_prompt = infile.read()
    convo = Convo(
        system_prompt=system_prompt,
        ai_is_called=args.ai_is_called,
        human_is_called=args.human_is_called,
    )
    while convo.last_human_message.lower().find('quit') != 0:
        input_msg = input(f"{convo.last_ai_message}\n\n>>")
        convo.process_human(input_msg)
    print("FINISHED")
    print("For reference, the AI would have responded to your quit command with :: ")
    print(f'"{convo.last_ai_message}"')



