"""Web app phân tích học sinh (Bản 2): hồ sơ từng em qua các năm, dự đoán lớp 9 + định hướng (LLM cục bộ), lớp học, toàn khối.

Chạy:  streamlit run apps/student_analytics/app.py --server.port 8502
"""
import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))
from e3m import advisor, analytics, llm  # noqa: E402
from e3m.data import EXAM, LEVELS, PRIVATE_MAP, ROOT, STATIC, SUBJECT_VN, SUBJECTS, input_periods, load, load_yearly, to_panel  # noqa: E402
from e3m.explain import attention_map, load_serving, occlusion  # noqa: E402
from e3m.pipeline import make_windows  # noqa: E402

OUT = os.path.join(ROOT, "outputs", "thong_diep_da_duyet.csv")
SCHOOLS = os.path.join(ROOT, "data", "external", "diem_chuan_thpt.csv")
BLUE, ORANGE, GREEN, RED, GREY = "#2563eb", "#ea580c", "#059669", "#dc2626", "#94a3b8"
PALETTE = ["#2563eb", "#ea580c", "#059669", "#7c3aed", "#db2777", "#0891b2", "#ca8a04", "#64748b"]
GROUP_COLOR = {advisor.GROUPS[0]: "#ea580c", advisor.GROUPS[1]: "#ca8a04", advisor.GROUPS[2]: "#059669"}
TREND_ICON = {"Tăng": "▲", "Giảm": "▼", "Ổn định": "■", "—": "—"}
TREND_COLOR = {"Tăng": GREEN, "Giảm": RED, "Ổn định": GREY, "—": GREY}

st.set_page_config(page_title="E3M · Phân tích học sinh", page_icon="🧭", layout="wide")


@st.cache_resource
def serving():
    return load_serving()


@st.cache_data
def data():
    df_all = load()
    X, M, C, sids, info, pers = to_panel(df_all)
    return load_yearly(df_all), X, M, C, sids, info, pers


@st.cache_data
def names():
    return pd.read_csv(PRIVATE_MAP).set_index("sid")["ho_ten"].to_dict() if os.path.exists(PRIVATE_MAP) else {}


df, X, M, C, sids, info, PERS = data()
models = serving()
sid_index = {s: i for i, s in enumerate(sids)}
lops_all = sorted(info["lop"].unique(), key=lambda s: (-int(s[0]), len(s), s))   # lớp 9 lên đầu

# ------------------------------------------------------------------ thanh bên
with st.sidebar:
    st.header("Thiết lập")
    show_name = st.toggle("Hiện họ tên (giáo viên)", value=False, help="Đọc từ data/private/; không gửi cho LLM")
    label = (lambda s: f"{names().get(s, s)} · {s}") if show_name else (lambda s: s)
    st.subheader("Mô hình dự đoán lớp 9")
    model_name = st.selectbox("Mô hình", list(models)) if models else None
    fitted = models[model_name] if models else None
    st.subheader("Tuyển sinh lớp 10")
    schools = pd.read_csv(SCHOOLS) if os.path.exists(SCHOOLS) else pd.DataFrame(columns=["truong", "diem_san"])
    school = st.selectbox("Trường THPT mục tiêu", ["(nhập tay)"] + schools["truong"].tolist())
    g9 = df[df["lop_so"] == 9]
    default_floor = float(schools.set_index("truong")["diem_san"].get(school, round(g9[EXAM].sum(axis=1).quantile(0.4), 1)))
    floor = st.number_input("Điểm sàn / điểm chuẩn (Toán + Văn + Anh, thang 30)", 0.0, 30.0, default_floor, 0.25)
    if school == "(nhập tay)":
        st.caption("Mặc định là **tạm tính** (phân vị 40% của khóa). Hãy nhập điểm chuẩn thật hoặc khai báo `data/external/diem_chuan_thpt.csv`.")
    margin = st.slider("Biên an toàn quanh điểm sàn", 0.5, 3.0, 1.5, 0.5)
    exam_shift = st.number_input("Điều chỉnh điểm thi so với điểm TB môn (mỗi môn)", -3.0, 1.0, 0.0, 0.25)
    max_step = st.slider("Mức tăng tối đa mỗi môn coi là khả thi", 0.5, 3.0, 1.5, 0.5)
    use_actual = st.toggle("Dùng điểm thật lớp 9 nếu đã có", value=False,
                           help="Tắt: luôn dùng dự đoán từ lớp 6–8 (tình huống dự báo sớm cuối lớp 8).")
    st.subheader("LLM cục bộ (Ollama)")
    llm_models = llm.available_models()
    llm_name = st.selectbox("Mô hình ngôn ngữ", llm_models) if llm_models else None
    if not llm_models:
        st.warning("Không kết nối được Ollama. Dùng thông điệp mẫu theo luật.")
    audience = st.radio("Người nhận thông điệp", list(llm.AUDIENCE))

