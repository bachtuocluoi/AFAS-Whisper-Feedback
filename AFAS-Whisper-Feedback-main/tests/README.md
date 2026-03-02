# Test Suite Documentation

## Tổng Quan

Thư mục `tests/` chứa các script test cho hệ thống AFAS, bao gồm:
- Test API endpoints
- Test feature extraction services
- Test workflow hoàn chỉnh

## Cấu Trúc Test Files

```
tests/
├── test_api.py          # Test tất cả API endpoints
├── test_services.py     # Test feature extraction services
├── test_full_workflow.py # Test workflow hoàn chỉnh
└── README.md           # File này
```

## Cách Chạy Tests

### 1. Test API Endpoints

**Yêu cầu**: Server phải đang chạy

```bash
# Khởi động server (terminal 1)
cd AFAS-Whisper-Feedback-main
python -m uvicorn src.main:app --reload

# Chạy test (terminal 2)
python tests/test_api.py
```

**Test này sẽ:**
- Test health check
- Test tạo và lấy transcripts
- Test tạo và lấy fluency metrics
- Test tạo và lấy lexical metrics
- Test tạo và lấy pronunciation metrics
- Test analytics endpoints

### 2. Test Services (Feature Extraction)

**Không cần server**, test trực tiếp các thuật toán:

```bash
python tests/test_services.py
```

**Test này sẽ:**
- Tạo sample transcript
- Test fluency calculation
- Test pronunciation assessment
- Test lexical diversity (TTR, MSTTR)
- Test CEFR level analysis

### 3. Test Full Workflow

**Yêu cầu**: Server phải đang chạy (nếu muốn lưu vào database)

```bash
# Với audio file thật
python tests/test_full_workflow.py path/to/audio.wav

# Không có audio file (dùng sample)
python tests/test_full_workflow.py
```

**Workflow này sẽ:**
1. Transcribe audio (hoặc dùng sample)
2. Extract tất cả features
3. Lưu vào database qua API
4. Retrieve và hiển thị kết quả

## Cơ Chế Test

### Test API

1. **Connection Test**: Kiểm tra server có đang chạy không
2. **Endpoint Test**: Test từng endpoint với dữ liệu mẫu
3. **Response Validation**: Kiểm tra status code và response format
4. **Error Handling**: Test các trường hợp lỗi (404, validation errors)

### Test Services

1. **Sample Data**: Tạo transcript CSV mẫu
2. **Algorithm Test**: Chạy từng thuật toán với sample data
3. **Result Validation**: Kiểm tra kết quả có hợp lý không
4. **Edge Cases**: Test với dữ liệu rỗng, dữ liệu đặc biệt

### Test Workflow

1. **End-to-End**: Test toàn bộ pipeline từ đầu đến cuối
2. **Integration**: Test tích hợp giữa services và API
3. **Data Flow**: Kiểm tra dữ liệu được xử lý đúng không

## Ví Dụ Output

### Test API
```
=== Testing Health Check ===
Status Code: 200
Response: {'status': 'healthy', 'service': 'AFAS'}
✅ Health check passed

=== Testing Create Fluency ===
Status Code: 201
Response: {
  "id": 1,
  "submit_id": 1,
  "speed_rate": 2.5,
  "pause_ratio": 0.15
}
✅ Create fluency passed
```

### Test Services
```
=== Testing Fluency Service ===
Results:
  File: test_transcript.csv
  Speech Rate: 1.750 words/second
  Pause Ratio: 5.234%

✅ Fluency service test passed
```

## Troubleshooting

### Lỗi: ConnectionError khi test API
- **Nguyên nhân**: Server chưa chạy
- **Giải pháp**: Khởi động server trước: `python -m uvicorn src.main:app --reload`

### Lỗi: FileNotFoundError khi test CEFR
- **Nguyên nhân**: Thiếu file `data/oxford_cerf.csv`
- **Giải pháp**: Đảm bảo file CEFR dictionary có trong thư mục `data/`

### Lỗi: ModuleNotFoundError
- **Nguyên nhân**: Chưa cài đặt dependencies hoặc sai thư mục
- **Giải pháp**: 
  - Cài đặt: `pip install -r requirements.txt`
  - Đảm bảo đang ở đúng thư mục

## Best Practices

1. **Chạy tests thường xuyên**: Đảm bảo code hoạt động đúng sau mỗi thay đổi
2. **Test trước khi commit**: Chạy tests trước khi commit code
3. **Test với dữ liệu thật**: Sau khi test với sample, test với audio files thật
4. **Kiểm tra edge cases**: Test với dữ liệu rỗng, dữ liệu lớn, etc.

## Mở Rộng Tests

Để thêm test mới:

1. Tạo file test mới trong `tests/`
2. Import các modules cần thiết
3. Viết test functions
4. Chạy và kiểm tra kết quả

Ví dụ:
```python
def test_new_feature():
    """Test new feature."""
    result = new_feature_function(input_data)
    assert result['expected_field'] == expected_value
    print("✅ New feature test passed")
```

