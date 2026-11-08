# -*- coding: utf-8 -*-

import os

from prompt_toolkit import prompt
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown


load_dotenv()

console = Console()

system_content = '''
Ты - ассистент по программированию и связанными с ним технологиями.
Отвечай кратко и по делу с примерами кода, если требуется. Формальное общение запрещено.
Если обнаружишь узкие места в переданном тебе коде - сообщи.
'''


class Client:
    def __init__(self, base_url: str='https://openrouter.ai/api/v1',
                 title: str='TerminalAI', http_referer: str='https://localhost'):
        self.__client = OpenAI(
            base_url=base_url,
            api_key=os.getenv('OPENROUTER_API_KEY'),
            default_headers={
                "X-Title": title,
                "HTTP-Referer": http_referer,
            }
        )
        self._messages: list[dict] = [
            {'role': 'system', 'content': system_content},
        ]

    def new_message(self, message_text: str) -> str:
        self._messages.append({'role': 'user', 'content': message_text})

        response = self.__client.chat.completions.create(
            # model="deepseek/deepseek-v4-flash",
            model="nvidia/nemotron-3-ultra-550b-a55b:free",
            messages=self._messages,
            stream=False,
        )

        assistant_reply = response.choices[0].message.content
        self._messages.append({'role': 'assistant', 'content': assistant_reply})

        return assistant_reply


def main():
    RUN = True
    client = Client()

    while RUN:
        split_string = '='*40 + '\n'*3
        user_input = prompt(split_string + 'Чтобы завершить ввод нажми Esc, а потом Enter\n~: ', multiline=True)

        if user_input.lower() in ('q', 'quit', 'exit'):
            RUN = False
            continue

        assistant_reply = client.new_message(user_input)
        markdown = Markdown(assistant_reply)
        console.print(markdown)


if __name__ == '__main__':
    main()
