"""Cửa sổ huấn luyện, chuẩn hóa, bộ bọc mô hình (Predictor), conformal tách tập và chỉ số đánh giá.

Mẫu học = (lưới điểm các mốc trước, cả năm của lớp mục tiêu). Mốc thời gian lấy từ dữ liệu (data.periods):
  - chỉ có sổ cả năm:        lớp 6 -> lớp 7; lớp 6, 7 -> lớp 8; lớp 6, 7, 8 -> lớp 9          (T = 3)
  - có sổ học kỳ:            HK1-6 ... HK1-7 -> cả năm 7; ... ; HK1-6 ... HK1-9 -> cả năm 9  (T = 7)
Các cửa sổ mục tiêu lớp 7, 8 chỉ dùng để tăng số mẫu huấn luyện; cửa sổ mục tiêu lớp 9 dùng để đánh giá.
Các mốc đầu vào của mọi cửa sổ là tiền tố của cùng một danh sách, nên vị trí (slot) của mỗi mốc cố định.
"""
from __future__ import annotations

import copy
import math
import os
import time
import warnings
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, r2_score

from .data import EXAM, STATIC, SUBJECTS, input_periods
from .models import ABLATIONS, TORCH_MODELS

N_CLASSES = 4
ALPHA = 0.10                      # khoảng dự đoán 90%
ROWS = SUBJECTS + STATIC          # 11 hàng của lưới: 8 môn + 3 đặc trưng theo năm
S_ROWS, N_SUBJ, K_STATIC = len(ROWS), len(SUBJECTS), 1
DEVICE = os.environ.get("E3M_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
TABPFN_FULL = os.environ.get("E3M_TABPFN_FULL", "1" if DEVICE == "cuda" else "0") == "1"
TABPFN_CONTEXT = 600
torch.set_num_threads(int(os.environ.get("E3M_THREADS", "2")))


# ----------------------------------------------------------------------------- cửa sổ
@dataclass
class Windows:
    xs: np.ndarray      # [N, S_ROWS, T] giá trị thô (ô khuyết = 0)
    m: np.ndarray       # [N, S_ROWS, T] mặt nạ
    st: np.ndarray      # [N, K] đặc trưng tĩnh: lớp mục tiêu
    y: np.ndarray       # [N, N_SUBJ] điểm thật năm mục tiêu (NaN nếu chưa có)
    c: np.ndarray       # [N] mức kết quả học tập năm mục tiêu (-1 nếu chưa có)
    sid: np.ndarray     # [N]
    g: np.ndarray       # [N] lớp mục tiêu
    periods: list = None  # nhãn các mốc đầu vào theo slot (vd. ["Lớp 6", "Lớp 7", "Lớp 8"] hoặc ["HK1 lớp 6", ...])

    def __len__(self):
        return len(self.sid)

    @property
    def T(self):
        return self.xs.shape[2]

    def __getitem__(self, idx):
        return Windows(self.xs[idx], self.m[idx], self.st[idx], self.y[idx], self.c[idx], self.sid[idx], self.g[idx], self.periods)


def make_windows(X, M, C, sids, periods, targets=None, require_target=True) -> Windows:
    """Tạo cửa sổ từ lưới học sinh × hàng × mốc (xem data.to_panel). `periods` là danh sách mốc của lưới."""
    grades_with_year = [p["grade"] for p in periods if p["ky"] == 0]
    if targets is None:
        targets = [g for g in grades_with_year if g > min(p["grade"] for p in periods)]
    glob_in = input_periods(periods, max(grades_with_year))          # danh sách slot chung (dài nhất)
    slot = {(p["grade"], p["ky"]): t for t, p in enumerate(glob_in)}
    col = {(p["grade"], p["ky"]): t for t, p in enumerate(periods)}
    T = len(glob_in)
    xs, ms, st, ys, cs, ss, gs = [], [], [], [], [], [], []
    for i in range(len(sids)):
        for g in targets:
            if (g, 0) not in col:
                continue
            tcn = col[(g, 0)]
            has_target = bool(M[i, :N_SUBJ, tcn].all())
            if require_target and not has_target:
                continue
            x_in = np.zeros((S_ROWS, T), np.float32)
            m_in = np.zeros((S_ROWS, T), np.float32)
            for p in input_periods(periods, g):
                k = (p["grade"], p["ky"])
                x_in[:, slot[k]] = X[i, :, col[k]]
                m_in[:, slot[k]] = M[i, :, col[k]]
            if m_in[:N_SUBJ].sum() == 0:
                continue                                   # không có mốc nào trước đó
            xs.append(x_in * m_in)
            ms.append(m_in)
            st.append([(g - 8) / 1.0])
            ys.append(X[i, :N_SUBJ, tcn] if has_target else np.full(N_SUBJ, np.nan, np.float32))
            cs.append(C[i, tcn])
            ss.append(sids[i])
            gs.append(g)
    return Windows(np.array(xs).reshape(-1, S_ROWS, T), np.array(ms).reshape(-1, S_ROWS, T), np.array(st, np.float32).reshape(-1, 1),
                   np.array(ys, np.float32).reshape(-1, N_SUBJ), np.array(cs), np.array(ss), np.array(gs), [p["label"] for p in glob_in])


# ----------------------------------------------------------------------------- chuẩn hóa
class Prep:
    """Chuẩn hóa theo tập huấn luyện trên các ô có mặt; ô khuyết giữ bằng mặt nạ, không điền giá trị giả."""

    def fit(self, w: Windows):
        v = self._raw(w)
        cnt = w.m.sum(axis=(0, 2))
        self.mu = (v * w.m).sum(axis=(0, 2)) / np.maximum(cnt, 1)
        self.sd = np.sqrt((((v - self.mu[None, :, None]) ** 2) * w.m).sum(axis=(0, 2)) / np.maximum(cnt, 1)) + 1e-6
        self.t_mu, self.t_sd = np.nanmean(w.y, 0), np.nanstd(w.y, 0) + 1e-6
        return self

    @staticmethod
    def _raw(w: Windows):
        v = w.xs.copy()
        v[:, N_SUBJ + 1:, :] = np.log1p(v[:, N_SUBJ + 1:, :])          # số buổi nghỉ: log1p
        return v

    def arrays(self, w: Windows):
        v = (self._raw(w) - self.mu[None, :, None]) / self.sd[None, :, None]
        return (v * w.m).astype(np.float32), w.m.astype(np.float32), w.st.astype(np.float32)

    def flat(self, w: Windows):
        xs, m, st = self.arrays(w)
        return np.hstack([xs.reshape(len(w), -1), m.reshape(len(w), -1), st])

    def y(self, w: Windows):
        return ((w.y - self.t_mu) / self.t_sd).astype(np.float32)

    def inv(self, y):
        return np.clip(y * self.t_sd + self.t_mu, 0, 10)


# ----------------------------------------------------------------------------- bộ bọc mô hình
class Predictor:
    name = "?"

    def fit(self, tr: Windows, va: Windows): ...
    def predict(self, w: Windows) -> tuple[np.ndarray, np.ndarray | None]: ...


class TorchPredictor(Predictor):
    def __init__(self, name, seed=0, epochs=300, patience=30, lr=2e-3, lam=0.3):
        self.name, self.seed, self.epochs, self.patience, self.lr = name, seed, epochs, patience, lr
        self.cls, kw = {**TORCH_MODELS, **ABLATIONS}[name]
        self.kw = dict(kw)
        self.lam = self.kw.pop("lam", lam)

    def _tensors(self, w):
        return [torch.from_numpy(a).to(DEVICE) for a in self.prep.arrays(w)]

    def fit(self, tr, va):
        torch.manual_seed(self.seed)
        self.prep = Prep().fit(tr)
        self.net = self.cls(S_ROWS, tr.T, K_STATIC, N_SUBJ, N_CLASSES, **self.kw).to(DEVICE)
        dev = lambda a: torch.from_numpy(a).to(DEVICE)
        X, Y, C = self._tensors(tr), dev(self.prep.y(tr)), dev(tr.c)
        Xv, Yv, Cv = self._tensors(va), dev(self.prep.y(va)), dev(va.c)
        opt = torch.optim.AdamW(self.net.parameters(), lr=self.lr, weight_decay=1e-4)
        sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=10)
        best, best_state, bad = math.inf, None, 0
        gen = torch.Generator().manual_seed(self.seed)
        for _ in range(self.epochs):
            self.net.train()
            for idx in torch.randperm(len(Y), generator=gen).to(DEVICE).split(128):
                reg, logit = self.net(*[x[idx] for x in X])
                loss = F.huber_loss(reg, Y[idx]) + self.lam * F.cross_entropy(logit, C[idx])
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.net.parameters(), 1.0)
                opt.step()
            self.net.eval()
            with torch.no_grad():
                reg, logit = self.net(*Xv)
                v = (F.huber_loss(reg, Yv) + self.lam * F.cross_entropy(logit, Cv)).item()
            sched.step(v)
            if v < best - 1e-5:
                best, best_state, bad = v, copy.deepcopy(self.net.state_dict()), 0
            else:
                bad += 1
                if bad >= self.patience:
                    break
        self.net.load_state_dict(best_state)
        self.net.eval()
        return self

    def predict(self, w):
        self.net.to(DEVICE)
        with torch.no_grad():
            reg, logit = self.net(*self._tensors(w))
        proba = F.softmax(logit, 1).cpu().numpy() if self.lam > 0 else None
        return self.prep.inv(reg.cpu().numpy()), proba

    def attention(self, w):
        """Trọng số chú ý của [CLS] lên các ô lưới (chỉ XEdu-KANFormer): [N, S_ROWS, T]."""
        self.predict(w)
        a = getattr(self.net, "last_attn", None)
        return None if a is None else a[:, :S_ROWS * w.T].reshape(len(w), S_ROWS, w.T).cpu().numpy()


