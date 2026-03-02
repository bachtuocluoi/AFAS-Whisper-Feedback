# Hướng Dẫn Test AFAS System

## Tổng Quan

Hệ thống AFAS có 3 cách test chính:

1. **Test qua Swagger UI** (Dễ nhất - Không cần code)
2. **Test qua Python Scripts** (Tự động hóa)
3. **Test qua cURL/Postman** (Linh hoạt)

## Cách 1: Test Qua Swagger UI (Khuyến Nghị Cho Người Mới)

### Bước 1: Khởi Động Server

```bash
cd AFAS-Whisper-Feedback-main
python -m uvicorn src.main:app --reload
```

### Bước 2: Mở Swagger UI

Mở trình duyệt và truy cập: **http://localhost:8000/docs**

### Bước 3: Test Endpoints

1. **Chọn endpoint** muốn test (ví dụ: `GET /api/v1/health`)
2. **Click "Try it out"**
3. **Điền thông tin** (nếu có parameters)
4. **Click "Execute"**
5. **Xem kết quả** trong phần "Responses"

### Ví Dụ: Test Health Check

1. Tìm endpoint `GET /health`
2. Click "Try it out"
3. Click "Execute"
4. Kết quả:
   ```json
   {
     "status": "healthy",
     "service": "AFAS"
   }
   ```

### Ví Dụ: Test Create Fluency

1. Tìm endpoint `POST /api/v1/fluency/`
2. Click "Try it out"
3. Điền JSON:
   ```json
   {
     "submit_id": 1,
     "speed_rate": 2.5,
     "pause_ratio": 0.15
   }
   ```
4. Click "Execute"
5. Xem kết quả trả về

## Cách 2: Test Qua Python Scripts

### Test API Endpoints

```bash
# Terminal 1: Khởi động server
python -m uvicorn src.main:app --reload

# Terminal 2: Chạy test
python tests/test_api.py
```

**Script này sẽ test:**
- ✅ Health check
- ✅ Tạo và lấy transcripts
- ✅ Tạo và lấy fluency metrics
- ✅ Tạo và lấy lexical metrics
- ✅ Tạo và lấy pronunciation metrics
- ✅ Analytics endpoints

### Test Feature Extraction Services

```bash
# Không cần server
python tests/test_services.py
```

**Script này sẽ:**
- ✅ Tạo sample transcript
- ✅ Test fluency calculation
- ✅ Test pronunciation assessment
- ✅ Test lexical diversity
- ✅ Test CEFR analysis

### Test Full Workflow

```bash
# Với audio file
python tests/test_full_workflow.py path/to/audio.wav

# Không có audio (dùng sample)
python tests/test_full_workflow.py
```

**Workflow:**
1. Transcribe audio → CSV
2. Extract features
3. Save to database
4. Retrieve results

## Cách 3: Test Qua cURL

### Health Check

```bash
curl http://localhost:8000/health
```

### Get Fluency

```bash
curl http://localhost:8000/api/v1/fluency/1
```

### Create Fluency

```bash
curl -X POST "http://localhost:8000/api/v1/fluency/" \
  -H "Content-Type: application/json" \
  -d '{
    "submit_id": 1,
    "speed_rate": 2.5,
    "pause_ratio": 0.15
  }'
```

### Get Analytics

```bash
# Most fluent user
curl http://localhost:8000/api/v1/analytics/most-fluent-user

# Best lexical user
curl http://localhost:8000/api/v1/analytics/best-lexical-user

# Best pronunciation user
curl http://localhost:8000/api/v1/analytics/best-pronunciation-user
```

## Cơ Chế Test Chi Tiết

### 1. Unit Tests (Services)

Test từng thuật toán riêng lẻ:

```python
from src.services.fluency_service import compute_fluency_metrics

# Test với sample data
result = compute_fluency_metrics("test_transcript.csv")
assert result['speech_rate_wps'] > 0
assert 0 <= result['ratio_pauses_to_duration'] <= 1
```

