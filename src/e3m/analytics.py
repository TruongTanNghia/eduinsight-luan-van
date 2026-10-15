"""Phân tích sổ điểm theo từng học sinh, lớp và khối: diễn biến từng môn qua các năm, xu hướng, thứ hạng.

Chỉ dùng dữ liệu thật trong sổ điểm (không dùng mô hình).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import EXAM, LEVELS, SUBJECTS, SUBJECT_VN

EPS = 0.3   # chênh lệch nhỏ hơn mức này coi là ổn định


def label(delta: float) -> str:
    if pd.isna(delta):
        return "—"
    return "Tăng" if delta >= EPS else "Giảm" if delta <= -EPS else "Ổn định"


def student_matrix(df: pd.DataFrame, sid: str) -> pd.DataFrame:
    """Bảng môn × lớp của một học sinh (điểm TB cả năm), thêm hàng ĐTB và tổng 3 môn thi."""
    h = df[df["sid"] == sid].sort_values("lop_so")
    m = h.set_index("lop_so")[SUBJECTS].T
    m.columns = [f"Lớp {g}" for g in m.columns]
    m.index = [SUBJECT_VN[s] for s in m.index]
    m.loc["ĐTB các môn"] = h.set_index("lop_so")[SUBJECTS].mean(axis=1).round(2).values
    m.loc["Tổng 3 môn thi"] = h.set_index("lop_so")[EXAM].sum(axis=1).round(1).values
    return m


def subject_trends(df: pd.DataFrame, sid: str) -> pd.DataFrame:
    """Với từng môn: điểm đầu, điểm cuối, chênh lệch năm cuối so với năm trước, độ dốc/năm, nhãn xu hướng."""
    h = df[df["sid"] == sid].sort_values("lop_so")
    rows = []
    for s in SUBJECTS:
        v = h[s].values.astype(float)
        g = h["lop_so"].values
        if len(v) == 0:
            continue
        slope = float(np.polyfit(g, v, 1)[0]) if len(v) >= 2 else np.nan
        last_delta = float(v[-1] - v[-2]) if len(v) >= 2 else np.nan
        rows.append({"Môn": SUBJECT_VN[s], "ma": s, f"Lớp {g[0]}": v[0], f"Lớp {g[-1]}": v[-1],
                     "Δ năm cuối": round(last_delta, 1) if not np.isnan(last_delta) else np.nan,
                     "Độ dốc/năm": round(slope, 2) if not np.isnan(slope) else np.nan,
                     "Tổng thay đổi": round(float(v[-1] - v[0]), 1),
                     "Xu hướng": label(float(v[-1] - v[0]) if len(v) >= 2 else np.nan)})
    return pd.DataFrame(rows)


def class_average(df: pd.DataFrame, sid: str) -> pd.DataFrame:
    """Điểm trung bình của lớp mà học sinh học, theo từng năm (lớp có thể đổi giữa các năm)."""
    h = df[df["sid"] == sid][["lop_so", "lop"]]
    out = []
    for _, r in h.iterrows():
        c = df[(df["lop_so"] == r["lop_so"]) & (df["lop"] == r["lop"])]
        out.append({"lop_so": r["lop_so"], "lop": r["lop"], "si_so": len(c), **{s: c[s].mean() for s in SUBJECTS},
                    "DTB": c[SUBJECTS].mean(axis=1).mean()})
    return pd.DataFrame(out).sort_values("lop_so")


def class_rank(df: pd.DataFrame, sid: str) -> pd.DataFrame:
    """Thứ hạng ĐTB của học sinh trong lớp theo từng năm."""
    h = df[df["sid"] == sid]
    rows = []
    for _, r in h.sort_values("lop_so").iterrows():
        c = df[(df["lop_so"] == r["lop_so"]) & (df["lop"] == r["lop"])].copy()
        c["dtb"] = c[SUBJECTS].mean(axis=1)
        c = c.sort_values("dtb", ascending=False).reset_index(drop=True)
        rank = int(c.index[c["sid"] == sid][0]) + 1
        rows.append({"Lớp": f"Lớp {r['lop_so']}", "Lớp học": r["lop"], "Hạng": rank, "Sĩ số": len(c),
                     "ĐTB": round(float(r[SUBJECTS].mean()), 2), "Mức": LEVELS[int(r["muc"])]})
    return pd.DataFrame(rows)


def class_table(df: pd.DataFrame, grade: int, lop: str) -> pd.DataFrame:
    """Bảng tổng hợp một lớp ở một năm: ĐTB, tổng 3 môn, số môn giảm so với năm trước, mức."""
    c = df[(df["lop_so"] == grade) & (df["lop"] == lop)].copy()
    prev = df[df["lop_so"] == grade - 1].set_index("sid")
    rows = []
    for _, r in c.iterrows():
        d = {"Mã": r["sid"], "ĐTB": round(float(r[SUBJECTS].mean()), 2), "Tổng 3 môn thi": round(float(r[EXAM].sum()), 1),
             "Mức": LEVELS[int(r["muc"])], "Rèn luyện": LEVELS[int(r["ren_luyen"])], "Nghỉ": int(r["nghi_p"] + r["nghi_k"])}
        if r["sid"] in prev.index:
            p = prev.loc[r["sid"]]
            deltas = {s: float(r[s] - p[s]) for s in SUBJECTS}
            d["Δ ĐTB"] = round(float(r[SUBJECTS].mean() - p[SUBJECTS].mean()), 2)
            d["Môn giảm"] = sum(v <= -EPS for v in deltas.values())
            d["Môn tăng"] = sum(v >= EPS for v in deltas.values())
            d["Giảm nhiều nhất"] = SUBJECT_VN[min(deltas, key=deltas.get)] + f" ({min(deltas.values()):+.1f})" if min(deltas.values()) <= -EPS else ""
        else:
            d.update({"Δ ĐTB": np.nan, "Môn giảm": np.nan, "Môn tăng": np.nan, "Giảm nhiều nhất": "—"})
        rows.append(d)
    return pd.DataFrame(rows).sort_values("ĐTB", ascending=False).reset_index(drop=True)


def cohort_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Điểm trung bình từng môn của cả khối theo từng năm."""
    g = df.groupby("lop_so")[SUBJECTS].mean().round(2)
    g["ĐTB"] = df.groupby("lop_so")[SUBJECTS].mean().mean(axis=1).round(2)
    g["Số học sinh"] = df.groupby("lop_so")["sid"].size()
    return g