st.title("E3M — Phân tích và định hướng học sinh")
st.caption("Trường THCS Phú An · khóa 2022–2026 · 8 môn tính điểm · dữ liệu ẩn danh. "
           "Hồ sơ từng em qua các năm → dự đoán lớp 9 và định hướng (mô hình + Thông tư 22 + LLM cục bộ) → lớp học → toàn khối.")
tab_profile, tab_predict, tab_class, tab_cohort = st.tabs(["Hồ sơ học sinh", "Dự đoán lớp 9 & định hướng", "Lớp học", "Toàn khối"])


@st.cache_data
def roster_table(lop, with_names):
    return analytics.roster(df, None if lop == "Tất cả" else lop, names() if with_names else None)


def pick_student(key, compact=False):
    """Danh sách học sinh dạng bảng; bấm một dòng để chọn. Trả về mã học sinh."""
    c = st.columns([1, 2, 1.3])
    lop = c[0].selectbox("Lớp (gần nhất)", ["Tất cả"] + lops_all, index=1, key=f"lop_{key}")
    q = c[1].text_input("Tìm theo mã hoặc họ tên", key=f"q_{key}", placeholder="vd. HS-05C hoặc Nguyễn")
    xu = c[2].multiselect("Lọc xu hướng", ["Tăng", "Giảm", "Ổn định"], key=f"xu_{key}")
    tbl = roster_table(lop, show_name)
    if q:
        mask = tbl["Mã"].str.contains(q, case=False)
        if "Họ tên" in tbl:
            mask |= tbl["Họ tên"].str.contains(q, case=False, na=False)
        tbl = tbl[mask]
    if xu:
        tbl = tbl[tbl["Xu hướng"].isin(xu)]
    tbl = tbl.reset_index(drop=True)
    if tbl.empty:
        st.warning("Không có học sinh nào khớp bộ lọc.")
        st.stop()
    st.caption(f"{len(tbl)} học sinh · bấm vào một dòng để xem chi tiết")
    disp = tbl.copy()                                   # chuỗi hiển thị: ô trống thành "—"
    for c_ in disp.columns:
        if c_.startswith("ĐTB") or c_.startswith("Δ"):
            disp[c_] = disp[c_].map(lambda v: "—" if pd.isna(v) else f"{v:.2f}")
    disp["Tổng 3 môn thi (năm cuối)"] = disp["Tổng 3 môn thi (năm cuối)"].map(lambda v: f"{v:.1f}")
    disp["Môn giảm (năm cuối)"] = disp["Môn giảm (năm cuối)"].map(lambda v: "—" if pd.isna(v) else f"{v:.0f}")
    sty = disp.style.map(lambda v: f"color:{TREND_COLOR.get(v, '')}; font-weight:600" if v in TREND_COLOR else "", subset=["Xu hướng"])               .map(lambda v: f"color:{RED}" if isinstance(v, str) and v.startswith("-") else "", subset=["Δ đầu → cuối"])
    ev = st.dataframe(sty, hide_index=True, width="stretch", height=180 if compact else 320,
                      on_select="rerun", selection_mode="single-row", key=f"tbl_{key}")
    rows = ev.selection.rows if ev and ev.selection else []
    row = tbl.iloc[rows[0]] if rows else tbl.iloc[0]
    sid_ = row["Mã"]
    st.markdown(f"**Đang xem:** {label(sid_)} · lớp {row['Lớp']} · {row['Số năm có điểm']} năm có điểm"
                + ("" if rows else " *(mặc định dòng đầu — bấm dòng khác để đổi)*"))
    return sid_


def ref_for(grade):
    return df[df["lop_so"] == grade]