### 2. Integration Tests (API)

Test tích hợp giữa API và database:

```python
import requests

# Create
response = requests.post(
    "http://localhost:8000/api/v1/fluency/",
    json={"submit_id": 1, "speed_rate": 2.5, "pause_ratio": 0.15}
)
assert response.status_code == 201

# Read
response = requests.get("http://localhost:8000/api/v1/fluency/1")
assert response.status_code == 200
```

### 3. End-to-End Tests (Workflow)

Test toàn bộ pipeline:

```python
# 1. Transcribe
asr_service.transcribe_to_csv("audio.wav", "transcript.csv")

# 2. Extract features
fluency = compute_fluency_metrics("transcript.csv")

# 3. Save to DB
requests.post("/api/v1/fluency/", json=fluency)

# 4. Retrieve
result = requests.get("/api/v1/fluency/1")
```

## Test Checklist

### Trước Khi Test

- [ ] Server đang chạy (nếu test API)
- [ ] Dependencies đã cài đặt (`pip install -r requirements.txt`)
- [ ] Database file có thể tạo được
- [ ] CEFR dictionary có sẵn (`data/oxford_cerf.csv`)

### Khi Test API

- [ ] Health check trả về 200
- [ ] Có thể tạo records
- [ ] Có thể đọc records
- [ ] Validation errors được xử lý đúng
- [ ] 404 errors cho records không tồn tại

### Khi Test Services

- [ ] Fluency metrics tính đúng
- [ ] Pronunciation distribution hợp lý (tổng = 100%)
- [ ] TTR và MSTTR trong khoảng [0, 1]
- [ ] CEFR distribution hợp lý (tổng = 100%)

## Ví Dụ Test Cases

### Test Case 1: Empty Transcript

```python
# Tạo transcript rỗng
df = pd.DataFrame(columns=['word', 'probability', 'start', 'end'])
df.to_csv('empty.csv', index=False)

# Test
result = compute_fluency_metrics('empty.csv')
assert result['speech_rate_wps'] == 0.0
```

### Test Case 2: Single Word

```python
# Tạo transcript với 1 từ
df = pd.DataFrame({
    'word': ['hello'],
    'probability': [0.95],
    'start': [0.0],
    'end': [1.0]
})
df.to_csv('single.csv', index=False)

# Test
result = compute_fluency_metrics('single.csv')
assert result['speech_rate_wps'] == 1.0
```

### Test Case 3: Invalid Data

```python
# Test với submit_id không tồn tại
response = requests.get("http://localhost:8000/api/v1/fluency/999")
assert response.status_code == 404
```

## Troubleshooting

### Lỗi: Connection refused
- **Nguyên nhân**: Server chưa chạy
- **Giải pháp**: `python -m uvicorn src.main:app --reload`

### Lỗi: ModuleNotFoundError
- **Nguyên nhân**: Thiếu dependencies
- **Giải pháp**: `pip install -r requirements.txt`

### Lỗi: Database locked
- **Nguyên nhân**: Database đang được sử dụng
- **Giải pháp**: Đóng các connection khác

### Lỗi: CEFR dictionary not found
- **Nguyên nhân**: Thiếu file `data/oxford_cerf.csv`
- **Giải pháp**: Đảm bảo file có trong thư mục `data/`

## Best Practices

1. **Test thường xuyên**: Chạy tests sau mỗi thay đổi code
2. **Test với dữ liệu thật**: Sau khi test với sample, test với audio thật
3. **Test edge cases**: Test với dữ liệu rỗng, dữ liệu lớn, etc.
4. **Document test results**: Ghi lại kết quả test để reference

## Tài Liệu Tham Khảo

- **User Guide**: `docs/USER_GUIDE.md` - Hướng dẫn sử dụng chi tiết
- **API Docs**: http://localhost:8000/docs - Swagger UI
- **Test Scripts**: `tests/` - Các script test mẫu

