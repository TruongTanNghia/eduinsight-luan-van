"""Đọc sổ điểm tổng kết của một khóa học sinh theo dõi dọc (lớp 6 -> lớp 9), ẩn danh và tạo bảng dữ liệu chuẩn.

Nhận cả sổ điểm CẢ NĂM lẫn sổ điểm HỌC KỲ I / HỌC KỲ II (nhận diện từ tiêu đề sheet, không phụ thuộc tên tệp).
Mỗi học sinh có tối đa một dòng cho mỗi (lớp, kỳ). Chạy:  python -m e3m.data   (PYTHONPATH=src, hoặc scripts/prepare_data.bat)
"""
from __future__ import annotations

import glob
import hashlib
import os
import re

import numpy as np
import pandas as pd
import xlrd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # thư mục gốc dự án
RAW_DIR = os.path.join(ROOT, "data", "raw")
OUT_DIR = os.path.join(ROOT, "data", "processed")
PROCESSED = os.path.join(OUT_DIR, "students_long.csv")
PRIVATE_MAP = os.path.join(ROOT, "data", "private", "id_map.csv")

SUBJECTS = ["Toan", "Van", "NgoaiNgu", "KHTN", "LSDL", "GDCD", "CongNghe", "Tin"]   # 8 môn đánh giá bằng điểm số
EXAM = ["Toan", "Van", "NgoaiNgu"]                                                  # 3 môn thi tuyển sinh 10
STATIC = ["ren_luyen", "nghi_p", "nghi_k"]                                          # đặc trưng theo từng kỳ
GRADES = [6, 7, 8, 9]
LEVELS = ["Chưa đạt", "Đạt", "Khá", "Tốt"]
KY_LABEL = {0: "Cả năm", 1: "HK1", 2: "HK2"}
KY_ORDER = {1: 0, 2: 1, 0: 2}            # thứ tự thời gian trong một năm học: HK1 < HK2 < Cả năm
SUBJECT_VN = {
    "Toan": "Toán", "Van": "Ngữ văn", "NgoaiNgu": "Tiếng Anh", "KHTN": "Khoa học tự nhiên",
    "LSDL": "Lịch sử và Địa lí", "GDCD": "Giáo dục công dân", "CongNghe": "Công nghệ", "Tin": "Tin học",
}
STATIC_VN = {"ren_luyen": "Kết quả rèn luyện", "nghi_p": "Nghỉ có phép", "nghi_k": "Nghỉ không phép"}

_COL = {"Toán": "Toan", "Văn": "Van", "Ng.ngữ": "NgoaiNgu", "KHTN": "KHTN", "LS&ĐL": "LSDL",
        "GDCD": "GDCD", "C.nghệ": "CongNghe", "Tin": "Tin"}
_PASS_COLS = ["GDTC", "Nghệ thuật", "NDGDCĐP", "HĐTN&HN"]
_LEVEL = {"Tốt": 3, "Khá": 2, "Đạt": 1, "Chưa đạt": 0}
# Thông tư 22, Điều 9: (mức, điểm sàn mọi môn, ngưỡng cao, số môn tối thiểu đạt ngưỡng cao)
_RULES = [(3, 6.5, 8.0, 6), (2, 5.0, 6.5, 6), (1, 3.5, 5.0, 6)]


def _num(v):
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).strip().replace(",", "."))
    except ValueError:
        return np.nan


def _level_rule(scores: list[float]) -> int:
    v = np.array([s for s in scores if not np.isnan(s)])
    for lv, floor, high, k in _RULES:
        if (v >= floor).all() and (v >= high).sum() >= min(k, len(v)):
            return lv
    return 0