class SkPredictor(Predictor):
    """Mô hình ngoài PyTorch thuần: một bộ hồi quy đa đầu ra + một bộ phân mức, cùng đặc trưng phẳng."""

    def __init__(self, name, seed=0):
        self.name, self.seed = name, seed

    def _make(self):
        s = self.seed
        if self.name == "Hồi quy tuyến tính":
            from sklearn.linear_model import LogisticRegression, Ridge
            return Ridge(alpha=1.0), LogisticRegression(max_iter=3000)
        if self.name == "XGBoost":
            from xgboost import XGBClassifier, XGBRegressor
            kw = dict(n_estimators=400, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=s)
            return XGBRegressor(**kw), XGBClassifier(**kw)
        if self.name == "TabPFN":
            from sklearn.multioutput import MultiOutputRegressor
            from tabpfn import TabPFNClassifier, TabPFNRegressor
            kw = dict(device=DEVICE, random_state=s, ignore_pretraining_limits=True)
            if not TABPFN_FULL:
                kw["n_estimators"] = 2
            return MultiOutputRegressor(TabPFNRegressor(**kw)), TabPFNClassifier(**kw)
        if self.name == "TabNet":
            from pytorch_tabnet.tab_model import TabNetClassifier, TabNetRegressor
            kw = dict(n_d=16, n_a=16, n_steps=3, seed=s, verbose=0, optimizer_params=dict(lr=2e-2), device_name=DEVICE)
            return TabNetRegressor(**kw), TabNetClassifier(**kw)
        raise KeyError(self.name)

    def fit(self, tr, va):
        if self.name == "TabPFN" and not TABPFN_FULL and len(tr) > TABPFN_CONTEXT:
            tr = tr[np.random.RandomState(self.seed).choice(len(tr), TABPFN_CONTEXT, replace=False)]
        self.prep = Prep().fit(tr)
        X, Xv = self.prep.flat(tr), self.prep.flat(va)
        Y, Yv = self.prep.y(tr), self.prep.y(va)
        self.classes = np.unique(tr.c)
        C = np.searchsorted(self.classes, tr.c)
        self.reg, self.clf = self._make()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if self.name == "TabNet":
                ok = np.isin(va.c, self.classes)
                fit_kw = dict(max_epochs=300, patience=40, batch_size=128, virtual_batch_size=64)
                self.reg.fit(X, Y, eval_set=[(Xv, Yv)], **fit_kw)
                self.clf.fit(X, C, eval_set=[(Xv[ok], np.searchsorted(self.classes, va.c[ok]))], **fit_kw)
            else:
                self.reg.fit(X, Y)
                self.clf.fit(X, C)
        return self

    def predict(self, w):
        X = self.prep.flat(w)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg = np.asarray(self.reg.predict(X)).reshape(len(w), -1)
            p = np.asarray(self.clf.predict_proba(X))
        proba = np.zeros((len(w), N_CLASSES))
        proba[:, self.classes] = p
        return self.prep.inv(reg), proba


