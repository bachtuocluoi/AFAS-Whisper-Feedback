# Migration Guide

This document describes the changes made to reorganize the project structure for better maintainability and paper publication readiness.

## Directory Structure Changes

### Old Structure
```
AFAS-Whisper-Feedback-main/
├── api/
│   └── auth.py
├── asr/
│   └── whisper_service.py
├── db/
│   ├── crud.py
│   ├── database.py
│   └── models.py
├── features/
│   ├── fluency.py
│   ├── lexical_cefr.py
│   ├── lexical_diversity.py
│   └── pronunciation.py
└── data/
    └── oxford_cerf.csv
```

### New Structure
```
AFAS-Whisper-Feedback-main/
├── config/              # Configuration management
│   └── settings.py
├── src/
│   ├── api/            # API layer (separated routes)
│   │   ├── routes/
│   │   └── dependencies.py
│   ├── core/           # Core functionality
│   │   ├── database.py
│   │   └── models.py
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic (renamed from features)
│   │   ├── asr_service.py
│   │   ├── fluency_service.py
│   │   ├── pronunciation_service.py
│   │   ├── lexical_diversity_service.py
│   │   └── lexical_cefr_service.py
│   └── main.py         # FastAPI app entry point
├── data/               # Data files
├── assets/             # Diagrams and assets
├── tests/              # Test files
└── docs/               # Documentation
```

## Key Improvements

### 1. Separation of Concerns
- **API Routes**: Separated into individual route files by domain
- **Schemas**: Extracted Pydantic models into dedicated schema files
- **Services**: Business logic separated from API layer
- **Core**: Database and models in dedicated core package

### 2. Configuration Management
- Centralized configuration in `config/settings.py`
- Environment variable support
- Type-safe settings with Pydantic

### 3. Documentation
- Comprehensive docstrings for all functions and classes
- Algorithm descriptions for paper publication
- API documentation via FastAPI auto-docs

### 4. Code Quality
- Type hints throughout
- Consistent naming conventions
- Proper error handling
- Modular design for easy testing

## Import Changes

### Old Imports
```python
from db.models import Submit
from db.database import SessionLocal
from features.fluency import compute_fluency_metrics
```

### New Imports
```python
from src.core.models import Submit
from src.core.database import SessionLocal
from src.services.fluency_service import compute_fluency_metrics
```

## API Changes

### Old API Structure
- All routes in `db/crud.py`
- Mixed CRUD and analytics functions

### New API Structure
- Routes organized by domain in `src/api/routes/`
- Analytics separated into dedicated route file
- Base path: `/api/v1/`

### Example: Old vs New Endpoints

**Old:**
```
GET /transcripts/{submit_id}
POST /transcript/
```

**New:**
```
GET /api/v1/transcripts/{submit_id}
POST /api/v1/transcripts/
```

## Running the Application

### Old Way
```bash
# If using db/crud.py directly
uvicorn db.crud:app --reload
```

### New Way
```bash
uvicorn src.main:app --reload
```

## Algorithm Preservation

**Important**: All algorithms remain unchanged. Only the code organization and documentation have been improved:

- ✅ Fluency calculation algorithm: **Unchanged**
- ✅ Pause detection algorithm: **Unchanged**
- ✅ TTR/MSTTR calculation: **Unchanged**
- ✅ CEFR level mapping: **Unchanged**
- ✅ Pronunciation scoring: **Unchanged**

## Benefits for Paper Publication

1. **Clear Algorithm Documentation**: Each algorithm is well-documented with formulas and explanations
2. **Modular Design**: Easy to reference specific components
3. **Professional Structure**: Industry-standard project organization
4. **Reproducibility**: Clear configuration and setup instructions
5. **Extensibility**: Easy to add new features or metrics

## Backward Compatibility

The old files are preserved in their original locations for reference. To use the new structure:

1. Update imports in your code
2. Use new API endpoints
3. Update configuration if needed

## Questions?

Refer to the main README.md for detailed documentation on the new structure.

