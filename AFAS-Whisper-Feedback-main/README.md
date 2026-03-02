# AFAS - Automatic Feedback for Speaking

A comprehensive system for automated speech assessment and feedback generation using Whisper ASR and advanced feature extraction algorithms.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Feature Extraction Algorithms](#feature-extraction-algorithms)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

AFAS (Automatic Feedback for Speaking) is an intelligent speech assessment system that provides automated, comprehensive feedback on speaking performance. The system uses OpenAI's Whisper model for Automatic Speech Recognition (ASR) and extracts multiple linguistic features to evaluate fluency, lexical complexity, and pronunciation quality.

### Key Capabilities

- **High-Quality ASR**: Word-level transcription with confidence scores using Whisper
- **Multi-Dimensional Analysis**: Evaluates fluency, vocabulary, and pronunciation
- **CEFR-Based Assessment**: Maps vocabulary to Common European Framework levels
- **Automated Feedback**: Generates comprehensive feedback based on extracted features
- **RESTful API**: Easy integration with web and desktop applications

## ✨ Features

### 1. Automatic Speech Recognition (ASR)
- Word-level transcription with timestamps
- Confidence probability scores for each word
- Support for multiple Whisper model sizes

### 2. Fluency Analysis
- **Speech Rate**: Words per second (WPS) calculation
- **Pause Detection**: Identifies and quantifies pauses in speech
- **Pause Ratio**: Ratio of pause time to total speech duration

### 3. Lexical Analysis
- **Type-Token Ratio (TTR)**: Measures vocabulary diversity
- **Mean Segmental TTR (MSTTR)**: More stable diversity measure
- **CEFR Level Distribution**: Percentage of words at each proficiency level (A1-C1)

### 4. Pronunciation Assessment
- Confidence-based evaluation using ASR scores
- Distribution analysis across confidence bins:
  - 0-50%: Poor pronunciation
  - 50-70%: Below average
  - 70-85%: Average
  - 85-95%: Good
  - 95-100%: Excellent

### 5. Analytics & Statistics
- User ranking by fluency, lexical complexity, and pronunciation
- Comparative analysis across submissions
- Performance tracking over time

## 🏗️ System Architecture

```
┌─────────────┐
│   Audio     │
│   Input     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Whisper   │  ──►  Word-level transcription
│    ASR      │       with timestamps & confidence
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Feature    │
│ Extraction  │
└──────┬──────┘
       │
       ├──► Fluency Metrics
       ├──► Lexical Diversity
       ├──► CEFR Distribution
       └──► Pronunciation Scores
       │
       ▼
┌─────────────┐
│  Database   │
│  Storage    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Feedback  │
│  Generation │
└─────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd AFAS-Whisper-Feedback-main
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download Whisper Model

The Whisper model will be automatically downloaded on first use. Alternatively, you can pre-download it:

```python
import whisper
model = whisper.load_model("base.en")
```

## ⚙️ Configuration

Configuration is managed through `config/settings.py` and can be overridden using environment variables.

### Default Settings

```python
# Database
database_url = "sqlite:///./asr.db"

# Whisper Model
whisper_model = "base.en"  # Options: tiny, base, small, medium, large

# Feature Extraction Parameters
pause_threshold = 0.25  # seconds
msttr_segment_size = 50

# Data Paths
cefr_dict_path = "data/oxford_cerf.csv"
```

### Environment Variables

Create a `.env` file to override defaults:

```env
DATABASE_URL=sqlite:///./asr.db
WHISPER_MODEL=base.en
PAUSE_THRESHOLD=0.25
MSTTR_SEGMENT_SIZE=50
CEFR_DICT_PATH=data/oxford_cerf.csv
```

## 🚀 Usage

### Starting the API Server

```bash
# Development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Using the Services Directly

```python
from src.services.asr_service import get_asr_service
from src.services.fluency_service import compute_fluency_metrics
from src.services.lexical_diversity_service import compute_lexical_diversity_metrics

# Transcribe audio
asr_service = get_asr_service()
df = asr_service.transcribe_to_csv("audio.wav", "transcript.csv")

# Compute fluency metrics
fluency = compute_fluency_metrics("transcript.csv")
print(f"Speech rate: {fluency['speech_rate_wps']:.2f} WPS")
print(f"Pause ratio: {fluency['ratio_pauses_to_duration']:.2%}")

# Compute lexical diversity
lexical = compute_lexical_diversity_metrics("transcript.csv")
print(f"TTR: {lexical['TTR']:.3f}")
print(f"MSTTR: {lexical['MSTTR']:.3f}")
```

## 📚 API Documentation

### Endpoints Overview

#### Transcripts
- `GET /api/v1/transcripts/{submit_id}` - Get all transcripts for a submission
- `POST /api/v1/transcripts/` - Create transcript entries

#### Fluency
- `GET /api/v1/fluency/{submit_id}` - Get fluency metrics
- `POST /api/v1/fluency/` - Create fluency metrics

#### Lexical
- `GET /api/v1/lexical/{submit_id}` - Get lexical metrics
- `POST /api/v1/lexical/` - Create lexical metrics

#### Pronunciation
- `GET /api/v1/pronunciation/{submit_id}` - Get pronunciation metrics
- `POST /api/v1/pronunciation/` - Create pronunciation metrics

#### Feedback
- `GET /api/v1/feedback/{submit_id}` - Get feedback for submission
- `POST /api/v1/feedback/` - Create feedback

#### Analytics
- `GET /api/v1/analytics/most-fluent-user` - Get user with best fluency
- `GET /api/v1/analytics/best-lexical-user` - Get user with best vocabulary
- `GET /api/v1/analytics/best-pronunciation-user` - Get user with best pronunciation

### Example API Request

```bash
# Get fluency metrics
curl http://localhost:8000/api/v1/fluency/1

# Create fluency metrics
curl -X POST http://localhost:8000/api/v1/fluency/ \
  -H "Content-Type: application/json" \
  -d '{
    "submit_id": 1,
    "speed_rate": 2.5,
    "pause_ratio": 0.15
  }'
```

## 🔬 Feature Extraction Algorithms

### Fluency Metrics

**Speech Rate (WPS)**
```
Speech Rate = Total Words / Total Duration (seconds)
```

**Pause Detection**
- Identifies gaps between consecutive words
- Gap duration ≥ threshold (default: 0.25s) is considered a pause
- Pause Ratio = Total Pause Time / Total Duration

### Lexical Diversity

**Type-Token Ratio (TTR)**
```
TTR = Number of Unique Words / Total Number of Words
```

**Mean Segmental TTR (MSTTR)**
- Divides text into fixed-size segments (default: 50 words)
- Calculates TTR for each segment
- Returns mean of all segment TTRs
- More stable than TTR for varying text lengths

### CEFR Level Analysis

- Maps each word to CEFR level using Oxford CEFR dictionary
- Calculates percentage distribution across levels (A1, A2, B1, B2, C1)
- Higher proportions of B2/C1 indicate advanced vocabulary

### Pronunciation Assessment

- Categorizes words into confidence bins based on ASR probability scores
- Calculates percentage distribution across bins
- Higher proportions in 85-100% range indicate better pronunciation

## 📁 Project Structure

```
AFAS-Whisper-Feedback-main/
├── config/                 # Configuration files
│   ├── __init__.py
│   └── settings.py        # Application settings
├── src/                    # Source code
│   ├── api/               # API layer
│   │   ├── routes/       # API route handlers
│   │   │   ├── transcripts.py
│   │   │   ├── fluency.py
│   │   │   ├── lexical.py
│   │   │   ├── pronunciation.py
│   │   │   ├── feedback.py
│   │   │   └── analytics.py
│   │   └── dependencies.py
│   ├── core/              # Core functionality
│   │   ├── database.py   # Database configuration
│   │   └── models.py     # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   │   ├── submit.py
│   │   ├── transcript.py
│   │   ├── fluency.py
│   │   ├── lexical.py
│   │   ├── pronunciation.py
│   │   └── feedback.py
│   ├── services/          # Business logic
│   │   ├── asr_service.py
│   │   ├── fluency_service.py
│   │   ├── pronunciation_service.py
│   │   ├── lexical_diversity_service.py
│   │   └── lexical_cefr_service.py
│   ├── utils/             # Utility functions
│   └── main.py           # FastAPI application
├── data/                  # Data files
│   └── oxford_cerf.csv   # CEFR dictionary
├── assets/                # Assets and diagrams
│   └── diagrams/         # System diagrams
├── tests/                 # Test files
├── docs/                  # Documentation
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest tests/
```

## 📝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenAI Whisper for ASR capabilities
- FastAPI for the web framework
- SQLAlchemy for ORM
- Oxford CEFR Dictionary for vocabulary level mapping

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Note**: This system is designed for research and educational purposes. The algorithms have been optimized for effectiveness and are ready for academic publication.

