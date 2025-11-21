# SETUP — Cài đặt & Chạy dự án

Tài liệu này mô tả các bước rõ ràng để cài đặt, cấu hình, chạy và kiểm thử cả backend (Django) và frontend (React). Bao gồm lệnh cho Windows (CMD/PowerShell) và macOS/Linux.

**Mục lục**

- Yêu cầu hệ thống
- Cài đặt backend (venv, dependencies, env, DB)
- Chạy backend (migrations, runserver, superuser)
- Cài đặt & chạy frontend
- Chạy tests
- Cấu hình production & troubleshooting

---

**Yêu cầu hệ thống (recommended)**

- Python 3.10+ (3.10, 3.11 tested)
- Node.js 18.x+ and npm
- Git
- MongoDB Atlas (hoặc MongoDB URI) — dùng để lưu dữ liệu chính
- (Optional) Redis nếu dùng Celery

---

## 1 — Clone repository

Mở terminal và chạy:

```cmd
git clone https://github.com/Yukichi-Cat-Can-Code/Schedule_binding_Interviews.git
cd Schedule_binding_Interviews
```

---

## 2 — Backend (Django)

Làm theo các bước dưới đây trong thư mục `backend/`.

### 2.1 Tạo và kích hoạt virtual environment

Windows (CMD):

```cmd
cd backend
python -m venv venv
venv\Scripts\activate
```

Windows (PowerShell):

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

Nếu activation thành công, prompt sẽ hiển thị tên `venv`.

### 2.2 Cài dependencies

Trong `backend` và venv đã kích hoạt:

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.3 Cấu hình biến môi trường

Sao chép mẫu `.env.example` và chỉnh thông tin:

Windows (CMD):

```cmd
copy .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS / Linux:

```bash
cp .env.example .env
```

Mở file `.env` và cập nhật ít nhất các mục sau:

- `SECRET_KEY` — khóa bí mật Django
- `DEBUG` — set `True` cho development
- `ALLOWED_HOSTS` — ví dụ: `localhost,127.0.0.1`
- `MONGODB_URI` — connection string MongoDB Atlas (ví dụ `mongodb+srv://<user>:<pass>@cluster0...`)
- `MONGODB_NAME` — tên database (ví dụ `schedule_interview`)
- `CORS_ALLOWED_ORIGINS` — ví dụ `http://localhost:3000,http://localhost:5173`
- (Tùy chọn) `REDIS_URL` nếu dùng Celery

Ví dụ (không lưu mật khẩu thật vào repo):

```env
SECRET_KEY=your-secret
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_NAME=schedule_interview
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 2.4 Migrations & tạo superuser

Chạy migrations (SQLite/Django models) và tạo superuser:

```cmd
# Trong CMD / PowerShell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

Nhập username, email và password khi được yêu cầu.

### 2.5 Chạy server (development)

```cmd
python manage.py runserver
```

- Backend mặc định chạy tại `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/api/docs/`
- Admin: `http://127.0.0.1:8000/admin/`

Muốn bind ra mọi interface (ví dụ dùng trong container/dev VM):

```cmd
python manage.py runserver 0.0.0.0:8000
```

---

## 3 — Frontend (React / Vite)

Mở terminal mới (không cần venv). Vào thư mục `frontend/`.

### 3.1 Cài dependencies

```cmd
cd frontend
npm install
```

### 3.2 Tạo file cấu hình frontend (tùy chọn)

Tạo `frontend/.env` nếu cần tùy chỉnh API URL:

```env
VITE_API_URL=http://localhost:8000/api
```

### 3.3 Chạy dev server

```cmd
npm run dev
```

- Vite thường hiển thị port 5173 hoặc 3000 tùy cấu hình. Mở URL được in ra.

### 3.4 Build production

```cmd
npm run build
npm run preview
```

---

## 4 — Chạy tests

### Backend

```cmd
# Trong backend venv
python manage.py test
```

Chạy test cụ thể app hoặc test name nếu cần (django supports -k type filters via pytest if configured).

### Frontend

Kiểm tra `package.json` để xem có script test/lint. Thường có:

```cmd
npm run lint
# hoặc nếu có test
npm test
```

---

## 5 — Một số lệnh hữu ích / benchmarks

- Chạy một script Python trong `backend/scripts/`:

```cmd
# trong backend venv
python backend\scripts\plot_ga_ndjson.py
```

- Chạy benchmark (ví dụ):

```cmd
python benchmarks\soft_penalty_sweep_multi.py --population 120 --generations 30 --runs 60
```

Lưu ý: chạy các script lớn nên đảm bảo venv active và biến môi trường (ví dụ MONGODB_URI) đã set.

---

## 6 — Troubleshooting (những lỗi phổ biến)

- MongoDB connection timeout (`pymongo.errors.ServerSelectionTimeoutError`):

  - Kiểm tra `MONGODB_URI` trong `.env`.
  - Kiểm tra Network Access trên MongoDB Atlas (whitelist IP hoặc 0.0.0.0/0 cho dev).
  - Kiểm tra user/password và tên DB `MONGODB_NAME`.

- CORS error: `Access to XMLHttpRequest blocked by CORS policy`:

  - Đảm bảo `CORS_ALLOWED_ORIGINS` chứa địa chỉ frontend (http://localhost:5173 hoặc http://localhost:3000).

- Port đã dùng (Windows):

```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

- Nếu frontend báo thiếu package hoặc lỗi node_modules:

```cmd
// Xoá node_modules + lockfile rồi cài lại
rmdir /S /Q node_modules
del package-lock.json
npm install
```

---

## 7 — Production checklist (tóm tắt)

- Set `DEBUG=False` và cấu hình `ALLOWED_HOSTS`.
- Đảm bảo các secret/credentials được lưu an toàn (env vars, vault).
- Chạy `python manage.py collectstatic` nếu dùng static files.
- Dùng Gunicorn / uWSGI + reverse proxy (nginx) cho Django; phục vụ frontend từ CDN hoặc static host.

---

## 8 — Tài nguyên & hỗ trợ

- API docs: `http://localhost:8000/api/docs/`
- Admin: `http://localhost:8000/admin/`
- Issues/Support: https://github.com/Yukichi-Cat-Can-Code/Schedule_binding_Interviews/issues

---

Nếu bạn muốn, tôi có thể: chạy tests (backend/frontend) ở môi trường hiện tại, hoặc tạo tập lệnh `run-dev.bat` / `run-dev.sh` để khởi động cả backend + frontend cùng lúc. Muốn tôi làm tiếp không?
