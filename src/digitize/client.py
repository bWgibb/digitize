"""Claude API client for vision calls."""

from __future__ import annotations

import base64
import json
import mimetypes
import subprocess
from pathlib import Path


class ClaudeClient:
    """Thin wrapper around the Anthropic SDK or Claude CLI for vision tasks."""

    def __init__(
        self, model: str = "claude-opus-4-6", provider: str = "api",
        debug: bool = False,
    ) -> None:
        self.model = model
        self.provider = provider
        self.debug = debug
        self.debug_log: list[dict] = []
        self._call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        if provider == "api":
            import anthropic
            self._client = anthropic.Anthropic()

    def analyze(
        self,
        file_path: Path,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
    ) -> str:
        """Send an image or PDF to Claude and return the text response.

        Automatically selects image vs document format based on file extension.
        Dispatches to CLI subprocess or Anthropic SDK based on provider.
        """
        self._call_count += 1
        step = f"call_{self._call_count}"

        if self.provider == "cli":
            text = self._call_cli(file_path, system_prompt, user_prompt)
        else:
            text = self._call_api(file_path, system_prompt, user_prompt, max_tokens)

        self._log(step, text)
        return text

    # Keep old names as aliases for backwards compatibility
    analyze_image = analyze
    analyze_pdf = analyze

    def _call_api(
        self, file_path: Path, system_prompt: str, user_prompt: str,
        max_tokens: int,
    ) -> str:
        """Send file via Anthropic SDK."""
        file_data = base64.standard_b64encode(file_path.read_bytes()).decode()
        content_block = _build_content_block(file_path, file_data)

        message = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": [content_block, {"type": "text", "text": user_prompt}],
            }],
        )
        self._track_usage(message.usage)
        return message.content[0].text

    def _call_cli(
        self, file_path: Path, system_prompt: str, user_prompt: str,
    ) -> str:
        """Send file via Claude Code CLI with direct base64 input."""
        file_data = base64.standard_b64encode(file_path.read_bytes()).decode()
        content_block = _build_content_block(file_path, file_data)

        msg = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [content_block, {"type": "text", "text": user_prompt}],
            },
        }

        cmd = [
            "claude", "-p",
            "--system-prompt", system_prompt,
            "--model", self.model,
            "--input-format", "stream-json",
            "--output-format", "stream-json",
            "--verbose",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, input=json.dumps(msg),
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Claude CLI failed (exit {result.returncode}): {result.stderr.strip()}"
            )

        text, usage = _parse_stream_json(result.stdout)
        self._track_usage(usage)
        return text

    def _track_usage(self, usage: object) -> None:
        """Accumulate token counts from an API response or CLI output."""
        if hasattr(usage, "input_tokens"):
            self.total_input_tokens += usage.input_tokens
            self.total_output_tokens += usage.output_tokens
        elif isinstance(usage, dict):
            inp = usage.get("input_tokens", 0)
            inp += usage.get("cache_creation_input_tokens", 0)
            inp += usage.get("cache_read_input_tokens", 0)
            self.total_input_tokens += inp
            self.total_output_tokens += usage.get("output_tokens", 0)

    def _log(self, step: str, response: str) -> None:
        """Record a debug log entry."""
        if self.debug:
            self.debug_log.append({"step": step, "response": response})


def _build_content_block(file_path: Path, file_data: str) -> dict:
    """Build the appropriate content block for an image or PDF."""
    if file_path.suffix.lower() == ".pdf":
        return {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": file_data,
            },
        }
    media_type = mimetypes.guess_type(str(file_path))[0] or "image/png"
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": file_data,
        },
    }


def _parse_stream_json(output: str) -> tuple[str, dict]:
    """Extract assistant text and usage from stream-json output."""
    text_parts = []
    usage: dict = {}
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            if msg.get("type") == "assistant":
                for block in msg.get("message", {}).get("content", []):
                    if block.get("type") == "text":
                        text_parts.append(block["text"])
            elif msg.get("type") == "result":
                usage = msg.get("usage", {})
        except json.JSONDecodeError:
            continue
    return "".join(text_parts), usage
