# 🚀 Hướng dẫn Cài đặt và Chạy Project

## ✅ Yêu cầu hệ thống

- **Python**: 3.10 trở lên
- **Node.js**: 18.x trở lên
- **MongoDB Atlas**: Account (free tier)
- **Git**: Để clone repository

---

## 📥 Bước 1: Clone Repository

```bash
git clone https://github.com/Yukichi-Cat-Can-Code/Schedule_binding_Interviews.git
cd Schedule_binding_Interviews
```

---

## 🐍 Bước 2: Setup Backend (Django)

### 2.1. Tạo Virtual Environment

```bash
cd backend
python -m venv venv
```

### 2.2. Activate Virtual Environment

**Windows (CMD):**

```bash
venv\Scripts\activate
```

**Windows (PowerShell):**

```bash
venv\Scripts\Activate.ps1
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

### 2.3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2.4. Setup MongoDB Atlas

1. Truy cập [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Tạo account miễn phí
3. Tạo cluster mới (chọn Free tier)
4. Tạo database user (username & password)
5. Whitelist IP: `0.0.0.0/0` (Allow access from anywhere)
6. Copy Connection String

### 2.5. Configure Environment Variables

```bash
copy .env.example .env
```

Mở file `.env` và sửa:

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MongoDB Atlas Connection String
MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGODB_NAME=schedule_interview

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Redis (Optional - for Celery)
REDIS_URL=redis://localhost:6379/0

# Algorithm Settings (có thể giữ nguyên default)
GA_POPULATION_SIZE=100
GA_GENERATIONS=200
GA_CROSSOVER_RATE=0.8
GA_MUTATION_RATE=0.15

WEIGHT_CONFLICT=0.4
WEIGHT_IDLE=0.2
WEIGHT_FAIRNESS=0.2
WEIGHT_MATCHING=0.1
WEIGHT_ROOM=0.1
```

### 2.6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2.7. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

Nhập username, email, password

### 2.8. Run Development Server

```bash
python manage.py runserver
```

✅ Backend chạy tại: `http://localhost:8000`
✅ API docs: `http://localhost:8000/api/docs/`
✅ Admin: `http://localhost:8000/admin/`

---

## ⚛️ Bước 3: Setup Frontend (React)

### 3.1. Install Dependencies

Mở terminal mới (giữ nguyên terminal backend):

```bash
cd frontend
npm install
```

### 3.2. Configure Environment (Optional)

Tạo file `.env` trong thư mục `frontend`:

```env
VITE_API_URL=http://localhost:8000/api
```

### 3.3. Run Development Server

```bash
npm run dev
```

✅ Frontend chạy tại: `http://localhost:3000` hoặc `http://localhost:5173`

---

## 🎉 Bước 4: Kiểm tra hoạt động

1. Mở trình duyệt: `http://localhost:3000`
2. Bạn sẽ thấy Dashboard của ứng dụng
3. Thử import dữ liệu Excel hoặc thêm dữ liệu thủ công

---

## 📊 Bước 5: Import Sample Data

### 5.1. Chuẩn bị Excel File

Tạo file `interview_data.xlsx` với 3 sheets:

**Sheet 1: Applicants**

| Email           | Full Name    | Student ID | Available Time          | Position | Notes |
| --------------- | ------------ | ---------- | ----------------------- | -------- | ----- |
| son@example.com | Đặng Lam Sơn | B2405134   | Ca chiều T7 [13h30-18h] | Media    |       |

**Sheet 2: Interviewers**

| Full Name      | Email       | Position | Available Time | Preferred Room | Max Slots |
| -------------- | ----------- | -------- | -------------- | -------------- | --------- |
| Nguyễn Thị Thu | thu@club.vn | Media    | 13h30-18h      | P.201          | 6         |

**Sheet 3: Rooms**

| Room Code | Room Name         | Start Time | End Time | Preferred Position |
| --------- | ----------------- | ---------- | -------- | ------------------ |
| P.201     | Phòng 201 - Khu B | 13:30      | 18:00    | Media              |

### 5.2. Import vào hệ thống

1. Vào **Data Management**
2. Click **Import Excel**
3. Chọn file và upload
4. Kiểm tra dữ liệu đã import

---

## 🧬 Bước 6: Run Algorithm

1. Vào **Algorithm Settings**
2. Chọn thuật toán: GA / Greedy / SA / Compare All
3. Điều chỉnh parameters (optional)
4. Click **Run Algorithm**
5. Xem kết quả

---

## 🐛 Troubleshooting

### Lỗi MongoDB Connection

```
pymongo.errors.ServerSelectionTimeoutError
```

**Giải pháp:**

- Kiểm tra MongoDB URI trong `.env`
- Kiểm tra Network Access (Whitelist IP)
- Kiểm tra database user credentials

### Lỗi CORS

```
Access to XMLHttpRequest blocked by CORS policy
```

**Giải pháp:**

- Kiểm tra `CORS_ALLOWED_ORIGINS` trong `backend/.env`
- Thêm frontend URL vào settings

### Lỗi Port đã được sử dụng

**Backend (8000):**

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Frontend (3000):**

```bash
# Chọn port khác khi Vite hỏi
# Hoặc edit vite.config.js: server: { port: 3001 }
```

### Lỗi Import Django/React

**Django:**

```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**React:**

```bash
rm -rf node_modules package-lock.json
npm install
```

---

## 📝 Development Commands

### Backend

```bash
# Run server
python manage.py runserver

# Run tests
python manage.py test

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Shell
python manage.py shell
```

### Frontend

```bash
# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

---

## 🔧 Cấu hình Production

### Backend (Django)

1. Set `DEBUG=False` trong `.env`
2. Configure `ALLOWED_HOSTS`
3. Collect static files: `python manage.py collectstatic`
4. Use production-ready server (Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn interview_scheduler.wsgi:application
   ```

### Frontend (React)

```bash
npm run build
```

Deploy thư mục `dist/` lên hosting (Vercel, Netlify, etc.)

---

## 🎓 Next Steps

1. ✅ Import dữ liệu mẫu
2. ✅ Chạy Genetic Algorithm
3. ✅ So sánh với Greedy và SA
4. ✅ Xem Timeline và Conflicts
5. ✅ Phân tích kết quả trong Comparison

---

## 💡 Tips

- **MongoDB Atlas Free Tier**: Giới hạn 512MB, đủ cho development
- **Adaptive Mutation**: GA tự động tăng mutation rate khi stuck
- **Elitism**: Top 10% cá thể tốt nhất luôn được giữ lại
- **Heuristic Init**: 60% population được init thông minh → hội tụ nhanh hơn

---

## 📞 Support

Nếu gặp vấn đề:

1. Check console logs (F12)
2. Check backend terminal
3. Xem API docs: `http://localhost:8000/api/docs/`
4. Contact: [GitHub Issues](https://github.com/Yukichi-Cat-Can-Code/Schedule_binding_Interviews/issues)

---

**Chúc bạn code vui vẻ! 🚀**
