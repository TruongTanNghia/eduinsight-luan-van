"""Giải thích dùng chung cho hai bản demo: che ô lưới (occlusion), đường phụ thuộc, chú ý của XEdu."""
from __future__ import annotations

import json
import os
import pickle

import numpy as np
import pandas as pd

from .data import ROOT, STATIC_VN, SUBJECT_VN, SUBJECTS
from .pipeline import ROWS, Windows

ART = os.path.join(ROOT, "models")
ROW_VN = {**SUBJECT_VN, **STATIC_VN}


def load_serving() -> dict:
    """Đọc các mô hình đã huấn luyện (models/*.pkl)."""
    meta_path = os.path.join(ART, "serving.json")
    if not os.path.exists(meta_path):
        return {}
    meta = json.load(open(meta_path, encoding="utf-8"))
    return {n: pickle.load(open(os.path.join(ART, f"{n}.pkl"), "rb")) for n in meta["models"]
            if os.path.exists(os.path.join(ART, f"{n}.pkl"))}


def occlusion(fitted, w: Windows) -> pd.DataFrame:
    """Đóng góp cục bộ của từng ô (hàng × lớp) với một cửa sổ: dự đoán đổi bao nhiêu khi coi ô đó là khuyết.

    Trả về bảng chỉ số (hàng, lớp) × 8 môn dự đoán; giá trị dương = ô này đang kéo dự đoán lên.
    """
    cells = [(i, t) for i in range(len(ROWS)) for t in range(w.T) if w.m[0, i, t] > 0]
    xs = np.repeat(w.xs, len(cells) + 1, axis=0)
    m = np.repeat(w.m, len(cells) + 1, axis=0)
    for k, (i, t) in enumerate(cells, start=1):
        xs[k, i, t], m[k, i, t] = 0.0, 0.0
    batch = Windows(xs, m, np.repeat(w.st, len(cells) + 1, axis=0), np.repeat(w.y, len(cells) + 1, axis=0),
                    np.repeat(w.c, len(cells) + 1), np.repeat(w.sid, len(cells) + 1), np.repeat(w.g, len(cells) + 1), w.periods)
    pred = fitted.predict(batch)[0]
    idx = pd.MultiIndex.from_tuples([(ROW_VN[ROWS[i]], w.periods[t]) for i, t in cells], names=["Đặc trưng", "Mốc"])
    return pd.DataFrame(pred[0] - pred[1:], columns=SUBJECTS, index=idx)


def dependence(fitted, ref: Windows, row: str, period: str | None = None, grid=None) -> pd.DataFrame:
    """Đường phụ thuộc: cho một ô (môn, mốc) chạy từ thấp đến cao trên "học sinh trung vị" của tập tham chiếu."""
    grid = np.linspace(3, 10, 29) if grid is None else grid
    i, t = ROWS.index(row), (ref.periods.index(period) if period else ref.T - 1)
    med = np.median(np.where(ref.m > 0, ref.xs, np.nan), axis=0)
    med = np.nan_to_num(med)[None]
    xs = np.repeat(med, len(grid), axis=0).astype(np.float32)
    xs[:, i, t] = grid
    m = np.ones_like(xs)
    w = Windows(xs, m, np.full((len(grid), 1), 1.0, np.float32), np.full((len(grid), len(SUBJECTS)), np.nan, np.float32),
                np.full(len(grid), -1), np.array(["median"] * len(grid)), np.full(len(grid), 9), ref.periods)
    return pd.DataFrame(fitted.predict(w)[0], columns=SUBJECTS).assign(x=grid)


def attention_map(fitted, w: Windows) -> pd.DataFrame | None:
    """Trọng số chú ý của [CLS] lên lưới (XEdu-KANFormer); None với mô hình khác."""
    fn = getattr(fitted.model, "attention", None)
    a = fn(w) if fn else None
    if a is None:
        return None
    df = pd.DataFrame(a[0], index=[ROW_VN[r] for r in ROWS], columns=list(w.periods))
    return df.where(pd.DataFrame(w.m[0], index=df.index, columns=df.columns) > 0)
