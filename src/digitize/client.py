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

    def analyze_image(
        self,
        image_path: Path,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
    ) -> str:
        """Send an image to Claude with a prompt and return the text response."""
        self._call_count += 1
        step = f"call_{self._call_count}"
        if self.provider == "cli":
            result = self._run_cli(image_path, system_prompt, user_prompt)
            self._log(step, result)
            return result

        media_type = mimetypes.guess_type(str(image_path))[0] or "image/png"
        image_data = base64.standard_b64encode(image_path.read_bytes()).decode()

        message = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                }
            ],
        )
        text = message.content[0].text
        self._track_usage(message.usage)
        self._log(step, text)
        return text

    def analyze_pdf(
        self,
        pdf_path: Path,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
    ) -> str:
        """Send a PDF to Claude with a prompt and return the text response."""
        self._call_count += 1
        step = f"call_{self._call_count}"
        if self.provider == "cli":
            result = self._run_cli(pdf_path, system_prompt, user_prompt)
            self._log(step, result)
            return result

        pdf_data = base64.standard_b64encode(pdf_path.read_bytes()).decode()

        message = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_data,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                }
            ],
        )
        text = message.content[0].text
        self._track_usage(message.usage)
        self._log(step, text)
        return text

    def _track_usage(self, usage: object) -> None:
        """Accumulate token counts from an API response or CLI output."""
        if hasattr(usage, "input_tokens"):
            # API SDK response object
            self.total_input_tokens += usage.input_tokens
            self.total_output_tokens += usage.output_tokens
        elif isinstance(usage, dict):
            # CLI stream-json: input_tokens is just non-cached;
            # add cache fields for the real total
            inp = usage.get("input_tokens", 0)
            inp += usage.get("cache_creation_input_tokens", 0)
            inp += usage.get("cache_read_input_tokens", 0)
            self.total_input_tokens += inp
            self.total_output_tokens += usage.get("output_tokens", 0)

    def _log(self, step: str, response: str) -> None:
        """Record a debug log entry."""
        if self.debug:
            self.debug_log.append({"step": step, "response": response})

    def _run_cli(
        self, file_path: Path, system_prompt: str, user_prompt: str
    ) -> str:
        """Run analysis via the Claude Code CLI with direct image/PDF input."""
        file_data = base64.standard_b64encode(file_path.read_bytes()).decode()

        if file_path.suffix.lower() == ".pdf":
            content_block = {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": file_data,
                },
            }
        else:
            media_type = mimetypes.guess_type(str(file_path))[0] or "image/png"
            content_block = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": file_data,
                },
            }

        msg = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [content_block, {"type": "text", "text": user_prompt}],
            },
        }
        input_data = json.dumps(msg)

        cmd = [
            "claude",
            "-p",
            "--system-prompt", system_prompt,
            "--model", self.model,
            "--input-format", "stream-json",
            "--output-format", "stream-json",
            "--verbose",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, input=input_data,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Claude CLI failed (exit {result.returncode}): {result.stderr.strip()}"
            )

        text, usage = self._parse_stream_json(result.stdout)
        self._track_usage(usage)
        return text

    @staticmethod
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
