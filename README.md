# Chatterbox TTS Service

A streaming Text-to-Speech service using Chatterbox TTS, wrapped in a FastAPI application.

This was purpose built for a specific project but is generic enough to be used in other projects.

## Features
- **Streaming Audio**: Returns audio bytes directly for low-latency playback.
- **Custom Voices**: Easily add new voices via configuration files.
- **Parameter Control**: Fine-tune speech generation with temperature, and more.
- **CUDA Acceleration**: Automatic GPU support if available.
- **Docker Ready**: Designed to run in a containerized environment.

## Development Setup

### Prerequisites
- **Python**: Managed via `pyenv` (Requires Python 3.11).
- **Dependency Management**: Uses `poetry`.

### Installation

1.  **Set Python Version**:
    Ensure you have the correct python version installed and active.
    ```bash
    pyenv install 3.11
    pyenv local 3.11
    ```

2.  **Install Dependencies**:
    ```bash
    poetry install
    ```

### Helper Tasks

This project uses `taskipy` to simplify common commands. Run these with `poetry run task <command>`.

- **Start Development Server**:
  ```bash
  poetry run task dev
  ```
  Runs the uvicorn server with hot-reload enabled on port 8000.

- **Build Docker Image**:
  ```bash
  poetry run task build
  ```
  Builds the `py-chatterbox-tts` Docker image.

- **Run Docker Container**:
  ```bash
  poetry run task run
  ```
  Runs the container with GPU support, listening on port 8000.

## API Endpoints

### 1. Synthesize Speech
**Endpoint**: `POST /api/v1/synthesize`

Generates audio from text. Returns a WAV audio stream.

**Parameters (JSON Body):**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | **Required** | The text to speak. |
| `voice` | string | `null` | The ID of the voice to use (e.g., `af_bella`, `tech_guru`). |
| `temperature` | float | `0.7` | Randomness in generation (higher = more varied). |
| `cfg_weight` | float | `0.5` | Classifier Free Guidance weight. |
| `exaggeration` | float | `0.5` | Level of emotional exaggeration. |


**Example Request (httpie):**
```bash
http POST :8000/api/v1/synthesize text="Hello, this is a test of the Chatterbox TTS system." voice="af_bella"
```

**Save to file:**
```bash
http POST :8000/api/v1/synthesize text="Saving this to a file." > output.wav
```


**Play direct from API:**
```bash
http POST :8000/api/v1/synthesize text="Play back immediately." | ffplay -i pipe: -nodisp -autoexit
```

### 2. List Voices
**Endpoint**: `GET /api/v1/voices`

Returns a list of all available voice IDs.

**Example Request:**
```bash
http GET :8000/api/v1/voices
```

### 3. Health Check
**Endpoint**: `GET /health`

Checks if the service is running and if CUDA is available.

**Example Request:**
```bash
http GET :8000/health
```

## Adding Custom Voices

You can add custom voices by creating `.toml` configuration files in the `voices/` directory.

### Step 1: Add Audio File
Place your reference audio file (e.g., `my_voice.wav`) in the `voices/` directory or a subdirectory.

### Step 2: Create Configuration
Create a file named `voices/my_voice_id.toml`. The filename (minus extension) becomes the `voice` ID.

**Example `voices/my_voice_id.toml`:**
```toml
# Relative path to the audio reference file
audio_path = "my_voice.wav"

# Optional default parameters for this voice
temperature = 0.65

exaggeration = 1.2
```

Restart the service to load the new voice.
