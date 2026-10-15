# Bài báo đối chiếu theo từng thuật toán

Tài liệu này ghép mỗi thuật toán trong thực nghiệm với các công trình đã dùng thuật toán đó cho bài toán dự đoán kết quả học tập, để viết phần tổng quan và phần bàn luận.

**Cách đọc cột "Nguồn":**

- **ĐC [n]**: đã có trong danh mục tài liệu tham khảo của đề cương, số thứ tự [n].
- **Bổ sung · P**: tìm thêm ngày 05/10/2026, đã mở được trang nhà xuất bản, PMC hoặc arXiv.
- **Bổ sung · O**: tìm thêm ngày 05/10/2026, mới xác nhận qua bản ghi DOI (OpenAlex/Crossref) vì trang nhà xuất bản chặn truy cập tự động.

Các con số ở cột "Kết quả công bố" của nhóm *Bổ sung* được đọc từ phần tóm tắt. Cần đối chiếu lại với bản PDF trước khi trích vào luận văn. Kết quả của các nghiên cứu khác nhau không so sánh trực tiếp được với nhau hay với thực nghiệm của luận văn, vì khác dữ liệu, thang điểm và bài toán.

## 1. MLP (mạng nơ-ron truyền thẳng)

| Công trình | Dữ liệu, bậc học | Bài toán | Kết quả công bố | Nguồn |
|---|---|---|---|---|
| Pham và cs., "A data-centric MLOps framework for academic prediction with socioeconomic context in Vietnamese high schools", *SN Computer Science*, 2026. doi:10.1007/s42979-025-04654-2 | 2.283 học sinh THPT Việt Nam | Hồi quy điểm lớp 12 (LR, MLP, LSTM) | Bối cảnh kinh tế – xã hội cải thiện độ chính xác cho nhóm yếu thế | ĐC [26] |
| Qiang, Liu, Zhang, "Explainable AI in education: integrating educational domain knowledge into the deep learning model…", *Scientific Reports*, 2026. doi:10.1038/s41598-026-40538-y | UCI student-mat, trung học Bồ Đào Nha, n = 395 | Dự đoán điểm G3 bằng mạng 6 lớp + SHAP | Accuracy 37,8% → 64,7%; RMSE 10,44 → 4,27 | Bổ sung · P |
| Korchi và cs., "Machine Learning and Deep Learning-Based Students' Grade Prediction", *Operations Research Forum* 4(4), 2023. doi:10.1007/s43069-023-00267-8 | Đại học | Hồi quy điểm, DNN so với RF, DT, KNN, XGBoost | Chưa đọc được số liệu trên trang gốc | Bổ sung · O |

## 2. LSTM / Bi-LSTM

| Công trình | Dữ liệu, bậc học | Bài toán | Kết quả công bố | Nguồn |
|---|---|---|---|---|
| Kalita và cs., "Predicting student academic performance using Bi-LSTM…", *Frontiers in Education*, 2025. doi:10.3389/feduc.2025.1581247 | Điểm học kỳ, đại học | Dự đoán điểm TB học kỳ, Bi-LSTM + SHAP | 88,23%, vượt các mô hình tăng cường gradient có kiểm định | ĐC [18] |
| Waheed và cs., "Early prediction of learners at risk in self-paced education", *Expert Systems with Applications*, 2023. doi:10.1016/j.eswa.2022.118868 | 22.437 người học trực tuyến | Phân loại nguy cơ bằng LSTM | 84,57% | ĐC [17] |
| Chen và cs., "Week-wise student performance early prediction…", *Applied Sciences*, 2022. doi:10.3390/app12041885 | OULAD | CNN-LSTM theo tuần | — | ĐC [16] |
| Fazil, Rísquez, Halpin, "A Novel Deep Learning Model for Student Performance Prediction Using Engagement Data", *Journal of Learning Analytics* 11(2), 2024. doi:10.18608/jla.2024.7985 | Đại học Ireland, dữ liệu VLE | Phân loại 3 mức, attention + CNN + BiLSTM | AUC 0,86–0,90 | Bổ sung · P |
| Al-azazi, Ghurab, "ANN-LSTM: A deep learning model for early student performance prediction in MOOC", *Heliyon* 9(4), 2023. doi:10.1016/j.heliyon.2023.e15382 | MOOC | Phân loại đa lớp theo ngày | Khoảng 70% ở tháng thứ 3 | Bổ sung · O |

## 3. TabNet

| Công trình | Dữ liệu, bậc học | Bài toán | Kết quả công bố | Nguồn |
|---|---|---|---|---|
| Yang và cs., "Student academic performance prediction via hypergraph and TabNet", *Journal of Big Data*, 2025. doi:10.1186/s40537-025-01170-1 | — | Siêu đồ thị + TabNet | F1 = 93,10% | ĐC [30] |
| Prasanth, "TabNet–XGBoost Hybrid Model for Student Performance Prediction and Customized Feedback", *IJACSA* 16(10), 2025. doi:10.14569/ijacsa.2025.0161008 | OULAD | Phân loại + phản hồi SHAP | Accuracy 98,8% | Bổ sung · O |
| Susheelamma và cs., "Enhancing Academic Performance Prediction: A Novel Approach Using the TabNet Algorithm", IFIP AICT (Springer), 2025. doi:10.1007/978-3-031-98364-1_1 | Đại học | So với XGBoost | Chưa đọc được số liệu | Bổ sung · O |

