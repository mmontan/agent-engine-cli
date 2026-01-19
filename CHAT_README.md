# Agent Engine Chat Client

Interactive command-line client for chatting with your deployed agent on Vertex AI Agent Engine.

## Features

- Clean turn-based conversation interface
- Color-coded user and agent responses
- Automatic session management and memory persistence
- Streaming responses from the remote agent
- Session saved to memory on exit

## Quick Start

```bash
ae chat AGENT_ID -p PROJECT_ID -l us-central1
```

## Command-Line Options

```bash
ae chat --help

Usage: ae chat [OPTIONS] AGENT_ID

  Start an interactive chat session with an agent.

Arguments:
  AGENT_ID  Agent ID or full resource name [required]

Options:
  -p, --project TEXT    Google Cloud project ID [required]
  -l, --location TEXT   Google Cloud region [required]
  -u, --user TEXT       User ID for the chat session [default: cli-user]
  -d, --debug           Enable verbose HTTP debug logging
  --help                Show this message and exit.
```

## Usage Examples

```bash
# Basic chat session
ae chat 172357243746910208 -p my-project -l us-central1

# With custom user ID
ae chat 172357243746910208 -p my-project -l us-central1 --user john@example.com

# With debug logging to see HTTP requests/responses
ae chat 172357243746910208 -p my-project -l us-central1 --debug
```

## Interactive Session

1. **Start the client:**
   ```bash
   ae chat AGENT_ID -p PROJECT_ID -l LOCATION
   ```

2. **Chat with your agent:**
   - Type your message and press Enter
   - Agent responses stream in real-time
   - Tools used by the agent are displayed

3. **Exit gracefully:**
   - Type `quit` or `exit`
   - Or press `Ctrl+C`

## Example Session

```
Ready. User: cli-user, Session: abc123...

Type your message and press Enter. Type 'quit' or 'exit' to end.

You: Hello! How are you?

Agent: Hello! I'm doing well, thank you for asking. How can I help you today?

You: What can you do?

Tools: [search_documents] [get_user_info]

Agent: I can help you with several things including searching documents,
retrieving user information, and answering questions. What would you like to do?

You: quit
Chat session ended.
```

## How It Works

1. Connects to your deployed Agent Engine on Vertex AI
2. Creates a new session (or resumes existing one)
3. Sends your messages to the remote agent
4. Streams responses back in real-time
5. Saves conversation to memory bank on exit

## Troubleshooting

**Error: "Error in chat session: ..."**
- Check your GCP credentials: `gcloud auth application-default login`
- Verify agent is deployed: `ae list -p PROJECT_ID -l LOCATION`
- Ensure the agent ID is correct

**No response from agent:**
- Check your network connection
- Verify agent is running: `ae get AGENT_ID -p PROJECT_ID -l LOCATION`
