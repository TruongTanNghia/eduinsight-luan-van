# E3M — Dự đoán năng lực học tập và định hướng cho học sinh lớp 9

Hai bản demo dùng chung một bộ dữ liệu (sổ điểm tổng kết của một khóa học sinh Trường THCS Phú An, theo dõi từ lớp 6 năm 2022–2023 đến lớp 9 năm 2025–2026) và chung mã nguồn lõi trong `e3m/`.

| | Bản 1 — Luận văn | Bản 2 — Có LLM |
|---|---|---|
| Mục đích | Huấn luyện các thuật toán trong đề cương, so sánh, kiểm định thống kê, kèm bài báo đối chiếu | Trợ lý định hướng: dự đoán lớp 9 từ lớp 6–8 → luật Thông tư 22, điểm sàn, xu hướng → LLM cục bộ viết thông điệp → giáo viên duyệt |
| Chạy | `scripts
un_thesis_dashboard.bat` → http://localhost:8501 | `scripts
un_student_analytics.bat` → http://localhost:8502 |
| Mã nguồn | `apps/thesis_dashboard/`, `experiments/` | `apps/student_analytics/` |

## Web app EduInsight (Next.js + FastAPI) — hướng triển khai thực tế

Giao diện web theo design system "Sticker lớp học" (bộ `UI/eduinsight-ui-mcp`), 8 màn hình:
Tổng quan · Danh sách học sinh · Hồ sơ học sinh · Phân tích lớp · Dự đoán & định hướng · Đánh giá mô hình · Báo cáo · Quản lý dữ liệu.

```
scripts\run_eduinsight.bat        # mở cả API (cổng 8010) và web (cổng 3005), rồi mở trình duyệt
# hoặc chạy tay:
uvicorn backend.main:app --port 8010          # API /api/v1 (đọc data/processed, models/, reports/)
cd frontend && npm install && npm run dev -- --port 3005     # http://localhost:3005 (proxy /api/v1 -> 8010)
```

- `backend/core.py`: toàn bộ phép tính (xu hướng, nhóm tiến bộ/sa sút, cảnh báo, dự đoán, báo cáo, nhập dữ liệu); `backend/main.py`: các route `/api/v1`.
- `frontend/app/*`: 8 trang; `frontend/components/ui/*`: component của design system; `frontend/lib/*`: gọi API và định dạng số kiểu Việt Nam.
- Tiêu chí "Theo dõi" (chỉ dựa trên điểm số): ĐTB giảm ≥ 0,3 so với năm trước, hoặc ≥ 2 môn giảm ≥ 1,0, hoặc một môn giảm ≥ 2,0, hoặc ĐTB dưới 5,5.
- Dự đoán tuyển sinh THPT **không** hiển thị xác suất đỗ/trượt vì chưa có nhãn kết quả thi; chỉ so chênh lệch tổng 3 môn dự đoán với điểm chuẩn do nhà trường nhập (kèm nguồn) trong màn Dự đoán.
- Kiểm tra giao diện: `node UI/eduinsight-ui-mcp/audit.mjs frontend/app/*/page.tsx` (bộ audit của design system). MCP `eduinsight-ui` đã đăng ký trong `.mcp.json` cho Claude Code.

## Cấu trúc dự án

```
LuanVan/
├── frontend/                      # Web app Next.js (EduInsight, 8 màn hình, design system Sticker lớp học)
├── backend/                       # API FastAPI /api/v1 phục vụ frontend
├── UI/eduinsight-ui-mcp/          # Design system + MCP server + audit.mjs
├── apps/
│   ├── student_analytics/app.py   # Bản Streamlit 2: phân tích học sinh (bản demo nhanh, vẫn dùng được)
│   └── thesis_dashboard/app.py    # Bản Streamlit 1: dashboard kết quả thực nghiệm cho luận văn
├── experiments/run_benchmark.py   # huấn luyện + đánh giá mọi mô hình, kiểm định thống kê, xuất mô hình phục vụ
├── src/e3m/                       # mã nguồn lõi (package e3m)
│   ├── data.py        # đọc sổ điểm .xls, nối học sinh qua các năm, ẩn danh, lưới học sinh × môn × lớp
│   ├── models.py      # MLP, Bi-LSTM, FT-Transformer, TabKANet, Kanformer, XEdu-KANFormer, KAN/GR-KAN
│   ├── pipeline.py    # cửa sổ huấn luyện, chuẩn hóa, bộ bọc mô hình (TabNet, TabPFN, XGBoost…), conformal, chỉ số
│   ├── advisor.py     # luật Thông tư 22, phản thực, điểm sàn tuyển sinh, xu hướng, điểm sáng, gói dữ kiện cho LLM
│   ├── llm.py         # LLM cục bộ (Ollama), prompt, hàng rào kiểm soát, thông điệp mẫu
│   ├── explain.py     # che ô lưới, đường phụ thuộc, trọng số chú ý
│   └── analytics.py   # phân tích sổ điểm theo học sinh / lớp / khối (không dùng mô hình)
├── data/
│   ├── raw/           # 4 tệp .xls gốc (KHOI 6 -22-23 … KHOI 9-25-26)
│   ├── processed/     # students_long.csv (đã ẩn danh)
│   ├── external/      # diem_chuan_thpt.csv — nhà trường điền điểm chuẩn thật
│   └── private/       # id_map.csv (mã ↔ họ tên), không đưa vào huấn luyện, không commit
├── models/            # mô hình phục vụ demo (XEdu-KANFormer.pkl, TabPFN.pkl, serving.json)
├── reports/           # BAO_CAO_KET_QUA.md và các bảng số liệu (metrics_runs, summary, wilcoxon, nemenyi, importance…)
├── outputs/           # thông điệp đã được giáo viên duyệt
├── docs/              # đề cương (v2 gốc, v3 đã thêm ý), bài báo đối chiếu, ý tưởng
├── scripts/           # *.bat: prepare_data, train, run_eduinsight (web), run_thesis_dashboard, run_student_analytics
├── requirements.txt
└── README.md
```

## Chạy nhanh

```
pip install -r requirements.txt
scripts\prepare_data.bat             # đọc 4 tệp .xls -> data/processed/students_long.csv (tự chạy nếu chưa có)
scripts	rain.bat                    # huấn luyện + đánh giá mọi mô hình (chạy tiếp được nếu bị ngắt), xuất models/ và reports/
scripts
un_thesis_dashboard.bat     # Bản 1: http://localhost:8501
scripts
un_student_analytics.bat    # Bản 2: http://localhost:8502 (cần Ollama đang chạy để dùng LLM)
```

Chạy tay (từ thư mục gốc): `python experiments/run_benchmark.py [--fresh | --models MLP XGBoost | --report-only | --serving-only]`,
`streamlit run apps/student_analytics/app.py`. Các script tự thêm `src/` vào `sys.path`; khi gọi trực tiếp module thì đặt `PYTHONPATH=src`.

Bản 2 dùng các mô hình đã huấn luyện ở Bản 1 (`models/*.pkl`), nên cần chạy bước huấn luyện trước.

## Dữ liệu và bài toán

Bốn tệp `data/raw/KHOI 6 -22-23.xls` … `KHOI 9-25-26.xls` là **cùng một khóa học sinh** qua bốn năm (613 học sinh xuất hiện ít nhất một năm, 449 em có đủ bốn năm). Mỗi năm có điểm trung bình cả năm của 8 môn tính điểm (Toán, Ngữ văn, Tiếng Anh, KHTN, Lịch sử và Địa lí, GDCD, Công nghệ, Tin học), kết quả rèn luyện, số buổi nghỉ, và mức kết quả học tập theo Thông tư 22.

Bài toán đúng như đề cương, với trục thời gian là **năm học** (sổ điểm chưa có theo học kỳ):

- **Đầu vào:** lưới 11 hàng (8 môn + rèn luyện + nghỉ có phép + nghỉ không phép) × 3 cột (lớp 6, 7, 8). Ô khuyết dùng mặt nạ, không điền giá trị giả.
- **Đầu ra:** điểm trung bình cả năm lớp 9 của 8 môn (hồi quy đa đầu ra) và mức kết quả học tập lớp 9 (phân mức), kèm khoảng dự đoán conformal 90% cho từng môn.
- **Cửa sổ huấn luyện:** để tăng số mẫu, mô hình học cả các cặp lớp 6 → 7 và lớp 6–7 → 8 (dự đoán năm kế tiếp). Chỉ cửa sổ lớp 6–8 → 9 được dùng để đánh giá, và mọi cửa sổ của một học sinh luôn ở cùng một phần khi chia tập.

### Thêm sổ điểm theo học kỳ (khi nhà trường xuất được)

Bộ đọc nhận diện **loại sổ** từ tiêu đề sheet (`BẢNG TỔNG HỢP KẾT QUẢ GIÁO DỤC HỌC KỲ I / HỌC KỲ II / CẢ NĂM, NĂM HỌC …` và `Khối N`), không phụ thuộc tên tệp; tên tệp chỉ là dự phòng (`KHOI 7 HK1 23-24.xls`). Chỉ cần:

1. Chép các tệp `.xls` học kỳ vào `data/raw/` (cùng mẫu cột với sổ cả năm), hoặc tải lên ở màn **Quản lý dữ liệu** của web app.
2. Chạy `scripts\prepare_data.bat` → `data/processed/students_long.csv` có thêm cột `ky` (0 = cả năm, 1 = HK1, 2 = HK2). Lớp nào có HK1 + HK2 mà thiếu sổ cả năm thì cả năm được tính theo Thông tư 22: (HK1 + 2·HK2)/3.
3. Chạy `scripts	rain.bat --fresh`. Trục thời gian tự chuyển từ 3 mốc (lớp 6, 7, 8) sang **7 mốc** (HK1 lớp 6 → HK1 lớp 9) đúng như đề cương; mục tiêu vẫn là điểm cả năm lớp 9. Lớp chỉ có sổ cả năm vẫn dùng mốc cả năm, nên dữ liệu trộn (vài lớp có học kỳ, vài lớp không) vẫn chạy.
4. `reports/BAO_CAO_KET_QUA.md`, `models/`, hai dashboard và web app cập nhật theo; tài liệu `docs/MO_TA_10_THUAT_TOAN.pdf` cần sinh lại từ bản `.html` với số liệu mới.

Ẩn danh trong `src/e3m/data.py`: mã học sinh thay bằng mã băm một chiều (giữ nguyên qua các năm để nối chuỗi); họ tên tách ra `data/private/id_map.csv`, không dùng cho huấn luyện và không gửi cho LLM; số định danh cá nhân và ngày sinh bị loại bỏ.

## Bản 1 — thực nghiệm

Mô hình (đều trong `src/e3m/models.py`, `src/e3m/pipeline.py`):

| Nhóm | Mô hình |
|---|---|
| Học sâu (đề cương, mục 5.6) | MLP, Bi-LSTM, TabNet, FT-Transformer, TabPFN, TabKANet, Kanformer |
| Đề xuất | XEdu-KANFormer: token hóa KAN, khối chú ý theo trục thời gian (mặt nạ nhân quả) và trục môn học, GR-KAN, đầu ra đa nhiệm |
| Tham chiếu | Hồi quy Ridge, XGBoost |
| Loại bỏ thành phần | bỏ chú ý liên môn, GR-KAN → MLP, bỏ token hóa KAN, bỏ đa nhiệm |

Quy trình đánh giá (`experiments/run_benchmark.py`):

- Kiểm định chéo 5 lần theo lớp (GroupKFold) × 3 hạt giống = 15 lần chạy cho mỗi mô hình.
- Mỗi lần: 70% học sinh huấn luyện, 15% dừng sớm, 15% hiệu chỉnh conformal (ưu tiên cửa sổ lớp 9).
- Chỉ số: RMSE, MAE, R² (8 môn và riêng 3 môn thi), Macro-F1 và Acc (mức), PICP, MPIW. Kiểm định Friedman, hậu kiểm Nemenyi, Wilcoxon từng cặp.

Kết quả ghi vào `reports/`: `BAO_CAO_KET_QUA.md` (bảng dùng cho Chương 4), `metrics_runs.csv`, `summary.csv`, `predictions.csv`, `wilcoxon.csv`, `nemenyi_p.csv`, `stats.json`, `importance.csv`. Bài báo đối chiếu theo từng thuật toán: `docs/BAI_BAO_DOI_CHIEU.md`.

## Bản 2 — web app phân tích học sinh (hướng ứng dụng thực tế)

Bốn trang, dữ liệu lấy thẳng từ sổ điểm:

1. **Hồ sơ học sinh:** điểm trung bình từng năm (kèm chênh lệch so với năm trước, mức, thứ hạng trong lớp, số buổi nghỉ); biểu đồ diễn biến ĐTB và trung bình 3 môn thi so với lớp; biểu đồ radar 8 môn so với lớp; 8 biểu đồ nhỏ từng môn qua các năm (màu theo xu hướng tăng/giảm/ổn định, nét đứt là trung bình lớp); bảng điểm môn × lớp kèm Δ và xu hướng; bản đồ nhiệt thay đổi năm sau so với năm trước.
2. **Dự đoán lớp 9 & định hướng (phần của đề tài):** mô hình dự đoán điểm 8 môn lớp 9 từ lớp 6–8 với khoảng tin cậy 90% và xác suất mức; tổng Toán – Văn – Anh so với điểm sàn trường THPT mục tiêu; nhóm định hướng; điểm sáng; mục tiêu khả thi theo Thông tư 22; giải thích (ô điểm nào kéo dự đoán lên/xuống, trọng số chú ý của XEdu-KANFormer); LLM chạy cục bộ (Ollama) viết thông điệp cho học sinh / phụ huynh / giáo viên chủ nhiệm, qua hàng rào kiểm soát và giáo viên duyệt mới lưu.
3. **Lớp học:** sĩ số, ĐTB lớp so với khối, số học sinh có ≥ 3 môn giảm; điểm từng môn lớp so với khối; quỹ đạo ĐTB của các em trong lớp; phân bố điểm; danh sách học sinh với Δ ĐTB, số môn tăng/giảm, môn giảm nhiều nhất; tải CSV.
4. **Toàn khối:** điểm từng môn qua các năm; cơ cấu mức theo năm; bản đồ nhiệt thay đổi giữa hai năm; học sinh tiến bộ / giảm sút nhiều nhất; ĐTB lớp 9 theo lớp học.

Hai chỗ cần nhà trường cung cấp số liệu:

- **Điểm sàn/điểm chuẩn:** khai báo trong `data/external/diem_chuan_thpt.csv` (cột `truong,diem_san`, tổng 3 môn thang 30) hoặc nhập tay ở thanh bên. Khi chưa nhập, ứng dụng dùng giá trị tạm tính là phân vị 40% tổng 3 môn lớp 9 của khóa, không phải điểm chuẩn thật.
- **Điểm thi so với điểm trung bình môn:** điểm thi tuyển sinh thường thấp hơn; ô "điều chỉnh điểm thi" ở thanh bên để trừ bớt mỗi môn khi có số liệu đối chiếu.

## Giới hạn cần nêu trong luận văn

- Một khóa, một trường, 494 cửa sổ đánh giá; mức Chưa đạt không xuất hiện nên phân mức thực tế là 3 lớp.
- Trục thời gian hiện là năm học (3 mốc) vì chỉ có sổ cả năm; khi thêm sổ học kỳ, pipeline tự chuyển sang 7 mốc (đã kiểm thử bằng dữ liệu học kỳ giả lập).
- Siêu tham số dùng một cấu hình cố định cho mỗi mô hình, chưa dò tìm.
- Giải thích là độ quan trọng hoán vị, đường phụ thuộc, che ô lưới và chú ý của XEdu. SHAP, Integrated Gradients, attention rollout và DiCE trong đề cương chưa được cài đặt; phản thực tính trực tiếp trên luật Thông tư 22.
- TabPFN dùng bản v2 trọng số mở (bản mới nhất bắt đăng nhập tài khoản); khi không có GPU, chạy cấu hình rút gọn (600 mẫu, 2 bộ ước lượng).
