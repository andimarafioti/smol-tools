import platform
from abc import ABC, abstractmethod
from typing import Generator, List, Dict, Any, Union, Tuple

class SmolTool(ABC):
    def __init__(self, model_repo: str, model_filename: str, system_prompt: str, prefix_text: str = "", n_ctx: int = 2048):
        self.system_prompt = system_prompt
        self.prefix_text = prefix_text
        self.is_mac = platform.system() == "Darwin"
        self._load_model(model_repo, model_filename, n_ctx)
        

    def _load_model(self, model_repo: str, model_filename: str, n_ctx: int):
        if self.is_mac:
            from mlx_lm import load, stream_generate
            self.model, self.tokenizer = load(model_repo)
        else:
            from llama_cpp import Llama
            self.model = Llama.from_pretrained(
                repo_id=model_repo,
                filename=model_filename,
                n_ctx=n_ctx,
                verbose=False
            )
        
        self._warm_up()

    def _warm_up(self):
        """Warm up the model with a test prompt"""
        print(f"Warming up {self.__class__.__name__}...")
        test_text = "This is a test message to warm up the model."
        # Consume the generator to complete the warm-up
        for _ in self.process(test_text):
            pass
        print(f"{self.__class__.__name__} ready!")

    @abstractmethod
    def process(self, text: str) -> Generator[str, None, None]:
        """Process the input text and yield results as they're generated"""
        pass

    def _create_mlx_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.4,
        top_p: float = 0.9,
        top_k: int = 50,
        repeat_penalty: float = 1.2,
        stop_sequences: List[str] = ["<end_action>", "<|endoftext|>"]
    ) -> Generator[str, None, None]:
        """Helper method for MLX chat completions"""
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False)
        output = ""
        for token in stream_generate(self.model, self.tokenizer, prompt=prompt, temp=temperature, top_p=top_p, repetition_penalty=repeat_penalty):
            output += token
            if token in stop_sequences:
                break
            yield output

    def _create_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.4,
        top_p: float = 0.9,
        top_k: int = 50,
        repeat_penalty: float = 1.2,
        max_tokens: int = 256
    ) -> Generator[str, None, None]:
        """Helper method to create chat completions with standard parameters"""
        if self.is_mac:
            yield from self._create_mlx_completion(messages)
            return

        output = ""
        for chunk in self.model.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            stream=True
        ):
            content = chunk['choices'][0]['delta'].get('content')
            if content:
                if content in ["<end_action>", "<|endoftext|>"]:
                    break
                output += content
                yield output