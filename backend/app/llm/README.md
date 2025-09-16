# LLM Helpers

This module provides utilities for managing different language model providers (OpenAI and Google Gemini) in the team activity monitor application.

## Configuration

Set the `PREFERRED_LLM_PROVIDER` environment variable to choose your preferred provider:

```bash
# For Google Gemini (default)
export PREFERRED_LLM_PROVIDER=GOOGLE

# For OpenAI
export PREFERRED_LLM_PROVIDER=OPENAI
```

## Usage

### Basic Usage

```python
from app.llm.helpers import create_llm

# Create an LLM instance with default settings
llm = create_llm()

# Create with custom settings
llm = create_llm(
    model_name="gpt-4",  # or "gemini-1.5-pro"
    temperature=0.7,
    system_instruction="You are a helpful assistant."
)
```

### Provider Information

```python
from app.llm.helpers import get_provider_info, get_current_provider, is_provider_configured

# Get current provider information
info = get_provider_info()
print(f"Current provider: {info['current_provider']}")
print(f"Available models: {info['available_models']}")

# Check if a provider is configured
if is_provider_configured("OPENAI"):
    print("OpenAI is configured")
```

## Supported Models

### OpenAI Models
- `gpt-3.5-turbo` (default)
- `gpt-3.5-turbo-16k`
- `gpt-4`
- `gpt-4-turbo-preview`
- `gpt-4-32k`

### Google Gemini Models
- `gemini-1.5-flash` (default)
- `gemini-1.5-pro`
- `gemini-pro`

## Environment Variables

Make sure to set the appropriate API keys:

```bash
# For OpenAI
export OPENAI_API_KEY=your_openai_api_key

# For Google Gemini
export GOOGLE_API_KEY=your_google_api_key
```

## Integration

The LLM helper is automatically used by:
- `BasicAgent` in `app/core/services/basic_agent.py`
- `AgentIntentParser` in `app/core/services/intent_parser.py`

No changes are needed in existing code - the provider selection is handled automatically based on the configuration.
