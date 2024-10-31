# smol-tools

A collection of lightweight AI-powered tools built with LLaMA.cpp and small language models. These tools are designed to run locally on your machine without requiring expensive GPU resources.

## Features

### SmolSummarizer
- Quick text summarization using a fine-tuned 1.7B parameter model
- Maintains key points while providing concise summaries
- Runs entirely locally

### SmolRewriter
- Rewrites text to be more professional and approachable
- Maintains the original message's intent and key points
- Perfect for email and message drafting

### SmolAgent
- An AI agent that can perform various tasks through tool integration
- Built-in tools include:
  - Weather lookup
  - Random number generation
  - Current time
  - Web browser control
- Extensible tool system for adding new capabilities

## Installation

1. Clone the repository:

```bash
git clone https://github.com/andimarafioti/smol-tools.git
cd smol-tools
```

2. Install dependencies:

```bash
uv pip install -r requirements.txt
```
## Usage

### GUI Demo
Run the Tkinter-based demo application:

```bash
python demo_tkinter.py
```

The demo provides a user-friendly interface with the following shortcuts:
- `F9`: Summarize selected text
- `F10` or `Ctrl+S`: Open SmolAgent interface

### Programmatic Usage

```python
from smol_tools.summarizer import SmolSummarizer
from smol_tools.rewriter import SmolRewriter
from smol_tools.agent import SmolToolAgent
# Initialize tools
summarizer = SmolSummarizer()
rewriter = SmolRewriter()
agent = SmolToolAgent()
# Generate a summary
for summary in summarizer.process("Your text here"):
    print(summary)
# Rewrite text
for improved in rewriter.process("Your text here"):
    print(improved)
# Use the agent
for response in agent.process("What's the weather in London?"):
    print(response)
```


## Models

The tools use the following models:
- SmolSummarizer: SmolLM2-1.7B Intermediate SFT v2 (summarization-optimized)
- SmolRewriter: SmolLM2-1B Numina DPO Mix3
- SmolAgent: SmolLM2-1.7B Intermediate SFT v2

All models are quantized to 16-bit floating-point (F16) for efficient CPU inference.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.