## 4. FT-Transformer / TabTransformer

| Công trình | Dữ liệu, bậc học | Bài toán | Kết quả công bố | Nguồn |
|---|---|---|---|---|
| Son, Quynh, Minh, "Early prediction students' graduation rank using LAGT", *Journal of Computer Science and Cybernetics*, 2024. doi:10.15625/1813-9663/21095 | 3 trường đại học Việt Nam | GCN + Transformer, xếp loại tốt nghiệp | 92,73% | ĐC [22] |
| Yang, Li, Liu, "A machine learning based framework for predictive school management using student and faculty analytics", *Scientific Reports*, 2026. doi:10.1038/s41598-026-47278-z | UCI Student Performance, trung học Bồ Đào Nha, n = 649 | TabTransformer, FT-Transformer, SAINT làm mô hình cơ sở | Số liệu mới thấy ở đoạn trích tìm kiếm, cần đọc PDF | Bổ sung · P |
| Namitha và cs., "AI-Powered Student Dropout Prediction Using AutoGluon FT-Transformer", IEEE ACCTHPA 2025. doi:10.1109/accthpa65749.2025.11168572 | Đại học | Phân loại 3 lớp | FT-Transformer 78% | Bổ sung · O |

**Không trích dẫn:** Gong và cs., "TGEL-transformer", *PLoS ONE* 2025 (doi:10.1371/journal.pone.0327481). Bài này đã bị rút lại ngày 08/04/2026.

## 5. TabPFN

| Công trình | Dữ liệu, bậc học | Bài toán | Kết quả công bố | Nguồn |
|---|---|---|---|---|
| Yin, "Predicting student academic performance using TabPFN and SHAP: An interpretable machine learning approach", *PLOS ONE*, 2026. doi:10.1371/journal.pone.0328634 | 4.000 học sinh trung học | Hồi quy điểm thi cuối kỳ | RMSE 4,845; MAE 3,795; R² 0,9216 (thang 100) | Bổ sung · P |
| Eren, Niksarlı, "Benchmarking and interpreting a tabular foundation model for PISA 2022 mathematical literacy", *Int. J. Assessment Tools in Education* 13(3), 2026. doi:10.21449/ijate.1856645 | PISA 2022 Thổ Nhĩ Kỳ, học sinh 15 tuổi, n = 7.250 | Phân loại nhị phân, so với XGBoost, LightGBM, RF | Chưa có số liệu trong tóm tắt | Bổ sung · O |

## 6. KAN, TabKANet, Kanformer

| Công trình | Dữ liệu, bậc học | Bài toán | Kết quả công bố | Nguồn |
|---|---|---|---|---|
| Alnasyan và cs., "Kanformer: An attention-enhanced deep learning model for predicting student performance in virtual learning environments", *Social Network Analysis and Mining*, 2025. doi:10.1007/s13278-025-01446-7 | OULAD, 32.593 người học | Phân loại nhị phân, attention + KAN | 99,21% | ĐC [21] |
| Gupta và cs., "Graph-KAN: Bridging accuracy and interpretability in student performance prediction", *J. Discrete Mathematical Sciences and Cryptography* 29(7), 2026. doi:10.47974/jdmsc-2825 | OULAD | Phân loại | Macro-F1 0,536 | Bổ sung · O |
| Wang, Chen, "Early Academic Performance Warning in Online Education via Dual-Stream Heterogeneous Graph and Kolmogorov–Arnold Networks", IEEE ICSP 2026. doi:10.1109/icsp69961.2026.11540574 | OULAD | Cảnh báo sớm | Chưa đọc được số liệu | Bổ sung · O |

Chưa tìm thấy công trình nào áp dụng TabKANet hoặc KAN thuần cho điểm số học sinh phổ thông. Đây là điểm mới có thể nêu trong luận văn; TabKANet chỉ có bài phương pháp gốc (ĐC [36]).

## 7. Mô hình cây + SHAP (chỉ để tham chiếu)

| Công trình | Dữ liệu, bậc học | Bài toán | Kết quả công bố | Nguồn |
|---|---|---|---|---|
| Huang và cs., *Journal of Intelligence*, 2024. doi:10.3390/jintelligence12100093 | PISA 2022, 34.495 học sinh THCS | XGBoost + SHAP | Niềm tin năng lực toán là yếu tố mạnh nhất | ĐC [12] |
| Ahmed và cs., *Scientific Reports*, 2025. doi:10.1038/s41598-025-12353-4 | 2 bộ dữ liệu | Hồi quy, mô hình kết hợp + LIME/SHAP | RMSE, R² | ĐC [15] |
| Guevara-Reyes và cs., "Machine learning models for academic performance prediction: interpretability and application in educational decision-making", *Frontiers in Education*, 2025. doi:10.3389/feduc.2025.1632315 | Trung học Ecuador, khoảng 50.000 bản ghi | XGBoost, RF + SHAP | XGBoost R² 0,91 | Bổ sung · P |
| Abukader, Alzubi, Adegboye, *Applied Sciences* 15(20), 10875, 2025. doi:10.3390/app152010875 | — | LightGBM tối ưu metaheuristic + SHAP | R² 0,941 | Bổ sung · O |

