"""Lõi tính toán cho API EduInsight: đọc sổ điểm đã xử lý, hồ sơ học sinh, lớp, khối, dự đoán, báo cáo, nhập dữ liệu.

"Kỳ" trong giao diện = một mốc trong sổ điểm: HK1, HK2 hoặc Cả năm của từng lớp (key: L6H1, L6H2, L6, ...).
Xu hướng tăng/giảm tính theo chuỗi học kỳ (HK1 lớp 6 → HK2 lớp 9); nếu chưa có sổ học kỳ thì theo chuỗi cả năm.
Mọi số liệu "thực tế" tính trực tiếp từ bảng điểm; chỉ phần /ai dùng mô hình.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import sys
import uuid

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from e3m import advisor, analytics, llm  # noqa: E402
from e3m.data import EXAM, GRADES, LEVELS, PRIVATE_MAP, PROCESSED, RAW_DIR, STATIC, SUBJECT_VN, SUBJECTS, build, load, load_yearly, periods as data_periods, to_panel  # noqa: E402
from e3m.explain import attention_map, load_serving, occlusion  # noqa: E402
from e3m.pipeline import make_windows  # noqa: E402

THRESHOLD = 0.3
SHORT = {"Toan": "Toán", "Van": "Văn", "NgoaiNgu": "Anh", "KHTN": "KHTN", "LSDL": "LS&ĐL", "GDCD": "GDCD", "CongNghe": "CN", "Tin": "Tin"}
LEVEL_KEY = {3: "Tốt", 2: "Khá", 1: "Đạt", 0: "Chưa đạt"}
OUT_DIR = os.path.join(ROOT, "outputs")
REPORTS_DIR = os.path.join(OUT_DIR, "reports")
VERSION_FILE = os.path.join(ROOT, "data", "processed", "version.json")
HISTORY_FILE = os.path.join(OUT_DIR, "import_history.json")
SCHOOLS_FILE = os.path.join(ROOT, "data", "external", "diem_chuan_thpt.csv")
SCHOOL_COLS = ["id", "truong", "nam", "phuong_thuc", "diem_san", "loai_hinh", "nguon"]


def r2(v):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), 2)


def r3(v):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), 3)


def _json_file(path, default):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return default


def _save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)


# ----------------------------------------------------------------------------- xu hướng (theo đặc tả student-profile)
def trend_of(values: list[float | None], t: float = THRESHOLD) -> dict:
    """Δ chỉ tính giữa hai kỳ liên tiếp đều có điểm; streak đếm từ kỳ gần nhất lùi lại, cùng dấu và |Δ| ≥ ngưỡng."""
    ds = [{"i": i, "d": round(values[i] - values[i - 1], 2)} for i in range(1, len(values))
          if values[i] is not None and values[i - 1] is not None]
    n = sum(v is not None for v in values)
    if n < 3:
        return {"kind": "insufficient", "label": "Chưa đủ dữ liệu", "streak": 0, "dir": 0, "deltas": ds}
    streak, direction = 0, 0
    for k in range(len(ds) - 1, -1, -1):
        s = 1 if ds[k]["d"] >= t else -1 if ds[k]["d"] <= -t else 0
        expected = len(values) - 1 if k == len(ds) - 1 else ds[k + 1]["i"] - 1
        if s == 0 or (direction != 0 and s != direction) or ds[k]["i"] != expected:
            break
        direction, streak = s, streak + 1
    if streak >= 2:
        return {"kind": "up" if direction > 0 else "down", "label": f"{'Tăng' if direction > 0 else 'Giảm'} {streak} kỳ liên tiếp", "streak": streak, "dir": direction, "deltas": ds}
    if streak == 1:
        return {"kind": "up_last" if direction > 0 else "down_last", "label": f"{'Tăng' if direction > 0 else 'Giảm'} kỳ gần nhất", "streak": 1, "dir": direction, "deltas": ds}
    return {"kind": "flat", "label": "Ổn định", "streak": 0, "dir": 0, "deltas": ds}


def overall_trend(delta: float | None, t: float = THRESHOLD) -> str:
    if delta is None:
        return "insufficient"
    return "up" if delta >= t else "down" if delta <= -t else "flat"


# ----------------------------------------------------------------------------- kho dữ liệu
class Store:
    def __init__(self):
        self.reload()

    def reload(self):
        self.df_all = load()                              # mọi kỳ (đầu vào mô hình)
        self.df = load_yearly(self.df_all)                # cả năm (phân tích, báo cáo)
        self.df["dtb"] = self.df[SUBJECTS].mean(axis=1)
        self.names = pd.read_csv(PRIVATE_MAP).set_index("sid")["ho_ten"].to_dict() if os.path.exists(PRIVATE_MAP) else {}
        self.X, self.M, self.C, self.sids, self.info, self.panel_periods = to_panel(self.df_all)
        self.sid_index = {s: i for i, s in enumerate(self.sids)}
        self.year_of = self.df.groupby("lop_so")["nam_hoc"].first().to_dict()
        # ---- bảng theo mốc (HK1 / HK2 / Cả năm)
        self.P = []
        for p in data_periods(self.df_all):
            q = dict(p)
            q["kind"] = "year" if p["ky"] == 0 else "semester"
            q["label"] = f"Cả năm lớp {p['grade']}" if p["ky"] == 0 else f"HK{p['ky']} lớp {p['grade']}"
            q["short"] = f"CN·{p['grade']}" if p["ky"] == 0 else f"HK{p['ky']}·{p['grade']}"
            self.P.append(q)
        self.PK = {p["key"]: p for p in self.P}
        self.SEM = [p for p in self.P if p["kind"] == "semester"]
        self.YEAR = [p for p in self.P if p["kind"] == "year"]
        self.SEQ = self.SEM if self.SEM else self.YEAR          # chuỗi dùng để tính xu hướng
        dfa = self.df_all.copy()
        dfa["pk"] = [f"L{int(g)}" + ("" if int(k) == 0 else f"H{int(k)}") for g, k in zip(dfa["lop_so"], dfa["ky"])]
        dfa["dtb"] = dfa[SUBJECTS].mean(axis=1)
        self.dfa = dfa
        self._rows = {k: g for k, g in dfa.groupby("pk")}
        self._models = None
        if not os.path.exists(VERSION_FILE):
            _save_json(VERSION_FILE, {"version": "ds-2026.10.1", "updated": dt.date.today().isoformat(), "records": int(len(self.df) * len(SUBJECTS)), "students": int(self.df["sid"].nunique())})
        self.version = _json_file(VERSION_FILE, {})

    @property
    def models(self):
        if self._models is None:
            self._models = load_serving()
        return self._models

    # ---- mốc thời gian
    def periods(self):
        return [{k: p[k] for k in ("key", "grade", "ky", "kind", "label", "short", "year")} for p in self.P]

    def key_of(self, key):
        """Chuẩn hóa tham số kỳ: None -> mốc gần nhất của chuỗi; 'L9' cả năm; 'L9H2' học kỳ."""
        if not key:
            return self.SEQ[-1]["key"]
        key = str(key)
        if key in self.PK:
            return key
        if key.isdigit() and f"L{key}" in self.PK:
            key = f"L{key}"
        g = re.match(r"L(\d)", key)
        if g:                                                 # mốc không có -> mốc cuối cùng của lớp đó trong chuỗi
            cands = [p["key"] for p in self.SEQ if p["grade"] == int(g.group(1))]
            if cands:
                return cands[-1]
        return self.SEQ[-1]["key"]

    def prev_key(self, key):
        fam = self.SEQ if self.PK[key]["kind"] == ("semester" if self.SEM else "year") else self.YEAR
        keys = [p["key"] for p in fam]
        i = keys.index(key) if key in keys else -1
        return keys[i - 1] if i > 0 else None

    def rows(self, key):
        return self._rows.get(key, self.dfa.iloc[0:0])

    def grade_of(self, key):
        return self.PK[self.key_of(key)]["grade"]

    def meta(self):
        last = self.SEQ[-1]["key"]
        return {"datasetVersion": self.version.get("version"), "updated": self.version.get("updated"), "threshold": THRESHOLD,
                "periods": self.periods(), "seq": [p["key"] for p in self.SEQ], "defaultPeriod": last,
                "hasSemesters": bool(self.SEM),
                "classes": sorted(self.rows(last)["lop"].unique(), key=lambda s: (len(s), s)),
                "classesByPeriod": {k: sorted(g["lop"].unique(), key=lambda s: (len(s), s)) for k, g in self._rows.items()},
                "subjects": [{"key": s, "name": SUBJECT_VN[s], "short": SHORT[s]} for s in SUBJECTS],
                "students": int(self.dfa["sid"].nunique()), "school": "Trường THCS Phú An", "showNames": bool(self.names)}

    def name(self, sid):
        return self.names.get(sid, sid)

    def _period_out(self, key):
        p = self.PK[key]
        return {"key": key, "grade": p["grade"], "ky": p["ky"], "kind": p["kind"], "label": p["label"], "short": p["short"], "year": p["year"]}

    # ---- hồ sơ học sinh
    def _class_avg(self, key, cls):
        c = self.rows(key)
        c = c[c["lop"] == cls]
        return {s: r2(c[s].mean()) for s in SUBJECTS} | {"dtb": r2(c["dtb"].mean()), "n": int(len(c)), "lop": cls}

    def profile(self, sid, t=THRESHOLD):
        if sid not in self.sid_index:
            return None
        h = self.dfa[self.dfa["sid"] == sid].set_index("pk")
        if h.empty:
            return None
        seq = self.SEQ
        val = lambda key, col: r2(h.loc[key, col]) if key in h.index else None
        ser = {s: [val(p["key"], s) for p in seq] for s in SUBJECTS}
        avgs = [val(p["key"], "dtb") for p in seq]
        have = [i for i, v in enumerate(avgs) if v is not None]
        if not have:
            return None
        last_i = have[-1]
        prev_i = have[-2] if len(have) >= 2 else None
        d_overall = r2(avgs[last_i] - avgs[prev_i]) if prev_i is not None and prev_i == last_i - 1 else None
        last_key = seq[last_i]["key"]
        last_row = h.loc[last_key]
        cavg = {k: self._class_avg(k, h.loc[k, "lop"]) for k in h.index}
        rows = []
        for s in SUBJECTS:
            tr = trend_of(ser[s], t)
            rows.append({"key": s, "name": SUBJECT_VN[s], "short": SHORT[s], "values": ser[s], "classAvg": cavg[last_key][s], "trend": tr,
                         "lastDelta": next((d["d"] for d in reversed(tr["deltas"]) if d["i"] == last_i), None),
                         "cells": [val(p["key"], s) for p in self.P]})
        # thứ hạng trong lớp ở mọi mốc có dữ liệu
        ranks = []
        for p in self.P:
            if p["key"] not in h.index:
                continue
            c = self.rows(p["key"])
            c = c[c["lop"] == h.loc[p["key"], "lop"]].sort_values("dtb", ascending=False).reset_index(drop=True)
            ranks.append({"Lớp": p["label"], "Lớp học": h.loc[p["key"], "lop"], "Hạng": int(c.index[c["sid"] == sid][0]) + 1, "Sĩ số": int(len(c)),
                          "ĐTB": r2(h.loc[p["key"], "dtb"]), "Mức": LEVEL_KEY[int(h.loc[p["key"], "muc"])], "kind": p["kind"]})
        with_delta = [r for r in rows if r["lastDelta"] is not None]
        up = max(with_delta, key=lambda r: r["lastDelta"]) if with_delta else None
        dn = min(with_delta, key=lambda r: r["lastDelta"]) if with_delta else None
        vol = max(rows, key=lambda r: np.std([v for v in r["values"] if v is not None]) if sum(v is not None for v in r["values"]) >= 2 else -1)
        down_rows = [r for r in rows if r["trend"]["dir"] < 0 and r["trend"]["streak"] >= 2]
        longest_down = max(down_rows, key=lambda r: r["trend"]["streak"]) if down_rows else None
        first_i = have[0]
        missing = [r for r in rows if any(v is None for v in r["values"][first_i: last_i + 1])]
        late_start = first_i > 0
        unit = "học kỳ" if self.SEM else "năm"
        analysis = [
            {"k": f"Môn tăng nhiều nhất ({seq[last_i]['label']})", "v": up["name"] if up else "—", "d": f"{up['lastDelta']:+.1f} điểm".replace(".", ",") if up else "chưa có 2 kỳ", "tone": "positive"},
            {"k": f"Môn giảm nhiều nhất ({seq[last_i]['label']})", "v": dn["name"] if dn else "—", "d": f"{dn['lastDelta']:+.1f} điểm".replace(".", ",") if dn else "chưa có 2 kỳ", "tone": "negative"},
            {"k": f"ĐTB theo {unit}", "v": " → ".join(f"{v:.2f}".replace(".", ",") for v in avgs if v is not None), "d": f"{len(have)} {unit} có dữ liệu", "tone": "ink"},
            {"k": "Môn biến động nhất", "v": vol["name"], "d": f"độ lệch chuẩn {np.std([v for v in vol['values'] if v is not None]):.2f}".replace(".", ","), "tone": "ink"},
            {"k": "Số kỳ giảm liên tiếp", "v": f"{longest_down['trend']['streak']} kỳ · {longest_down['name']}" if longest_down else "Không có", "d": f"ngưỡng ±{t:.2f}".replace(".", ","), "tone": "negative" if longest_down else "ink"},
            {"k": "Môn thiếu dữ liệu", "v": ", ".join(r["name"] for r in missing) if missing else "Không có", "d": "thiếu kỳ trước" if missing else (f"có điểm từ {seq[first_i]['label']}" if late_start else f"đủ {len(have)} {unit}"), "tone": "warning" if missing else "ink"},
        ]
        remarks, evidence = [], []
        f1 = lambda v: f"{v:.1f}".replace(".", ",")
        sgn = lambda v: ("+" if v > 0 else "−" if v < 0 else "±") + f"{abs(v):.1f}".replace(".", ",")
        for r in rows:
            tr = r["trend"]
            if tr["streak"] >= 2:
                a_, b_ = r["values"][last_i - tr["streak"]], r["values"][last_i]
                if tr["dir"] > 0:
                    remarks.append(f"Điểm {r['name']} tăng qua {tr['streak']} kỳ liên tiếp ({f1(a_)} → {f1(b_)}).")
                else:
                    gap = r2(b_ - r["classAvg"]) if r["classAvg"] is not None else 0
                    remarks.append(f"{r['name']} giảm trong {tr['streak']} kỳ liên tiếp ({f1(a_)} → {f1(b_)})"
                                   + (f", hiện thấp hơn ĐTB lớp {f1(-gap)} điểm" if gap < 0 else "")
                                   + f". Nên xem lại các phần kiến thức {r['name']} có kết quả thấp và theo dõi ở kỳ tiếp theo.")
                evidence.append(f"{r['name']}: " + ", ".join(sgn(d["d"]) for d in tr["deltas"][-tr["streak"]:]))
        for r in missing:
            remarks.append(f"{r['name']} thiếu điểm ở kỳ trước nên chưa đủ căn cứ để nhận xét xu hướng dài hạn của môn này.")
        if late_start:
            remarks.append(f"Học sinh có điểm từ {seq[first_i]['label']} ({len(have)} {unit}); cần ít nhất 3 kỳ để nhận xét xu hướng dài hạn.")
        if len(remarks) == len(missing) + int(late_start):
            remarks.insert(0, f"Chưa có môn nào thay đổi vượt ngưỡng ±{t:.2f} trong hai kỳ liên tiếp; kết quả nhìn chung ổn định.".replace("0.30", "0,30"))
        evidence.append(f"Ngưỡng ±{t:.2f}".replace(".", ","))
        if d_overall is not None:
            evidence.append(f"ĐTB {seq[last_i]['label']} so với {seq[last_i - 1]['label']}: {sgn(d_overall)}")
        grid = [{"key": p["key"], "grade": p["grade"], "ky": p["ky"], "kind": p["kind"], "label": p["label"], "short": p["short"],
                 "avg": val(p["key"], "dtb"), "level": LEVEL_KEY[int(h.loc[p["key"], "muc"])] if p["key"] in h.index else None} for p in self.P]
        return {
            "id": sid, "name": self.name(sid), "initials": _initials(self.name(sid)), "class": last_row["lop"], "grade": int(last_row["lop_so"]),
            "year": str(last_row["nam_hoc"]).replace("-", "–"), "level": LEVEL_KEY[int(last_row["muc"])], "conduct": LEVEL_KEY[int(last_row["ren_luyen"])],
            "absences": int(last_row["nghi_p"] + last_row["nghi_k"]), "periods": [self._period_out(p["key"]) for p in seq], "avgs": avgs, "lastIndex": last_i,
            "latestAvg": avgs[last_i], "delta": d_overall, "overall": overall_trend(d_overall, t), "threshold": t, "unit": unit,
            "subjects": rows, "classAvgByPeriod": cavg, "ranks": ranks, "analysis": analysis, "grid": grid,
            "remarks": remarks, "evidence": evidence, "strengths": advisor.strengths({s: last_row[s] for s in SUBJECTS}, self.rows(last_key)),
            "levelsByPeriod": [LEVEL_KEY[int(h.loc[p["key"], "muc"])] if p["key"] in h.index else None for p in seq],
        }

    # ---- danh sách học sinh
    def _status_rows(self, key=None, t=THRESHOLD):
        key = self.key_of(key)
        cur = self.rows(key)
        pk = self.prev_key(key)
        prev = self.rows(pk).set_index("sid") if pk else self.dfa.iloc[0:0].set_index("sid")
        n_per = self.dfa[self.dfa["pk"].isin([p["key"] for p in self.SEQ])].groupby("sid")["pk"].nunique()
        cls_avg = {c: g[SUBJECTS].mean() for c, g in cur.groupby("lop")}
        out = []
        for _, r in cur.iterrows():
            sid = r["sid"]
            p = prev.loc[sid] if sid in prev.index else None
            if isinstance(p, pd.DataFrame):
                p = p.iloc[0]
            delta = r2(r["dtb"] - p["dtb"]) if p is not None else None
            cavg = cls_avg[r["lop"]]
            strong = max(SUBJECTS, key=lambda s: (r[s] - cavg[s]) if pd.notna(r[s]) else -99)
            weak, weak_reason = None, ""
            if p is not None:
                drops = {s: r[s] - p[s] for s in SUBJECTS if pd.notna(r[s]) and pd.notna(p[s])}
                if drops:
                    w = min(drops, key=drops.get)
                    if drops[w] <= -0.5:
                        weak, weak_reason = w, f"giảm {abs(drops[w]):.1f}".replace(".", ",")
            if weak is None and p is not None:
                low = [s for s in SUBJECTS if pd.notna(r[s]) and pd.notna(p[s]) and r[s] < 6.5 and p[s] < 6.5]
                if low:
                    weak, weak_reason = min(low, key=lambda s: r[s]), "dưới 6,5 hai kỳ liền"
            reasons = []
            if p is None:
                status = "Thiếu dữ liệu"
            else:
                if delta is not None and delta <= -t:
                    reasons.append(f"ĐTB giảm {abs(delta):.2f}".replace(".", ","))
                big = sorted([s for s in SUBJECTS if pd.notna(r[s]) and pd.notna(p[s]) and r[s] - p[s] <= -1.0], key=lambda s: r[s] - p[s])
                if len(big) >= 2:
                    reasons.append(f"{len(big)} môn giảm ≥ 1,0 ({', '.join(SHORT[s] for s in big[:3])})")
                elif big and r[big[0]] - p[big[0]] <= -2.0:
                    reasons.append(f"{SUBJECT_VN[big[0]]} giảm {abs(r[big[0]] - p[big[0]]):.1f}".replace(".", ","))
                if r["dtb"] < 5.5:
                    reasons.append("ĐTB dưới 5,5")
                status = "Theo dõi" if reasons else "Bình thường"
            out.append({"id": sid, "name": self.name(sid), "initials": _initials(self.name(sid)), "class": r["lop"], "grade": int(r["lop_so"]),
                        "period": key, "avg": r2(r["dtb"]), "delta": delta, "level": LEVEL_KEY[int(r["muc"])], "strong": SUBJECT_VN[strong],
                        "weak": SUBJECT_VN[weak] if weak else None, "weakReason": weak_reason, "status": status, "reasons": reasons,
                        "nPeriods": int(n_per.get(sid, 0)), "exam": r2(r[EXAM].sum())})
        return out

    def students(self, q="", cls="", status="", sort="name", direction="asc", page=1, size=20, grade=None, period=None):
        key = self.key_of(period or (f"L{grade}" if grade else None))
        if grade and not period and self.SEM:
            key = self.key_of(f"L{grade}H2") if f"L{grade}H2" in self.PK else key
        rows = self._status_rows(key)
        if cls and cls != "all":
            rows = [r for r in rows if r["class"] == cls]
        if status and status != "all":
            rows = [r for r in rows if r["status"] == status]
        if q:
            ql = q.lower()
            rows = [r for r in rows if ql in r["id"].lower() or ql in r["name"].lower()]
        keyf = {"avg": lambda r: (r["avg"] is None, r["avg"]), "delta": lambda r: (r["delta"] is None, r["delta"] or 0), "name": lambda r: r["name"].split()[-1] + r["name"]}[sort if sort in ("avg", "delta") else "name"]
        rows.sort(key=keyf, reverse=direction == "desc")
        total = len(rows)
        start = (page - 1) * size
        pk = self.prev_key(key)
        return {"total": total, "page": page, "size": size, "pages": max(1, -(-total // size)), "items": rows[start:start + size],
                "period": self._period_out(key), "prevPeriod": self._period_out(pk) if pk else None,
                "counts": {s: sum(r["status"] == s for r in rows) for s in ("Theo dõi", "Bình thường", "Thiếu dữ liệu")}}

    # ---- tổng quan
    def overview(self, period=None, cls="", t=THRESHOLD):
        key = self.key_of(period)
        cur = self.rows(key)
        if cls and cls != "all":
            cur = cur[cur["lop"] == cls]
        pk = self.prev_key(key)
        prev = self.rows(pk).drop_duplicates("sid").set_index("sid") if pk else self.dfa.iloc[0:0].set_index("sid")
        common = cur[cur["sid"].isin(prev.index)]
        deltas = (common.set_index("sid")["dtb"] - prev.loc[common["sid"], "dtb"]).dropna()
        avg_now = cur["dtb"].mean()
        avg_prev = prev.loc[common["sid"], "dtb"].mean() if len(common) else np.nan
        n_up, n_down = int((deltas >= t).sum()), int((deltas <= -t).sum())
        risk = [r for r in self._status_rows(key, t) if (not cls or cls == "all" or r["class"] == cls) and r["status"] == "Theo dõi"]
        fam = self.SEQ if self.PK[key]["kind"] == ("semester" if self.SEM else "year") else self.YEAR
        series = []
        for p in fam:
            all_ = self.rows(p["key"])
            row = {"semester": p["short"], "all": r2(all_["dtb"].mean())}
            if cls and cls != "all":
                ids = cur["sid"]
                row["class"] = r2(all_[all_["sid"].isin(ids)]["dtb"].mean()) if all_["sid"].isin(ids).any() else None
            series.append(row)
        subj = [{"subject": SHORT[s], "name": SUBJECT_VN[s], "value": r2(cur[s].mean())} for s in SUBJECTS]
        bins = [0, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 10.01]
        labels = ["<5", "5", "5,5", "6", "6,5", "7", "7,5", "8", "8,5", "≥9"]
        hist = [{"label": labels[i], "n": int(((cur["dtb"] >= bins[i]) & (cur["dtb"] < bins[i + 1])).sum()), "low": bins[i + 1] <= 5.5} for i in range(10)]
        groups = [{"name": LEVEL_KEY[k], "n": int((cur["muc"] == k).sum())} for k in (3, 2, 1, 0)]
        classes = []
        for c, cdf in self.rows(key).groupby("lop"):
            cm = cdf[cdf["sid"].isin(prev.index)]
            dd = (cm.set_index("sid")["dtb"] - prev.loc[cm["sid"], "dtb"]) if len(cm) else pd.Series(dtype=float)
            classes.append({"id": c, "name": c, "avg": r2(cdf["dtb"].mean()), "up": int((dd >= t).sum()), "down": int((dd <= -t).sum()), "n": int(len(cdf))})
        classes.sort(key=lambda x: (len(x["name"]), x["name"]))
        d_school = r2(avg_now - avg_prev) if not np.isnan(avg_prev) else None
        low_subjects = [s["name"] for s in subj if s["value"] is not None and s["value"] <= cur[SUBJECTS].mean().mean() - t]
        summary = (f"So với {self.PK[pk]['label']}: {n_up} bạn tiến bộ rõ rệt, {n_down} bạn đang đi xuống" if pk else f"{self.PK[key]['label']} là kỳ đầu tiên có dữ liệu")
        summary += (f"; môn cần đỡ: {', '.join(low_subjects[:2])}" if low_subjects else "") + f". Có {len(risk)} bạn thầy cô nên xem lại sớm."
        return {"period": self._period_out(key), "prevPeriod": self._period_out(pk) if pk else None, "class": cls or "all", "n": int(len(cur)),
                "kpi": {"avg": r2(avg_now), "delta": d_school, "up": n_up, "upPct": r2(100 * n_up / max(len(deltas), 1)), "down": n_down,
                        "downPct": r2(100 * n_down / max(len(deltas), 1)), "watch": len(risk), "compared": int(len(deltas))},
                "summary": summary, "series": series, "subjects": subj, "subjectAverage": r2(cur[SUBJECTS].mean().mean()), "histogram": hist,
                "lowCount": int((cur["dtb"] < 5.5).sum()), "groups": groups, "classes": classes, "risk": risk[:12], "threshold": t}

    # ---- lớp
    def class_analysis(self, cls, period=None, t=THRESHOLD):
        key = self.key_of(period)
        cur = self.rows(key)
        cur = cur[cur["lop"] == cls]
        if cur.empty:
            return None
        ids = cur["sid"]
        pk = self.prev_key(key)
        prev = self.rows(pk) if pk else self.dfa.iloc[0:0]
        prev = prev[prev["sid"].isin(ids)].drop_duplicates("sid").set_index("sid")
        cohort = self.rows(key)
        rows, drops = [], {s: 0 for s in SUBJECTS}
        for _, r in cur.iterrows():
            p = prev.loc[r["sid"]] if r["sid"] in prev.index else None
            d = r2(r["dtb"] - p["dtb"]) if p is not None else None
            dropped = [s for s in SUBJECTS if p is not None and pd.notna(r[s]) and pd.notna(p[s]) and r[s] - p[s] <= -t]
            for s in dropped:
                drops[s] += 1
            rows.append({"id": r["sid"], "name": self.name(r["sid"]), "prev": r2(p["dtb"]) if p is not None else None, "avg": r2(r["dtb"]), "delta": d,
                         "group": overall_trend(d, t), "drops": [SUBJECT_VN[s] for s in dropped], "dropKeys": dropped, "level": LEVEL_KEY[int(r["muc"])]})
        groups = {k: sum(r["group"] == k for r in rows) for k in ("up", "flat", "down", "insufficient")}
        dist = []
        for kk in ([pk] if pk else []) + [key]:
            dd = self.rows(kk)
            dd = dd[dd["sid"].isin(ids)]
            if len(dd):
                dist.append({"period": self.PK[kk]["short"], "parts": [{"name": LEVEL_KEY[k], "n": int((dd["muc"] == k).sum())} for k in (3, 2, 1, 0)]})
        subj = [{"subject": SHORT[s], "name": SUBJECT_VN[s], "prev": r2(prev[s].mean()) if len(prev) else None, "cur": r2(cur[s].mean()), "cohort": r2(cohort[s].mean())} for s in SUBJECTS]
        watch = [r for r in self._status_rows(key, t) if r["class"] == cls and r["status"] == "Theo dõi"]
        d_cls = r2(cur["dtb"].mean() - prev["dtb"].mean()) if len(prev) else None
        return {"class": cls, "period": self._period_out(key), "prevLabel": self.PK[pk]["label"] if pk and len(prev) else None,
                "n": int(len(cur)), "kpi": {"avg": r2(cur["dtb"].mean()), "prevAvg": r2(prev["dtb"].mean()) if len(prev) else None, "cohortAvg": r2(cohort["dtb"].mean()),
                                            "delta": d_cls, "deltaLabel": overall_trend(d_cls, t), "goodPct": r2(100 * (cur["muc"] >= 2).mean()), "good": int((cur["muc"] >= 2).sum()), "watch": len(watch)},
                "subjects": subj, "distribution": dist, "groups": groups, "drops": [{"key": s, "name": SUBJECT_VN[s], "n": drops[s]} for s in SUBJECTS],
                "students": sorted(rows, key=lambda r: (r["delta"] is None, r["delta"] or 0)), "threshold": t}

    # ---- dự đoán
    def prediction(self, sid, model_name=None, floor=None, margin=1.5, school=None):
        if sid not in self.sid_index or not self.models:
            return None
        name = model_name if model_name in self.models else list(self.models)[0]
        fitted = self.models[name]
        i = self.sid_index[sid]
        w = make_windows(self.X[i:i + 1], self.M[i:i + 1], self.C[i:i + 1], self.sids[i:i + 1], self.panel_periods, targets=(9,), require_target=False)
        if len(w) == 0:
            return {"id": sid, "available": False, "reason": "Học sinh chưa có điểm lớp nào trước lớp 9."}
        h = self.df[self.df["sid"] == sid]
        prior = h[h["lop_so"] < 9].sort_values("lop_so")
        ha = self.dfa[self.dfa["sid"] == sid].set_index("pk")
        in_keys = [k for k in [p["key"] for p in self.P if p["kind"] == "semester" or not self.SEM] if k in ha.index and (self.PK[k]["grade"] < 9 or self.PK[k]["ky"] == 1)]
        if in_keys:
            lr = ha.loc[in_keys[-1]]
            latest_label = self.PK[in_keys[-1]]["label"]
        elif len(prior):
            lr = prior.iloc[-1]
            latest_label = f"Cả năm lớp {int(lr['lop_so'])}"
        else:
            return {"id": sid, "available": False, "reason": "Học sinh chưa có điểm mốc nào trước lớp 9."}
        a9 = h[h["lop_so"] == 9]
        actual9 = {s: float(a9.iloc[0][s]) for s in SUBJECTS} if len(a9) else None
        if getattr(fitted, "T", None) not in (None, w.T):
            return {"id": sid, "available": False, "reason": f"Mô hình {name} được huấn luyện với {fitted.T} mốc, dữ liệu hiện có {w.T} mốc. Hãy chạy lại scripts/train.bat."}
        try:
            reg, lo, hi, proba = fitted.predict(w)
        except Exception as e:
            return {"id": sid, "available": False, "reason": f"Mô hình {name} không khớp dữ liệu hiện tại ({type(e).__name__}); đang cần huấn luyện lại."}
        latest = {s: float(lr[s]) for s in SUBJECTS}
        ref = self.rows(in_keys[-1]) if in_keys else self.df[self.df["lop_so"] == int(lr["lop_so"])]
        g9 = self.df[self.df["lop_so"] == 9]
        if floor is None:
            floor = round(float(g9[EXAM].sum(axis=1).quantile(0.4)), 1)
            floor_source = "tạm tính: phân vị 40% tổng 3 môn lớp 9 của khóa"
        else:
            floor_source = "nhập tay / danh sách trường"
        facts = advisor.build_facts(latest, int(lr["lop_so"]), reg[0], lo[0], hi[0], None if proba is None else proba[0], ref, floor, margin, school,
                                    None, advisor.history_table(prior) if len(prior) else None, int(lr["n_cd"]))
        facts["moc_gan_nhat"] = latest_label
        occ = occlusion(fitted, w)
        att = attention_map(fitted, w)
        return {
            "id": sid, "available": True, "model": name, "models": list(self.models), "latestGrade": int(lr["lop_so"]), "latestLabel": latest_label,
            "predicted": [{"key": s, "name": SUBJECT_VN[s], "short": SHORT[s], "value": r2(reg[0][j]), "lo": r2(lo[0][j]), "hi": r2(hi[0][j]), "latest": latest[s],
                           "actual": actual9[s] if actual9 else None} for j, s in enumerate(SUBJECTS)],
            "levelProba": {LEVELS[k]: r2(proba[0][k]) for k in range(4)} if proba is not None else None,
            "actualLevel": LEVEL_KEY[int(a9.iloc[0]["muc"])] if len(a9) else None, "hasActual9": actual9 is not None,
            "facts": facts, "floor": floor, "floorSource": floor_source,
            "occlusion": [{"feature": idx[0], "period": idx[1], **{s: r2(v) for s, v in row.items()}} for idx, row in occ.iterrows()],
            "inputPeriods": list(w.periods),
            "attention": None if att is None else [{"feature": f, **{c: r2(v) for c, v in r.items()}} for f, r in att.iterrows()],
            "intervalNote": "Khoảng 90% split conformal, hiệu chỉnh trên 15% học sinh không dùng để huấn luyện.",
        }

    def message(self, sid, audience, model=None, use_llm=True, floor=None, margin=1.5, school=None):
        p = self.prediction(sid, None, floor, margin, school)
        if not p or not p.get("available"):
            return None
        facts = p["facts"]
        if use_llm and model:
            text, issues = llm.generate(facts, audience, model)
            return {"text": text, "issues": issues, "source": model}
        text = llm.template(facts, audience)
        return {"text": text, "issues": llm.check(text, facts, audience), "source": "mẫu theo luật"}

    # ---- mô hình
    def models_list(self):
        rep = os.path.join(ROOT, "reports")
        summary = pd.read_csv(os.path.join(rep, "summary.csv")) if os.path.exists(os.path.join(rep, "summary.csv")) else pd.DataFrame()
        meta = _json_file(os.path.join(ROOT, "models", "serving.json"), {})
        from e3m.models import ABLATIONS
        from e3m.pipeline import DEEP, REFERENCE
        out = []
        for _, r in summary.iterrows():
            m = r["model"]
            group = "ablation" if m in ABLATIONS else "reference" if m in REFERENCE else "deep" if m in DEEP else "other"
            out.append({"id": m, "name": m, "group": group, "served": m in meta.get("models", []), "proposed": m == meta.get("proposed"),
                        "best": m == meta.get("best"), "rmse": r3(r["RMSE_mean"]), "rmseStd": r3(r["RMSE_std"]), "mae": r3(r["MAE_mean"]), "r2": r3(r["R2_mean"]),
                        "macroF1": r3(r["MacroF1_mean"]), "acc": r3(r["Acc_mean"]), "picp": r3(r["PICP_mean"]), "mpiw": r2(r["MPIW_mean"]),
                        "examRmse": r3(r["thi_RMSE"]), "seconds": r2(r["seconds_mean"]), "status": "evaluated"})
        return out

    def model_metrics(self, model_id):
        rep = os.path.join(ROOT, "reports")
        rd = lambda n: pd.read_csv(os.path.join(rep, n)) if os.path.exists(os.path.join(rep, n)) else None
        runs, stats, wil, nem, imp = rd("metrics_runs.csv"), _json_file(os.path.join(rep, "stats.json"), {}), rd("wilcoxon.csv"), rd("nemenyi_p.csv"), rd("importance.csv")
        if runs is None or model_id not in set(runs["model"]):
            return None
        m = runs[runs["model"] == model_id]
        per_subject = [{"subject": SUBJECT_VN[s], "short": SHORT[s], "rmse": r3(m[m["target"] == s]["RMSE"].mean()), "mae": r3(m[m["target"] == s]["MAE"].mean()),
                        "picp": r3(m[m["target"] == s]["PICP"].mean())} for s in SUBJECTS]
        runs_tb = m[m["target"] == "TB"].sort_values("run")
        per_run = [{"run": r["run"], "rmse": r3(r["RMSE"]), "mae": r3(r["MAE"]), "macroF1": r3(r["MacroF1"]), "picp": r3(r["PICP"])} for _, r in runs_tb.iterrows()]
        rank = stats.get("avg_rank", {}).get(model_id)
        wil_rows = [] if wil is None else [{"vs": r["so_voi"], "maeProposed": r3(r["MAE_de_xuat"]), "maeOther": r3(r["MAE_doi_thu"]), "diff": r3(r["chenh_lech"]),
                                             "pStudent": round(float(r["p_hoc_sinh"]), 4) if r["p_hoc_sinh"] >= 0.0001 else "<0,0001", "pBlock": None if pd.isna(r["p_khoi"]) else round(float(r["p_khoi"]), 4)} for _, r in wil.iterrows()]
        importance = None
        if imp is not None and model_id in set(imp["model"]):
            ii = imp[(imp["model"] == model_id) & (imp["target"] == "TB")]
            importance = [{"feature": r["feature"], "period": str(r["period"]) if "period" in ii else f"Lớp {int(r['grade'])}", "value": r3(r["delta_rmse"])} for _, r in ii.iterrows()]
        w_all = make_windows(self.X, self.M, self.C, self.sids, self.panel_periods)
        n_windows = int((w_all.g == 9).sum())
        return {"id": model_id, "task": "Hồi quy đa đầu ra 8 môn lớp 9 + phân mức kết quả học tập (Tốt/Khá/Đạt/Chưa đạt)",
                "card": {"inputs": f"Lưới 11 hàng (8 môn + rèn luyện + nghỉ có phép + nghỉ không phép) × {w_all.T} mốc ({', '.join(w_all.periods)}); ô khuyết dùng mặt nạ",
                         "split": "Kiểm định chéo 5 lần theo lớp, 3 hạt giống; trong mỗi lần: 70% huấn luyện / 15% dừng sớm / 15% hiệu chỉnh conformal; chia theo học sinh",
                         "selection": "RMSE trung bình 8 môn trên cửa sổ mục tiêu lớp 9 ngoài tập huấn luyện", "datasetVersion": self.version.get("version"),
                         "checkpoint": f"models/{model_id}.pkl" if os.path.exists(os.path.join(ROOT, "models", f"{model_id}.pkl")) else None, "seeds": "0, 1, 2",
                         "evalWindows": n_windows, "trainWindows": int(len(w_all)), "inputPeriods": list(w_all.periods)},
                "perSubject": per_subject, "perRun": per_run, "avgRank": r2(rank), "friedman": {k: stats.get(k) for k in ("friedman_chi2", "friedman_p", "nemenyi_cd", "n_blocks")},
                "wilcoxon": wil_rows, "nemenyi": None if nem is None else {"models": list(nem.columns[1:]), "rows": nem.values.tolist()}, "importance": importance,
                "hidden": [{"metric": "Confusion matrix / ROC-AUC / ECE", "reason": "Đầu phân mức được huấn luyện đa nhiệm nhưng xác suất từng lần chạy chưa được lưu; chỉ có Macro-F1 và Acc trung bình."},
                           {"metric": "Loss theo epoch", "reason": "Chưa ghi nhật ký huấn luyện theo epoch trong lần thực nghiệm này."}]}

    # ---- trường THPT / điểm chuẩn
    def schools(self):
        if not os.path.exists(SCHOOLS_FILE):
            return []
        d = pd.read_csv(SCHOOLS_FILE)
        for c in SCHOOL_COLS:
            if c not in d.columns:
                d[c] = "" if c != "diem_san" else np.nan
        d = d.dropna(subset=["diem_san"])
        return [{"id": str(r["id"]) if str(r["id"]) not in ("", "nan") else f"S{i}", "name": r["truong"], "year": str(r["nam"]), "method": r["phuong_thuc"] or "Thi tuyển 3 môn",
                 "cut": float(r["diem_san"]), "type": r["loai_hinh"] or "Công lập", "source": r["nguon"] or ""} for i, (_, r) in enumerate(d.iterrows())]

    def add_school(self, item):
        rows = self.schools()
        rows.append({"id": uuid.uuid4().hex[:8], **item})
        pd.DataFrame([{"id": r["id"], "truong": r["name"], "nam": r["year"], "phuong_thuc": r["method"], "diem_san": r["cut"], "loai_hinh": r["type"], "nguon": r["source"]} for r in rows]).to_csv(SCHOOLS_FILE, index=False, encoding="utf-8-sig")
        return rows

    def delete_school(self, sid):
        rows = [r for r in self.schools() if r["id"] != sid]
        pd.DataFrame([{"id": r["id"], "truong": r["name"], "nam": r["year"], "phuong_thuc": r["method"], "diem_san": r["cut"], "loai_hinh": r["type"], "nguon": r["source"]} for r in rows], columns=SCHOOL_COLS).to_csv(SCHOOLS_FILE, index=False, encoding="utf-8-sig")
        return rows

    # ---- báo cáo
    def create_report(self, scope, target, sections, fmt, created_by="GV"):
        rid = f"RP-{dt.date.today().year}-{uuid.uuid4().hex[:4].upper()}"
        rep = {"id": rid, "scope": scope, "target": target, "sections": sections, "format": fmt, "createdBy": created_by, "createdAt": dt.datetime.now().isoformat(timespec="seconds"),
               "datasetVersion": self.version.get("version"), "dataDate": self.version.get("updated"), "school": "Trường THCS Phú An"}
        if scope == "student":
            prof = self.profile(target)
            rep["data"] = {"profile": prof}
            if sections.get("prediction"):
                rep["data"]["prediction"] = self.prediction(target)
        elif scope == "class":
            rep["data"] = {"class": self.class_analysis(target)}
        elif scope == "period":
            rep["data"] = {"overview": self.overview(target)}
        else:
            rep["data"] = {"overview": self.overview(None)}
        _save_json(os.path.join(REPORTS_DIR, f"{rid}.json"), rep)
        return rep

    def list_reports(self):
        if not os.path.isdir(REPORTS_DIR):
            return []
        out = []
        for f in sorted(os.listdir(REPORTS_DIR), reverse=True):
            r = _json_file(os.path.join(REPORTS_DIR, f), {})
            out.append({k: r.get(k) for k in ("id", "scope", "target", "format", "createdBy", "createdAt", "datasetVersion")})
        return out

    def get_report(self, rid):
        p = os.path.join(REPORTS_DIR, f"{rid}.json")
        return _json_file(p, None) if os.path.exists(p) else None

    # ---- nhập dữ liệu
    def schema(self):
        req = [("STT", "số", True), ("Mã học sinh", "số/chuỗi", True), ("Họ và tên", "chuỗi", True), ("Ngày sinh", "dd/mm/yyyy", False)]
        sub = [(h, "điểm 0–10", True) for h in ("Toán", "LS&ĐL", "KHTN", "Tin", "Văn", "Ng.ngữ", "GDCD", "C.nghệ")]
        rest = [("GDTC / Nghệ thuật / NDGDCĐP / HĐTN&HN", "Đ / CĐ", False), ("Kết quả học tập", "Tốt/Khá/Đạt/Chưa đạt", True), ("Kết quả rèn luyện", "Tốt/Khá/Đạt/Chưa đạt", True), ("Buổi nghỉ (P, K)", "số", False)]
        return [{"col": c, "type": t, "required": r} for c, t, r in req + sub + rest]

    def dictionary(self):
        d = self.df
        n = len(d)
        rows = [{"field": "sid", "desc": "Mã học sinh ẩn danh (băm một chiều từ mã trong sổ điểm)", "missing": 0.0},
                {"field": "lop_so / nam_hoc / lop", "desc": "Lớp (6–9), năm học, lớp học", "missing": 0.0}]
        rows += [{"field": s, "desc": f"Điểm TB cả năm môn {SUBJECT_VN[s]}", "missing": r2(100 * d[s].isna().mean())} for s in SUBJECTS]
        rows += [{"field": "muc", "desc": "Mức kết quả học tập theo Thông tư 22", "missing": 0.0}, {"field": "ren_luyen", "desc": "Kết quả rèn luyện", "missing": 0.0},
                 {"field": "nghi_p / nghi_k", "desc": "Số buổi nghỉ có phép / không phép", "missing": 0.0},
                 {"field": "ket_qua_tuyen_sinh_10", "desc": "Nhãn kết quả thi tuyển sinh lớp 10 (chưa có trong dataset)", "missing": 100.0}]
        return rows

    def import_preview(self, path, filename):
        import xlrd
        from e3m.data import _read_sheet
        issues, rows_all, sheets = [], [], 0
        m = re.search(r"KHOI\s*(\d)", filename, re.I)
        y = re.search(r"(\d{2})-(\d{2})", filename)
        grade = int(m.group(1)) if m else None
        year = f"20{y.group(1)}-20{y.group(2)}" if y else None
        try:
            wb = xlrd.open_workbook(path, ignore_workbook_corruption=True)
        except Exception as e:
            return {"ok": False, "issues": [{"kind": "Lỗi", "title": "Không đọc được tệp", "detail": str(e)[:200]}], "schema": [], "preview": [], "valid": 0, "invalid": 0, "warnings": 0}
        from e3m.data import sheet_info
        ky = 0
        for sh in wb.sheets():
            g0, y0, ky = sheet_info(sh, filename)
            grade, year = grade or g0, year or y0
            break
        if grade is None or year is None:
            issues.append({"kind": "Lỗi", "title": "Không xác định được lớp / năm học", "detail": "Tiêu đề sheet cần có 'Khối N' và 'NĂM HỌC yyyy - yyyy' (hoặc tên tệp dạng 'KHOI 7-23-24.xls')."})
        schema_result = []
        header_seen = set()
        for sh in wb.sheets():
            try:
                hr = next(r for r in range(min(sh.nrows, 15)) if str(sh.cell_value(r, 0)).strip() == "STT")
            except StopIteration:
                issues.append({"kind": "Cảnh báo", "title": f"Sheet {sh.name} không có bảng điểm", "detail": "Không tìm thấy dòng tiêu đề bắt đầu bằng 'STT'; sheet bị bỏ qua."})
                continue
            header_seen |= {str(c).strip() for c in sh.row_values(hr)}
            sheets += 1
            rows_all += [dict(r, _sheet=sh.name) for r in _read_sheet(sh, grade or 0, year or "", ky)]
        for s in self.schema():
            cols = [c.strip() for c in s["col"].split("/")] if "/" in s["col"] else [s["col"]]
            found = any(any(h.startswith(c) for h in header_seen) for c in cols) if s["col"] != "Buổi nghỉ (P, K)" else "Buổi nghỉ" in header_seen
            schema_result.append({**s, "found": found})
            if s["required"] and not found:
                issues.append({"kind": "Lỗi", "title": f"Thiếu cột '{s['col']}'", "detail": "Cột bắt buộc không có trong bất kỳ sheet nào."})
        valid, invalid, warn = [], [], 0
        existing = set(zip(self.df_all["sid"], self.df_all["lop_so"], self.df_all["ky"]))
        import hashlib
        for i, r in enumerate(rows_all):
            note = []
            if any(pd.isna(r.get(s)) for s in ("Toan", "Van", "NgoaiNgu")):
                note.append("thiếu điểm môn thi")
            if pd.isna(r.get("muc")):
                note.append("thiếu mức kết quả học tập")
            if any(isinstance(r.get(s), float) and not pd.isna(r.get(s)) and not 0 <= r.get(s) <= 10 for s in SUBJECTS):
                note.append("điểm ngoài 0–10")
            sid = "HS-" + hashlib.sha256(f"e3m|{r['_ma']}".encode()).hexdigest()[:8].upper()
            dup = (sid, grade, ky) in existing
            if dup:
                warn += 1
            (invalid if note else valid).append({"row": i + 1, "sheet": r["_sheet"], "id": sid, "name": r["_ten"], "class": r["lop"], "grade": grade, "year": year,
                                                  "toan": r.get("Toan"), "van": r.get("Van"), "anh": r.get("NgoaiNgu"), "muc": r.get("muc"), "note": "; ".join(note), "dup": dup})
        preview = (valid[:8] + invalid[:12])
        return {"ok": not any(x["kind"] == "Lỗi" for x in issues), "file": filename, "size": os.path.getsize(path), "sheets": sheets, "rows": len(rows_all), "grade": grade, "year": year, "ky": ky, "kyLabel": {0: "Cả năm", 1: "HK1", 2: "HK2"}[ky],
                "valid": len(valid), "invalid": len(invalid), "warnings": warn, "issues": issues, "schema": schema_result,
                "preview": [{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in p.items()} for p in preview],
                "overwrite": sum(v["dup"] for v in valid), "newRecords": len(valid) - sum(v["dup"] for v in valid)}

    def import_confirm(self, path, filename, preview, created_by="GV"):
        dest = os.path.join(RAW_DIR, filename)
        if os.path.exists(dest):
            bak = os.path.join(OUT_DIR, "backup", f"{dt.datetime.now():%Y%m%d-%H%M%S}-{filename}")
            os.makedirs(os.path.dirname(bak), exist_ok=True)
            shutil.copy2(dest, bak)
        shutil.copy2(path, dest)
        build()
        old = self.version.get("version", "ds-2026.10.0")
        m = re.match(r"ds-(\d{4})\.(\d{2})\.(\d+)", old)
        today = dt.date.today()
        new_version = f"ds-{today.year}.{today.month:02d}.{(int(m.group(3)) + 1) if m and m.group(1) == str(today.year) and int(m.group(2)) == today.month else 1}"
        self.reload()
        _save_json(VERSION_FILE, {"version": new_version, "updated": today.isoformat(), "records": int(len(self.df) * len(SUBJECTS)), "students": int(self.df["sid"].nunique())})
        self.version = _json_file(VERSION_FILE, {})
        hist = _json_file(HISTORY_FILE, [])
        hist.insert(0, {"version": new_version, "file": filename, "valid": preview.get("valid"), "invalid": preview.get("invalid"), "by": created_by,
                        "at": dt.datetime.now().isoformat(timespec="seconds"), "status": "Đã nhập", "note": "Mô hình cần huấn luyện lại (scripts/train.bat)"})
        _save_json(HISTORY_FILE, hist)
        return {"version": new_version, "students": int(self.df["sid"].nunique()), "records": int(len(self.df) * len(SUBJECTS))}

    def import_history(self):
        return _json_file(HISTORY_FILE, [])


def _initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return "HS"
    return (parts[-2][0] + parts[-1][0]).upper() if len(parts) >= 2 else parts[-1][:2].upper()
