# Swahili Data Quality Pipeline

A production-ready Python pipeline for cleaning, filtering, and preparing Swahili (Kiswahili) text data for LLM training, fine-tuning, and RLHF.

## Features

- **Language filtering** — Heuristic Swahili detection using common word overlap (fast, no ML model required)
- **Deduplication** — SHA256-based exact duplicate removal
- **PII removal** — Emails, Kenyan phone numbers (+254/07), credit cards, generic IDs
- **Encoding fix** — Repairs common mojibake (UTF-8 misdecoded as Latin-1)
- **Length filtering** — Configurable min/max character bounds
- **JSONL I/O** — Streaming read/write for large datasets
- **CLI & Library** — Use as a command-line tool or import in Python
- **Zero dependencies** — Pure Python stdlib (optional: `fasttext` for better lang detection)

## Installation

```bash
# Clone and install
git clone https://github.com/yourusername/swahili-data-pipeline
cd swahili-data-pipeline
pip install -e .[dev]  # with dev tools
```

## Quick Start

### Command Line

```bash
# Process a JSONL file
swahili-pipeline input.jsonl -o output.jsonl --stats

# Process a directory of .txt files
swahili-pipeline ./raw_data/ -o cleaned.jsonl --min-swahili-ratio 0.8

# With custom config
swahili-pipeline data.jsonl -o clean.jsonl \
  --min-length 50 \
  --max-length 5000 \
  --no-deduplicate
```

### Python API

```python
from swahili_pipeline import SwahiliPipeline, PipelineConfig, Document, read_jsonl, write_jsonl

# Configure
config = PipelineConfig(
    min_length=50,
    max_length=5000,
    min_swahili_ratio=0.75,
    deduplicate=True,
    fix_encoding=True,
    remove_pii=True,
)
pipeline = SwahiliPipeline(config)

# Process documents
docs = read_jsonl(Path("raw_data.jsonl"))
cleaned = pipeline.process_batch(docs)
write_jsonl(cleaned, Path("clean_data.jsonl"))
```

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_length` | 10 | Minimum document length (chars) |
| `max_length` | 10000 | Maximum document length (chars) |
| `min_swahili_ratio` | 0.7 | Minimum Swahili word ratio (0.0–1.0) |
| `deduplicate` | True | Remove exact duplicates |
| `fix_encoding` | True | Repair mojibake |
| `remove_pii` | True | Redact emails, phones, cards |

## PII Patterns Handled

- **Emails**: `user@example.com` → `[EMAIL_REDACTED]`
- **Kenyan phones**: `+254712345678`, `0712345678` → `[PHONE_REDACTED]`
- **Credit cards**: `1234-5678-9012-3456` → `[CARD_REDACTED]`
- **Generic IDs**: `123-456-789` → `[ID_REDACTED]`

## Sample Output

Input:
```json
{"text": "Ninaenda shuleni leo, jina langu ni John. Email: john@example.com", "metadata": {"source": "web"}}
```

Output:
```json
{"text": "Ninaenda shuleni leo, jina langu ni John. Email: [EMAIL_REDACTED]", "metadata": {"source": "web"}}
```

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=swahili_pipeline --cov-report=html
```

## Project Structure

```
swahili-data-pipeline/
├── swahili_pipeline/
│   ├── __init__.py
│   ├── core.py       # Pipeline logic
│   └── cli.py        # Command-line interface
├── tests/
│   └── test_core.py  # Unit tests
├── data/             # Sample data (gitignored)
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Use Cases

- **LLM pre-training data prep** — Clean CommonCrawl, OSCAR, or custom Swahili corpora
- **RLHF/RLAIF** — Prepare high-quality Swahili preference data
- **Fine-tuning datasets** — Filter instruction/response pairs for Swahili tasks
- **Data annotation QA** — Pre-filter before human annotation to reduce cost

## Performance

- **Streaming I/O** — Processes files larger than RAM
- **O(n) deduplication** — Hash set lookup
- **No external deps** — Runs anywhere Python runs
- **Typical throughput**: ~100K docs/min on modern CPU

## Extending

### Add fasttext for better language detection

```bash
pip install -e .[fasttext]
```

```python
# In core.py, replace swahili_ratio() with:
import fasttext
model = fasttext.load_model("lid.176.bin")

def swahili_ratio(self, text: str) -> float:
    preds = model.predict(text.replace("\n", " "), k=1)
    return 1.0 if preds[0][0] == "__label__swa" else 0.0
```

### Custom PII patterns

```python
config = PipelineConfig()
pipeline = SwahiliPipeline(config)
pipeline.PII_PATTERNS.append(
    (re.compile(r"YOUR_REGEX"), "[YOUR_REPLACEMENT]")
)
```

## License

MIT — Free for commercial and research use.

## Author

Built for the **Masakhane** / **African NLP** community. Contributions welcome!

---

**Keywords**: Swahili, Kiswahili, NLP, LLM, data cleaning, deduplication, PII, RLHF, Masakhane, low-resource languages