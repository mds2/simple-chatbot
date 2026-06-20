
import os
from typing import Optional
from datetime import datetime

def get_completion_fun(
        backend_type: str = "openai",
        cached_fun = None,
        debug_logfile: Optional[Path] = None,
):
    if cached_fun is not None:
        return cached_fun
    import openai
    client = openai.OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
    def openai_completion_fun(
            sys_prompt: str,
            text_in: str,
            ai_is_called: str,
            human_is_called: str,
    ) -> str:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": text_in},
            ],
            temperature=0.9,
            max_tokens=650,
        )
        raw_response = response.choices[0].message.content.strip()
        if debug_logfile is not None:
            split_strs = [f"[{name}]" for name in [ai_is_called,
                                                   human_is_called]]
            trim1 = raw_response.split(split_strs[0])[-1]
            trimmed_response = trim1.split(split_strs[1])[0]

            with open(debug_logfile, "a") as outfile:
                divider = "".join(["#" for i in range(80)])
                for label, data in [
                        ("sys_prompt", sys_prompt),
                        ("text_in", text_in),
                        ("raw_response", raw_response),
                        ("trimmed_response", trimmed_response),
                        ("character1", split_strs[0]),
                        ("character2", split_strs[1]),
                        ("date", str(datetime.now())),
                ]:
                    outfile.write(f"{divider}\n{label}\n{divider}\n")
                    outfile.write(data)
                    outfile.write(f"\n{divider}\nend {label}\n{divider}\n")
            outfile.close()
        return raw_response
    return openai_completion_fun

def complete(
        text_in: str,
        sys_prompt: str,
        completion_fun = None,
        ai_is_called = "AI",
        human_is_called = "HUMAN",
):
    # TODO: dissolve this function into completion_fun and process_human
    if completion_fun is None:
        completion_fun = get_completion_fun()
    raw_response = completion_fun(
        sys_prompt,
        text_in,
        ai_is_called=ai_is_called,
        human_is_called=human_is_called,
    )
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
            debug_logfile: Optional[Path] = None,
    ):
        self.completion_fun = get_completion_fun(
            debug_logfile=debug_logfile,
        )
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
            "In the following conversation, lines spoken by ",
            self.ai_is_called,
            f" are preceded by [{self.ai_is_called}], ",
            f"while lines spoken by {self.human_is_called} are preceded by ",
            f"[{self.human_is_called}]",
            "", "", "", self.get_said(),
        ])
        self.last_ai_message = complete(
            prompt,
            sys_prompt=self.system_prompt,
            completion_fun=self.completion_fun,
            human_is_called=self.human_is_called,
            ai_is_called=self.ai_is_called,
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
    parser.add_argument(
        '--debug-logfile',
        type=Path,
        default=None,
        help="If present, dump all prompts and responses here",
    )
    args = parser.parse_args()

    system_prompt = "Please complete the following conversation"
    # was "You are role-playing as an angry toaster from dimension X"

    if args.system_prompt_file is not None:
        with open(args.system_prompt_file) as infile:
            system_prompt = infile.read()
    convo = Convo(
        system_prompt=system_prompt,
        ai_is_called=args.ai_is_called,
        human_is_called=args.human_is_called,
        debug_logfile = args.debug_logfile,
    )
    while convo.last_human_message.lower().find('quit') != 0:
        input_msg = input(f"{convo.last_ai_message}\n\n>>")
        convo.process_human(input_msg)
    print("FINISHED")
    print("For reference, the AI would have responded to your quit command with :: ")
    print(f'"{convo.last_ai_message}"')



