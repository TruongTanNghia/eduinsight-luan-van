# Kết quả thực nghiệm (tự sinh từ reports/)

Bài toán: từ 7 mốc điểm (HK1 lớp 6, HK2 lớp 6, HK1 lớp 7, HK2 lớp 7, HK1 lớp 8, HK2 lớp 8, HK1 lớp 9; 8 môn, kết quả rèn luyện, số buổi nghỉ) dự đoán điểm trung bình cả năm lớp 9 của 8 môn và mức kết quả học tập lớp 9. Thang điểm 10. Kiểm định chéo 5 lần theo lớp × 3 hạt giống = 15 lần chạy; trung bình ± độ lệch chuẩn giữa các lần chạy.

## Bảng 1. So sánh mô hình (trung bình 8 môn, và riêng 3 môn thi Toán – Văn – Anh)

| Mô hình | Nhóm | RMSE | MAE | R² | Macro-F1 | Acc | PICP | MPIW | RMSE 3 môn thi | MAE 3 môn thi | Thời gian (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TabPFN | Học sâu | 0,444 ± 0,035 | 0,331 ± 0,026 | 0,912 | 0,812 | 0,813 | 0,919 | 1,49 | 0,440 | 0,346 | 57,3 |
| XGBoost | Tham chiếu | 0,552 ± 0,040 | 0,412 ± 0,030 | 0,863 | 0,788 | 0,788 | 0,917 | 1,83 | 0,595 | 0,467 | 2,3 |
| MLP | Học sâu | 0,605 ± 0,045 | 0,452 ± 0,037 | 0,836 | 0,810 | 0,811 | 0,924 | 2,02 | 0,704 | 0,551 | 1,9 |
| TabKANet | Học sâu | 0,622 ± 0,029 | 0,465 ± 0,023 | 0,826 | 0,790 | 0,791 | 0,924 | 2,06 | 0,731 | 0,574 | 5,5 |
| Kanformer | Học sâu | 0,627 ± 0,030 | 0,471 ± 0,025 | 0,823 | 0,811 | 0,811 | 0,919 | 2,06 | 0,727 | 0,569 | 357,5 |
| XEdu-KANFormer | Đề xuất | 0,634 ± 0,032 | 0,480 ± 0,025 | 0,820 | 0,795 | 0,797 | 0,925 | 2,14 | 0,720 | 0,567 | 22,0 |
| Bi-LSTM | Học sâu | 0,644 ± 0,033 | 0,488 ± 0,027 | 0,814 | 0,811 | 0,811 | 0,923 | 2,17 | 0,736 | 0,577 | 4,2 |
| FT-Transformer | Học sâu | 0,655 ± 0,027 | 0,493 ± 0,024 | 0,808 | 0,782 | 0,783 | 0,923 | 2,16 | 0,777 | 0,613 | 3,8 |
| TabNet | Học sâu | 0,671 ± 0,094 | 0,487 ± 0,036 | 0,792 | 0,745 | 0,748 | 0,927 | 2,20 | 0,770 | 0,587 | 74,9 |
| Hồi quy tuyến tính | Tham chiếu | 0,700 ± 0,054 | 0,528 ± 0,043 | 0,781 | 0,772 | 0,774 | 0,919 | 2,24 | 0,786 | 0,609 | 0,1 |

## Bảng 2. RMSE theo từng môn

| Mô hình | Toán | Ngữ văn | Tiếng Anh | Khoa học tự nhiên | Lịch sử và Địa lí | Giáo dục công dân | Công nghệ | Tin học |
|---|---|---|---|---|---|---|---|---|
| TabPFN | 0,458 | 0,414 | 0,446 | 0,517 | 0,392 | 0,253 | 0,552 | 0,443 |
| XGBoost | 0,663 | 0,515 | 0,595 | 0,624 | 0,472 | 0,310 | 0,625 | 0,519 |
| MLP | 0,788 | 0,590 | 0,716 | 0,662 | 0,474 | 0,378 | 0,599 | 0,514 |
| TabKANet | 0,795 | 0,599 | 0,777 | 0,679 | 0,464 | 0,375 | 0,623 | 0,519 |
| Kanformer | 0,806 | 0,612 | 0,741 | 0,712 | 0,482 | 0,391 | 0,618 | 0,524 |
| XEdu-KANFormer | 0,789 | 0,599 | 0,753 | 0,739 | 0,486 | 0,442 | 0,623 | 0,526 |
| Bi-LSTM | 0,772 | 0,637 | 0,784 | 0,711 | 0,511 | 0,401 | 0,674 | 0,550 |
| FT-Transformer | 0,869 | 0,652 | 0,790 | 0,719 | 0,497 | 0,384 | 0,642 | 0,533 |
| TabNet | 0,872 | 0,653 | 0,763 | 0,734 | 0,531 | 0,448 | 0,667 | 0,580 |
| Hồi quy tuyến tính | 0,909 | 0,652 | 0,772 | 0,757 | 0,605 | 0,535 | 0,701 | 0,583 |

## Bảng 3. Loại bỏ thành phần của XEdu-KANFormer

| Biến thể | RMSE | ΔRMSE | MAE | Macro-F1 | RMSE 3 môn thi |
|---|---|---|---|---|---|
| XEdu (bỏ đa nhiệm) | 0,570 ± 0,040 | -0.063 | 0,427 | – | 0,628 |
| XEdu (GR-KAN → MLP) | 0,614 ± 0,042 | -0.019 | 0,466 | 0,803 | 0,696 |
| XEdu (bỏ token hóa KAN) | 0,624 ± 0,042 | -0.009 | 0,472 | 0,785 | 0,708 |
| XEdu-KANFormer | 0,634 ± 0,032 | +0.000 | 0,480 | 0,795 | 0,720 |
| XEdu (nhỏ: d=16, 1 khối, dropout 0.2) | 0,635 ± 0,044 | +0.002 | 0,478 | 0,793 | 0,728 |
| XEdu (bỏ chú ý liên môn) | 0,646 ± 0,042 | +0.012 | 0,486 | 0,785 | 0,730 |

## Kiểm định thống kê

Friedman trên 120 khối (lần chạy × môn), 10 mô hình: χ² = 559,11, p = 1.24e-114. Khoảng cách tới hạn Nemenyi (α = 0,05): 1,24.

| Mô hình | Hạng trung bình |
|---|---|
| TabPFN | 1,14 |
| XGBoost | 3,23 |
| MLP | 4,30 |
| TabKANet | 5,04 |
| Kanformer | 5,66 |
| XEdu-KANFormer | 5,97 |
| FT-Transformer | 6,95 |
| Bi-LSTM | 7,02 |
| TabNet | 7,03 |
| Hồi quy tuyến tính | 8,65 |

## Bảng 4. Wilcoxon: XEdu-KANFormer so với từng mô hình

| So với | MAE đề xuất | MAE đối thủ | Chênh lệch | p (theo học sinh) | p (theo khối) |
|---|---|---|---|---|---|
| Bi-LSTM | 0,481 | 0,486 | -0.005 | 0.4943 | 0,0203 |
| FT-Transformer | 0,481 | 0,492 | -0.011 | 0.0278 | 0,0041 |
| Hồi quy tuyến tính | 0,481 | 0,523 | -0.042 | 0.0050 | 0,0000 |
| Kanformer | 0,481 | 0,470 | +0.011 | 0.0003 | 0,2889 |
| MLP | 0,481 | 0,451 | +0.030 | 0.0000 | 0,0000 |
| TabKANet | 0,481 | 0,464 | +0.018 | 0.0000 | 0,0097 |
| TabNet | 0,481 | 0,485 | -0.004 | 0.5993 | 0,0102 |
| TabPFN | 0,481 | 0,329 | +0.152 | 0.0000 | 0,0000 |
| XGBoost | 0,481 | 0,409 | +0.072 | 0.0000 | 0,0000 |

Chênh lệch âm: mô hình đề xuất sai số thấp hơn. p theo học sinh: Wilcoxon trên sai số tuyệt đối trung bình của từng học sinh lớp 9 (dự đoán ngoài tập huấn luyện); p theo khối: Wilcoxon trên RMSE của các khối (lần chạy × môn).
