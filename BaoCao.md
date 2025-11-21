# BÁO CÁO DỰ ÁN — INTERVIEW SCHEDULER (GENETIC ALGORITHM)

**Phiên bản:** V1.1.1

**Dựa trên mã nguồn:** `backend/scheduler/*`, `settings.py`, `requirements.txt`

---

## Mục lục

- **1. Tổng quan**
- **2. Yêu cầu & Môi trường**
- **3. Đặc tả chức năng (SRS)**
- **4. Kiến trúc & Thiết kế**
- **5. Phân tích thuật toán (GA) — Chi tiết**
- **6. Triển khai, Chạy & Cấu hình**
- **7. Rủi ro, Hạn chế & Đề xuất**
- **8. Kết luận**

---

## 1. Tổng quan

- **Mục tiêu:** Tự động hóa việc lập lịch phỏng vấn — ghép ứng viên, nhà phỏng vấn, phòng, khung giờ sao cho:
  - Không vi phạm ràng buộc cứng (hard constraints).
  - Tối thiểu thời gian chờ, cân bằng tải giữa nhà phỏng vấn, tận dụng phòng hiệu quả.
- **Thuật toán lõi:** Genetic Algorithm (GA) với các biến thể (crossover/mutation/repair/memetic). Mô-đun chính nằm trong `backend/scheduler`.

## 2. Yêu cầu & Môi trường

- **Phần mềm:** Python 3.11–3.13, Django 4.2.x, Django REST Framework, `numpy`, `pandas`, `pymongo` (tùy chọn).
- **Cài đặt nhanh (Windows `cmd.exe`):**
  - Tạo venv & cài dependencies:
    ```cmd
    cd backend
    python -m venv .venv
    .venv\Scripts\activate
    pip install --upgrade pip
    pip install -r requirements.txt
    ```
  - Biến môi trường (ví dụ):
    ```cmd
    set SECRET_KEY=your-secret-key
    set DEBUG=True
    set MONGODB_URI=mongodb://localhost:27017/
    set GA_POPULATION_SIZE=100
    set GA_GENERATIONS=200
    set GA_CROSSOVER_RATE=0.8
    set GA_MUTATION_RATE=0.15
    ```
- **Tài nguyên gợi ý:** Dev nhỏ: 2 CPU, 4GB RAM; production: 4–8 CPU, 16–32GB RAM; batch lớn: cân nhắc worker/Celery + Redis.

## 3. Đặc tả chức năng (SRS)

- **FR1:** Nhận `applicants` (id, position, available_time, preferred_time, ...).
- **FR2:** Nhận `interviewers` (id, skills/position, availability).
- **FR3:** Nhận `rooms` (id, capacity, availability).
- **FR4:** Parse thời gian (TimeParser trong `time_parser.py`) → tập các time slots chuẩn.
- **FR5:** Khởi tạo quần thể (greedy / earliest / random) trong `GeneticAlgorithm.initialize_population`.
- **FR6:** Tính fitness (kết hợp conflict, idle, fairness, matching, room usage).
- **FR7:** Evolve: selection, crossover, mutation, repair, elitism; trả về best_solution + fitness_history.
- **FR8:** API trigger job sync/async (Celery optional) và endpoint truy xuất kết quả.

## 4. Kiến trúc & Thiết kế

- **Modules chính:**
  - `time_parser.py` — parse strings tiếng Việt → slots.
  - `genetic_algorithm.py` — core GA (Gene dataclass, Chromosome, evolve).
  - `genetic_algorithm_variant*.py` — các biến thể selection/crossover/mutation.
  - `api/` — serializers, views để khởi chạy và lấy kết quả.
- **Lưu trữ:**
  - `SQLite` cho Django admin (mặc định).
  - `MongoDB` tùy chọn cho dữ liệu lịch/phân tích (`MONGODB_URI`).
- **Luồng hoạt động tóm tắt:**
  1. API nhận payload → validate.
  2. TimeParser chuẩn hóa → slots.
  3. Khởi tạo population.
  4. Evolve → trả best solution, lưu snapshot.

## 5. Phân tích thuật toán (GA) — Chi tiết

### 5.1 Biểu diễn (Encoding)

- `Gene = (applicant_id, interviewer_id, room_id, start_time, end_time, position)`.
- `Chromosome = [Gene_1, ..., Gene_n]` với n ≈ số applicants scheduled.
- Đây là encoding object/record-based — thuận tiện thao tác metadata nhưng cần repair để tránh duplicate/conflict.

### 5.2 Khởi tạo quần thể

- Tích hợp 3 chiến lược: Greedy (30%), Earliest-first (30%), Random (40%).
- Greedy ưu tiên applicants có ít slot khả dụng.

### 5.3 Hàm fitness — công thức

- Fitness tổng (chuẩn hoá 0..1):
  $$ Fitness(C) = w_C(1 - S_C(C)) + w_I(1 - S_I(C)) + w_F S_F(C) + w_M S_M(C) + w_R S_R(C) $$
  - Mặc định gợi ý: $w_C=0.4$, $w_I=0.2$, $w_F=0.2$, $w_M=0.1$, $w_R=0.1$.
