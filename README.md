# Interview Scheduler - Genetic Algorithm

Ứng dụng web tự động sắp xếp lịch phỏng vấn sử dụng Genetic Algorithm và các thuật toán tối ưu khác.

## 🎯 Tính năng chính

- **Genetic Algorithm**: Thuật toán di truyền với các kỹ thuật tối ưu nâng cao

  - Heuristic initialization (30% Greedy, 30% Earliest-time, 40% Random)
  - Adaptive mutation rate
  - Elitism selection
  - Constraint handling

- **So sánh thuật toán**:

  - Greedy Algorithm: Nhanh, đơn giản
  - Simulated Annealing: Thoát khỏi local optimum
  - Side-by-side comparison với charts

- **Fitness Function đa tiêu chí**:

  - Conflict minimization (g₁ = 0.4)
  - Idle time reduction (g₂ = 0.2)
  - Fairness distribution (g₃ = 0.2)
  - Position matching (g₄ = 0.1)
  - Room usage optimization (g₅ = 0.1)

- **Giao diện thân thiện**:
  - Dashboard tổng quan
  - Data Management (Import/Export Excel)
  - Algorithm Settings (Config parameters)
  - Schedule View (Timeline + Table)
  - Comparison (Charts + Analytics)

## 🛠️ Tech Stack

### Backend

- **Framework**: Django 4.2 + Django REST Framework
- **Database**: MongoDB Atlas (via Djongo)
- **Algorithms**: NumPy, DEAP
- **Data Processing**: Pandas, OpenPyXL

### Frontend

- **Framework**: React 18 + Vite
- **UI**: TailwindCSS
- **Charts**: Recharts
- **State**: React Query + Zustand
- **Routing**: React Router v6

## 📦 Installation

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
copy .env.example .env
# Edit .env with your MongoDB URI

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

## 🗂️ Project Structure

```
Schedule_binding_Interviews/
├── backend/
│   ├── interview_scheduler/    # Django project settings
│   ├── api/                    # REST API (models, views, serializers)
│   ├── scheduler/              # Algorithm implementations
│   │   ├── genetic_algorithm.py
│   │   ├── greedy_algorithm.py
│   │   └── simulated_annealing.py
│   ├── requirements.txt
│   └── manage.py
│
└── frontend/
    ├── src/
    │   ├── components/         # Reusable components
    │   ├── pages/              # Page components
    │   ├── services/           # API services
    │   ├── App.jsx
    │   └── main.jsx
    ├── package.json
    └── vite.config.js
```

## 📊 Data Format

### Excel Import Format (3 sheets)

**Sheet 1 - Applicants:**

- Email, Full Name, Student ID, Available Time, Preferred Time, Position, Notes

**Sheet 2 - Interviewers:**

- Full Name, Email, Position, Available Time, Preferred Room, Max Slots, Notes

**Sheet 3 - Rooms:**

- Room Code, Room Name, Start Time, End Time, Preferred Position, Facilities, Notes

## 🧬 Algorithm Details

### Genetic Algorithm

```python
Population Size: 100
Generations: 200
Crossover Rate: 0.8
Mutation Rate: 0.15 (adaptive)
Tournament Size: 3
Elitism: 10%
```

### Fitness Function

```
Fitness = g₁(1-Conflicts) + g₂(1-IdleTime) + g₃(Fairness) + g₄(Matching) + g₅(RoomUsage)
```

## 🚀 Usage

1. **Import Data**: Upload Excel file với 3 sheets
2. **Configure Algorithm**: Adjust parameters
3. **Run Algorithm**: Choose GA, Greedy, SA, or Compare All
4. **View Results**: Check schedule timeline, conflicts, metrics
5. **Compare**: Analyze performance across algorithms

## 📄 License

This project is for educational purposes - CTU AI Fundamental Course 2025.