DEEP = ["MLP", "Bi-LSTM", "TabNet", "FT-Transformer", "TabPFN", "TabKANet", "Kanformer", "XEdu-KANFormer"]
REFERENCE = ["Hồi quy tuyến tính", "XGBoost"]
PROPOSED = "XEdu-KANFormer"


def make(name, seed=0) -> Predictor:
    return TorchPredictor(name, seed) if name in TORCH_MODELS or name in ABLATIONS else SkPredictor(name, seed)


# ----------------------------------------------------------------------------- conformal + chỉ số
def conformal_q(pred_cal, y_cal, alpha=ALPHA):
    """Split conformal theo từng môn: phân vị ⌈(n+1)(1-α)⌉/n của phần dư tuyệt đối trên tập hiệu chỉnh."""
    r = np.abs(y_cal - pred_cal)
    n = len(r)
    return np.quantile(r, min(1.0, math.ceil((n + 1) * (1 - alpha)) / n), axis=0, method="higher")


def split3(w: Windows, seed, frac=(0.70, 0.15, 0.15)):
    """Chia theo học sinh (mọi cửa sổ của một học sinh ở cùng một phần)."""
    sids = np.unique(w.sid)
    rng = np.random.RandomState(seed).permutation(len(sids))
    a, b = int(frac[0] * len(sids)), int((frac[0] + frac[1]) * len(sids))
    part = {s: 0 for s in sids[rng[:a]]} | {s: 1 for s in sids[rng[a:b]]} | {s: 2 for s in sids[rng[b:]]}
    lab = np.array([part[s] for s in w.sid])
    return w[lab == 0], w[lab == 1], w[lab == 2]


