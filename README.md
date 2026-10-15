<div align="center">

# EduInsight · E3M

### Khung học sâu tích hợp cơ chế giải thích dự đoán năng lực học tập học sinh cuối cấp THCS

Dự đoán **điểm học kỳ 2 lớp 9** của 8 môn từ 7 học kỳ trước (HK1 lớp 6 → HK1 lớp 9).
So sánh **10 thuật toán**, giải thích dự đoán, và triển khai thành **web app** phân tích từng học sinh.

![Python](https://img.shields.io/badge/Python-3.11-111111?style=for-the-badge&logo=python&logoColor=FFD23F&labelColor=2B59FF)
![PyTorch](https://img.shields.io/badge/PyTorch-2.5-111111?style=for-the-badge&logo=pytorch&logoColor=white&labelColor=FF5A36)
![FastAPI](https://img.shields.io/badge/FastAPI-API-111111?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=3DDC97)
![Next.js](https://img.shields.io/badge/Next.js-16-111111?style=for-the-badge&logo=nextdotjs&logoColor=white&labelColor=111111)
![Ollama](https://img.shields.io/badge/LLM-Ollama_cục_bộ-111111?style=for-the-badge&labelColor=B8A4FF)

<img src="docs/images/ui/01_tong_quan.png" alt="Màn Tổng quan của EduInsight" width="100%">

</div>

---

## Mục lục

1. [Kết quả nổi bật](#1-kết-quả-nổi-bật)
2. [Demo giao diện](#2-demo-giao-diện)
3. [Biểu đồ kết quả thực nghiệm](#3-biểu-đồ-kết-quả-thực-nghiệm)
4. [Bài toán và dữ liệu](#4-bài-toán-và-dữ-liệu)
5. [Kiến trúc hệ thống](#5-kiến-trúc-hệ-thống)
6. [Cài đặt](#6-cài-đặt)
7. [**Hướng dẫn huấn luyện**](#7-hướng-dẫn-huấn-luyện)
8. [Chạy web app](#8-chạy-web-app)
9. [API](#9-api)
10. [Cấu trúc thư mục](#10-cấu-trúc-thư-mục)
11. [Giới hạn](#11-giới-hạn)
12. [Tài liệu kèm theo](#12-tài-liệu-kèm-theo)

---

## 1. Kết quả nổi bật

Mọi con số dưới đây là **kiểm định chéo**: mỗi học sinh được dự đoán bởi một mô hình **chưa từng thấy điểm lớp 9 của em đó**. Số liệu tính trên 502 học sinh lớp 9.

| | TabPFN (tốt nhất) | XGBoost | XEdu-KANFormer (đề xuất) |
|---|:---:|:---:|:---:|
| **Điểm HK2 lệch ≤ 0,5 điểm** | **64,0%** | 55,5% | 48,6% |
| **Điểm HK2 lệch ≤ 1 điểm** | **89,2%** | 83,0% | 77,7% |
| Điểm cả năm lệch ≤ 0,5 điểm | **78,8%** | 70,2% | 64,3% |
| Điểm cả năm lệch ≤ 1 điểm | **96,9%** | 93,0% | 90,0% |
| ĐTB cả năm lệch ≤ 0,5 điểm | **95,6%** | 90,6% | 90,0% |
| Mức học lực TT22 trùng khớp | **86,7%** | 82,3% | 78,5% |
| RMSE điểm cả năm (8 môn) | **0,444** | 0,552 | 0,634 |
| MAE điểm HK2 | **0,47** | 0,57 | 0,66 |

- Công thức **Cả năm = (HK1 + 2 × HK2) / 3** (Thông tư 22) đã được đối chiếu với sổ điểm thật: khớp **100%** số ô điểm.
- Kiểm định Friedman: χ² = 559,1, p < 10⁻¹⁰⁰. Các mô hình khác nhau có ý nghĩa thống kê.
- Khoảng dự đoán conformal 90% phủ đúng **91,7–92,7%** điểm thật, sát mức danh định.

---

## 2. Demo giao diện

Web app **EduInsight** gồm 8 màn hình, theo design system *"Sticker lớp học"*. Ảnh chụp ở chế độ ẩn danh, nên chỉ hiện mã học sinh, không có họ tên.

<table>
<tr>
<td width="50%"><b>Danh sách học sinh</b>: lọc theo kỳ, lớp, trạng thái; ĐTB, chênh lệch so với kỳ trước, môn mạnh, môn cần chú ý.<br><img src="docs/images/ui/02_danh_sach_hoc_sinh.png"></td>
<td width="50%"><b>Phân tích lớp</b>: so sánh HK1/HK2, phân bố mức TT22, học sinh tiến bộ/sa sút, số em giảm điểm theo từng môn.<br><img src="docs/images/ui/04_phan_tich_lop.png"></td>
</tr>
</table>

### Hồ sơ từng học sinh: điểm 8 học kỳ, tăng hay giảm, biểu đồ

<img src="docs/images/ui/03_ho_so_hoc_sinh.png" alt="Hồ sơ học sinh">

Bảng điểm theo **môn × HK1/HK2/Cả năm × lớp 6–9**, xu hướng từng môn, biểu đồ từng môn qua các học kỳ, so sánh với lớp, mức tăng/giảm so với kỳ trước và heatmap.

### Dự đoán và giải thích

<img src="docs/images/ui/05_du_doan.png" alt="Dự đoán và giải thích">

Dự đoán 8 môn kèm khoảng tin cậy 90%. Lưới **che ô (occlusion)** cho biết ô điểm nào (môn × học kỳ) kéo dự đoán lên hoặc xuống.

### Dự đoán so với điểm thật

<table>
<tr>
<td width="50%"><b>Từng học sinh</b>: HK1 thật · HK2 dự đoán · HK2 thật · độ lệch (xanh ≤ 0,5 · vàng 0,5–1 · đỏ &gt; 1).<br><img src="docs/images/ui/06_du_doan_so_voi_thuc_te.png"></td>
<td width="50%"><b>Toàn khóa</b>: tỉ lệ dự đoán lệch ≤ 0,5 / ≤ 1 điểm theo môn, ma trận mức TT22, chọn được từng mô hình.<br><img src="docs/images/ui/07_do_sat_toan_khoa.png"></td>
</tr>
</table>

<table>
<tr>
<td width="33%"><b>Đánh giá mô hình</b><br><img src="docs/images/ui/08_danh_gia_mo_hinh.png"></td>
<td width="33%"><b>Báo cáo PDF / CSV</b><br><img src="docs/images/ui/09_bao_cao.png"></td>
<td width="33%"><b>Quản lý dữ liệu</b><br><img src="docs/images/ui/10_quan_ly_du_lieu.png"></td>
</tr>
</table>

---

## 3. Biểu đồ kết quả thực nghiệm

> Sinh lại toàn bộ bằng `python -X utf8 experiments/make_figures.py` sau khi huấn luyện.

### 3.1. So sánh 10 thuật toán

![RMSE 10 mô hình](docs/images/charts/01_rmse_10_mo_hinh.png)

TabPFN (mô hình nền tảng cho dữ liệu bảng) dẫn đầu rõ rệt, tiếp theo là XGBoost. Mô hình đề xuất XEdu-KANFormer xếp thứ 6/10, tốt hơn Bi-LSTM, FT-Transformer, TabNet và hồi quy tuyến tính.

### 3.2. Dự đoán sát thực tế đến đâu

![Độ sát thực tế](docs/images/charts/04_do_sat_thuc_te.png)

![Dự đoán vs thực tế](docs/images/charts/05_du_doan_vs_thuc_te.png)

Mỗi chấm là một học sinh × một môn. Càng nằm sát đường chéo thì dự đoán càng đúng. Dải vàng đậm là vùng lệch ≤ 0,5 điểm.

### 3.3. Kiểm định thống kê

![Friedman](docs/images/charts/02_xep_hang_friedman.png)

### 3.4. Loại bỏ thành phần (ablation) của XEdu-KANFormer

![Ablation](docs/images/charts/03_loai_bo_thanh_phan.png)

- Bỏ **chú ý liên môn** làm sai số tăng, nghĩa là cấu trúc liên môn có đóng góp.
- Bỏ **đầu ra đa nhiệm** làm RMSE giảm còn 0,570 (xếp thứ 3 nếu tính như một mô hình). Trọng số λ = 0,3 chọn thủ công đang làm giảm chất lượng hồi quy; đây là hướng hoàn thiện.

### 3.5. Mô hình dựa vào đâu để dự đoán

![Độ quan trọng](docs/images/charts/07_do_quan_trong_tabpfn.png)

Học kỳ gần nhất (HK1 lớp 9) chi phối dự đoán, đặc biệt là Toán, Tiếng Anh và KHTN. Các học kỳ xa hơn đóng góp ít.

### 3.6. Diễn biến điểm của cả khóa và mức học lực

![Diễn biến 8 học kỳ](docs/images/charts/06_dien_bien_8_hoc_ky.png)

<p align="center"><img src="docs/images/charts/08_muc_tt22.png" width="55%"></p>

---

## 4. Bài toán và dữ liệu

### Dữ liệu

**12 sổ điểm** `.xls` của **cùng một khóa** học sinh Trường THCS Phú An, theo dõi từ lớp 6 (2022–2023) đến lớp 9 (2025–2026). Mỗi lớp có 3 sổ: HK1, HK2 và Cả năm. Tổng cộng 613 học sinh và 16.792 bản ghi điểm.

| Nhóm | Nội dung |
|---|---|
| 8 môn tính điểm | Toán, Ngữ văn, Tiếng Anh, KHTN, Lịch sử & Địa lí, GDCD, Công nghệ, Tin học |
| Đặc trưng khác | Kết quả rèn luyện, số buổi nghỉ có phép / không phép |
| Nhãn phụ | Mức kết quả học tập theo Thông tư 22 (Tốt / Khá / Đạt / Chưa đạt) |

> **Quyền riêng tư:** sổ điểm gốc chứa họ tên, ngày sinh, số định danh của học sinh vị thành niên, nên **không có trong repo** (xem `.gitignore`). Mã học sinh được thay bằng mã băm một chiều (`HS-xxxxxxxx`). Họ tên tách riêng vào `data/private/id_map.csv`, không dùng để huấn luyện và không gửi cho LLM. Muốn chạy lại, chép sổ điểm vào `data/raw/`.

### Bài toán

```
Đầu vào : lưới 11 hàng (8 môn + rèn luyện + nghỉ P + nghỉ K) × 7 học kỳ (HK1 lớp 6 → HK1 lớp 9), ô khuyết dùng mặt nạ
Đầu ra  : điểm 8 môn lớp 9 (hồi quy đa đầu ra) + khoảng tin cậy conformal 90% cho từng môn
          → điểm HK2 = (3 × Cả năm − HK1) / 2   (Thông tư 22: Cả năm = (HK1 + 2 × HK2) / 3)
          → mức học lực TT22 suy ra từ điểm dự đoán
```

- **Cửa sổ huấn luyện:** mô hình học cả các cặp dự đoán lớp 7 và lớp 8, tổng 1.531 cửa sổ. Chỉ 502 cửa sổ lớp 9 được dùng để đánh giá.
- **Đánh giá:** GroupKFold 5 lần **theo lớp** × 3 hạt giống = **15 lần chạy** cho mỗi mô hình. Mỗi lần chia 70% huấn luyện, 15% dừng sớm, 15% hiệu chỉnh conformal. Mọi cửa sổ của một học sinh luôn nằm cùng một phần.
- **Chỉ số:** RMSE, MAE, R², tỉ lệ lệch ≤ 0,5 / ≤ 1 điểm, PICP, MPIW. Kiểm định Friedman, hậu kiểm Nemenyi, Wilcoxon từng cặp.

### 10 thuật toán

| Nhóm | Mô hình |
|---|---|
| Tham chiếu | Hồi quy tuyến tính (Ridge), XGBoost |
| Học sâu | MLP, Bi-LSTM, TabNet, FT-Transformer, TabPFN v2, TabKANet, Kanformer |
| **Đề xuất** | **XEdu-KANFormer**: token hóa KAN, chú ý theo trục thời gian (mặt nạ nhân quả) và trục môn học, GR-KAN, đầu ra đa nhiệm |
| Ablation | bỏ chú ý liên môn · GR-KAN → MLP · bỏ token hóa KAN · bỏ đa nhiệm · bản nhỏ |

Mô tả chi tiết từng thuật toán (là gì, ưu/nhược, cách chạy trên dữ liệu này, lập luận chọn mô hình) có trong [`docs/MO_TA_10_THUAT_TOAN.pdf`](docs/MO_TA_10_THUAT_TOAN.pdf).

---

## 5. Kiến trúc hệ thống

```mermaid
flowchart LR
    A["12 sổ điểm .xls<br/>HK1 · HK2 · Cả năm<br/>lớp 6 → 9"] --> B["e3m.data<br/>đọc sổ, ẩn danh,<br/>nối học sinh qua các kỳ"]
    B --> C[("students_long.csv<br/>đã ẩn danh")]
    C --> D["Lưới 11 × 7<br/>+ mặt nạ ô khuyết"]
    D --> E["10 thuật toán<br/>+ 5 ablation"]
    E --> F["Kiểm định chéo<br/>15 lần chạy<br/>+ conformal 90%"]
    F --> G[("reports/<br/>bảng, kiểm định")]
    F --> H[("models/<br/>TabPFN, XEdu")]
    G & H & C --> I["FastAPI<br/>/api/v1 · cổng 8010"]
    I --> J["Next.js EduInsight<br/>8 màn hình · cổng 3005"]
    I <--> K["LLM cục bộ (Ollama)<br/>qwen3:8b · gemma3:4b<br/>+ hàng rào kiểm soát"]
    J --> L(["Giáo viên duyệt<br/>thông điệp"])
```

**XEdu-KANFormer** (mô hình đề xuất):

```mermaid
flowchart TB
    X["Lưới 11 đặc trưng × 7 học kỳ"] --> T["Token hóa KAN<br/>mỗi ô → vector d chiều<br/>+ nhúng đặc trưng + nhúng thời gian"]
    T --> AX1["Khối chú ý trục<br/>① trục thời gian (mặt nạ nhân quả)<br/>② trục môn học (liên môn)<br/>③ GR-KAN thay FFN"]
    AX1 --> AX2["… lặp N khối"]
    AX2 --> P["Token [CLS] đọc toàn lưới<br/>bằng chú ý (trọng số dùng để giải thích)"]
    P --> R["Đầu hồi quy:<br/>điểm 8 môn lớp 9"]
    P --> Cl["Đầu phân mức:<br/>Tốt / Khá / Đạt / Chưa đạt"]
    R --> CF["Conformal 90%<br/>khoảng dự đoán từng môn"]
```

---

## 6. Cài đặt

| Thành phần | Phiên bản đã kiểm thử | Ghi chú |
|---|---|---|
| Python | 3.11 | |
| Node.js | 22 | cho web app |
| GPU (tùy chọn) | NVIDIA RTX 3050 Laptop, CUDA 12.4 | không có GPU vẫn chạy được, chỉ chậm hơn |
| Ollama (tùy chọn) | `qwen3:8b`, `gemma3:4b` | chỉ cần cho phần LLM viết thông điệp |

```bash
git clone https://github.com/TruongTanNghia/eduinsight-luan-van.git
cd eduinsight-luan-van

# 1) Python
python -m venv .venv && .venv\Scripts\activate          # Windows (Linux/macOS: source .venv/bin/activate)
# Có GPU NVIDIA: cài PyTorch bản CUDA trước
pip install torch --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt

# 2) Web
cd frontend && npm install && cd ..

# 3) (Tùy chọn) LLM cục bộ
ollama pull qwen3:8b
```

---

## 7. Hướng dẫn huấn luyện

### Bước 1. Chuẩn bị dữ liệu

Chép các sổ điểm vào `data/raw/`. Bộ đọc nhận ra loại sổ (HK1 / HK2 / Cả năm) và khối lớp từ **tiêu đề trong sheet**; tên tệp chỉ dùng dự phòng.

```
data/raw/
├── KHOI 6-HK1-22-23.xls   KHOI 6-HK2-22-23.xls   KHOI 6 -22-23.xls
├── KHOI 7-HK1-23-24.xls   KHOI 7-HK2-23-24.xls   KHOI 7-23-24.xls
├── KHOI 8-HK1-24-25.xls   KHOI 8-HK2-24-25.xls   KHOI 8-24-25.xls
└── KHOI 9-HK1-25-26.xls   KHOI 9-HK2-25-26.xls   KHOI 9-25-26.xls
```

```bat
scripts\prepare_data.bat
:: hoặc:  set PYTHONPATH=src  rồi  python -X utf8 -m e3m.data
```

Kết quả:
- `data/processed/students_long.csv`: dữ liệu đã ẩn danh, có cột `ky` (0 = cả năm, 1 = HK1, 2 = HK2).
- `data/private/id_map.csv`: bảng mã ↔ họ tên, chỉ lưu trên máy.

> Lớp nào có HK1 + HK2 mà thiếu sổ cả năm thì điểm cả năm được tính theo Thông tư 22: (HK1 + 2·HK2)/3.

### Bước 2. Huấn luyện và đánh giá toàn bộ

```bat
scripts\train.bat --fresh
:: tương đương:  python -X utf8 -W ignore experiments\run_benchmark.py --fresh
```

Lệnh này chạy **10 thuật toán + 5 ablation**, mỗi mô hình 15 lần (5 lần gập × 3 hạt giống). Sau đó nó tính kiểm định thống kê, độ quan trọng đặc trưng, rồi huấn luyện lại 2 mô hình phục vụ web (TabPFN, XEdu-KANFormer).

**Tùy chọn dòng lệnh:**

| Lệnh | Tác dụng |
|---|---|
| `train.bat` | Chạy tiếp từ chỗ dừng: bỏ qua các lần chạy đã có trong `reports/metrics_runs.csv` (an toàn khi mất điện, tắt máy) |
| `train.bat --fresh` | Xóa kết quả cũ, chạy lại từ đầu (dùng khi **đổi dữ liệu**) |
| `train.bat --models MLP XGBoost TabPFN` | Chỉ chạy các mô hình được liệt kê |
| `train.bat --report-only` | Không huấn luyện; chỉ tính lại bảng tổng hợp, kiểm định, báo cáo |
| `train.bat --serving-only` | Chỉ huấn luyện lại mô hình phục vụ web (`models/*.pkl`) |
| `train.bat --no-serving` | Huấn luyện và đánh giá nhưng không xuất mô hình phục vụ |

Tên mô hình hợp lệ cho `--models`: `"Hồi quy tuyến tính"`, `XGBoost`, `MLP`, `Bi-LSTM`, `TabNet`, `FT-Transformer`, `TabPFN`, `TabKANet`, `Kanformer`, `XEdu-KANFormer`, và các biến thể `"XEdu (bỏ đa nhiệm)"`… Tên có dấu cách thì đặt trong ngoặc kép.

**Thời gian chạy** (RTX 3050 Laptop, 15 lần chạy mỗi mô hình): tổng **khoảng 2 giờ 45 phút**.

| Mô hình | Thời gian | Mô hình | Thời gian |
|---|---:|---|---:|
| Kanformer | ~89 phút | XEdu-KANFormer | ~6 phút |
| TabNet | ~19 phút | Các ablation XEdu | ~4–11 phút mỗi bản |
| TabPFN | ~14 phút | MLP, Bi-LSTM, FT, TabKANet, XGBoost, LR | < 2 phút mỗi mô hình |

> Muốn thử nhanh: `train.bat --models XGBoost MLP TabPFN --no-serving` (khoảng 15 phút).
> Không có GPU: mọi mô hình vẫn chạy trên CPU. TabPFN tự dùng cấu hình rút gọn; Kanformer và TabNet chậm hơn nhiều.

### Bước 3. Xem kết quả

| Tệp | Nội dung |
|---|---|
| `reports/BAO_CAO_KET_QUA.md` | Bảng kết quả viết sẵn cho chương thực nghiệm |
| `reports/summary.csv` | RMSE, MAE, R², PICP, MPIW… trung bình ± độ lệch chuẩn từng mô hình |
| `reports/metrics_runs.csv` | Chi tiết từng lần chạy, từng môn |
| `reports/stats.json`, `wilcoxon.csv`, `nemenyi_p.csv` | Friedman, Wilcoxon từng cặp, Nemenyi |
| `reports/importance.csv` | Độ quan trọng hoán vị theo môn × học kỳ |
| `reports/predictions.csv` | Dự đoán kiểm định chéo từng học sinh (không commit) |
| `reports/accuracy_vs_actual.json` | Tỉ lệ lệch ≤ 0,5 / ≤ 1 điểm so với điểm thật |
| `models/TabPFN.pkl`, `models/XEdu-KANFormer.pkl` | Mô hình phục vụ web (không commit, ~530 MB) |

```bat
python -X utf8 experiments\make_figures.py      :: vẽ lại 8 biểu đồ trong docs/images/charts
```

Sau khi huấn luyện lại, **khởi động lại API** để web nạp mô hình mới.

---

## 8. Chạy web app

```bat
scripts\run_eduinsight.bat
```

Lệnh này mở API (cổng 8010), web (cổng 3005) và trình duyệt tại http://localhost:3005/dashboard.

Chạy tay:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8010      # API
cd frontend && npm run dev -- --port 3005                   # Web (proxy /api/v1 → 8010)
```

| Biến môi trường | Tác dụng |
|---|---|
| `E3M_HIDE_NAMES=1` | Chế độ ẩn danh khi trình chiếu: chỉ hiện mã học sinh |
| `API_URL` | Địa chỉ API cho frontend (mặc định `http://127.0.0.1:8010`) |

Bản **Streamlit** cũ vẫn dùng được: `scripts\run_thesis_dashboard.bat` (cổng 8501, kết quả thực nghiệm) và `scripts\run_student_analytics.bat` (cổng 8502, phân tích học sinh + LLM).

Kiểm tra giao diện theo design system: `node UI/eduinsight-ui-mcp/audit.mjs frontend/app/*/page.tsx`

---

## 9. API

Tất cả các route có tiền tố `/api/v1`. Tài liệu tương tác ở http://127.0.0.1:8010/docs.

| Nhóm | Route |
|---|---|
| Chung | `GET /meta` |
| Phân tích | `GET /analytics/overview` · `/analytics/grades-by-semester` · `/analytics/subject-comparison` · `/analytics/class-comparison` · `/analytics/student-risk` |
| Học sinh | `GET /students` · `/students/{id}` · `/students/{id}/grades` · `/students/{id}/trends` · `/students/{id}/analysis` |
| Dự đoán | `GET /students/{id}/predictions?model=` (kèm so sánh với điểm thật) · `POST /ai/predict` |
| Mô hình | `GET /ai/models` · `/ai/models/{id}/metrics` · **`/ai/accuracy?model=`** (độ sát thực tế toàn khóa) |
| LLM | `POST /students/{id}/message` · `POST /students/{id}/message/approve` |
| Lớp | `GET /classes` · `/classes/{lop}` |
| Điểm chuẩn | `GET / POST /schools` · `DELETE /schools/{id}` |
| Báo cáo | `GET / POST /reports` · `POST /reports/student` · `POST /reports/class` · `GET /reports/{id}` |
| Dữ liệu | `GET /data/schema` · `/data/import/history` · `POST /data/import/preview` · `POST /data/import/confirm` |

---

## 10. Cấu trúc thư mục

```
├── frontend/                 # Web app Next.js 16 + Tailwind v4 + Recharts (8 màn hình)
│   ├── app/                  #   dashboard, students, students/[id], classes, predictions,
│   │                         #   model-evaluation, reports, data-management
│   ├── components/ui/        #   component của design system "Sticker lớp học"
│   └── lib/                  #   gọi API, định dạng số kiểu Việt Nam (7,12)
├── backend/                  # FastAPI: core.py (toàn bộ phép tính) + main.py (route /api/v1)
├── src/e3m/                  # Lõi học máy
│   ├── data.py               #   đọc sổ điểm, nhận diện HK1/HK2/Cả năm, ẩn danh, lưới học sinh × môn × kỳ
│   ├── models.py             #   MLP, Bi-LSTM, FT-Transformer, TabKANet, Kanformer, XEdu-KANFormer, KAN, GR-KAN
│   ├── pipeline.py           #   cửa sổ huấn luyện, chuẩn hóa, TabNet/TabPFN/XGBoost, conformal, chỉ số
│   ├── advisor.py            #   luật Thông tư 22, phản thực, điểm sàn, xu hướng, gói dữ kiện cho LLM
│   ├── llm.py                #   Ollama, prompt, hàng rào kiểm soát
│   └── explain.py            #   che ô lưới, đường phụ thuộc, trọng số chú ý
├── experiments/
│   ├── run_benchmark.py      #   huấn luyện + đánh giá + kiểm định + xuất mô hình phục vụ
│   └── make_figures.py       #   vẽ biểu đồ cho README
├── reports/                  # Kết quả thực nghiệm (bảng, kiểm định, độ quan trọng)
├── models/                   # Mô hình phục vụ web (không commit)
├── data/                     # raw/ (không commit) · processed/ (không commit) · external/diem_chuan_thpt.csv
├── docs/                     # Đề cương v4, mô tả 10 thuật toán (PDF), bài báo đối chiếu, ảnh README
├── apps/                     # Bản Streamlit (thesis_dashboard, student_analytics)
├── UI/eduinsight-ui-mcp/     # Design system + MCP server + công cụ audit giao diện
└── scripts/                  # prepare_data, train, run_eduinsight, run_api, run_web, …
```

---

## 11. Giới hạn

- Dữ liệu có **một trường, một khóa**. Kết quả là kiểm định chéo trên chính khóa này, chưa kiểm chứng trên khóa hoặc trường khác.
- Lớp 9 của khóa **không có học sinh mức "Chưa đạt"**, nên chưa đánh giá được khả năng nhận diện nhóm học sinh yếu nhất.
- Mô hình hiện học điểm **cả năm** lớp 9 rồi suy ra HK2 theo công thức TT22. Vì vậy sai số HK2 bằng 1,5 lần sai số cả năm. Huấn luyện trực tiếp với mục tiêu HK2 là hướng tiếp theo.
- Siêu tham số dùng cấu hình cố định, chưa dò tìm. Trọng số đa nhiệm λ = 0,3 đang làm XEdu kém hơn bản bỏ đa nhiệm.
- **Không hiển thị xác suất đỗ/trượt THPT**, vì chưa có nhãn kết quả thi vào lớp 10. Hệ thống chỉ so tổng 3 môn dự đoán với điểm chuẩn do nhà trường nhập kèm nguồn.
- Danh sách học sinh cần chú ý **chỉ dựa trên điểm số**, không dùng để đánh giá hoàn cảnh hay năng lực.

---

## 12. Tài liệu kèm theo

| Tài liệu | Nội dung |
|---|---|
| [`docs/DE_CUONG_LUAN_VAN_v4_du_lieu_hoc_ky.pdf`](docs/DE_CUONG_LUAN_VAN_v4_du_lieu_hoc_ky.pdf) | Đề cương luận văn (bản dữ liệu học kỳ) |
| [`docs/MO_TA_10_THUAT_TOAN.pdf`](docs/MO_TA_10_THUAT_TOAN.pdf) | 10 thuật toán: là gì, ưu/nhược, cách hoạt động trên dữ liệu, lập luận chọn mô hình |
| [`docs/BAI_BAO_DOI_CHIEU.md`](docs/BAI_BAO_DOI_CHIEU.md) | Bài báo đã dùng từng thuật toán cho bài toán tương tự |
| [`reports/BAO_CAO_KET_QUA.md`](reports/BAO_CAO_KET_QUA.md) | Bảng kết quả cho chương thực nghiệm |

<div align="center">
<sub>Luận văn thạc sĩ · Hồ Thị Hồng Vân · Trường Đại học Thủ Dầu Một</sub>
</div>
