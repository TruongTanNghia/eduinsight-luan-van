"""Dashboard báo cáo luận văn (Bản 1): so sánh các mô hình trên dữ liệu theo dõi dọc lớp 6 -> 9.

Chạy:  streamlit run apps/thesis_dashboard/app.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))
from e3m.data import EXAM, LEVELS, ROOT, SUBJECT_VN, SUBJECTS, load, load_yearly, to_panel  # noqa: E402
from e3m.explain import dependence, load_serving  # noqa: E402
from e3m.models import ABLATIONS  # noqa: E402
from e3m.pipeline import DEEP, PROPOSED, REFERENCE, make_windows  # noqa: E402

RES = os.path.join(ROOT, "reports")
BLUE, ORANGE, GREY = "#2563eb", "#ea580c", "#94a3b8"

st.set_page_config(page_title="E3M · Bản luận văn", page_icon="📊", layout="wide")
st.title("E3M — So sánh mô hình dự đoán năng lực học tập lớp 9")
st.caption("Bản 1 (luận văn): từ điểm cả năm lớp 6, 7, 8 dự đoán điểm cả năm lớp 9 (8 môn) và mức kết quả học tập. "
           "Một khóa học sinh Trường THCS Phú An, theo dõi 2022–2026. Dữ liệu đã ẩn danh.")


@st.cache_data
def read(name):
    p = os.path.join(RES, name)
    try:
        return pd.read_csv(p) if os.path.exists(p) else None
    except pd.errors.EmptyDataError:
        return None


@st.cache_resource
def serving():
    return load_serving()


@st.cache_data
def data():
    df_all = load()
    X, M, C, sids, info, pers = to_panel(df_all)
    return load_yearly(df_all), make_windows(X, M, C, sids, pers)


df, windows = data()
runs, summary = read("metrics_runs.csv"), read("summary.csv")
if runs is None or summary is None:
    st.error("Chưa có kết quả. Hãy chạy:  scripts\\train.bat  (python experiments/run_benchmark.py)")
    st.stop()
n_runs = runs["run"].nunique()

tabs = st.tabs(["Dữ liệu", "So sánh mô hình", "Kiểm định thống kê", "Loại bỏ thành phần",
                "Khoảng dự đoán", "Giải thích", "Bài báo đối chiếu"])

# ------------------------------------------------------------------ dữ liệu
with tabs[0]:
    n_full = df.groupby("sid")["lop_so"].nunique()
    c = st.columns(4)
    c[0].metric("Học sinh", df["sid"].nunique())
    c[1].metric("Có đủ 4 năm", int((n_full == 4).sum()))
    c[2].metric("Cửa sổ huấn luyện", len(windows), help=f"{windows.T} mốc đầu vào: {', '.join(windows.periods)}")
    c[3].metric("Cửa sổ đánh giá (mục tiêu lớp 9)", int((windows.g == 9).sum()))
    st.info("**Bài toán.** Mỗi học sinh là một lưới môn học × lớp (8 môn + rèn luyện + chuyên cần, lớp 6–8). Mô hình dự đoán "
            "điểm trung bình cả năm lớp 9 của cả 8 môn (hồi quy đa đầu ra) và mức kết quả học tập lớp 9 (phân mức). "
            "Để tăng số mẫu, các cửa sổ lớp 6→7 và lớp 6–7→8 cũng được học (dự đoán năm kế tiếp); chỉ cửa sổ mục tiêu lớp 9 "
            "được dùng để đánh giá, và mọi cửa sổ của một học sinh luôn nằm cùng một phần khi chia tập.")
    a, b = st.columns(2)
    by = df.groupby("lop_so").agg(so_hs=("sid", "size"), **{SUBJECT_VN[s]: (s, "mean") for s in SUBJECTS}).round(2)
    a.subheader("Điểm trung bình các môn theo lớp")
    a.dataframe(by.rename(columns={"so_hs": "Số học sinh"}), width="stretch")
    lv = df.groupby(["lop_so", "muc"]).size().reset_index(name="n")
    lv["Mức"] = lv["muc"].map(dict(enumerate(LEVELS)))
    lv["Lớp"] = "Lớp " + lv["lop_so"].astype(str)
    fig = px.bar(lv, x="Lớp", y="n", color="Mức", category_orders={"Mức": LEVELS[::-1]},
                 color_discrete_sequence=["#1d4ed8", "#60a5fa", "#fdba74", "#c2410c"], labels={"n": "Số học sinh"})
    b.subheader("Mức kết quả học tập theo lớp")
    b.plotly_chart(fig.update_layout(height=320, margin=dict(t=10)), width="stretch")
    a, b = st.columns(2)
    long = df.melt(id_vars="lop_so", value_vars=SUBJECTS, var_name="mon", value_name="diem").dropna()
    long["Môn"] = long["mon"].map(SUBJECT_VN)
    long["Lớp"] = "Lớp " + long["lop_so"].astype(str)
    a.subheader("Phân bố điểm từng môn theo lớp")
    a.plotly_chart(px.box(long, x="Môn", y="diem", color="Lớp", labels={"diem": "Điểm TB cả năm"},
                          color_discrete_sequence=["#bfdbfe", "#60a5fa", "#2563eb", "#1e3a8a"])
                   .update_layout(height=400, margin=dict(t=10)), width="stretch")
    wide = df.pivot(index="sid", columns="lop_so", values="Toan")
    corr = pd.concat([df[df["lop_so"] == g].set_index("sid")[SUBJECTS].add_suffix(f"_{g}") for g in (8, 9)], axis=1).corr()
    sub = corr.loc[[f"{s}_8" for s in SUBJECTS], [f"{s}_9" for s in SUBJECTS]].round(2)
    sub.index, sub.columns = [SUBJECT_VN[s] + " (lớp 8)" for s in SUBJECTS], [SUBJECT_VN[s] + " (lớp 9)" for s in SUBJECTS]
    b.subheader("Tương quan điểm lớp 8 với điểm lớp 9")
    b.plotly_chart(px.imshow(sub, text_auto=True, color_continuous_scale="Blues", zmin=0.3, zmax=1)
                   .update_layout(height=400, margin=dict(t=10)), width="stretch")
    st.subheader("Quỹ đạo điểm trung bình của từng học sinh")
    traj = df.assign(dtb=df[SUBJECTS].mean(axis=1)).pivot(index="sid", columns="lop_so", values="dtb").dropna()
    sample = traj.sample(min(80, len(traj)), random_state=0)
    fig = go.Figure()
    for _, r in sample.iterrows():
        fig.add_scatter(x=[f"Lớp {g}" for g in r.index], y=r.values, mode="lines", line=dict(color="rgba(37,99,235,0.18)", width=1), showlegend=False)
    fig.add_scatter(x=[f"Lớp {g}" for g in traj.columns], y=traj.mean().values, mode="lines+markers", name="Trung bình khóa", line=dict(color=ORANGE, width=4))
    st.plotly_chart(fig.update_layout(height=320, margin=dict(t=10), yaxis_title="ĐTB các môn"), width="stretch")
    st.caption("80 học sinh ngẫu nhiên có đủ 4 năm. Mức kết quả học tập lấy trực tiếp từ sổ điểm (Thông tư 22). "
               "Khóa này không có học sinh ở mức Chưa đạt nên phân mức thực tế là 3 lớp.")

# ------------------------------------------------------------------ so sánh
main = summary[~summary["model"].isin(ABLATIONS)].copy()
main["Nhóm"] = main["model"].map(lambda m: "Đề xuất" if m == PROPOSED else "Tham chiếu (không học sâu)" if m in REFERENCE else "Học sâu")
with tabs[1]:
    best = main.iloc[0]
    prop = main[main["model"] == PROPOSED]
    c = st.columns(3)
    c[0].metric(f"RMSE thấp nhất ({n_runs} lần chạy)", f"{best['RMSE_mean']:.3f}", best["model"], delta_color="off")
    if len(prop):
        c[1].metric(f"{PROPOSED} · RMSE", f"{prop['RMSE_mean'].iloc[0]:.3f}",
                    f"hạng {main['model'].tolist().index(PROPOSED) + 1}/{len(main)}", delta_color="off")
        c[2].metric(f"{PROPOSED} · MAE", f"{prop['MAE_mean'].iloc[0]:.3f} điểm")
    metric = st.radio("Chỉ số", ["RMSE", "MAE", "R2", "MacroF1"], horizontal=True)
    order = main.sort_values(f"{metric}_mean", ascending=metric in ("RMSE", "MAE"))
    fig = px.bar(order, x=f"{metric}_mean", y="model", error_x=f"{metric}_std", color="Nhóm", orientation="h",
                 color_discrete_map={"Đề xuất": ORANGE, "Học sâu": BLUE, "Tham chiếu (không học sâu)": GREY},
                 labels={f"{metric}_mean": f"{metric} (trung bình {n_runs} lần chạy, thanh sai số = độ lệch chuẩn)", "model": ""})
    fig.update_layout(height=420, margin=dict(t=10), yaxis=dict(categoryorder="array", categoryarray=order["model"][::-1]))
    lo = order[f"{metric}_mean"].min()
    fig.update_xaxes(range=[lo * 0.9 if metric != "R2" else lo - 0.05, None])
    st.plotly_chart(fig, width="stretch")

    st.subheader("Bảng tổng hợp")
    show = pd.DataFrame({
        "Mô hình": main["model"], "Nhóm": main["Nhóm"],
        "RMSE (8 môn)": main.apply(lambda r: f"{r.RMSE_mean:.3f} ± {r.RMSE_std:.3f}", axis=1),
        "MAE (8 môn)": main.apply(lambda r: f"{r.MAE_mean:.3f} ± {r.MAE_std:.3f}", axis=1),
        "R²": main["R2_mean"].round(3), "Macro-F1 (mức)": main["MacroF1_mean"].round(3), "Acc (mức)": main["Acc_mean"].round(3),
        "RMSE 3 môn thi": main["thi_RMSE"].round(3), "MAE 3 môn thi": main["thi_MAE"].round(3),
        "PICP": main["PICP_mean"].round(3), "MPIW": main["MPIW_mean"].round(2), "Thời gian (s)": main["seconds_mean"].round(1)})
    st.dataframe(show, hide_index=True, width="stretch")
    st.caption(f"Kiểm định chéo 5 lần theo lớp × 3 hạt giống = {n_runs} lần chạy; đánh giá trên cửa sổ mục tiêu lớp 9 ngoài tập huấn luyện. "
               "3 môn thi: Toán, Ngữ văn, Tiếng Anh.")

    st.subheader("RMSE theo từng môn")
    per = runs[runs["target"].isin(SUBJECTS) & ~runs["model"].isin(ABLATIONS)]
    per = per.pivot_table(index="model", columns="target", values="RMSE")[SUBJECTS].rename(columns=SUBJECT_VN)
    st.dataframe(per.loc[main["model"]].round(3).style.highlight_min(axis=0, color="#dbeafe"), width="stretch")

# ------------------------------------------------------------------ thống kê
with tabs[2]:
    sp = os.path.join(RES, "stats.json")
    if os.path.exists(sp):
        s = json.load(open(sp, encoding="utf-8"))
        if "friedman_p" in s:
            c = st.columns(3)
            c[0].metric("Friedman χ²", f"{s['friedman_chi2']:.2f}")
            c[1].metric("p-value", f"{s['friedman_p']:.2e}")
            c[2].metric("Khoảng cách tới hạn Nemenyi (α = 0,05)", f"{s['nemenyi_cd']:.2f}")
            rk = pd.Series(s["avg_rank"]).sort_values().reset_index()
            rk.columns = ["Mô hình", "Hạng trung bình"]
            fig = px.scatter(rk, x="Hạng trung bình", y="Mô hình", color_discrete_sequence=[BLUE])
            fig.update_traces(marker_size=12, error_x=dict(type="constant", value=s["nemenyi_cd"] / 2, color=GREY))
            fig.update_layout(height=380, margin=dict(t=10), yaxis=dict(autorange="reversed"))
            st.subheader("Hạng trung bình theo RMSE")
            st.plotly_chart(fig, width="stretch")
            st.caption(f"Xếp hạng trên {s['n_blocks']} khối (lần chạy × môn); hạng thấp là tốt. Hai mô hình có thanh ±CD/2 chồng lên nhau "
                       "thì chưa khác biệt có ý nghĩa thống kê.")
        nem = read("nemenyi_p.csv")
        if nem is not None:
            nem = nem.set_index(nem.columns[0])
            st.subheader("p-value hậu kiểm Nemenyi")
            st.plotly_chart(px.imshow(nem, text_auto=".2f", color_continuous_scale="Blues_r", zmin=0, zmax=0.2)
                            .update_layout(height=460, margin=dict(t=10)), width="stretch")
    w = read("wilcoxon.csv")
    if w is not None and len(w):
        st.subheader(f"Wilcoxon từng cặp: {PROPOSED} so với từng mô hình")
        w = w.rename(columns={"so_voi": "So với", "MAE_de_xuat": "MAE đề xuất", "MAE_doi_thu": "MAE đối thủ",
                              "chenh_lech": "Chênh lệch", "p_hoc_sinh": "p (theo học sinh)", "p_khoi": "p (theo khối)", "n": "Số học sinh"})
        st.dataframe(w.style.format({"MAE đề xuất": "{:.3f}", "MAE đối thủ": "{:.3f}", "Chênh lệch": "{:+.3f}",
                                     "p (theo học sinh)": "{:.4f}", "p (theo khối)": "{:.4f}"}), hide_index=True, width="stretch")
        st.caption("Chênh lệch âm nghĩa là mô hình đề xuất có sai số thấp hơn. p theo học sinh: sai số tuyệt đối trung bình 8 môn của từng "
                   "học sinh lớp 9 (dự đoán ngoài tập huấn luyện, trung bình các hạt giống). p theo khối: RMSE trên các khối lần chạy × môn.")

# ------------------------------------------------------------------ ablation
with tabs[3]:
    ab = summary[summary["model"].isin(list(ABLATIONS) + [PROPOSED])].copy()
    if len(ab) > 1:
        base = ab.loc[ab["model"] == PROPOSED, "RMSE_mean"].iloc[0]
        ab["ΔRMSE so với đầy đủ"] = ab["RMSE_mean"] - base
        ab["Biến thể"] = ab["model"].replace({PROPOSED: "XEdu-KANFormer (đầy đủ)"})
        fig = px.bar(ab.sort_values("RMSE_mean"), x="RMSE_mean", y="Biến thể", error_x="RMSE_std", orientation="h",
                     color_discrete_sequence=[BLUE], labels={"RMSE_mean": "RMSE (8 môn)", "Biến thể": ""})
        fig.update_xaxes(range=[ab["RMSE_mean"].min() * 0.95, None])
        st.plotly_chart(fig.update_layout(height=320, margin=dict(t=10)), width="stretch")
        st.dataframe(ab[["Biến thể", "RMSE_mean", "RMSE_std", "MAE_mean", "R2_mean", "MacroF1_mean", "thi_RMSE", "ΔRMSE so với đầy đủ"]].round(4),
                     hide_index=True, width="stretch")
        st.caption("Biến thể bỏ đa nhiệm không có đầu phân mức nên không có Macro-F1. Với dữ liệu 3 năm, chú ý theo trục thời gian "
                   "(mặt nạ nhân quả) đã hoạt động; phép thử bỏ trục thời gian có thể bổ sung bằng cờ trong models.py.")
    else:
        st.info("Chưa có kết quả loại bỏ thành phần.")

# ------------------------------------------------------------------ conformal
with tabs[4]:
    tb = runs[(runs["target"] == "TB") & ~runs["model"].isin(ABLATIONS)]
    g = tb.groupby("model")[["PICP", "MPIW"]].agg(["mean", "std"])
    g.columns = [f"{a}_{b}" for a, b in g.columns]
    g = g.reset_index()
    fig = px.scatter(g, x="MPIW_mean", y="PICP_mean", text="model", error_y="PICP_std", color_discrete_sequence=[BLUE],
                     labels={"MPIW_mean": "Độ rộng trung bình của khoảng (điểm)", "PICP_mean": "Độ phủ thực tế"})
    fig.add_hline(y=0.9, line_dash="dash", line_color=GREY, annotation_text="mục tiêu 90%")
    fig.update_traces(textposition="top center", textfont_size=10, marker_size=10)
    st.plotly_chart(fig.update_layout(height=460, margin=dict(t=10)), width="stretch")
    per = runs[runs["target"].isin(SUBJECTS) & ~runs["model"].isin(ABLATIONS)].pivot_table(index="model", columns="target", values="PICP")[SUBJECTS]
    st.subheader("Độ phủ theo từng môn")
    st.dataframe(per.rename(columns=SUBJECT_VN).loc[main["model"]].round(3), width="stretch")
    st.caption("Split conformal 90%, bán kính riêng cho từng môn, hiệu chỉnh trên 15% học sinh huấn luyện (ưu tiên cửa sổ mục tiêu lớp 9).")

# ------------------------------------------------------------------ giải thích
with tabs[5]:
    imp = read("importance.csv")
    models = serving()
    if imp is None or not models:
        st.info("Chưa có mô hình phục vụ. Hãy chạy benchmark đến hết (không dùng --no-serving).")
    else:
        name = st.selectbox("Mô hình", list(models))
        st.subheader("Mức 1 — Toàn cục: ô (đặc trưng × lớp) nào ảnh hưởng nhiều nhất")
        tgt = st.selectbox("Môn được dự đoán", ["TB"] + SUBJECTS, format_func=lambda s: "Trung bình 8 môn" if s == "TB" else SUBJECT_VN[s])
        col = "period" if "period" in imp.columns else "grade"
        p = imp[(imp["model"] == name) & (imp["target"] == tgt)].pivot(index="feature", columns=col, values="delta_rmse")
        if col == "grade":
            p.columns = [f"Lớp {c}" for c in p.columns]
        p = p.loc[p.sum(axis=1).sort_values(ascending=False).index]
        st.plotly_chart(px.imshow(p.round(3), text_auto=True, color_continuous_scale="Blues", aspect="auto",
                                  labels=dict(x="", y="", color="ΔRMSE")).update_layout(height=420, margin=dict(t=10)), width="stretch")
        st.caption("Độ quan trọng hoán vị trên lần gập đầu tiên: RMSE tăng bao nhiêu điểm khi xáo trộn một ô giữa các học sinh.")
        st.subheader(f"Quan hệ giữa điểm một môn ở mốc {windows.periods[-1]} và điểm dự đoán lớp 9")
        feat = st.selectbox(f"Môn đầu vào ({windows.periods[-1]})", SUBJECTS, format_func=SUBJECT_VN.get)
        dep = dependence(models[name], windows[windows.g == 9], feat, windows.periods[-1])
        fig = go.Figure()
        for s, col in zip(EXAM + [feat], [BLUE, ORANGE, "#059669", "#7c3aed"]):
            fig.add_scatter(x=dep["x"], y=dep[s], name=SUBJECT_VN[s] + " (lớp 9)", line=dict(color=col, width=3))
        fig.update_layout(height=360, margin=dict(t=10), xaxis_title=f"Điểm {SUBJECT_VN[feat]} ({windows.periods[-1]})", yaxis_title="Điểm dự đoán lớp 9")
        st.plotly_chart(fig, width="stretch")
        st.caption("Các ô khác giữ ở trung vị của khóa. Giải thích cho từng học sinh (che ô lưới, chú ý của XEdu) nằm ở Bản 2.")

# ------------------------------------------------------------------ bài báo
with tabs[6]:
    p = os.path.join(ROOT, "docs", "BAI_BAO_DOI_CHIEU.md")
    st.markdown(open(p, encoding="utf-8").read() if os.path.exists(p) else "Chưa có tệp docs/BAI_BAO_DOI_CHIEU.md")
