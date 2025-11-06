# Hướng dẫn Import Dữ liệu Mẫu

## Tổng quan

Script `import_sample_data.py` sẽ tạo dữ liệu mẫu đầy đủ cho hệ thống, bao gồm:

- **Positions (Vị trí)**: Media, HR, Event, Tech, Marketing
- **Interview Sessions (Đợt phỏng vấn)**: 2024 và 2025
- **Applicants (Ứng viên)**: 35 ứng viên từ dữ liệu thực tế
- **Interviewers (Người phỏng vấn)**: 5 người phỏng vấn
- **Rooms (Phòng họp)**: 6 phòng họp

## Cách chạy

### 1. Đảm bảo MongoDB đã kết nối

Kiểm tra file `.env` có đúng cấu hình:

```env
MONGODB_URI=mongodb+srv://Scheduler_Admin:SchedulerAdmin1@cluster0.abvvvhz.mongodb.net/
MONGODB_DB_NAME=schedule_interview
```

### 2. Kích hoạt virtual environment

```cmd
cd backend
venv\Scripts\activate
```

### 3. Chạy script import

```cmd
python scripts\import_sample_data.py
```

Script sẽ hỏi xác nhận trước khi xóa dữ liệu cũ. Nhập `yes` để tiếp tục.

## Kết quả

Sau khi chạy thành công, bạn sẽ thấy:

```
============================================================
✅ SAMPLE DATA IMPORT COMPLETED SUCCESSFULLY!
============================================================

📊 Summary:
   - Positions: 5
   - Interview Sessions: 2
   - Applicants: 35
   - Interviewers: 5
   - Rooms: 6

🚀 You can now run the scheduling algorithms!
```

## Cấu trúc dữ liệu

### Positions (Vị trí)

```json
{
  "name": "Media",
  "code": "Media",
  "description": "Media and Content Creation",
  "is_active": true
}
```

### Interview Sessions (Đợt phỏng vấn)

```json
{
  "name": "Tuyển thành viên Gen 2025",
  "code": "RECRUIT_2025_Q1",
  "year": 2025,
  "start_date": "2025-11-01",
  "end_date": "2025-11-30",
  "is_active": true
}
```

### Applicants (Ứng viên)

```json
{
  "session_id": "...",
  "email": "sonb2405134@student.ctu.edu.vn",
  "full_name": "Đặng Lam Sơn",
  "student_id": "B2405134",
  "position": "Media",
  "available_time": "Ca chiều T7 [ 1h30 - 6h00 ]",
  "preferred_time": "Chiều t7 17:00 -> 18:00",
  "notes": "",
  "status": "pending"
}
```

## API Endpoints mới

### Positions

- `GET /api/positions/` - Lấy danh sách vị trí
- `POST /api/positions/` - Tạo vị trí mới
- `PUT /api/positions/<id>/` - Cập nhật vị trí
- `DELETE /api/positions/<id>/` - Xóa vị trí

### Interview Sessions

- `GET /api/sessions/` - Lấy danh sách đợt phỏng vấn
- `GET /api/sessions/active/` - Lấy đợt phỏng vấn đang active
- `POST /api/sessions/` - Tạo đợt phỏng vấn mới
- `POST /api/sessions/<id>/activate/` - Kích hoạt đợt phỏng vấn
- `PUT /api/sessions/<id>/` - Cập nhật đợt phỏng vấn
- `DELETE /api/sessions/<id>/` - Xóa đợt phỏng vấn

## Lưu ý

1. **Dữ liệu cũ sẽ bị xóa**: Script sẽ xóa toàn bộ dữ liệu cũ trước khi import
2. **Session ID**: Mỗi applicant, interviewer, room sẽ được gắn với session_id của đợt phỏng vấn
3. **Active Session**: Mặc định đợt 2025 sẽ được active, đợt 2024 không active
4. **Position động**: Positions có thể thêm/xóa/sửa qua API, không còn hard-code

## Mở rộng

### Thêm vị trí mới

```bash
curl -X POST http://localhost:8000/api/positions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Design",
    "code": "Design",
    "description": "UI/UX Design",
    "is_active": true
  }'
```

### Tạo đợt phỏng vấn mới

```bash
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tuyển thành viên Gen 2026",
    "code": "RECRUIT_2026",
    "year": 2026,
    "start_date": "2026-11-01",
    "end_date": "2026-11-30",
    "description": "Đợt tuyển năm 2026",
    "is_active": false
  }'
```

### Chuyển đổi đợt phỏng vấn active

```bash
curl -X POST http://localhost:8000/api/sessions/<session_id>/activate/
```

## Troubleshooting

### Lỗi "MongoDB not connected"

Kiểm tra:

1. File `.env` có đúng cấu hình không
2. MongoDB Atlas có cho phép IP của bạn không
3. Username/Password có đúng không

### Lỗi "ModuleNotFoundError"

```cmd
pip install -r requirements.txt
```

### Script không chạy

Đảm bảo bạn đang ở thư mục `backend` và đã activate virtual environment:

```cmd
cd backend
venv\Scripts\activate
python scripts\import_sample_data.py
```
