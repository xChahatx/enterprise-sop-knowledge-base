"""
LLM Interface

Communicates with Ollama.

Responsibilities
----------------
- Send prompts
- Receive responses
- Return clean text
"""

import os
import time
import logging
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLM:

    def __init__(
        self,
        model=None,
        base_url=None
    ):

        self.model = model or os.environ.get(
            "OLLAMA_MODEL",
            "llama3.2:1b"
        )

        self.base_url = base_url or os.environ.get(
            "OLLAMA_HOST",
            "http://localhost:11434"
        )

        self.url = f"{self.base_url.rstrip('/')}/api/generate"

        logger.info(
            f"Using model: {self.model} @ {self.base_url}"
        )

    def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 500
    ) -> str:

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        try:

            logger.info("=" * 80)
            logger.info(f"MODEL : {self.model}")
            logger.info(f"PROMPT LENGTH : {len(prompt)}")
            logger.info("=" * 80)

            start = time.time()

            response = requests.post(
                self.url,
                json=payload,
                timeout=300
            )

            elapsed = round(time.time() - start, 2)

            response.raise_for_status()

            result = response.json()

            text = result.get(
                "response",
                ""
            ).strip()

            if not text:
                raise ValueError(
                    "Ollama returned an empty response."
                )

            logger.info(
                f"Generation completed in {elapsed} sec"
            )

            logger.info(
                f"Generated {len(text)} characters"
            )

            return text

        except requests.ConnectionError:

            msg = (
                "Cannot connect to Ollama.\n"
                "Run:\n\n"
                "ollama serve"
            )

            logger.error(msg)

            return msg

        except requests.HTTPError:

            detail = ""

            try:
                detail = response.json().get(
                    "error",
                    ""
                )
            except Exception:
                detail = response.text

            if response.status_code == 404:

                msg = (
                    f"Model '{self.model}' not found.\n"
                    f"Run:\n"
                    f"ollama pull {self.model}"
                )

            else:

                msg = (
                    f"Ollama Error "
                    f"({response.status_code})\n"
                    f"{detail}"
                )

            logger.error(msg)

            return msg

        except Exception as e:

            msg = f"LLM generation failed:\n{e}"

            logger.error(msg)

            return msg