## 8. Dự đoán conformal và độ bất định

| Công trình | Dữ liệu, bậc học | Bài toán | Kết quả công bố | Nguồn |
|---|---|---|---|---|
| Morsomme, Smirnov, "Conformal Prediction for Students' Grades in a Course Recommender System", PMLR 105 (COPA), 2019. proceedings.mlr.press/v105/morsomme19a.html | University College Maastricht | Khoảng dự đoán điểm bằng inductive conformal | Khoảng dự đoán hợp lệ | Bổ sung · P |
| Elmasry, Gafar, Elsabagh, *Inventions* 11(3), 65, 2026. doi:10.3390/inventions11030065 | Đại học, bỏ học | Xác suất hiệu chỉnh + conformal + XAI | Độ phủ gần mức danh định | Bổ sung · O |
| Wijiyanto, *Journal of Applied Data Sciences* 7(3), 2026. doi:10.47738/jads.v7i3.1419 | Đại học, n = 4.424 | Tập dự đoán split-conformal 3 lớp | — | Bổ sung · O |
| Hu, Rangwala, "Reliable Deep Grade Prediction with Uncertainty Estimation", arXiv:1902.10213, 2019 | Đại học | MLP/RNN Bayes (không phải conformal) | — | Bổ sung · P |

Chưa tìm thấy nghiên cứu conformal nào ở bậc phổ thông. Lưu ý: câu "chưa ghi nhận công trình nào áp dụng phương pháp này cho bài toán dự đoán điểm" ở mục 3.4 của đề cương nên sửa thành "ở bậc phổ thông", vì Morsomme và Smirnov (2019) đã làm ở bậc đại học.

## 9. LLM sinh phản hồi từ kết quả mô hình

| Công trình | Dữ liệu, bậc học | Bài toán | Kết quả công bố | Nguồn |
|---|---|---|---|---|
| Swamy và cs., "iLLuMinaTE", AAAI 2025. doi:10.1609/aaai.v39i27.35065 | MOOC | LLM chuyển kết quả XAI thành phản hồi | 89,52% lựa chọn ưu tiên phản hồi này | ĐC [25] |
| Yang, Li, Huang, "Leveraging Large Language Models to Enhance Self-Regulated Learning in Programming Education With Explainable AI", *J. Computer Assisted Learning* 42(2), 2026. doi:10.1002/jcal.70206 | Đại học, môn lập trình | Mô hình dự đoán → SHAP → GPT-4 viết báo cáo giữa kỳ | Cải thiện hành vi tự điều chỉnh và kết quả cuối kỳ | Bổ sung · O |
| Cuéllar Rojas, Contero, Hincapié, *Multimodal Technologies and Interaction* 9(5), 45, 2025. doi:10.3390/mti9050045 | Đại học, 42 thực nghiệm so với 39 đối chứng | RNN dự đoán → GPT-4 phản hồi | +12,63 điểm ở khối 4 | Bổ sung · O |

## 10. Giải thích phản thực

| Công trình | Dữ liệu, bậc học | Bài toán | Kết quả công bố | Nguồn |
|---|---|---|---|---|
| Buñay-Guisñan và cs., *Electronics* 15(1), 51, 2026. doi:10.3390/electronics15010051 | Học trực tuyến | Phản thực theo nhóm | Tỷ lệ phục hồi 99,3% | ĐC [24] |
| Smith, Chimedza, Bührmann, "Individualized help for at-risk students using model-agnostic and counterfactual explanations", *Education and Information Technologies* 27(2), 2022. doi:10.1007/s10639-021-10661-6 | — | LIME, SHAP, phản thực cho học sinh có nguy cơ | — | Bổ sung · O |
| Cavus, Kuzilek, *J. Measurement and Evaluation in Education and Psychology* 15, 2024. arXiv:2408.00676 | OULAD | So sánh các phương pháp phản thực | — | Bổ sung · P |

## Nhận xét dùng cho phần bàn luận

- Phần lớn công trình dùng OULAD hoặc dữ liệu đại học. Bằng chứng ở bậc phổ thông mới có cho MLP, Transformer dạng bảng (làm mô hình cơ sở), TabPFN và mô hình cây.
- TabPFN, KAN và conformal trong giáo dục hầu hết công bố năm 2026, một số ở tạp chí hạng thấp. Nên ưu tiên trích các bài ở *Scientific Reports*, *PLOS ONE*, *Frontiers in Education*, AAAI, PMLR.
- Chưa có công trình nào đồng thời dùng KAN-Transformer, conformal và LLM cho học sinh lớp 9 Việt Nam.