def level_share(df: pd.DataFrame) -> pd.DataFrame:
    t = df.groupby(["lop_so", "muc"]).size().unstack(fill_value=0)
    t.columns = [LEVELS[c] for c in t.columns]
    return (t.div(t.sum(axis=1), axis=0) * 100).round(1)


def movers(df: pd.DataFrame, grade: int, n: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Học sinh tiến bộ và giảm sút nhiều nhất về ĐTB giữa năm `grade-1` và `grade`."""
    a = df[df["lop_so"] == grade].set_index("sid")
    b = df[df["lop_so"] == grade - 1].set_index("sid")
    common = a.index.intersection(b.index)
    d = pd.DataFrame({"Lớp": a.loc[common, "lop"], f"ĐTB lớp {grade - 1}": b.loc[common, SUBJECTS].mean(axis=1).round(2),
                      f"ĐTB lớp {grade}": a.loc[common, SUBJECTS].mean(axis=1).round(2)})
    d["Δ"] = (d[f"ĐTB lớp {grade}"] - d[f"ĐTB lớp {grade - 1}"]).round(2)
    d = d.reset_index().rename(columns={"sid": "Mã"})
    return d.sort_values("Δ", ascending=False).head(n), d.sort_values("Δ").head(n)


def roster(df: pd.DataFrame, lop: str | None = None, names: dict | None = None) -> pd.DataFrame:
    """Danh sách học sinh (một dòng mỗi em): lớp gần nhất, ĐTB từng năm, xu hướng, mức và tổng 3 môn năm gần nhất.

    lop = None: toàn khối. names: từ điển mã -> họ tên (chỉ khi giáo viên bật hiện tên).
    """
    d = df.copy()
    d["dtb"] = d[SUBJECTS].mean(axis=1)
    d["t3"] = d[EXAM].sum(axis=1)
    last = d.sort_values("lop_so").groupby("sid").last()
    if lop is not None:
        last = last[last["lop"] == lop]
    wide = d.pivot(index="sid", columns="lop_so", values="dtb").reindex(last.index)
    out = pd.DataFrame({"Mã": last.index, "Lớp": last["lop"].values})
    if names:
        out.insert(1, "Họ tên", [names.get(s, "") for s in last.index])
    for g in sorted(wide.columns):
        out[f"ĐTB lớp {g}"] = wide[g].round(2).values
    first = wide.apply(lambda r: r.dropna().iloc[0] if r.notna().any() else np.nan, axis=1)
    lastv = wide.apply(lambda r: r.dropna().iloc[-1] if r.notna().any() else np.nan, axis=1)
    n_years = wide.notna().sum(axis=1)
    delta = (lastv - first).where(n_years >= 2)
    out["Δ đầu → cuối"] = delta.round(2).values
    out["Xu hướng"] = [label(v) for v in delta.values]
    # số môn giảm ở năm cuối so với năm trước
    prev = d.sort_values("lop_so").groupby("sid").nth(-2).set_index("sid")
    ndown = []
    for s in last.index:
        if s in prev.index and n_years.loc[s] >= 2:
            ndown.append(int(sum(last.loc[s, x] - prev.loc[s, x] <= -EPS for x in SUBJECTS)))
        else:
            ndown.append(np.nan)
    out["Môn giảm (năm cuối)"] = ndown
    out["Tổng 3 môn thi (năm cuối)"] = last["t3"].round(1).values
    out["Mức (năm cuối)"] = [LEVELS[int(m)] for m in last["muc"]]
    out["Số năm có điểm"] = n_years.values
    return out.sort_values(["Lớp", "Mã"]).reset_index(drop=True)
