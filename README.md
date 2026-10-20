# multilingual-safety-eval

A small Python tool for checking whether AI models give equally safe answers in **English, Romanian and Russian**.

Most AI safety testing happens in English, and research such as [Yong et al. (2023)](https://arxiv.org/abs/2310.02446) shows safety training does not always carry over to other languages. This project sends the same harmless, safety-relevant prompts in all three languages to a model, saves the replies to CSV, and creates a sheet for scoring them by hand.

> **Status: early stage. No results have been collected yet.**

## What it does
1. Reads prompts from `prompts.csv` (each prompt in `en`, `ro` and `ru`).
2. Sends every prompt in every language to an OpenAI-compatible chat API.
3. Saves the replies to `results/responses_<model>_<time>.csv`.
4. Creates `results/scoring_<model>_<time>.csv` with empty columns for manual scoring (see [scoring_guide.md](scoring_guide.md)).

## The prompts
All prompts are **benign**: medical and financial safety advice, scams, household chemical safety, privacy, and refusal-boundary questions a model should be able to answer helpfully. There are no harmful requests in this project.

**Translation note:** the Romanian and Russian translations are first drafts and still need to be checked by Daniel (a native speaker) before any results are collected.

## Setup
Requires Python 3.9 or later. The tool itself uses only the standard library; `pytest` is only for tests.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
Try it offline first (no API calls, fake replies):
```bash
python -m mseval.run --dry-run
```

Run against a real model by setting environment variables. Never commit API keys.
```bash
export MSEVAL_API_KEY="your-key"
export MSEVAL_MODEL="model-name"
export MSEVAL_BASE_URL="https://api.openai.com/v1"   # or any OpenAI-compatible endpoint
python -m mseval.run
```

Options: `--prompts FILE`, `--langs en,ro`, `--out-dir DIR`.

## Tests
```bash
python -m pytest
```

## Plans
- Check and finalise the translations
- Collect first results from ChatGPT, Claude and Grok
- Add more prompts and more than one wording per prompt, so results do not depend on a single translation

## License
MIT, see [LICENSE](LICENSE).