def sheet_info(sheet, filename: str = "") -> tuple[int | None, str | None, int]:
    """(lớp, năm học, kỳ) đọc từ tiêu đề sheet; thiếu thì suy từ tên tệp. kỳ: 0 = cả năm, 1 = HK I, 2 = HK II."""
    head = " ".join(str(c) for r in range(min(sheet.nrows, 4)) for c in sheet.row_values(r) if str(c).strip()).upper()
    src = head + " " + filename.upper()
    ky = 0
    if re.search(r"HỌC KỲ\s*II\b|HỌC KỲ\s*2\b|HK\s*II\b|HK\s*2\b|\(HK2\)", src):
        ky = 2
    elif re.search(r"HỌC KỲ\s*I\b|HỌC KỲ\s*1\b|HK\s*I\b|HK\s*1\b|\(HK1\)", src):
        ky = 1
    m = re.search(r"KHỐI\s*(\d)", head) or re.search(r"KHOI\s*(\d)", filename.upper()) or re.search(r"LỚP\s*(\d)A", head)
    grade = int(m.group(1)) if m else None
    y = re.search(r"NĂM HỌC\s*(\d{4})\s*-\s*(\d{4})", head)
    year = f"{y.group(1)}-{y.group(2)}" if y else None
    if year is None:
        y2 = re.search(r"(\d{2})-(\d{2})", filename)
        year = f"20{y2.group(1)}-20{y2.group(2)}" if y2 else None
    return grade, year, ky


def _read_sheet(sheet, grade: int, year: str, ky: int = 0) -> list[dict]:
    hr = next(r for r in range(min(sheet.nrows, 15)) if str(sheet.cell_value(r, 0)).strip() == "STT")
    head = [str(c).strip() for c in sheet.row_values(hr)]
    sub = [str(c).strip() for c in sheet.row_values(hr + 1)]
    cols, last = {}, ""
    for i, h in enumerate(head):
        last = h or last
        if last == "Buổi nghỉ":
            cols[f"nghi_{sub[i]}"] = i          # P / K / Tổng (thứ tự thay đổi theo năm)
        elif h:
            cols[h] = i
    rows = []
    for r in range(hr + 2, sheet.nrows):
        v = sheet.row_values(r)
        if not isinstance(v[0], float) or not str(v[cols["Họ và tên"]]).strip():
            continue
        rec = {"lop_so": grade, "ky": ky, "nam_hoc": year, "lop": sheet.name.upper(),
               "_ma": str(v[cols["Mã học sinh"]]).split(".")[0], "_ten": str(v[cols["Họ và tên"]]).strip()}
        for h, key in _COL.items():
            rec[key] = _num(v[cols[h]]) if h in cols else np.nan
        rec["n_cd"] = sum(str(v[cols[h]]).strip() == "CĐ" for h in _PASS_COLS if h in cols)
        rec["muc"] = _LEVEL.get(str(v[cols["Kết quả học tập"]]).strip(), np.nan) if "Kết quả học tập" in cols else np.nan
        rec["_has_muc"] = "Kết quả học tập" in cols
        rec["ren_luyen"] = _LEVEL.get(str(v[cols["Kết quả rèn luyện"]]).strip(), np.nan) if "Kết quả rèn luyện" in cols else np.nan
        rec["nghi_p"] = _num(v[cols["nghi_P"]]) if "nghi_P" in cols else np.nan
        rec["nghi_k"] = _num(v[cols["nghi_K"]]) if "nghi_K" in cols else np.nan
        rows.append(rec)
    return rows


def _synthesize_year(df: pd.DataFrame) -> pd.DataFrame:
    """Lớp nào có HK1 và HK2 nhưng chưa có sổ cả năm: tính cả năm = (HK1 + 2·HK2)/3 theo Thông tư 22."""
    out = [df]
    for (sid, g), grp in df.groupby(["sid", "lop_so"]):
        kys = set(grp["ky"])
        if 0 in kys or not {1, 2} <= kys:
            continue
        h1, h2 = grp[grp["ky"] == 1].iloc[0], grp[grp["ky"] == 2].iloc[0]
        rec = h2.copy()
        rec["ky"] = 0
        for s in SUBJECTS:
            rec[s] = round((h1[s] + 2 * h2[s]) / 3, 1) if pd.notna(h1[s]) and pd.notna(h2[s]) else np.nan
        rec["nghi_p"], rec["nghi_k"] = h1["nghi_p"] + h2["nghi_p"], h1["nghi_k"] + h2["nghi_k"]
        rec["muc"] = _level_rule([rec[s] for s in SUBJECTS]) if rec["n_cd"] <= 1 else 0
        out.append(pd.DataFrame([rec]))
    return pd.concat(out, ignore_index=True)


