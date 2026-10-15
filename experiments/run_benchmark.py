"""Thực nghiệm so sánh các mô hình trong đề cương trên dữ liệu theo dõi dọc lớp 6 -> 9 (Bản 1 — luận văn).

Chạy:  python experiments/run_benchmark.py              (chạy tiếp phần còn thiếu)
       python experiments/run_benchmark.py --fresh      (chạy lại từ đầu)
       python experiments/run_benchmark.py --models MLP XGBoost
       python experiments/run_benchmark.py --report-only

Kịch bản: kiểm định chéo 5 lần theo lớp (GroupKFold, mọi cửa sổ của một học sinh ở cùng một lần gập),
lặp với 3 hạt giống. Chỉ các cửa sổ mục tiêu lớp 9 được dùng để đánh giá.
Kết quả ghi vào reports/, mô hình phục vụ demo ghi vào models/.
"""
from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import GroupKFold

from e3m.data import ROOT, STATIC_VN, SUBJECT_VN, SUBJECTS, load, to_panel
from e3m.models import ABLATIONS, TORCH_MODELS
from e3m.pipeline import DEEP, PROPOSED, REFERENCE, ROWS, Windows, evaluate, fit_conformal, make_windows

RES = os.path.join(ROOT, "reports")
ART = os.path.join(ROOT, "models")
METRICS = os.path.join(RES, "metrics_runs.csv")
PREDS = os.path.join(RES, "predictions.csv")
SEEDS = [0, 1, 2]
EVAL_GRADE = 9


def windows_all() -> tuple[Windows, np.ndarray]:
    X, M, C, sids, info, pers = to_panel(load())
    w = make_windows(X, M, C, sids, pers)
    groups = info.set_index("sid").loc[w.sid, "lop"].values          # lớp gần nhất của học sinh
    return w, groups


def scenarios(w: Windows, groups):
    for k, (tr, te) in enumerate(GroupKFold(5).split(w.sid, groups=groups)):
        test = w[te]
        for seed in SEEDS:
            yield f"cv{k}_s{seed}", seed, w[tr], test[test.g == EVAL_GRADE]


def run(models, fresh=False):
    os.makedirs(RES, exist_ok=True)
    w, groups = windows_all()
    done = pd.read_csv(METRICS) if os.path.exists(METRICS) and not fresh else pd.DataFrame(columns=["model", "run"])
    if fresh and os.path.exists(PREDS):
        os.remove(PREDS)
    for name in models:
        for run_id, seed, tr, te in scenarios(w, groups):
            if ((done["model"] == name) & (done["run"] == run_id)).any():
                continue
            t0 = time.time()
            try:
                fitted = fit_conformal(name, tr, seed=seed)
                rows, reg = evaluate(fitted, te)
            except Exception as e:  # mô hình ngoài (TabPFN, TabNet) có thể thiếu trọng số / thư viện
                print(f"[BỎ QUA] {name} {run_id}: {type(e).__name__}: {str(e)[:200]}", flush=True)
                break
            new = pd.DataFrame(rows).assign(run=run_id)
            done = pd.concat([done, new], ignore_index=True)
            done.to_csv(METRICS, index=False, encoding="utf-8-sig")
            p = pd.DataFrame(reg, columns=[f"pred_{s}" for s in SUBJECTS]).assign(sid=te.sid, model=name, run=run_id)
            p.to_csv(PREDS, mode="a", header=not os.path.exists(PREDS), index=False, encoding="utf-8-sig")
            tb = rows[-1]
            print(f"{name:28s} {run_id:8s} RMSE={tb['RMSE']:.3f} MAE={tb['MAE']:.3f} R2={tb['R2']:.3f} "
                  f"PICP={tb['PICP']:.3f} F1={tb['MacroF1']:.3f}  ({time.time() - t0:.0f}s)", flush=True)
    return w, done


