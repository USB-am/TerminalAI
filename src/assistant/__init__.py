import json
import os
import re
import subprocess
from typing import Any

import openai

from .allowed_commands import ALLOWED_COMMANDS
from .denied_substrings import DENIED_SUBSTRINGS
from .git_readonly_subcommands import GIT_READONLY_SUBCOMMANDS
from .read_only_flags import READ_ONLY_FLAGS
from .tools import TOOLS


def _check_command_safety(command: str) -> tuple[bool, str]:
    """
    Проверяет команду на соответствие белому списку.
    Возвращает (разрешено, сообщение_об_ошибке).
    """
    stripped = command.strip()
    if not stripped:
        return False, "Empty command is not allowed"

    lower = stripped.lower()
    for deny in DENIED_SUBSTRINGS:
        if deny in lower:
            return False, f"Command contains denied pattern: '{deny}'"

    segments = re.split(r"\s*\|\s*|\s*&&\s*|\s*\|\|\s*|;\s*", stripped)

    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        parts = seg.split()
        base = parts[0]

        base_name = os.path.basename(base)
        if base_name in ALLOWED_COMMANDS or base in ALLOWED_COMMANDS:
            pass
        elif base_name.endswith(".py") or base_name.endswith(".sh"):
            if not os.path.isfile(base):
                return False, f"Script '{base}' not found or not allowed"
        else:
            return False, f"Command '{base}' is not in the whitelist"

        if base_name == "git":
            for i, part in enumerate(parts[1:], start=1):
                if not part.startswith("-"):
                    subcommand = part
                    if subcommand not in GIT_READONLY_SUBCOMMANDS:
                        return False, (
                            f"Git subcommand '{subcommand}' is not allowed "
                            f"(write operations are disabled). "
                            f"Allowed read-only subcommands: "
                            f"{', '.join(sorted(GIT_READONLY_SUBCOMMANDS))}"
                        )
                    break

        if base_name in READ_ONLY_FLAGS or base in READ_ONLY_FLAGS:
            allowed = READ_ONLY_FLAGS.get(base_name) or READ_ONLY_FLAGS.get(base)
            for arg in parts[1:]:
                key = arg.split("=")[0]
                if key.startswith("-") and key not in allowed:
                    return False, (
                        f"Flag '{key}' is not allowed for '{base_name}'. "
                        f"Allowed flags: {', '.join(sorted(allowed))}"
                    )

        for part in parts:
            if part.startswith(">"):
                target = part[1:].strip()
                if "dev/" in target or "sd" in target:
                    return False, f"Redirect to '{target}' is not allowed"

    return True, ""


def run_command(command: str) -> str:
    """Run terminal command with whitelist restrictions"""
    is_allowed, msg = _check_command_safety(command)
    if not is_allowed:
        return f"Error: Command rejected by security policy. {msg}"

    print(f'Try run "{command}"')
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        out = ""
        if result.stdout:
            out += f"stdout:\n{result.stdout}"
        if result.stderr:
            out += f"stderr:\n{result.stderr}"
        if not out:
            out = "(no output)"
        return out.strip()
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (30s limit)"
    except Exception as e:
        return f"Error: {e}"


def read_file(path: str) -> str:
    """Read file content"""
    print(f'Try read "{path}" file')
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to file"""
    print(f'Try write <{content[:20]}> to "{path}" file')
    try:
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"Written to {path}"
    except Exception as e:
        return f"Error: {e}"


def list_files(path: str = ".") -> str:
    """List files in directory"""
    print(f'Check list "{path}" files')
    try:
        files = os.listdir(path)
        return "\n".join(files)
    except Exception as e:
        return f"Error: {e}"


class Assistant:
    def __init__(
        self,
        base_url: str = "https://openrouter.ai/api/v1",
        title: str = "TerminalAI",
        http_referer: str = "https://localhost",
    ):
        self.__client = openai.OpenAI(
            base_url=base_url,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            default_headers={
                "X-Title": title,
                "HTTP-Referer": http_referer,
            },
        )
        self._messages: list[dict] = [
            {"role": "system", "content": os.getenv("SYSTEM_CONTENT")},
        ]

    def handle_tool_call(self, tool_call):
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if func_name == "read_file":
            return read_file(**args)
        elif func_name == "write_file":
            return write_file(**args)
        elif func_name == "run_command":
            return run_command(**args)
        elif func_name == "list_files":
            return list_files(**args)

    def chat(self, message: str) -> Any:
        self._messages.append({"role": "user", "content": message})

        # Use tenacity lib for handle this string
        response = self.__client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=self._messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        msg = response.choices[0].message

        while msg.tool_calls:
            self._messages.append(msg)

            for tool_call in msg.tool_calls:
                result = self.handle_tool_call(tool_call)
                self._messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result}
                )

            response = self.__client.chat.completions.create(
                model=os.getenv("MODEL"),
                messages=self._messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            msg = response.choices[0].message

        self._messages.append(msg)
        return msg.content

    def add_reply(self, reply: str) -> None:
        self._messages.append({"role": "assistant", "content": reply})