class Fitted:
    """Mô hình đã huấn luyện kèm bán kính khoảng conformal q̂ cho từng môn."""

    def __init__(self, model: Predictor, q: np.ndarray, seconds: float):
        self.model, self.q, self.seconds, self.name = model, q, seconds, model.name

    def predict(self, w: Windows):
        reg, proba = self.model.predict(w)
        return reg, np.clip(reg - self.q, 0, 10), np.clip(reg + self.q, 0, 10), proba


def fit_conformal(name, train: Windows, seed=0, eval_grade=9) -> Fitted:
    tr, va, cal = split3(train, seed)
    if (cal.g == eval_grade).sum() >= 30:              # hiệu chỉnh trên đúng tầm dự đoán khi đủ mẫu
        cal = cal[cal.g == eval_grade]
    t0 = time.time()
    model = make(name, seed).fit(tr, va)
    q = conformal_q(model.predict(cal)[0], cal.y)
    f = Fitted(model, q, time.time() - t0)
    f.T, f.periods = tr.T, list(tr.periods or [])          # để nơi phục vụ kiểm tra trục thời gian khớp
    return f


def evaluate(fitted: Fitted, test: Windows) -> tuple[list[dict], np.ndarray]:
    reg, lo, hi, proba = fitted.predict(test)
    y, c = test.y, test.c
    if proba is None:
        f1 = acc = np.nan
    else:
        ch = proba.argmax(1)
        f1, acc = f1_score(c, ch, average="macro"), accuracy_score(c, ch)
    rows = []
    groups = {**{s: [j] for j, s in enumerate(SUBJECTS)}, "TB_thi": [SUBJECTS.index(s) for s in EXAM], "TB": list(range(N_SUBJ))}
    for t, cols in groups.items():
        yy, pp, ll, hh = (a[:, cols].ravel() for a in (y, reg, lo, hi))
        rows.append(dict(model=fitted.name, target=t, RMSE=mean_squared_error(yy, pp) ** 0.5,
                         MAE=mean_absolute_error(yy, pp), R2=r2_score(yy, pp),
                         PICP=float(((yy >= ll) & (yy <= hh)).mean()), MPIW=float((hh - ll).mean()),
                         MacroF1=f1, Acc=acc, seconds=fitted.seconds))
    return rows, reg