def build(raw_dir: str = RAW_DIR, save: bool = True) -> pd.DataFrame:
    rows = []
    for f in sorted(glob.glob(os.path.join(raw_dir, "*.xls"))):
        name = os.path.basename(f)
        wb = xlrd.open_workbook(f, ignore_workbook_corruption=True)
        for sh in wb.sheets():
            grade, year, ky = sheet_info(sh, name)
            if grade is None or year is None:
                print(f"[bỏ qua] {name} / {sh.name}: không xác định được lớp hoặc năm học")
                continue
            try:
                rows += _read_sheet(sh, grade, year, ky)
            except StopIteration:
                print(f"[bỏ qua] {name} / {sh.name}: không có bảng điểm")
    df = pd.DataFrame(rows)
    df = df.dropna(subset=["Toan", "Van", "NgoaiNgu"]).reset_index(drop=True)   # bỏ dòng không có kết quả
    df = df[~(df["_has_muc"] & df["muc"].isna())].reset_index(drop=True)          # sổ có cột mức mà để trống: chưa được đánh giá
    df[["nghi_p", "nghi_k"]] = df[["nghi_p", "nghi_k"]].fillna(0)
    df["ren_luyen"] = df["ren_luyen"].fillna(3)
    # Ẩn danh: mã giả một chiều từ mã học sinh (giữ nguyên qua các năm để nối chuỗi)
    df["sid"] = ["HS-" + hashlib.sha256(f"e3m|{m}".encode()).hexdigest()[:8].upper() for m in df["_ma"]]
    df = df.drop_duplicates(subset=["sid", "lop_so", "ky"], keep="first")
    df["muc"] = df.apply(lambda r: r["muc"] if pd.notna(r["muc"]) else _level_rule([r[s] for s in SUBJECTS]), axis=1).astype(int)
    df = _synthesize_year(df)
    keep = ["sid", "lop_so", "ky", "nam_hoc", "lop"] + SUBJECTS + ["n_cd"] + STATIC + ["muc"]
    df = df.sort_values(["sid", "lop_so", "ky"], key=lambda c: c.map(KY_ORDER) if c.name == "ky" else c).reset_index(drop=True)
    if save:
        os.makedirs(os.path.dirname(PRIVATE_MAP), exist_ok=True)
        os.makedirs(OUT_DIR, exist_ok=True)
        df.sort_values(["sid", "lop_so"]).drop_duplicates("sid", keep="last")[["sid", "_ten", "lop"]].rename(
            columns={"_ten": "ho_ten", "lop": "lop_gan_nhat"}).to_csv(PRIVATE_MAP, index=False, encoding="utf-8-sig")
        df[keep].to_csv(PROCESSED, index=False, encoding="utf-8-sig")
    return df[keep]


def load() -> pd.DataFrame:
    """Bảng dài đầy đủ (mọi kỳ). Cột `ky`: 0 = cả năm, 1 = HK1, 2 = HK2."""
    if not os.path.exists(PROCESSED):
        return build()
    df = pd.read_csv(PROCESSED)
    if "ky" not in df.columns:
        df["ky"] = 0
    return df


