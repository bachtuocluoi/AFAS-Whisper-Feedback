# Hướng Dẫn Sử Dụng AFAS System

## Mục Lục

1. [Tổng Quan](#tổng-quan)
2. [Cơ Chế Test](#cơ-chế-test)
3. [Hướng Dẫn Sử Dụng API](#hướng-dẫn-sử-dụng-api)
4. [Workflow Hoàn Chỉnh](#workflow-hoàn-chỉnh)
5. [Ví Dụ Thực Tế](#ví-dụ-thực-tế)

## Tổng Quan

AFAS là hệ thống đánh giá và phản hồi tự động cho kỹ năng nói. Hệ thống hoạt động theo quy trình:

```
Audio File → ASR Transcription → Feature Extraction → Database → Feedback
```

## Cơ Chế Test

### 1. Test Qua API Documentation (Swagger UI)

**Cách đơn giản nhất để test:**

1. **Khởi động server:**
   ```bash
   cd AFAS-Whisper-Feedback-main
   python -m uvicorn src.main:app --reload
   ```

2. **Mở trình duyệt:**
   - Truy cập: http://localhost:8000/docs
   - Đây là giao diện Swagger UI cho phép test trực tiếp

3. **Test các endpoints:**
   - Click vào endpoint muốn test
   - Click "Try it out"
   - Điền dữ liệu vào form
   - Click "Execute"
   - Xem kết quả trả về

### 2. Test Qua Python Scripts

Xem file `tests/test_api.py` và `tests/test_services.py` để có ví dụ chi tiết.

### 3. Test Qua cURL/Postman

Xem phần [Ví Dụ API](#ví-dụ-api) bên dưới.

## Hướng Dẫn Sử Dụng API

### Bước 1: Khởi Động Server

```bash
# Vào thư mục dự án
cd AFAS-Whisper-Feedback-main

# Chạy server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Bước 2: Kiểm Tra Server Đang Chạy

```bash
# Test health check
curl http://localhost:8000/health

# Hoặc mở trình duyệt
http://localhost:8000/health
```

Kết quả mong đợi:
```json
{
  "status": "healthy",
  "service": "AFAS"
}
```

### Bước 3: Workflow Sử Dụng

#### Workflow 1: Xử Lý Audio File Mới

**Bước 3.1: Transcribe Audio (Sử dụng Service trực tiếp)**

```python
from src.services.asr_service import get_asr_service

# Khởi tạo ASR service
asr_service = get_asr_service()

# Transcribe audio file
df = asr_service.transcribe_to_csv(
    audio_file_path="path/to/audio.wav",
    output_csv_path="transcript.csv"
)
```

**Bước 3.2: Tính Toán Features**

```python
from src.services.fluency_service import compute_fluency_metrics
from src.services.pronunciation_service import compute_pronunciation_metrics
from src.services.lexical_diversity_service import compute_lexical_diversity_metrics
from src.services.lexical_cefr_service import compute_lexical_cefr_metrics

# Tính fluency
fluency_result = compute_fluency_metrics("transcript.csv")
print(f"Speech Rate: {fluency_result['speech_rate_wps']:.2f} WPS")
print(f"Pause Ratio: {fluency_result['ratio_pauses_to_duration']:.2%}")

# Tính pronunciation
pronunciation_result = compute_pronunciation_metrics("transcript.csv")
print(f"Excellent (95-100%): {pronunciation_result['95-100%']:.1f}%")

# Tính lexical diversity
lexical_diversity = compute_lexical_diversity_metrics("transcript.csv")
print(f"TTR: {lexical_diversity['TTR']:.3f}")
print(f"MSTTR: {lexical_diversity['MSTTR']:.3f}")

# Tính CEFR distribution
cefr_result = compute_lexical_cefr_metrics("transcript.csv")
print(f"A1: {cefr_result['A1']:.1f}%")
print(f"C1: {cefr_result['C1']:.1f}%")
```

**Bước 3.3: Lưu Vào Database (Qua API)**

```bash
# 1. Tạo Submit entry (giả sử đã có audio_path)
# POST /api/v1/submits/ (nếu có endpoint này)

# 2. Lưu transcripts
curl -X POST "http://localhost:8000/api/v1/transcripts/" \
  -H "Content-Type: application/json" \
  -d '{
    "submit_id": 1,
    "word_index": 0,
    "word": "hello",
    "prob": 0.95,
    "start": 0.0,
    "end": 0.5
  }'

# 3. Lưu fluency metrics
curl -X POST "http://localhost:8000/api/v1/fluency/" \
  -H "Content-Type: application/json" \
  -d '{
    "submit_id": 1,
    "speed_rate": 2.5,
    "pause_ratio": 0.15
  }'

# 4. Lưu lexical metrics
curl -X POST "http://localhost:8000/api/v1/lexical/" \
  -H "Content-Type: application/json" \
  -d '{
    "submit_id": 1,
    "ttr": 0.75,
    "mttr": 0.82,
    "A1": 20.0,
    "A2": 30.0,
    "B1": 25.0,
    "B2": 15.0,
    "C1": 10.0
  }'

# 5. Lưu pronunciation metrics
curl -X POST "http://localhost:8000/api/v1/pronunciation/" \
  -H "Content-Type: application/json" \
  -d '{
    "submit_id": 1,
    "score_0_50": 5.0,
    "score_50_70": 10.0,
    "score_70_85": 20.0,
    "score_85_95": 30.0,
    "score_95_100": 35.0
  }'
```

**Bước 3.4: Lấy Kết Quả**

```bash
# Lấy transcripts
curl http://localhost:8000/api/v1/transcripts/1

# Lấy fluency
curl http://localhost:8000/api/v1/fluency/1

# Lấy lexical
curl http://localhost:8000/api/v1/lexical/1

# Lấy pronunciation
curl http://localhost:8000/api/v1/pronunciation/1
```

## Workflow Hoàn Chỉnh

### Workflow Tự Động (Python Script)

Xem file `tests/test_full_workflow.py` để có script hoàn chỉnh.

### Workflow Thủ Công (Qua API)

1. **Upload audio file** (nếu có endpoint upload)
2. **Transcribe** → Lấy transcript CSV
3. **Extract features** → Tính toán metrics
4. **Save to database** → Lưu qua API
5. **Generate feedback** → Tạo feedback dựa trên metrics
6. **Retrieve results** → Lấy kết quả đánh giá

## Ví Dụ Thực Tế

### Ví Dụ 1: Test Fluency Metrics

```python
# Tạo file transcript.csv mẫu
import pandas as pd

data = {
    'word': ['hello', 'world', 'this', 'is', 'a', 'test'],
    'probability': [0.95, 0.92, 0.88, 0.90, 0.85, 0.93],
    'start': [0.0, 0.5, 1.0, 1.5, 2.0, 2.5],
    'end': [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
}
df = pd.DataFrame(data)
df.to_csv('test_transcript.csv', index=False)

# Tính fluency
from src.services.fluency_service import compute_fluency_metrics
result = compute_fluency_metrics('test_transcript.csv')
print(result)
```

### Ví Dụ 2: Test API Endpoints

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Test health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Test create fluency
fluency_data = {
    "submit_id": 1,
    "speed_rate": 2.5,
    "pause_ratio": 0.15
}
response = requests.post(f"{BASE_URL}/fluency/", json=fluency_data)
print(response.json())

# Test get fluency
response = requests.get(f"{BASE_URL}/fluency/1")
print(response.json())
```

### Ví Dụ 3: Test Analytics

```bash
# Lấy user có fluency tốt nhất
curl http://localhost:8000/api/v1/analytics/most-fluent-user

# Lấy user có vocabulary tốt nhất
curl http://localhost:8000/api/v1/analytics/best-lexical-user

# Lấy user có pronunciation tốt nhất
curl http://localhost:8000/api/v1/analytics/best-pronunciation-user
```

## Lưu Ý Quan Trọng

1. **Database**: SQLite database sẽ được tạo tự động khi chạy lần đầu
2. **Whisper Model**: Model sẽ được download tự động lần đầu sử dụng
3. **CEFR Dictionary**: Cần có file `data/oxford_cerf.csv`
4. **Audio Format**: Whisper hỗ trợ nhiều format (wav, mp3, m4a, etc.)

## Troubleshooting

### Lỗi: ModuleNotFoundError
- **Giải pháp**: Đảm bảo đang ở đúng thư mục và đã cài đặt dependencies

### Lỗi: Database locked
- **Giải pháp**: Đảm bảo không có process nào khác đang sử dụng database

### Lỗi: Whisper model not found
- **Giải pháp**: Model sẽ tự động download, đợi lần đầu tiên

### Lỗi: CEFR dictionary not found
- **Giải pháp**: Kiểm tra file `data/oxford_cerf.csv` có tồn tại không

## Tài Liệu Tham Khảo

- API Documentation: http://localhost:8000/docs
- Architecture: `docs/ARCHITECTURE.md`
- Migration Guide: `docs/MIGRATION.md`

