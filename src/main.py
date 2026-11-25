from dotenv import load_dotenv
from prompt_toolkit import prompt
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from assistant import Assistant

load_dotenv()


def main():
    assistant = Assistant()
    console = Console(force_terminal=True)

    RUN = True

    while RUN:
        user_input = prompt(
            "Чтобы завершить ввод нажми Esc, а потом Enter\n~: ",
            multiline=True,
        )

        if user_input.strip().lower() in ("q", "quit", "exit"):
            RUN = False
            continue

        assistant_response = assistant.chat(user_input)
        accumulated_text = ""

        with Live(console=console, refresh_per_second=10) as live:
            if assistant_response is None:
                live.update(Markdown(accumulated_text))
                continue
            for chunk in assistant_response:
                if chunk:
                    accumulated_text += chunk
                    live.update(Markdown(accumulated_text))
        console.print("\n" + "=" * 40 + "\n" * 3)

        assistant.add_reply(accumulated_text)


if __name__ == "__main__":
    main()
