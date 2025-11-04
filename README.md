# Interview Scheduler - Genetic Algorithm 🧬

Ứng dụng web tự động sắp xếp lịch phỏng vấn thông minh sử dụng Genetic Algorithm và các thuật toán tối ưu hóa tiên tiến.

## 🎯 Tính năng chính

### 🧬 Thuật toán Genetic Algorithm

Thuật toán di truyền với các kỹ thuật tối ưu nâng cao:

- **Heuristic Initialization**: 30% Greedy + 30% Earliest-time + 40% Random
- **Adaptive Mutation Rate**: Tự điều chỉnh tỷ lệ đột biến theo thế hệ
- **Elitism Selection**: Giữ lại 10% cá thể tốt nhất
- **Tournament Selection**: Lựa chọn cha mẹ thông minh
- **Constraint Handling**: Xử lý ràng buộc cứng và mềm

### 📊 So sánh thuật toán

- **Genetic Algorithm**: Tối ưu toàn cục, chất lượng cao
- **Greedy Algorithm**: Nhanh chóng, đơn giản, kết quả khá tốt
- **Simulated Annealing**: Thoát khỏi local optimum hiệu quả
- **Side-by-side Comparison**: Biểu đồ so sánh trực quan

### 🎯 Fitness Function đa tiêu chí

```
Fitness = 0.4×ConflictFree + 0.2×LowIdleTime + 0.2×Fairness + 0.1×PositionMatch + 0.1×RoomUsage
```

- **Conflict Minimization (40%)**: Tránh xung đột lịch
- **Idle Time Reduction (20%)**: Giảm thời gian chờ
- **Fairness Distribution (20%)**: Phân bổ công bằng
- **Position Matching (10%)**: Phù hợp vị trí
- **Room Usage (10%)**: Tối ưu sử dụng phòng

### 🎨 Giao diện người dùng

- **Dashboard**: Tổng quan thống kê và insights
- **Data Management**: Import/Export Excel, CRUD operations
- **Algorithm Settings**: Cấu hình tham số thuật toán
- **Schedule View**: Timeline + Table view với filter
- **Comparison**: Biểu đồ so sánh hiệu suất

## 🛠️ Tech Stack

### Backend

- **Framework**: Django 4.2.16 + Django REST Framework 3.15.2
- **Database**:
  - MongoDB Atlas (PyMongo 4.10.1) - Dữ liệu chính
  - SQLite - Django admin/auth
- **Algorithms**: NumPy 2.0+, Pandas 2.2+
- **Data Processing**: OpenPyXL 3.1.5
- **Python**: 3.13 compatible

### Frontend

- **Framework**: React 18 + Vite 5
- **Styling**: TailwindCSS 3.4
- **Charts**: Recharts 2.10
- **State Management**: React Query 5.17 + Zustand 4.4
- **Routing**: React Router v6.21
- **UI Components**: FullCalendar 6.1, React Hot Toast

## 📦 Cài đặt

### Yêu cầu hệ thống

- Python 3.13+
- Node.js 16+
- MongoDB Atlas account (free tier)

### 🔧 Backend Setup

```bash
# 1. Di chuyển vào thư mục backend
cd backend

# 2. Tạo môi trường ảo
python -m venv venv

# 3. Kích hoạt môi trường ảo
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 4. Cài đặt dependencies
pip install -r requirements.txt

# 5. Tạo file .env từ template
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# 6. Chỉnh sửa .env với MongoDB Atlas connection string
# MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/
# MONGODB_DB_NAME=schedule_interview

# 7. Chạy migrations
python manage.py migrate

# 8. Tạo superuser
python manage.py createsuperuser

# 9. Chạy development server
python manage.py runserver
```

**Backend sẽ chạy tại**: `http://127.0.0.1:8000/`

### 🎨 Frontend Setup

```bash
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt dependencies
npm install

# 3. Chạy development server
npm run dev
```

**Frontend sẽ chạy tại**: `http://localhost:3000/`

### 🗄️ MongoDB Atlas Setup

