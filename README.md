# Google Search Agent - Claude AI Powered

An intelligent web automation system that performs Google searches and web navigation tasks through natural language commands, powered by Claude AI.

## Features

- **Natural Language Control**: Describe tasks in plain English
- **Claude AI Integration**: Intelligent decision-making for web interactions
- **Mobile & Desktop Support**: Emulates iPhone or runs in desktop mode
- **Stealth Automation**: Uses undetected-chromedriver with anti-detection measures
- **Bright Data Proxy Support**: Built-in proxy configuration with CA certificate handling
- **Interactive & Batch Modes**: Run interactively or with single tasks

## Architecture

The project is modularly organized:

- `browser_setup.py` - Browser initialization with mobile emulation and proxy
- `dom_extractor.py` - Extracts and simplifies DOM for Claude analysis
- `actions.py` - Human-like browser interactions (click, type, scroll)
- `search_agent.py` - Claude-powered agent logic
- `main.py` - Entry point and CLI interface
- `brightdata_proxy_headless.py` - Legacy standalone proxy test (kept for compatibility)

## Setup

### Requirements

- Python 3.8-3.11 (not 3.12+)
- Chrome/Chromium browser
- Anthropic API key for Claude

### Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```env
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional - for Bright Data proxy
BRIGHTDATA_PROXY=http://username:password@proxy.brightdata.com:port

# Optional - CA certificates (base64 encoded)
BRIGHTDATA_CA_B64=...
SELENIUMWIRE_CA_B64=...
```

## Usage

### Interactive Mode

Start the agent in interactive mode:
```bash
python main.py
```

Available commands:
- `search <query>` - Search Google
- `visit <query> -> <link text>` - Search and click specific result
- `task <description>` - Execute custom task
- `screenshot` - Capture current page
- `results` - Show search results
- `url` - Display current URL
- `back/forward/refresh` - Navigation
- `help` - Show commands
- `quit` - Exit

### Command Line Mode

Execute single tasks:
```bash
# Simple search
python main.py --search "Python tutorials"

# Custom task
python main.py --task "Search for weather in New York and tell me the temperature"

# Headless mode (no browser window)
python main.py --headless --search "latest news"

# Desktop mode instead of mobile
python main.py --desktop --search "programming blogs"
```

### Docker

Build and run in Docker:
```bash
# Build image
docker build -t google-agent .

# Run with environment variables
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
           -e BRIGHTDATA_PROXY=$BRIGHTDATA_PROXY \
           google-agent python main.py --task "Search for Python documentation"

# Interactive mode (requires -it flags)
docker run -it -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY google-agent python main.py
```

### AWS ECS/Fargate

The agent is configured for AWS deployment:

1. Push to ECR:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_URI
docker tag google-agent:latest $ECR_URI/google-agent:latest
docker push $ECR_URI/google-agent:latest
```

2. Update task definition with secrets from SSM:
- `/anthropic/api_key` → `ANTHROPIC_API_KEY`
- `/brightdata/proxy` → `BRIGHTDATA_PROXY`
- `/brightdata/ca_b64` → `BRIGHTDATA_CA_B64`

3. Run tasks with custom commands:
```json
{
  "overrides": {
    "containerOverrides": [{
      "name": "google-agent",
      "command": ["python", "main.py", "--headless", "--task", "Your task here"]
    }]
  }
}
```

## Examples

### Search and Extract Results
```python
from browser_setup import create_browser
from search_agent import GoogleSearchAgent

# Create browser
driver = create_browser(headless=False, mobile=True)

# Initialize agent
agent = GoogleSearchAgent(driver)

# Perform search
result = agent.search("machine learning tutorials")

# Extract search results
results = agent.extract_search_results()
for r in results:
    print(f"{r['title']}: {r['url']}")
```

### Custom Task Automation
```python
# Complex multi-step task
task = """
1. Search for 'best Python IDE 2024'
2. Click on the first result
3. Find and summarize the top 3 recommendations
"""

result = agent.run(task)
print(result['result'])
```

## API Reference

### GoogleSearchAgent

Main agent class for web automation.

#### Methods

- `run(task: str, start_url: str = None)` - Execute a custom task
- `search(query: str)` - Perform Google search
- `search_and_visit(query: str, link_text: str)` - Search and click result
- `extract_search_results()` - Get search results from current page
- `take_screenshot(filename: str = None)` - Capture screenshot

### BrowserActions

Provides human-like interaction methods.

#### Methods

- `type_text(element, text, clear_first=True)` - Type with delays
- `click_element(element, use_js=False)` - Click with random offset
- `scroll_page(direction, amount=None)` - Smooth scrolling
- `wait_for_element(selector, timeout=10)` - Smart waiting
- `submit_form(element=None)` - Form submission

### DOMExtractor

Extracts and simplifies DOM for AI analysis.

#### Methods

- `extract_page_info()` - Get page structure
- `format_for_claude(page_info)` - Format for Claude AI
- `get_element_by_id(element_id)` - Get WebElement reference

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY` - Claude API key (required)
- `BRIGHTDATA_PROXY` - Proxy URL (optional)
- `BRIGHTDATA_CA_B64` - Bright Data CA cert (base64)
- `SELENIUMWIRE_CA_B64` - Selenium-Wire CA cert (base64)

### Command Line Arguments

- `--task <description>` - Task to execute
- `--search <query>` - Search query
- `--headless` - Run without browser window
- `--desktop` - Use desktop mode (default: mobile)
- `--max-steps <n>` - Maximum agent steps (default: 20)
- `--api-key <key>` - Override API key from env

## Troubleshooting

### Certificate Issues

If you encounter SSL/certificate errors:

1. Ensure CA certificates are properly installed:
```bash
python brightdata_proxy_headless.py
```

2. For Docker, mount certificates:
```bash
docker run -v /path/to/certs:/app/certs ...
```

### Proxy Connection

Test proxy connection:
```bash
python detect_real_ip.py
```

### Claude API Errors

- Verify API key is correct
- Check rate limits
- Ensure you have sufficient credits

## Development

### Adding New Actions

Extend `actions.py`:
```python
def custom_action(self, element, param):
    # Implementation
    return success_boolean
```

### Custom DOM Extraction

Modify `dom_extractor.py`:
```python
def _extract_custom_elements(self):
    # Extract specific elements
    return element_list
```

### Agent Behaviors

Customize `search_agent.py`:
```python
def custom_task_handler(self, task_description):
    # Task-specific logic
    return result
```

## License

[Your License Here]

## Contributing

[Contributing Guidelines]