# ----------------------------------------------------------------------------- kiểm định thống kê
def statistics(w: Windows, metrics):
    cv = metrics[metrics["target"].isin(SUBJECTS)]
    main = [m for m in DEEP + REFERENCE if m in set(cv["model"])]
    piv = cv[cv["model"].isin(main)].pivot_table(index=["run", "target"], columns="model", values="RMSE")[main].dropna()
    out = {"n_blocks": int(len(piv)), "models": main}
    if len(main) >= 3 and len(piv) >= 3:
        fr = stats.friedmanchisquare(*[piv[m].values for m in main])
        ranks = piv.rank(axis=1).mean().sort_values()
        k, n = len(main), len(piv)
        q05 = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164,
               11: 3.219, 12: 3.268}[k]
        out.update(friedman_chi2=float(fr.statistic), friedman_p=float(fr.pvalue),
                   avg_rank=ranks.round(3).to_dict(), nemenyi_cd=float(q05 * np.sqrt(k * (k + 1) / (6 * n))))
        import scikit_posthocs as sp
        nem = sp.posthoc_nemenyi_friedman(piv.values)
        nem.index = nem.columns = main
        nem.round(4).to_csv(os.path.join(RES, "nemenyi_p.csv"), encoding="utf-8-sig")
    # Wilcoxon từng cặp trên sai số tuyệt đối trung bình (8 môn, các hạt giống) của từng học sinh lớp 9
    truth = pd.DataFrame(w.y, columns=SUBJECTS).assign(sid=w.sid)[w.g == EVAL_GRADE]
    pred = pd.read_csv(PREDS).merge(truth, on="sid")
    pred["abs_err"] = np.mean([np.abs(pred[f"pred_{s}"] - pred[s]) for s in SUBJECTS], axis=0)
    err = pred.groupby(["sid", "model"])["abs_err"].mean().unstack()
    rows = []
    for m in [c for c in err.columns if c != PROPOSED and PROPOSED in err and c in main]:
        pair = err[[PROPOSED, m]].dropna()
        wt = stats.wilcoxon(pair[PROPOSED], pair[m])
        blk = piv[[PROPOSED, m]] if m in piv and PROPOSED in piv else None
        wb = stats.wilcoxon(blk[PROPOSED], blk[m]) if blk is not None and len(blk) > 5 and (blk[PROPOSED] != blk[m]).any() else None
        rows.append(dict(so_voi=m, MAE_de_xuat=pair[PROPOSED].mean(), MAE_doi_thu=pair[m].mean(),
                         chenh_lech=pair[PROPOSED].mean() - pair[m].mean(), p_hoc_sinh=wt.pvalue,
                         p_khoi=wb.pvalue if wb else np.nan, n=len(pair)))
    pd.DataFrame(rows).to_csv(os.path.join(RES, "wilcoxon.csv"), index=False, encoding="utf-8-sig")
    json.dump(out, open(os.path.join(RES, "stats.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return out


def summary(metrics):
    cols = ["RMSE", "MAE", "R2", "MacroF1", "Acc", "PICP", "MPIW", "seconds"]
    tb = metrics[metrics["target"] == "TB"].groupby("model")[cols].agg(["mean", "std"])
    tb.columns = [f"{a}_{b}" for a, b in tb.columns]
    ex = metrics[metrics["target"] == "TB_thi"].groupby("model")[["RMSE", "MAE", "R2"]].mean().add_prefix("thi_")
    s = tb.join(ex).sort_values("RMSE_mean").reset_index()
    s.to_csv(os.path.join(RES, "summary.csv"), index=False, encoding="utf-8-sig")
    return s


# ----------------------------------------------------------------------------- báo cáo markdown
def report(metrics, s, st):
    """Ghi reports/BAO_CAO_KET_QUA.md: các bảng số liệu dùng thẳng cho Chương 4."""
    f = lambda v, d=3: "–" if pd.isna(v) else f"{v:.{d}f}".replace(".", ",")
    group = lambda m: "Đề xuất" if m == PROPOSED else "Tham chiếu" if m in REFERENCE else "Loại bỏ thành phần" if m in ABLATIONS else "Học sâu"
    n_runs = metrics["run"].nunique()
    w0 = windows_all()[0]
    L = ["# Kết quả thực nghiệm (tự sinh từ reports/)", "",
         f"Bài toán: từ {w0.T} mốc điểm ({', '.join(w0.periods)}; 8 môn, kết quả rèn luyện, số buổi nghỉ) dự đoán điểm "
         "trung bình cả năm lớp 9 của 8 môn và mức kết quả học tập lớp 9. Thang điểm 10. "
         f"Kiểm định chéo 5 lần theo lớp × {len(SEEDS)} hạt giống = {n_runs} lần chạy; trung bình ± độ lệch chuẩn giữa các lần chạy.", "",
         "## Bảng 1. So sánh mô hình (trung bình 8 môn, và riêng 3 môn thi Toán – Văn – Anh)", "",
         "| Mô hình | Nhóm | RMSE | MAE | R² | Macro-F1 | Acc | PICP | MPIW | RMSE 3 môn thi | MAE 3 môn thi | Thời gian (s) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in s[~s["model"].isin(ABLATIONS)].iterrows():
        L.append(f"| {r.model} | {group(r.model)} | {f(r.RMSE_mean)} ± {f(r.RMSE_std)} | {f(r.MAE_mean)} ± {f(r.MAE_std)} | {f(r.R2_mean)} | "
                 f"{f(r.MacroF1_mean)} | {f(r.Acc_mean)} | {f(r.PICP_mean)} | {f(r.MPIW_mean, 2)} | {f(r.thi_RMSE)} | {f(r.thi_MAE)} | {f(r.seconds_mean, 1)} |")
    per = metrics[metrics["target"].isin(SUBJECTS) & ~metrics["model"].isin(ABLATIONS)].pivot_table(index="model", columns="target", values="RMSE")
    L += ["", "## Bảng 2. RMSE theo từng môn", "", "| Mô hình | " + " | ".join(SUBJECT_VN[x] for x in SUBJECTS) + " |", "|---|" + "---|" * len(SUBJECTS)]
    for m in s[~s["model"].isin(ABLATIONS)]["model"]:
        L.append(f"| {m} | " + " | ".join(f(per.loc[m, x]) for x in SUBJECTS) + " |")
    ab = s[s["model"].isin(list(ABLATIONS) + [PROPOSED])]
    if len(ab) > 1:
        base = ab.loc[ab["model"] == PROPOSED, "RMSE_mean"].iloc[0]
        L += ["", "## Bảng 3. Loại bỏ thành phần của XEdu-KANFormer", "", "| Biến thể | RMSE | ΔRMSE | MAE | Macro-F1 | RMSE 3 môn thi |", "|---|---|---|---|---|---|"]
        for _, r in ab.iterrows():
            L.append(f"| {r.model} | {f(r.RMSE_mean)} ± {f(r.RMSE_std)} | {r.RMSE_mean - base:+.3f} | {f(r.MAE_mean)} | {f(r.MacroF1_mean)} | {f(r.thi_RMSE)} |")
    if "friedman_p" in st:
        L += ["", "## Kiểm định thống kê", "",
              f"Friedman trên {st['n_blocks']} khối (lần chạy × môn), {len(st['models'])} mô hình: χ² = {f(st['friedman_chi2'], 2)}, p = {st['friedman_p']:.2e}. "
              f"Khoảng cách tới hạn Nemenyi (α = 0,05): {f(st['nemenyi_cd'], 2)}.", "",
              "| Mô hình | Hạng trung bình |", "|---|---|"] + [f"| {m} | {f(r, 2)} |" for m, r in sorted(st["avg_rank"].items(), key=lambda kv: kv[1])]
    wp = os.path.join(RES, "wilcoxon.csv")
    if os.path.exists(wp):
        wdf = pd.read_csv(wp)
        L += ["", f"## Bảng 4. Wilcoxon: {PROPOSED} so với từng mô hình", "",
              "| So với | MAE đề xuất | MAE đối thủ | Chênh lệch | p (theo học sinh) | p (theo khối) |", "|---|---|---|---|---|---|"]
        L += [f"| {r.so_voi} | {f(r.MAE_de_xuat)} | {f(r.MAE_doi_thu)} | {r.chenh_lech:+.3f} | {r.p_hoc_sinh:.4f} | {f(r.p_khoi, 4)} |" for _, r in wdf.iterrows()]
        L += ["", "Chênh lệch âm: mô hình đề xuất sai số thấp hơn. p theo học sinh: Wilcoxon trên sai số tuyệt đối trung bình của từng học sinh lớp 9 "
              "(dự đoán ngoài tập huấn luyện); p theo khối: Wilcoxon trên RMSE của các khối (lần chạy × môn)."]
    open(os.path.join(RES, "BAO_CAO_KET_QUA.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")


# ----------------------------------------------------------------------------- mô hình phục vụ + độ quan trọng
def permutation_importance(fitted, test: Windows, n_rep=5):
    """Độ quan trọng hoán vị theo từng ô (hàng × lớp): RMSE tăng bao nhiêu khi xáo trộn ô đó giữa các học sinh."""
    base = fitted.predict(test)[0]
    rmse0 = np.sqrt(((base - test.y) ** 2).mean(0))
    rows, rng = [], np.random.RandomState(0)
    for i, row in enumerate(ROWS):
        for t in range(test.T):
            if test.m[:, i, t].sum() < 10:
                continue
            d = np.zeros(len(SUBJECTS))
            for _ in range(n_rep):
                sh = test[np.arange(len(test))]
                perm = rng.permutation(len(sh))
                sh.xs = sh.xs.copy(); sh.m = sh.m.copy()
                sh.xs[:, i, t], sh.m[:, i, t] = sh.xs[perm, i, t], sh.m[perm, i, t]
                d += np.sqrt(((fitted.predict(sh)[0] - test.y) ** 2).mean(0)) - rmse0
            name = SUBJECT_VN.get(row, STATIC_VN.get(row))
            rows += [dict(model=fitted.name, feature=name, period=test.periods[t], target=s, delta_rmse=v / n_rep) for s, v in zip(SUBJECTS, d)]
            rows.append(dict(model=fitted.name, feature=name, period=test.periods[t], target="TB", delta_rmse=float(d.mean() / n_rep)))
    return rows


def export_serving(w: Windows, groups, s):
    """Huấn luyện lại trên toàn bộ cửa sổ cho bản demo; độ quan trọng tính trên lần gập đầu tiên."""
    os.makedirs(ART, exist_ok=True)
    best = s["model"].iloc[0]
    names = list(dict.fromkeys([PROPOSED, best]))
    tr_i, te_i = next(GroupKFold(5).split(w.sid, groups=groups))
    te = w[te_i]
    imp = []
    for name in names:
        n_rep = 5 if name in TORCH_MODELS else 1          # TabPFN / TabNet dự đoán chậm
        imp += permutation_importance(fit_conformal(name, w[tr_i]), te[te.g == EVAL_GRADE], n_rep=n_rep)
        fitted = fit_conformal(name, w, seed=0)
        if hasattr(fitted.model, "net"):
            fitted.model.net.cpu()
        try:
            pickle.dump(fitted, open(os.path.join(ART, f"{name}.pkl"), "wb"))
        except Exception as e:
            print(f"Không lưu được {name}: {e}", flush=True)
            continue
        print("Đã lưu mô hình phục vụ:", name, "q̂ =", np.round(fitted.q, 2), flush=True)
    pd.DataFrame(imp).to_csv(os.path.join(RES, "importance.csv"), index=False, encoding="utf-8-sig")
    json.dump({"best": best, "proposed": PROPOSED, "models": names},
              open(os.path.join(ART, "serving.json"), "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--models", nargs="*", default=REFERENCE + DEEP + list(ABLATIONS))
    ap.add_argument("--no-serving", action="store_true")
    ap.add_argument("--report-only", action="store_true", help="Không huấn luyện, chỉ tính lại bảng và kiểm định")
    ap.add_argument("--serving-only", action="store_true", help="Chỉ huấn luyện lại mô hình phục vụ demo từ summary.csv")
    a = ap.parse_args()
    if a.serving_only:
        w, groups = windows_all()
        s = pd.read_csv(os.path.join(RES, "summary.csv"))
        export_serving(w, groups, s[~s["model"].isin(ABLATIONS)])
        sys.exit(0)
    if a.report_only:
        w, groups = windows_all()
        metrics = pd.read_csv(METRICS)
    else:
        w, metrics = run(a.models, a.fresh)
        groups = windows_all()[1]
    s = summary(metrics)
    print(s[["model", "RMSE_mean", "MAE_mean", "R2_mean", "MacroF1_mean", "PICP_mean", "thi_RMSE"]].round(3).to_string())
    st = statistics(w, metrics)
    report(metrics, s, st)
    print(json.dumps(st, ensure_ascii=False)[:600])
    if not a.no_serving and not a.report_only:
        export_serving(w, groups, s[~s["model"].isin(ABLATIONS)])
