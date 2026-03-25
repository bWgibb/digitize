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
        self, model: str = "claude-sonnet-4-20250514", provider: str = "api"
    ) -> None:
        self.model = model
        self.provider = provider
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
        if self.provider == "cli":
            return self._run_cli(image_path, system_prompt, user_prompt)

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
        return message.content[0].text

    def analyze_pdf(
        self,
        pdf_path: Path,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
    ) -> str:
        """Send a PDF to Claude with a prompt and return the text response."""
        if self.provider == "cli":
            return self._run_cli(pdf_path, system_prompt, user_prompt)

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
        return message.content[0].text

    def _run_cli(
        self, file_path: Path, system_prompt: str, user_prompt: str
    ) -> str:
        """Run analysis via the Claude Code CLI subprocess."""
        abs_path = file_path.resolve()
        prompt = (
            f"Read the file at {abs_path}, then:\n\n{user_prompt}\n\n"
            "IMPORTANT: Respond with ONLY the requested output. "
            "Do not include any preamble, explanation, or commentary."
        )

        cmd = [
            "claude",
            "-p", prompt,
            "--system-prompt", system_prompt,
            "--model", self.model,
            "--output-format", "stream-json",
            "--verbose",
            "--allowedTools", "Read",
            "--dangerously-skip-permissions",
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Claude CLI failed (exit {result.returncode}): {result.stderr.strip()}"
            )

        return self._parse_stream_json(result.stdout)

    @staticmethod
    def _parse_stream_json(output: str) -> str:
        """Extract assistant text content from stream-json output."""
        text_parts = []
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
            except json.JSONDecodeError:
                continue
        return "".join(text_parts)