# ================================================================== 1. HỒ SƠ HỌC SINH
with tab_profile:
    sid = pick_student("p")
    h = df[df["sid"] == sid].sort_values("lop_so")
    mat = analytics.student_matrix(df, sid)
    tr = analytics.subject_trends(df, sid)
    cavg = analytics.class_average(df, sid)
    rank = analytics.class_rank(df, sid)
    years = [int(g) for g in h["lop_so"]]

    st.subheader("Điểm trung bình các môn qua các năm")
    k = st.columns(max(len(years), 1))
    dtb = h[SUBJECTS].mean(axis=1).values
    for j, (g, v) in enumerate(zip(years, dtb)):
        delta = None if j == 0 else f"{v - dtb[j - 1]:+.2f} so với lớp {years[j - 1]}"
        k[j].metric(f"Lớp {g} · {h.iloc[j]['lop']}", f"{v:.2f}", delta)
        k[j].caption(f"Mức **{LEVELS[int(h.iloc[j]['muc'])]}** · hạng {rank.iloc[j]['Hạng']}/{rank.iloc[j]['Sĩ số']} trong lớp · "
                     f"nghỉ {int(h.iloc[j]['nghi_p'] + h.iloc[j]['nghi_k'])} buổi")

    a, b = st.columns([3, 2])
    with a:
        fig = go.Figure()
        xs = [f"Lớp {g}" for g in years]
        fig.add_scatter(x=xs, y=dtb, name="ĐTB của em", mode="lines+markers+text", text=[f"{v:.2f}" for v in dtb],
                        textposition="top center", line=dict(color=BLUE, width=4), marker=dict(size=10))
        fig.add_scatter(x=xs, y=cavg["DTB"], name="ĐTB lớp", mode="lines+markers", line=dict(color=GREY, width=2, dash="dash"))
        fig.add_scatter(x=xs, y=h[EXAM].mean(axis=1), name="TB 3 môn thi (Toán, Văn, Anh)", mode="lines+markers",
                        line=dict(color=ORANGE, width=3, dash="dot"))
        fig.update_layout(height=330, margin=dict(t=60, b=10), yaxis=dict(title="Điểm", range=[0, 10.5]),
                          legend=dict(orientation="h", y=1.08, x=0), title=dict(text="Diễn biến điểm trung bình", y=0.97))
        st.plotly_chart(fig, width="stretch")
    with b:
        last = h.iloc[-1]
        cl = cavg.iloc[-1]
        cats = [SUBJECT_VN[s] for s in SUBJECTS]
        fig = go.Figure()
        fig.add_scatterpolar(r=[last[s] for s in SUBJECTS] + [last[SUBJECTS[0]]], theta=cats + [cats[0]], fill="toself",
                             name=f"Em (lớp {years[-1]})", line=dict(color=BLUE))
        fig.add_scatterpolar(r=[cl[s] for s in SUBJECTS] + [cl[SUBJECTS[0]]], theta=cats + [cats[0]], name="TB lớp",
                             line=dict(color=GREY, dash="dash"))
        fig.update_layout(height=330, margin=dict(t=60, b=10, l=30, r=30), polar=dict(radialaxis=dict(range=[0, 10])),
                          legend=dict(orientation="h", y=-0.1), title=dict(text=f"Hồ sơ 8 môn lớp {years[-1]} so với lớp", y=0.97))
        st.plotly_chart(fig, width="stretch")

    st.subheader("Từng môn qua các năm (nét đứt xám: trung bình lớp)")
    fig = make_subplots(rows=2, cols=4, subplot_titles=[SUBJECT_VN[s] for s in SUBJECTS], vertical_spacing=0.18)
    for j, s in enumerate(SUBJECTS):
        r, c = j // 4 + 1, j % 4 + 1
        col = TREND_COLOR[tr.loc[tr["ma"] == s, "Xu hướng"].iloc[0]] if len(tr) else BLUE
        fig.add_scatter(x=xs, y=h[s], mode="lines+markers+text", text=[f"{v:.1f}" for v in h[s]], textposition="top center",
                        line=dict(color=col, width=3), marker=dict(size=8), showlegend=False, row=r, col=c)
        fig.add_scatter(x=xs, y=cavg[s], mode="lines", line=dict(color=GREY, width=1.5, dash="dash"), showlegend=False, row=r, col=c)
        fig.update_yaxes(range=[max(0, float(min(h[s].min(), cavg[s].min())) - 1.5), 10.6], row=r, col=c)
    fig.update_layout(height=480, margin=dict(t=40, b=10))
    st.plotly_chart(fig, width="stretch")
    st.caption("Màu đường: xanh lá = tăng, đỏ = giảm, xám = ổn định (so năm cuối với năm đầu, ngưỡng ±0,3 điểm).")

    a, b = st.columns([3, 2])
    with a:
        st.subheader("Bảng điểm và xu hướng từng môn")
        show = mat.copy()
        cols = list(show.columns)
        if len(cols) >= 2:
            d = show[cols[-1]] - show[cols[-2]]
            show[f"Δ {cols[-1]} so {cols[-2]}"] = d.map(lambda v: "—" if pd.isna(v) else f"{TREND_ICON[analytics.label(v)]} {v:+.1f}")
        if len(tr):
            show["Xu hướng chung"] = [f"{TREND_ICON[x]} {x}" for x in tr["Xu hướng"]] + ["", ""]
            show["Độ dốc/năm"] = [("" if pd.isna(v) else f"{v:+.2f}") for v in tr["Độ dốc/năm"]] + ["", ""]
        st.dataframe(show, width="stretch")
    with b:
        st.subheader("Thay đổi năm sau so với năm trước")
        if len(years) >= 2:
            vals = h.set_index("lop_so")[SUBJECTS].diff().iloc[1:]
            z = vals.T.values
            fig = go.Figure(data=go.Heatmap(z=z, x=[f"Lớp {g} vs {g - 1}" for g in vals.index], y=[SUBJECT_VN[s] for s in SUBJECTS],
                                            colorscale="RdYlGn", zmid=0, zmin=-2.5, zmax=2.5, text=np.round(z, 1), texttemplate="%{text:+.1f}",
                                            colorbar=dict(title="Δ điểm")))
            fig.update_layout(height=360, margin=dict(t=10, b=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Chỉ có một năm dữ liệu, chưa tính được thay đổi.")
    st.subheader("Thứ hạng trong lớp")
    st.dataframe(rank, hide_index=True, width="stretch")
    if len(tr):
        down = tr[tr["Xu hướng"] == "Giảm"]
        up = tr[tr["Xu hướng"] == "Tăng"]
        msg = []
        if len(up):
            msg.append("**Tăng:** " + ", ".join(f"{r['Môn']} ({r['Tổng thay đổi']:+.1f})" for _, r in up.iterrows()))
        if len(down):
            msg.append("**Giảm:** " + ", ".join(f"{r['Môn']} ({r['Tổng thay đổi']:+.1f})" for _, r in down.iterrows()))
        if msg:
            st.markdown(" · ".join(msg))

# ================================================================== 2. DỰ ĐOÁN & ĐỊNH HƯỚNG
with tab_predict:
    if fitted is None:
        st.error("Chưa có mô hình. Hãy chạy huấn luyện trước:  scripts\\train.bat")
        st.stop()
    src = st.radio("Nguồn dữ liệu", ["Chọn từ sổ điểm", "Nhập tay"], horizontal=True, label_visibility="collapsed")
    if src == "Chọn từ sổ điểm":
        sid = pick_student("q", compact=True)
        i = sid_index[sid]
        w = make_windows(X[i:i + 1], M[i:i + 1], C[i:i + 1], sids[i:i + 1], PERS, targets=(9,), require_target=False)
        if len(w) == 0:
            st.warning("Học sinh này chưa có điểm mốc nào trước lớp 9 nên không dự đoán được.")
            st.stop()
        hist_df = df[df["sid"] == sid]
        prior = hist_df[hist_df["lop_so"] < 9].sort_values("lop_so")
        latest_row = prior.iloc[-1]
        latest, latest_grade = {s: latest_row[s] for s in SUBJECTS}, int(latest_row["lop_so"])
        a9 = hist_df[hist_df["lop_so"] == 9]
        actual9 = {s: float(a9.iloc[0][s]) for s in SUBJECTS} if len(a9) else None
        history = advisor.history_table(prior if not use_actual else hist_df)
        n_cd = int(latest_row["n_cd"])
    else:
        in_pers = input_periods(PERS, 9)
        st.caption("Nhập điểm trung bình các mốc đã có (để trống mốc chưa có). Rèn luyện: 3 = Tốt, 2 = Khá, 1 = Đạt.")
        cols = [SUBJECT_VN[s] for s in SUBJECTS] + ["Rèn luyện", "Nghỉ có phép", "Nghỉ không phép"]
        blank = pd.DataFrame([[None] * len(cols)] * len(in_pers), columns=cols, index=[p["label"] for p in in_pers])
        ed = st.data_editor(blank, width="stretch", column_config={c: st.column_config.NumberColumn(min_value=0.0, max_value=60.0, step=0.1) for c in cols})
        Xm = np.zeros((1, len(SUBJECTS) + len(STATIC), len(PERS)), np.float32)
        Mm = np.zeros_like(Xm)
        col_of = {(p["grade"], p["ky"]): t for t, p in enumerate(PERS)}
        filled = []
        for p in in_pers:
            r = ed.loc[p["label"]]
            vals = [r[SUBJECT_VN[s]] for s in SUBJECTS] + [r["Rèn luyện"], r["Nghỉ có phép"], r["Nghỉ không phép"]]
            if all(pd.notna(v) for v in vals[:len(SUBJECTS)]):
                vals = [float(v) if pd.notna(v) else (3.0 if k == len(SUBJECTS) else 0.0) for k, v in enumerate(vals)]
                t = col_of[(p["grade"], p["ky"])]
                Xm[0, :, t], Mm[0, :, t] = vals, 1
                filled.append((p, t))
        if not filled:
            st.info("Nhập đủ 8 môn của ít nhất một mốc để dự đoán.")
            st.stop()
        w = make_windows(Xm, Mm, np.full((1, len(PERS)), -1), np.array(["NHAP-TAY"]), PERS, targets=(9,), require_target=False)
        p_last, tl = filled[-1]
        latest, latest_grade = {s: float(Xm[0, j, tl]) for j, s in enumerate(SUBJECTS)}, p_last["grade"]
        actual9, n_cd, sid = None, 0, "NHAP-TAY"
        history = pd.DataFrame([dict(Lớp=p["grade"], ĐTB=round(float(Xm[0, :len(SUBJECTS), t].mean()), 2),
                                     **{"Tổng 3 môn thi": round(float(sum(Xm[0, SUBJECTS.index(s), t] for s in EXAM)), 1)},
                                     Mức=LEVELS[advisor.level_tt22({s: Xm[0, j, t] for j, s in enumerate(SUBJECTS)})])
                                for p, t in filled if p["ky"] == 0])
        if history.empty:
            history = pd.DataFrame([dict(Lớp=p["grade"], ĐTB=round(float(Xm[0, :len(SUBJECTS), t].mean()), 2),
                                         **{"Tổng 3 môn thi": round(float(sum(Xm[0, SUBJECTS.index(s), t] for s in EXAM)), 1)},
                                         Mức=LEVELS[advisor.level_tt22({s: Xm[0, j, t] for j, s in enumerate(SUBJECTS)})])
                                    for p, t in filled])

    try:
        reg, lo, hi, proba = fitted.predict(w)
    except Exception as e:
        st.error(f"Mô hình {model_name} không khớp trục thời gian hiện tại ({w.T} mốc): {type(e).__name__}. Hãy chạy lại scripts/train.bat.")
        st.stop()
    reg, lo, hi = reg[0], lo[0], hi[0]
    facts = advisor.build_facts(latest, latest_grade, reg, lo, hi, None if proba is None else proba[0], ref_for(latest_grade),
                                floor, margin, None if school == "(nhập tay)" else school, actual9 if use_actual else None,
                                history, n_cd, max_step, exam_shift)
    group, ts, xh = facts["nhom_dinh_huong"], facts["tuyen_sinh_lop_10"], facts.get("xu_huong", {})
    arrow = lambda t: "—" if not t else f"{TREND_ICON[t['xu_huong']]} {t['xu_huong']} ({t['thay_doi']:+})"

    st.markdown(f"<div style='padding:14px 18px;border-radius:10px;background:{GROUP_COLOR[group]}14;"
                f"border-left:6px solid {GROUP_COLOR[group]}'><span style='font-size:0.85rem;color:#475569'>Nhóm định hướng"
                f"</span><br><span style='font-size:1.5rem;font-weight:700;color:{GROUP_COLOR[group]}'>{group}</span>"
                f"<span style='color:#475569'> &nbsp;·&nbsp; {ts['nhan_dinh']}" + (f" ({ts['truong']})" if ts.get("truong") else "") +
                (f" &nbsp;·&nbsp; khoảng 90% của tổng dự đoán: {ts['khoang_tong_3_mon_90'][0]}–{ts['khoang_tong_3_mon_90'][1]}"
                 if "khoang_tong_3_mon_90" in ts else "") + "</span></div>", unsafe_allow_html=True)
    st.write("")
    m = st.columns(4)
    m[0].metric(f"ĐTB lớp {latest_grade} (thực tế)", facts["diem_trung_binh_lop_gan_nhat"], f"Mức {history.iloc[-1]['Mức'] if len(history) else '—'}", delta_color="off")
    m[1].metric("ĐTB lớp 9 (dự đoán)", facts["diem_trung_binh_du_doan_lop_9"], f"Mức {facts['muc_ket_qua_hoc_tap_du_doan_lop_9']}", delta_color="off")
    m[2].metric(f"Tổng Toán + Văn + Anh ({facts['nguon_diem_3_mon']})", ts["tong_3_mon"], f"{ts['chenh_lech']:+} so với sàn {ts['diem_san']}")
    m[3].metric("Xu hướng ĐTB", arrow(xh.get("diem_trung_binh")), f"3 môn thi: {arrow(xh.get('tong_3_mon_thi'))}", delta_color="off")

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Dự đoán điểm cả năm lớp 9 (khoảng tin cậy 90%)")
        labels = [SUBJECT_VN[s] for s in SUBJECTS]
        fig = go.Figure()
        fig.add_bar(x=labels, y=reg, name="Dự đoán lớp 9", marker_color=BLUE, width=0.4,
                    error_y=dict(type="data", symmetric=False, array=hi - reg, arrayminus=reg - lo, color="#1e3a8a"),
                    text=[f"{v:.1f}" for v in reg], textposition="inside")
        fig.add_scatter(x=labels, y=[latest[s] for s in SUBJECTS], mode="markers", name=f"Thực tế lớp {latest_grade}",
                        marker=dict(color=GREY, size=10))
        if actual9:
            fig.add_scatter(x=labels, y=[actual9[s] for s in SUBJECTS], mode="markers", name="Thực tế lớp 9",
                            marker=dict(color=ORANGE, size=13, symbol="diamond"))
        fig.update_layout(height=340, margin=dict(t=10, b=10), yaxis=dict(range=[0, 10.8], title="Điểm"), legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig, width="stretch")
        if proba is not None:
            st.caption("Xác suất mức kết quả học tập lớp 9 theo mô hình: " + " · ".join(f"{LEVELS[i]} {proba[0][i]:.0%}" for i in range(3, -1, -1)))
        if actual9:
            err = np.abs(reg - np.array([actual9[s] for s in SUBJECTS]))
            st.caption(f"So với điểm thật lớp 9: sai số tuyệt đối trung bình {err.mean():.2f} điểm, lớn nhất {err.max():.2f} ({SUBJECT_VN[SUBJECTS[int(err.argmax())]]}).")
    with right:
        st.subheader("Điểm sáng")
        for s in advisor.strengths(latest, ref_for(latest_grade)):
            st.markdown(f"**{s['mon']}** — {s['diem']:.1f} điểm (lớp {latest_grade}) · bằng hoặc cao hơn {s['phan_vi']}% bạn cùng khối")
        nxt = facts.get("muc_tieu_tiep_theo")
        st.subheader("Mục tiêu khả thi cho lớp 9")
        if nxt and nxt["can_cai_thien"]:
            st.markdown(f"Để đạt mức **{nxt['muc']}** (Thông tư 22, căn cứ {nxt['can_cu']}) cần ít nhất:")
            st.dataframe(pd.DataFrame(nxt["can_cai_thien"]).rename(columns={"mon": "Môn", "tu": "Hiện tại", "len": "Mục tiêu"}), hide_index=True, width="stretch")
            if not nxt["kha_thi"]:
                st.caption(f"Có môn cần tăng hơn {max_step} điểm: nên đặt mục tiêu theo từng chặng.")
        else:
            st.markdown("Dự kiến ở mức **Tốt**: duy trì kết quả hiện tại.")
        if facts["du_kien_du_dieu_kien_hoc_tap_tot_nghiep"]:
            st.success("Dự kiến đủ điều kiện học tập để xét tốt nghiệp THCS (từ mức Đạt).")
        else:
            st.warning("Cần đạt mức Đạt ở lớp 9 để đủ điều kiện xét tốt nghiệp THCS.")

    with st.expander("Vì sao mô hình dự đoán như vậy? (ô điểm nào kéo kết quả lên / xuống)"):
        occ = occlusion(fitted, w)
        tgt = st.selectbox("Môn được dự đoán", SUBJECTS, format_func=SUBJECT_VN.get, key="occ_t")
        vals = occ[tgt].unstack("Mốc")
        fig3 = go.Figure(data=go.Heatmap(z=vals.values, x=list(vals.columns), y=vals.index, colorscale="RdBu", zmid=0,
                                         text=np.round(vals.values, 2), texttemplate="%{text}", colorbar=dict(title="Δ điểm")))
        st.plotly_chart(fig3.update_layout(height=380, margin=dict(t=10)), width="stretch")
        st.caption("Giá trị dương: ô này đang kéo điểm dự đoán lên (nếu coi ô là khuyết, dự đoán sẽ giảm bấy nhiêu).")
        att = attention_map(fitted, w)
        if att is not None:
            st.markdown("**Trọng số chú ý của XEdu-KANFormer trên lưới môn × lớp**")
            fig4 = go.Figure(data=go.Heatmap(z=att.values, x=att.columns, y=att.index, colorscale="Blues", text=np.round(att.values, 3), texttemplate="%{text}"))
            st.plotly_chart(fig4.update_layout(height=380, margin=dict(t=10)), width="stretch")

    st.subheader("Thông điệp gửi " + audience.lower())
    key = f"msg|{sid}|{audience}|{json.dumps(facts, ensure_ascii=False)}"
    if st.session_state.get("msg_key") != key:
        st.session_state.update(msg_key=key, msg_text=llm.template(facts, audience), msg_src="mẫu theo luật")
    c = st.columns([1, 1, 4])
    if c[0].button("Viết bằng LLM", type="primary", disabled=not llm_name):
        try:
            with st.status(f"{llm_name} đang viết trên máy này…", expanded=True):
                raw = st.write_stream(llm.stream(facts, audience, llm_name))
            st.session_state.update(msg_text=llm.clean(raw), msg_src=llm_name)
            st.rerun()
        except Exception as e:
            st.error(f"LLM lỗi: {e}")
    if c[1].button("Dùng mẫu theo luật"):
        st.session_state.update(msg_text=llm.template(facts, audience), msg_src="mẫu theo luật")
    text = st.text_area(f"Nguồn: {st.session_state['msg_src']} — giáo viên có thể sửa trước khi duyệt", st.session_state["msg_text"], height=200)
    issues = llm.check(text, facts, audience)
    if issues:
        st.warning("Hàng rào kiểm soát phát hiện: " + "; ".join(issues))
    else:
        st.caption("Hàng rào kiểm soát: không có từ ngữ tiêu cực, mọi số liệu đều khớp dữ kiện, đúng câu mở đầu.")
    if st.button("Giáo viên duyệt và lưu", disabled=bool(issues)):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        rec = pd.DataFrame([dict(thoi_gian=dt.datetime.now().isoformat(timespec="seconds"), sid=sid, nguoi_nhan=audience,
                                 nhom=group, nguon=st.session_state["msg_src"], thong_diep=text)])
        rec.to_csv(OUT, mode="a", header=not os.path.exists(OUT), index=False, encoding="utf-8-sig")
        st.success("Đã lưu vào outputs/thong_diep_da_duyet.csv")
    with st.expander("Dữ kiện gửi cho LLM (JSON)"):
        st.json(facts)

# ================================================================== 3. LỚP HỌC
with tab_class:
    c = st.columns([1, 1, 3])
    grade = c[0].selectbox("Năm học (lớp)", [9, 8, 7, 6], format_func=lambda g: f"Lớp {g}")
    lops_g = sorted(df[df["lop_so"] == grade]["lop"].unique(), key=lambda s: (len(s), s))
    lop = c[1].selectbox("Lớp học", lops_g)
    cls = df[(df["lop_so"] == grade) & (df["lop"] == lop)]
    tbl = analytics.class_table(df, grade, lop)
    k = st.columns(5)
    k[0].metric("Sĩ số", len(cls))
    k[1].metric("ĐTB lớp", f"{cls[SUBJECTS].mean(axis=1).mean():.2f}", f"khối: {df[df['lop_so'] == grade][SUBJECTS].mean(axis=1).mean():.2f}", delta_color="off")
    k[2].metric("Mức Tốt / Khá / Đạt", " / ".join(str(int((cls['muc'] == m).sum())) for m in (3, 2, 1)))
    if tbl["Môn giảm"].notna().any():
        k[3].metric("HS có ≥ 3 môn giảm so với năm trước", int((tbl["Môn giảm"] >= 3).sum()))
        k[4].metric("HS giảm ĐTB", int((tbl["Δ ĐTB"] <= -analytics.EPS).sum()))
    a, b = st.columns(2)
    with a:
        st.subheader("Điểm trung bình từng môn: lớp so với khối")
        comp = pd.DataFrame({"Môn": [SUBJECT_VN[s] for s in SUBJECTS], "Lớp": cls[SUBJECTS].mean().values,
                             "Khối": df[df["lop_so"] == grade][SUBJECTS].mean().values})
        fig = px.bar(comp.melt(id_vars="Môn", var_name="Phạm vi", value_name="Điểm"), x="Môn", y="Điểm", color="Phạm vi", barmode="group",
                     color_discrete_sequence=[BLUE, GREY], text_auto=".1f")
        st.plotly_chart(fig.update_layout(height=340, margin=dict(t=10), yaxis_range=[0, 10.8]), width="stretch")
    with b:
        st.subheader("Diễn biến ĐTB của các em trong lớp qua các năm")
        ids = cls["sid"].tolist()
        traj = df[df["sid"].isin(ids)].assign(dtb=lambda d: d[SUBJECTS].mean(axis=1)).pivot(index="sid", columns="lop_so", values="dtb")
        fig = go.Figure()
        for s_, r in traj.iterrows():
            fig.add_scatter(x=[f"Lớp {g}" for g in r.index], y=r.values, mode="lines", line=dict(color="rgba(37,99,235,0.25)", width=1),
                            name=label(s_), showlegend=False, hovertemplate=f"{label(s_)}<br>%{{y:.2f}}")
        fig.add_scatter(x=[f"Lớp {g}" for g in traj.columns], y=traj.mean().values, mode="lines+markers", name="TB lớp", line=dict(color=ORANGE, width=4))
        st.plotly_chart(fig.update_layout(height=340, margin=dict(t=10), yaxis_title="ĐTB"), width="stretch")
    st.subheader("Phân bố điểm từng môn trong lớp")
    long = cls.melt(value_vars=SUBJECTS, var_name="mon", value_name="Điểm")
    long["Môn"] = long["mon"].map(SUBJECT_VN)
    st.plotly_chart(px.box(long, x="Môn", y="Điểm", points="all", color_discrete_sequence=[BLUE]).update_layout(height=320, margin=dict(t=10)), width="stretch")
    st.subheader("Danh sách học sinh")
    tshow = tbl.copy()
    if show_name:
        tshow.insert(1, "Họ tên", tshow["Mã"].map(names()))
    st.dataframe(tshow.style.map(lambda v: f"color:{RED}" if isinstance(v, (int, float)) and not pd.isna(v) and v <= -analytics.EPS else
                                 (f"color:{GREEN}" if isinstance(v, (int, float)) and not pd.isna(v) and v >= analytics.EPS else ""), subset=["Δ ĐTB"]),
                 hide_index=True, width="stretch", height=480)
    st.download_button("Tải bảng lớp (CSV)", tshow.to_csv(index=False).encode("utf-8-sig"), f"lop_{lop}_{grade}.csv")

# ================================================================== 4. TOÀN KHỐI
with tab_cohort:
    by = analytics.cohort_by_year(df)
    k = st.columns(4)
    k[0].metric("Học sinh (ít nhất 1 năm)", df["sid"].nunique())
    k[1].metric("Có đủ 4 năm", int((df.groupby("sid")["lop_so"].nunique() == 4).sum()))
    k[2].metric("ĐTB lớp 6 → lớp 9", f"{by.loc[6, 'ĐTB']:.2f} → {by.loc[9, 'ĐTB']:.2f}" if 6 in by.index and 9 in by.index else "—")
    k[3].metric("Tỉ lệ mức Tốt lớp 9", f"{analytics.level_share(df).loc[9, 'Tốt']:.0f}%" if 9 in analytics.level_share(df).index else "—")
    a, b = st.columns(2)
    with a:
        st.subheader("Điểm trung bình từng môn qua các năm (toàn khối)")
        fig = go.Figure()
        for j, s in enumerate(SUBJECTS):
            fig.add_scatter(x=[f"Lớp {g}" for g in by.index], y=by[s], name=SUBJECT_VN[s], mode="lines+markers", line=dict(color=PALETTE[j], width=2.5))
        st.plotly_chart(fig.update_layout(height=380, margin=dict(t=10), yaxis_title="Điểm TB"), width="stretch")
    with b:
        st.subheader("Cơ cấu mức kết quả học tập theo năm (%)")
        ls = analytics.level_share(df).reset_index().melt(id_vars="lop_so", var_name="Mức", value_name="%")
        ls["Lớp"] = "Lớp " + ls["lop_so"].astype(str)
        fig = px.bar(ls, x="Lớp", y="%", color="Mức", category_orders={"Mức": LEVELS[::-1]}, text_auto=".0f",
                     color_discrete_sequence=["#1d4ed8", "#60a5fa", "#fdba74", "#c2410c"])
        st.plotly_chart(fig.update_layout(height=380, margin=dict(t=10)), width="stretch")
    st.subheader("Thay đổi điểm từng môn giữa hai năm liên tiếp (trung bình toàn khối)")
    d = by[SUBJECTS].diff().iloc[1:]
    z = d.T.values
    fig = go.Figure(data=go.Heatmap(z=z, x=[f"Lớp {g} vs {g - 1}" for g in d.index], y=[SUBJECT_VN[s] for s in SUBJECTS], colorscale="RdYlGn",
                                    zmid=0, text=np.round(z, 2), texttemplate="%{text:+.2f}", colorbar=dict(title="Δ điểm")))
    st.plotly_chart(fig.update_layout(height=360, margin=dict(t=10)), width="stretch")
    g_sel = st.selectbox("Xem tiến bộ / giảm sút giữa năm", [9, 8, 7], format_func=lambda g: f"Lớp {g - 1} → lớp {g}")
    up, down = analytics.movers(df, g_sel)
    a, b = st.columns(2)
    for col, t_, title in ((a, up, "Tiến bộ nhiều nhất"), (b, down, "Giảm sút nhiều nhất")):
        with col:
            st.subheader(title)
            t2 = t_.copy()
            if show_name:
                t2.insert(1, "Họ tên", t2["Mã"].map(names()))
            st.dataframe(t2, hide_index=True, width="stretch")
    st.subheader("Điểm trung bình lớp 9 theo lớp học")
    c9 = df[df["lop_so"] == 9].groupby("lop")[SUBJECTS].mean().mean(axis=1).sort_values(ascending=False).reset_index()
    c9.columns = ["Lớp", "ĐTB"]
    st.plotly_chart(px.bar(c9, x="Lớp", y="ĐTB", text_auto=".2f", color_discrete_sequence=[BLUE]).update_layout(height=300, margin=dict(t=10)), width="stretch")
