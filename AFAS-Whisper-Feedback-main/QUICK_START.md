# Quick Start Guide

## Vấn đề đã gặp và cách giải quyết

### Lỗi 1: Không tìm thấy requirements.txt
**Nguyên nhân**: File nằm trong thư mục con  
**Giải pháp**: Đã copy file lên thư mục gốc

### Lỗi 2: uvicorn không được nhận diện
**Nguyên nhân**: Scripts không có trong PATH  
**Giải pháp**: Sử dụng `python -m uvicorn` thay vì `uvicorn`

### Lỗi 3: ModuleNotFoundError
**Nguyên nhân**: Đang ở sai thư mục  
**Giải pháp**: Cần vào thư mục con `AFAS-Whisper-Feedback-main`

## Cách chạy server

### Cách 1: Sử dụng script (Dễ nhất)
```bash
# Chạy file batch
start_server.bat
```

### Cách 2: Chạy thủ công
```bash
# Bước 1: Vào đúng thư mục
cd AFAS-Whisper-Feedback-main

# Bước 2: Chạy server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Cách 3: Từ thư mục gốc
```bash
# Từ thư mục AFAS-Whisper-Feedback-main (thư mục ngoài)
cd AFAS-Whisper-Feedback-main
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Kiểm tra server

Sau khi chạy, mở trình duyệt và truy cập:
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Cấu trúc thư mục quan trọng

```
AFAS-Whisper-Feedback-main/          ← Thư mục gốc (có requirements.txt)
└── AFAS-Whisper-Feedback-main/      ← Thư mục con (có src/)
    ├── src/
    │   └── main.py                  ← File chính
    ├── config/
    ├── data/
    └── ...
```

**Lưu ý**: Phải chạy từ thư mục con `AFAS-Whisper-Feedback-main` (nơi có thư mục `src/`)

