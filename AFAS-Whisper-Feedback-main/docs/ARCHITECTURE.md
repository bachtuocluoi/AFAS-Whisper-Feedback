# System Architecture Documentation

This document provides detailed technical documentation of the AFAS system architecture, suitable for academic paper publication.

## System Overview

AFAS (Automatic Feedback for Speaking) is a multi-component system for automated speech assessment. The system processes audio input through several stages: ASR transcription, feature extraction, metric calculation, and feedback generation.

## Component Architecture

### 1. ASR Module (`src/services/asr_service.py`)

**Purpose**: Convert speech audio to text with word-level granularity.

**Technology**: OpenAI Whisper model

**Output Format**:
- Word-level transcription
- Timestamps (start, end) for each word
- Confidence probability scores (0.0 to 1.0)

**Key Methods**:
- `transcribe()`: Core transcription function
- `transcribe_to_csv()`: Transcription with CSV export

### 2. Fluency Analysis Module (`src/services/fluency_service.py`)

**Purpose**: Measure speech fluency through rate and pause analysis.

**Metrics Computed**:

1. **Speech Rate (WPS)**
   ```
   Speech Rate = Total Words / Total Duration (seconds)
   ```
   - Measures words per second
   - Higher values indicate faster speech

2. **Pause Ratio**
   ```
   Pause Ratio = Total Pause Time / Total Duration
   ```
   - Identifies pauses between words
   - Threshold: 0.25 seconds (configurable)
   - Lower values indicate more fluent speech

**Algorithm**:
1. Extract word timestamps from transcript
2. Calculate gaps between consecutive words
3. Identify gaps ≥ threshold as pauses
4. Compute total pause duration
5. Calculate ratio to total speech duration

### 3. Lexical Diversity Module (`src/services/lexical_diversity_service.py`)

**Purpose**: Assess vocabulary richness and diversity.

**Metrics Computed**:

1. **Type-Token Ratio (TTR)**
   ```
   TTR = Number of Unique Words / Total Number of Words
   ```
   - Range: 0.0 to 1.0
   - Higher values indicate more diverse vocabulary
   - Sensitive to text length

2. **Mean Segmental Type-Token Ratio (MSTTR)**
   ```
   MSTTR = Mean(TTR_segment_1, TTR_segment_2, ..., TTR_segment_n)
   ```
   - More stable than TTR
   - Divides text into fixed-size segments (default: 50 words)
   - Calculates TTR for each segment
   - Returns mean of segment TTRs
   - Less sensitive to text length variations

**Algorithm**:
1. Tokenize and normalize words
2. For TTR: Calculate unique types / total tokens
3. For MSTTR:
   - Divide tokens into segments of size N
   - Calculate TTR for each segment
   - Return arithmetic mean of segment TTRs

### 4. CEFR Level Analysis Module (`src/services/lexical_cefr_service.py`)

**Purpose**: Evaluate vocabulary complexity using CEFR framework.

**CEFR Levels**: A1 (Beginner) → A2 → B1 → B2 → C1 → C2 (Advanced)

**Metrics Computed**:
- Percentage distribution of words across CEFR levels
- Provides insight into vocabulary sophistication

**Algorithm**:
1. Load CEFR dictionary (word → level mapping)
2. For each word in transcript:
   - Normalize word (lowercase, remove punctuation)
   - Lookup CEFR level in dictionary
3. Count words per level
4. Calculate percentage distribution

**Data Source**: Oxford CEFR Dictionary (`data/oxford_cerf.csv`)

### 5. Pronunciation Assessment Module (`src/services/pronunciation_service.py`)

**Purpose**: Evaluate pronunciation quality using ASR confidence scores.

**Hypothesis**: Higher ASR confidence scores correlate with better pronunciation accuracy.

**Confidence Bins**:
- 0-50%: Poor pronunciation
- 50-70%: Below average
- 70-85%: Average
- 85-95%: Good
- 95-100%: Excellent

**Metrics Computed**:
- Percentage of words in each confidence bin
- Distribution provides pronunciation quality profile

**Algorithm**:
1. Extract probability scores from transcript
2. Categorize words into confidence bins
3. Count words per bin
4. Calculate percentage distribution

### 6. Database Schema (`src/core/models.py`)

**Entity Relationship Diagram**:

```
Submit (1) ──< (1) Transcript
         │
         ├──< (1) Fluency
         │
         ├──< (1) Lexical
         │
         ├──< (1) Pronunciation
         │
         └──< (N) Feedback
```

**Key Tables**:

- **Submit**: User submissions (audio files)
- **Transcript**: Word-level transcription results
- **Fluency**: Fluency metrics per submission
- **Lexical**: Lexical diversity and CEFR metrics
- **Pronunciation**: Pronunciation confidence distribution
- **Feedback**: Generated feedback text

### 7. API Layer (`src/api/routes/`)

**RESTful API Design**:

- **Resource-based URLs**: `/api/v1/{resource}/{id}`
- **HTTP Methods**: GET (retrieve), POST (create)
- **Response Format**: JSON with Pydantic validation
- **Error Handling**: Standard HTTP status codes

**Route Organization**:
- `transcripts.py`: Transcript management
- `fluency.py`: Fluency metrics
- `lexical.py`: Lexical metrics
- `pronunciation.py`: Pronunciation metrics
- `feedback.py`: Feedback management
- `analytics.py`: Statistical analysis

## Data Flow

```
Audio File
    │
    ▼
[Whisper ASR]
    │
    ▼
Word-level Transcript (CSV)
    │
    ├──► [Fluency Service] ──► Fluency Metrics
    │
    ├──► [Lexical Diversity Service] ──► TTR, MSTTR
    │
    ├──► [CEFR Service] ──► CEFR Distribution
    │
    └──► [Pronunciation Service] ──► Confidence Distribution
            │
            ▼
    [Database Storage]
            │
            ▼
    [Feedback Generation]
```

## Configuration Management

**Centralized Configuration** (`config/settings.py`):
- Database connection string
- Whisper model selection
- Feature extraction parameters
- File paths

**Environment Variable Support**:
- Override defaults via `.env` file
- Type-safe with Pydantic Settings

## Design Principles

1. **Separation of Concerns**: Clear boundaries between API, services, and data layers
2. **Modularity**: Each feature extraction algorithm is independent
3. **Extensibility**: Easy to add new metrics or features
4. **Documentation**: Comprehensive docstrings for all components
5. **Type Safety**: Type hints throughout codebase

## Performance Considerations

- **ASR Processing**: Whisper model loading is cached (singleton pattern)
- **Database**: SQLite for development, easily upgradeable to PostgreSQL
- **Feature Extraction**: Efficient pandas operations for large transcripts

## Algorithm Preservation

**Important**: All feature extraction algorithms remain unchanged from the original implementation. Only code organization and documentation have been improved for:
- Better maintainability
- Easier paper publication
- Enhanced reproducibility

## Future Enhancements

Potential areas for extension:
- Real-time processing support
- Additional fluency metrics (articulation rate, disfluency detection)
- Advanced pronunciation models (phonetic alignment)
- Machine learning-based feedback generation
- Multi-language support

