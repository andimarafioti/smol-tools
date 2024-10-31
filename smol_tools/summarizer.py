from .base import SmolTool
from typing import Generator

class SmolSummarizer(SmolTool):
    def __init__(self):
        super().__init__(
            model_repo="andito/SmolLM2-1.7B-8k-dpo-F16-GGUF",
            model_filename="smollm2-1.7b-8k-dpo-f16.gguf",
            system_prompt="Concisely summarize the main points of the input text in up to three sentences, focusing on key information and events.",
        )

    def process(self, text: str) -> Generator[str, None, None]:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"{self.prefix_text}\n{text}"}
        ]
        yield from self._create_chat_completion(messages, max_tokens=1024, temperature=0.1, top_p=0.9)