- Các thành phần chuẩn hoá:
  - Conflict score $S_C(C)$:
    - Đếm số vi phạm overlap giữa genes (interviewer/room/applicant).
    - Chuẩn hoá đề xuất:
      $$ S_C(C) = \frac{conflicts}{\binom{|C|}{2}} $$
    - Khuyến nghị: xem là hard constraint (nên repair hoặc fitness→0).
  - Idle time $S_I(C)$:
    $$ S*I(C) = \frac{\sum_i \sum_k \max(0, start*{k+1}^{(i)} - end*k^{(i)})}{\sum_i (end*{last}^{(i)} - start\_{first}^{(i)})} $$
  - Fairness $S_F(C)$ (ví dụ CV-based):
    $$ S_F(C) = 1 - \frac{\sigma(c_i)}{\mu(c_i) + \epsilon} $$
    với $c_i$ = số ca của interviewer $i$.
  - Matching $S_M(C)$:
    $$ S*M(C) = \frac{1}{|C|}\sum*{g\in C}\mathbf{1}\{position(applicant(g))=position(interviewer(g))\} $$
  - Room usage $S_R(C)$:
    $$ S*R(C) = \frac{\sum*{g\in C} duration(g)}{\sum\_{r\in rooms} available_time(r)} $$

### 5.4 Selection / Crossover / Mutation

- Selection mặc định: tournament selection (k=3). Variant: rank selection, roulette.
- Crossover: single-point (base), uniform (variant), Order Crossover (OX) cho representation permutation.
- Mutation: change room, shift time (±slot), swap genes, reassign interviewer.
- Adaptive mutation: tăng khi stagnation.

### 5.5 Repair & Constraint handling

- `repair_chromosome()` hiện là placeholder — cần implement:
  - Index resource calendars (interviewer/room).
  - Khi overlap: try shift later gene→nearest valid slot; nếu không được thì reassign interviewer (same skill) hoặc room.
  - Nếu không thể fix → mark chromosome invalid (fitness=0) hoặc loại bỏ offending gene.
- Recommendation: treat hard constraints strictly (repair-first, heavy-penalty if unfixable).

### 5.6 Độ phức tạp & tối ưu hoá

- Naive conflict check O(n^2) per chromosome → tổng O(P \* n^2) per generation.
- Tối ưu: group-by-resource + sort → O(n log n) per chromosome.
- Parallelize evaluation across population (multiprocessing / Celery).

### 5.7 Điều kiện dừng

- Mặc định: max generations $G_{max}$ (ví dụ 200).
- Khuyến nghị: thêm early-stopping khi best fitness ≥ target_threshold (ví dụ 0.98) hoặc stagnation limit hoặc time budget.

## 6. Triển khai, Chạy & Cấu hình

- **Chạy GA từ Python shell:**
  ```py
  from scheduler.genetic_algorithm import GeneticAlgorithm
  from interview_scheduler.settings import ALGORITHM_CONFIG
  config = ALGORITHM_CONFIG['GA']
  ga = GeneticAlgorithm(config)
  result = ga.evolve(applicants, interviewers, rooms)
  print(result['best_fitness'])
  ```
- **Cấu hình quan trọng (có thể qua `.env`):**
  - `GA_POPULATION_SIZE`, `GA_GENERATIONS`, `GA_CROSSOVER_RATE`, `GA_MUTATION_RATE`, `GA_TARGET_FITNESS`, `MAX_WALL_TIME_SECONDS`.

## 7. Rủi ro, Hạn chế & Đề xuất

- **Vấn đề hiện tại:**
  - `repair_chromosome` chưa triển khai → nguy cơ trả lịch vi phạm hard constraints.
  - `_calculate_matching` và `_calculate_room_usage` dùng heuristic/placeholder → cần logic thật.
  - Fitness hiện xử conflict như soft-penalty.
- **Ưu tiên cải tiến:**
  1. Implement `repair_chromosome()` (fix overlaps → reassign → shift).
  2. Thay placeholder matching/room usage bằng công thức xác thực.
  3. Parallelize fitness eval + caching time slots.
  4. Thêm logging/metrics (fitness_history, diversity_history).
  5. Thử nghiệm toán tử (benchmark convergence).
  6. Consider memetic local search (hill-climbing per child).

## 8. Kết luận

- Hệ thống có cấu trúc tốt, `TimeParser` phù hợp cho input tiếng Việt, và framework GA có nhiều biến thể để thử nghiệm. Để đưa vào production hoặc trả lịch có tính thực thi cao cần hoàn thiện repair, logic matching, và tối ưu hoá/eval song song.

---

### Tiếp theo (tùy chọn)

- (A) Implement `repair_chromosome()` và tạo patch vào `backend/scheduler/genetic_algorithm.py`.
- (B) Chạy benchmark nhanh với dataset mẫu (tạo ~100 applicants) và so sánh vài biến thể.
- (C) Triển khai memetic local search trong `genetic_algorithm_variant3.py`.

Nếu bạn muốn, tôi sẽ thực hiện (A) và chạy unit test/benchmark cơ bản.