1. **Đăng ký tài khoản** tại [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. **Tạo cluster** (chọn FREE tier M0)
3. **Tạo database user** với quyền Read/Write
4. **Whitelist IP**: Thêm `0.0.0.0/0` (Allow from anywhere)
5. **Lấy connection string** và cập nhật vào `.env`:
   ```
   MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

## 🗂️ Cấu trúc Project

```
Schedule_binding_Interviews/
├── backend/
│   ├── interview_scheduler/      # Django settings & configuration
│   │   ├── settings.py          # MongoDB + SQLite config
│   │   ├── urls.py              # Main URL routing
│   │   └── wsgi.py
│   │
│   ├── api/                     # REST API
│   │   ├── models.py            # Django models (empty - using MongoDB)
│   │   ├── mongo_models.py      # MongoDB collection models
│   │   ├── mongo_helper.py      # MongoDB utilities
│   │   ├── views.py             # API endpoints
│   │   ├── serializers.py       # Data serialization
│   │   ├── urls.py              # API routing
│   │   └── admin.py
│   │
│   ├── scheduler/               # Algorithm implementations
│   │   ├── genetic_algorithm.py       # GA với heuristic init
│   │   ├── greedy_algorithm.py        # Greedy scheduler
│   │   └── simulated_annealing.py     # SA optimizer
│   │
│   ├── .env                     # Environment variables
│   ├── .env.example             # Template
│   ├── requirements.txt         # Python 3.13 compatible
│   ├── db.sqlite3              # SQLite for Django admin
│   └── manage.py
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── Layout.jsx       # Navigation & layout
    │   ├── pages/
    │   │   ├── Dashboard.jsx    # Trang tổng quan
    │   │   ├── DataManagement.jsx  # CRUD + Import/Export
    │   │   ├── AlgorithmSettings.jsx  # Config thuật toán
    │   │   ├── ScheduleView.jsx  # Timeline + Table view
    │   │   └── Comparison.jsx   # So sánh thuật toán
    │   ├── services/
    │   │   └── api.js           # Axios API calls
    │   ├── App.jsx              # Main app with routing
    │   ├── main.jsx             # Entry point
    │   └── index.css            # TailwindCSS
    │
    ├── postcss.config.js        # PostCSS configuration
    ├── tailwind.config.js       # TailwindCSS config
    ├── vite.config.js           # Vite configuration
    └── package.json
```

## 📊 Định dạng dữ liệu

### Excel Import (3 sheets)

#### Sheet 1: Applicants (Ứng viên)

| Column         | Type  | Description       | Example               |
| -------------- | ----- | ----------------- | --------------------- |
| email          | Email | Email ứng viên    | student@ctu.edu.vn    |
| full_name      | Text  | Họ tên đầy đủ     | Nguyễn Văn A          |
| student_id     | Text  | Mã số sinh viên   | B2014XXX              |
| available_time | Text  | Khung giờ rảnh    | "Mon 8-12, Tue 14-17" |
| preferred_time | Text  | Thời gian ưu tiên | "Tue 14:00"           |
| position       | Text  | Vị trí ứng tuyển  | Media/HR/Event        |
| notes          | Text  | Ghi chú           | Optional              |

#### Sheet 2: Interviewers (Người phỏng vấn)

| Column         | Type    | Description       | Example                |
| -------------- | ------- | ----------------- | ---------------------- |
| full_name      | Text    | Họ tên            | Trần Văn B             |
| email          | Email   | Email             | interviewer@ctu.edu.vn |
| position       | Text    | Vị trí phụ trách  | Media/HR/Event         |
| available_time | Text    | Ca rảnh           | "Mon 8-17, Wed 14-17"  |
| preferred_room | Text    | Phòng ưu tiên     | A101                   |
| max_slots      | Integer | Số ca tối đa/ngày | 6                      |
| notes          | Text    | Ghi chú           | Optional               |

#### Sheet 3: Rooms (Phòng phỏng vấn)

| Column             | Type    | Description    | Example              |
| ------------------ | ------- | -------------- | -------------------- |
| room_code          | Text    | Mã phòng       | A101                 |
| room_name          | Text    | Tên phòng      | Phòng họp A101       |
| start_time         | Time    | Giờ mở         | 08:00                |
| end_time           | Time    | Giờ đóng       | 17:00                |
| preferred_position | Text    | Vị trí ưu tiên | Media                |
| capacity           | Integer | Sức chứa       | 1                    |
| facilities         | Text    | Trang thiết bị | "Máy chiếu, bàn dài" |
| notes              | Text    | Ghi chú        | Optional             |

## 🧬 Chi tiết thuật toán

### Genetic Algorithm Parameters

```python
# Population & Generations
POPULATION_SIZE = 100           # Kích thước quần thể
GENERATIONS = 200               # Số thế hệ
MAX_STAGNANT = 30              # Dừng sớm nếu không cải thiện

# Genetic Operators
CROSSOVER_RATE = 0.8           # Tỷ lệ lai ghép
MUTATION_RATE = 0.15           # Tỷ lệ đột biến (adaptive)
TOURNAMENT_SIZE = 3            # Kích thước tournament
ELITISM_RATIO = 0.1            # Giữ lại 10% tốt nhất

# Initialization Strategy
HEURISTIC_GREEDY = 0.3         # 30% Greedy
HEURISTIC_EARLIEST = 0.3       # 30% Earliest-time
RANDOM_INIT = 0.4              # 40% Random
```

### Fitness Function

```python
def fitness(solution):
    # Các trọng số
    W_CONFLICT = 0.4      # Xung đột (quan trọng nhất)
    W_IDLE = 0.2          # Thời gian chờ
    W_FAIRNESS = 0.2      # Công bằng
    W_MATCHING = 0.1      # Phù hợp vị trí
    W_ROOM = 0.1          # Sử dụng phòng

    return (W_CONFLICT * (1 - conflict_ratio) +
            W_IDLE * (1 - idle_time_ratio) +
            W_FAIRNESS * fairness_score +
            W_MATCHING * matching_score +
            W_ROOM * room_usage_score)
```

### Constraints (Ràng buộc)

#### Hard Constraints (Bắt buộc)

- ✅ Không trùng lịch ứng viên
- ✅ Không trùng lịch interviewer
- ✅ Không trùng lịch phòng
- ✅ Thời gian trong khung available

#### Soft Constraints (Tối ưu)

- 🎯 Ưu tiên preferred time
- 🎯 Match position (Media↔Media, HR↔HR, Event↔Event)
- 🎯 Preferred room cho interviewer
- 🎯 Max slots per day cho interviewer
- 🎯 Giảm idle time
- 🎯 Phân bổ đều workload

## 🚀 Hướng dẫn sử dụng

### 1️⃣ Import Data

- Truy cập **Data Management**
- Upload file Excel (3 sheets: Applicants, Interviewers, Rooms)
- Hệ thống tự động validate và import

### 2️⃣ Configure Algorithm

- Vào **Algorithm Settings**
- Điều chỉnh parameters:
  - Population Size (50-200)
  - Generations (100-500)
  - Crossover Rate (0.6-0.9)
  - Mutation Rate (0.1-0.3)
  - Fitness Weights

### 3️⃣ Run Algorithm

Chọn thuật toán:

- **Genetic Algorithm**: Tối ưu nhất, thời gian trung bình
- **Greedy Algorithm**: Nhanh nhất, kết quả tốt
- **Simulated Annealing**: Thoát local optimum
- **Compare All**: Chạy cả 3 và so sánh

### 4️⃣ View Results

- **Schedule View**: Xem lịch theo timeline hoặc table
- **Metrics**: Fitness score, conflicts, idle time, fairness
- **Export**: Xuất kết quả ra Excel/PDF

### 5️⃣ Compare & Analyze

- **Comparison Page**: Biểu đồ so sánh 3 thuật toán
- **Performance**: Execution time, fitness evolution
- **Quality**: Conflict count, constraint satisfaction

## 📡 API Endpoints

### CRUD Operations

```
GET/POST    /api/applicants/         # Quản lý ứng viên
GET/POST    /api/interviewers/       # Quản lý interviewer
GET/POST    /api/rooms/              # Quản lý phòng
GET/POST    /api/schedules/          # Quản lý lịch
GET/POST    /api/configs/            # Cấu hình thuật toán
```

### Data Management

```
POST   /api/data/import/             # Import Excel
GET    /api/data/statistics/         # Thống kê dashboard
```

### Algorithms

```
POST   /api/algorithm/genetic/       # Chạy GA
POST   /api/algorithm/greedy/        # Chạy Greedy
POST   /api/algorithm/simulated-annealing/  # Chạy SA
GET    /api/algorithm/results/       # Lấy kết quả
```

### Admin

```
GET    /admin/                       # Django admin panel
GET    /api/schema/                  # API documentation (Swagger)
```

## 🐛 Troubleshooting

### Backend không chạy

```bash
# Kiểm tra Python version
python --version  # Cần 3.13+

# Kiểm tra virtual environment
where python  # Windows
which python  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend lỗi 404

```bash
# Xóa node_modules và reinstall
rm -rf node_modules package-lock.json
npm install

# Chạy từ đúng thư mục
cd frontend
npm run dev
```

### MongoDB connection failed

```bash
# Kiểm tra .env file
cat .env  # Linux/Mac
type .env  # Windows

# Test connection string
# Đảm bảo whitelist IP đúng trong MongoDB Atlas
# Kiểm tra username/password không có ký tự đặc biệt
```

## 📚 Tài liệu tham khảo

- [Django Documentation](https://docs.djangoproject.com/)
- [React Documentation](https://react.dev/)
- [MongoDB Atlas](https://docs.atlas.mongodb.com/)
- [Genetic Algorithms - Introduction](https://www.geeksforgeeks.org/genetic-algorithms/)

## 👥 Team

**CTU AI Fundamental Course 2025**

- Instructor: [Tên giảng viên]
- Students: [Danh sách sinh viên]

## 📄 License

This project is for educational purposes - CTU AI Fundamental Course 2025.

---

**Made with ❤️ by CTU Students**
