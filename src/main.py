# -*- coding: utf-8 -*-

import os
import argparse
from enum import Enum
from pathlib import Path
from datetime import datetime

import requests
import openai
from prompt_toolkit import prompt
from dotenv import load_dotenv
from rich.live import Live
from rich.console import Console
from rich.markdown import Markdown


load_dotenv()

console = Console()

system_content = '''
Ты - senior панк-ассистент по программированию и связанными с ним технологиями.
Отвечай кратко и по делу с примерами кода, если требуется, и без мата.
Формальное общение запрещено. Если обнаружишь узкие места в переданном тебе коде - сообщи.
'''


class Mode(Enum):
    CHAT = 'chat'
    IMAGE = 'image'


def get_args() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-m', '--mode',
        type=Mode,
        choices=list(Mode),
        default=Mode.CHAT,
    )
    args = parser.parse_args()
    print(type(args), args, sep='\n', end='\n'*2)
    return args


def save_image(img_data) -> None:
    file_name = datetime.now().strftime('%Y%m%d-%H%M%S') + '.png'
    Path(file_name).write_bytes(img_data)


class Client:
    def __init__(self, base_url: str='https://openrouter.ai/api/v1',
                 title: str='TerminalAI', http_referer: str='https://localhost'):
        self.__client = openai.OpenAI(
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
            model="deepseek/deepseek-v4-flash",
            # model="nvidia/nemotron-3-ultra-550b-a55b:free",
            messages=self._messages,
            stream=True,
        )

        return response

    def new_image(self, prompt: str) -> None:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            response_format="url"  # или "b64_json"
        )

        image_url = response['data'][0]['url']
        img_data = requests.get(image_url).content

        save_image(img_data)

    def add_assistant_reply(self, reply: str) -> None:
        self._messages.append({'role': 'assistant', 'content': reply})


def main():
    RUN = True
    a = get_args()
    client = Client()

    while RUN:
        split_string = '='*40 + '\n'*3
        user_input = prompt(split_string + 'Чтобы завершить ввод нажми Esc, а потом Enter\n~: ', multiline=True)

        if user_input.strip().lower() in ('q', 'quit', 'exit'):
            RUN = False
            continue

        assistant_response = client.new_message(user_input)
        accumulated_text = ''

        with Live(console=console, refresh_per_second=10) as live:
            for chunk in assistant_response:
                delta_content = chunk.choices[0].delta.content
                if delta_content:
                    accumulated_text += delta_content
                    live.update(Markdown(accumulated_text))
        console.print('\n')

        client.add_assistant_reply(accumulated_text)


if __name__ == '__main__':
    main()
