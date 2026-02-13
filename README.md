# Bailiff

Bailiff is a local-first, privacy-focused voice assistant framework designed to capture, transcribe, analyze, and interact with meetings or voice inputs in real-time. It leverages advanced AI models for transcription, diarization, and semantic search, all running locally on your machine.

## Key Features

-   **Real-time Transcription**: Uses `faster-whisper` for high-performance, local speech-to-text.
-   **Speaker Diarization**: Identifies different speakers using `SpeechBrain` embeddings and clustering.
-   **Local RAG (Retrieval-Augmented Generation)**: Stores meeting context in a vector database (`ChromaDB`) for semantic search.
-   **AI Assistant**: Interact with your meeting data using local LLMs (via `Ollama` or compatible APIs).
-   **Privacy-First**: Designed to run entirely offline, keeping your sensitive voice data secure.
-   **Terminal User Interface (TUI)**: A rich, keyboard-centric interface built with `Textual`.

## Prerequisites

-   **Python 3.10+**: Ensure you have a compatible Python version installed.
-   **System Audio Capture (Windows)**: Bailiff uses `pyaudiowpatch` which is specific to Windows for capturing loopback audio.
-   **Ollama**: For the locally AI Assistant features, you need a running instance of [Ollama](https://ollama.com/) with the required models.
    - You can also set any OpenAI compatible cloud API, for this, follow the specific instructions of your LLM provider to get the API key and base URL.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ricardovinicius/bailiff.git
    cd bailiff
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install PyTorch with CUDA support** (Recommended for performance):
    Follow the instructions at [pytorch.org](https://pytorch.org/get-started/locally/) to install the correct version for your system.

## Configuration

Bailiff uses environment variables for configuration.

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```

2.  Edit `.env` to configure your settings:
    -   `BAILIFF_MODELS__LLM_BASE_URL`: URL of your Local LLM provider (default: `http://localhost:11434/v1` for Ollama).
    -   `BAILIFF_APP__LOG_LEVEL`: Logging verbosity.

See `bailiff/core/config.py` for all available configuration options.

## Usage

To start the application:

```bash
python -m bailiff.features.ui.app
```

This will launch the TUI. You can start a new meeting, view transcriptions live, and ask questions to the assistant about the current conversation.

## Architecture

Bailiff uses a multiprocessing pipeline architecture:

-   **Ingest**: Captures system audio (loopback) and microphone input.
-   **Fan-out**: Duplicates audio streams for parallel processing.
-   **Transcription**: Converts audio to text using `faster-whisper`.
-   **Diarization**: Extract speaker embeddings and clusters them to identify speakers.
-   **Merge**: Synchronizes transcription segments with speaker labels.
-   **Memory/Assistant**: Indexes text for search and provides an AI interface.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)