def load_yearly(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Chỉ các dòng cả năm (một dòng mỗi học sinh mỗi lớp) — dùng cho phân tích, dashboard, báo cáo."""
    df = load() if df is None else df
    return df[df["ky"] == 0].drop(columns=["ky"]).reset_index(drop=True)


# ----------------------------------------------------------------------------- mốc thời gian
def periods(df: pd.DataFrame) -> list[dict]:
    """Các mốc (lớp, kỳ) có trong dữ liệu, xếp theo thời gian. Mỗi mốc: key, grade, ky, label, short, year, input.

    `input` = mốc được dùng làm đầu vào: HK1/HK2 của mọi lớp, và cả năm của lớp không có dữ liệu học kỳ.
    """
    present = df.groupby(["lop_so", "ky"])["nam_hoc"].first().to_dict()
    has_sem = {g for (g, k) in present if k in (1, 2)}
    out = []
    for (g, k) in sorted(present, key=lambda gk: (gk[0], KY_ORDER[gk[1]])):
        label = f"Lớp {g}" if k == 0 else f"{KY_LABEL[k]} lớp {g}"
        out.append({"key": f"L{g}" + ("" if k == 0 else f"H{k}"), "grade": int(g), "ky": int(k), "label": label,
                    "short": f"L{g}" + ("" if k == 0 else f"H{k}"), "year": str(present[(g, k)]).replace("-", "–"),
                    "input": k != 0 or g not in has_sem})
    return out


def input_periods(all_periods: list[dict], target_grade: int) -> list[dict]:
    """Mốc đầu vào hợp lệ để dự đoán cả năm của `target_grade`: mọi mốc trước HK2 của lớp đó (và không phải cả năm lớp đó)."""
    return [p for p in all_periods if p["input"] and (p["grade"] < target_grade or (p["grade"] == target_grade and p["ky"] == 1))]


def to_panel(df: pd.DataFrame):
    """Bảng dài -> lưới học sinh × hàng × mốc.

    Trả về X [N, S+K, P] (8 môn + 3 đặc trưng tĩnh theo từng mốc), M mặt nạ cùng kích thước,
    C [N, P] mức kết quả học tập từng mốc (-1 nếu thiếu), mã học sinh, bảng thông tin (lớp gần nhất) và danh sách mốc.
    """
    pers = periods(df)
    pidx = {(p["grade"], p["ky"]): t for t, p in enumerate(pers)}
    sids = sorted(df["sid"].unique())
    idx = {s: i for i, s in enumerate(sids)}
    feats = SUBJECTS + STATIC
    X = np.full((len(sids), len(feats), len(pers)), np.nan, dtype=np.float32)
    C = np.full((len(sids), len(pers)), -1, dtype=np.int64)
    for _, r in df.iterrows():
        i, t = idx[r["sid"]], pidx[(int(r["lop_so"]), int(r["ky"]))]
        X[i, :, t] = r[feats].values.astype(np.float32)
        C[i, t] = int(r["muc"])
    M = (~np.isnan(X)).astype(np.float32)
    yearly = df[df["ky"] == 0] if (df["ky"] == 0).any() else df
    info = yearly.sort_values("lop_so").groupby("sid").last()[["lop", "lop_so", "n_cd"]].reindex(sids).reset_index()
    return np.nan_to_num(X), M, C, np.array(sids), info, pers


if __name__ == "__main__":
    d = build()
    print(d.shape)
    print(d.groupby(["lop_so", "ky"]).agg(n=("sid", "size"), lop=("lop", "nunique"), **{s: (s, "mean") for s in SUBJECTS}).round(2))
    print("mốc thời gian:", [p["label"] + ("" if p["input"] else " (chỉ làm mục tiêu)") for p in periods(d)])
    print("mốc đầu vào cho lớp 9:", [p["label"] for p in input_periods(periods(d), 9)])
    n = d[d["ky"] == 0].groupby("sid")["lop_so"].agg(lambda s: tuple(sorted(s)))
    print("số năm có dữ liệu:", n.map(len).value_counts().sort_index().to_dict())
