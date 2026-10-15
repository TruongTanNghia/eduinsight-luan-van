"""Sinh biểu đồ cho README (docs/images/charts). Chạy: python -X utf8 experiments/make_figures.py  (cần reports/ và data/processed/).

Biểu đồ cho README theo phong cách 'Sticker lớp học' (nền vàng bơ, viền đen dày, bóng đổ cứng)."""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter
from backend.core import Store
from e3m.data import SUBJECTS

OUT = os.path.join(os.getcwd(), "docs", "images", "charts")
os.makedirs(OUT, exist_ok=True)
INK, PAPER, WHITE = "#111111", "#FFF4D6", "#FFFFFF"
Y, CO, TO, MI, PI, LI, AM, MUTED, LINE = "#FFD23F", "#2B59FF", "#FF5A36", "#3DDC97", "#FF8FC7", "#B8A4FF", "#FFB020", "#5A5444", "#EADFC3"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK, "axes.linewidth": 2.5,
                     "axes.labelweight": "bold", "axes.titleweight": "bold", "xtick.color": INK, "ytick.color": INK,
                     "axes.facecolor": WHITE, "figure.facecolor": PAPER, "savefig.facecolor": PAPER})
vn = lambda d=2: FuncFormatter(lambda v, _: f"{v:.{d}f}".replace(".", ","))
c = lambda v, d=2: f"{v:.{d}f}".replace(".", ",")
SVN = {"Toan": "Toán", "Van": "Ngữ văn", "NgoaiNgu": "Tiếng Anh", "KHTN": "KHTN", "LSDL": "LS & ĐL", "GDCD": "GDCD", "CongNghe": "Công nghệ", "Tin": "Tin học"}


def frame(fig, title, sub=None):
    fig.text(0.012, 0.975, title, fontsize=17, fontweight="bold", va="top", color=INK)
    if sub:
        fig.text(0.012, 0.915, sub, fontsize=10.5, va="top", color=MUTED)


def hbar(ax, labels, vals, colors, err=None, fmt=lambda v: c(v, 3)):
    y = np.arange(len(labels))[::-1]
    ax.barh(y - 0.07, vals, height=0.62, color=INK, left=0, zorder=1, transform=ax.transData + matplotlib.transforms.ScaledTranslation(4 / 72, -4 / 72, ax.figure.dpi_scale_trans))
    ax.barh(y, vals, height=0.62, color=colors, edgecolor=INK, linewidth=2.2, zorder=2)
    if err is not None:
        ax.errorbar(vals, y, xerr=err, fmt="none", ecolor=INK, elinewidth=1.8, capsize=4, zorder=3)
    for yi, v, e in zip(y, vals, err if err is not None else [0] * len(vals)):
        ax.text(v + e + max(vals) * 0.015, yi, fmt(v), va="center", fontsize=10.5, fontweight="bold", family="DejaVu Sans Mono", zorder=4)
    ax.set_yticks(y, labels, fontweight="bold")
    ax.grid(axis="x", color=LINE, linewidth=1.2, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


S = pd.read_csv("reports/summary.csv").set_index("model")
MAIN = ["TabPFN", "XGBoost", "MLP", "TabKANet", "Kanformer", "XEdu-KANFormer", "Bi-LSTM", "FT-Transformer", "TabNet", "Hồi quy tuyến tính"]
col = lambda m: MI if m == "TabPFN" else CO if m == "XEdu-KANFormer" else Y

# 1. RMSE 10 mô hình
m = S.loc[MAIN].sort_values("RMSE_mean")
fig, ax = plt.subplots(figsize=(11, 6.2))
fig.subplots_adjust(left=0.2, right=0.96, top=0.82, bottom=0.1)
hbar(ax, m.index.tolist(), m["RMSE_mean"].values, [col(x) for x in m.index], m["RMSE_std"].values)
ax.set_xlabel("RMSE điểm cả năm lớp 9 (thấp hơn là tốt hơn) · trung bình ± độ lệch chuẩn 15 lần chạy")
ax.xaxis.set_major_formatter(vn(1))
frame(fig, "So sánh 10 thuật toán", "8 môn · đầu vào 7 học kỳ (HK1 lớp 6 → HK1 lớp 9) · GroupKFold 5 lần theo lớp × 3 hạt giống")
fig.savefig(f"{OUT}/01_rmse_10_mo_hinh.png", dpi=130); plt.close(fig)

# 2. Xếp hạng trung bình (Friedman + Nemenyi CD)
st = json.load(open("reports/stats.json", encoding="utf8"))
r = pd.Series(st["avg_rank"]).sort_values()
fig, ax = plt.subplots(figsize=(11, 5.6))
fig.subplots_adjust(left=0.2, right=0.96, top=0.8, bottom=0.12)
hbar(ax, r.index.tolist(), r.values, [col(x) for x in r.index], fmt=lambda v: c(v, 2))
best = r.iloc[0]
ax.axvspan(best, best + st["nemenyi_cd"], color=MI, alpha=0.25, zorder=0)
ax.set_xlabel(f"Hạng trung bình trên {st['n_blocks']} khối (lần chạy × môn) · vùng xanh = khoảng cách tới hạn Nemenyi CD = {c(st['nemenyi_cd'])}")
ax.xaxis.set_major_formatter(vn(0))
frame(fig, "Kiểm định Friedman: các mô hình khác nhau có ý nghĩa thống kê",
      f"χ² = {c(st['friedman_chi2'], 1)}, p < 10⁻¹⁰⁰ · mô hình nằm ngoài vùng xanh kém hơn TabPFN có ý nghĩa")
fig.savefig(f"{OUT}/02_xep_hang_friedman.png", dpi=130); plt.close(fig)

# 3. Loại bỏ thành phần
AB = ["XEdu-KANFormer", "XEdu (bỏ đa nhiệm)", "XEdu (GR-KAN → MLP)", "XEdu (bỏ token hóa KAN)", "XEdu (nhỏ: d=16, 1 khối, dropout 0.2)", "XEdu (bỏ chú ý liên môn)"]
a = S.loc[AB].sort_values("RMSE_mean")
fig, ax = plt.subplots(figsize=(11, 4.8))
fig.subplots_adjust(left=0.3, right=0.96, top=0.77, bottom=0.14)
hbar(ax, [x.replace("XEdu (nhỏ: d=16, 1 khối, dropout 0.2)", "XEdu (nhỏ: d=16, 1 khối)") for x in a.index], a["RMSE_mean"].values,
     [CO if x == "XEdu-KANFormer" else LI for x in a.index], a["RMSE_std"].values)
ax.axvline(S.loc["XEdu-KANFormer", "RMSE_mean"], color=INK, linestyle="--", linewidth=1.8)
ax.set_xlabel("RMSE (thấp hơn là tốt hơn)")
ax.set_xlim(0.5, 0.72)
ax.set_xticks(np.arange(0.5, 0.71, 0.05))
ax.xaxis.set_major_formatter(vn(2))
frame(fig, "Nghiên cứu loại bỏ thành phần của XEdu-KANFormer", "Bỏ chú ý liên môn làm sai số tăng; bỏ đầu ra đa nhiệm (λ = 0,3) lại giảm sai số rõ rệt")
fig.savefig(f"{OUT}/03_loai_bo_thanh_phan.png", dpi=130); plt.close(fig)

# 4. Độ sát thực tế (tỉ lệ lệch ≤ 0,5 / ≤ 1 điểm) cho 10 mô hình
store = Store()
acc = {mm: store.accuracy(mm) for mm in MAIN}
order = sorted(MAIN, key=lambda mm: -acc[mm]["hk2"]["w05"])
fig, axes = plt.subplots(1, 2, figsize=(13, 6.2), sharey=True)
fig.subplots_adjust(left=0.16, right=0.97, top=0.8, bottom=0.11, wspace=0.08)
for ax, key, ttl in ((axes[0], "hk2", "Điểm HK2 lớp 9"), (axes[1], "cn", "Điểm cả năm lớp 9")):
    y = np.arange(len(order))[::-1]
    w1 = [acc[mm][key]["w10"] for mm in order]; w05 = [acc[mm][key]["w05"] for mm in order]
    ax.barh(y, w1, height=0.66, color=WHITE, edgecolor=INK, linewidth=2, label="lệch ≤ 1 điểm", zorder=2)
    ax.barh(y, w05, height=0.66, color=[col(mm) for mm in order], edgecolor=INK, linewidth=2, label="lệch ≤ 0,5 điểm", zorder=3)
    for yi, a1, a5 in zip(y, w1, w05):
        ax.text(a5 - 1.5, yi, f"{c(a5, 1)}%", ha="right", va="center", fontsize=9.5, fontweight="bold", zorder=4)
        ax.text(a1 + 1, yi, f"{c(a1, 1)}%", va="center", fontsize=9.5, fontweight="bold", color=MUTED, zorder=4)
    ax.set_xlim(0, 112); ax.set_title(ttl, loc="left", fontsize=13)
    ax.grid(axis="x", color=LINE, linewidth=1.2, zorder=0)
    ax.set_xlabel("% dự đoán (học sinh × môn)")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axes[0].set_yticks(np.arange(len(order))[::-1], order, fontweight="bold")
h, l = axes[1].get_legend_handles_labels(); fig.legend(h, l, loc="upper right", bbox_to_anchor=(0.985, 0.985), ncol=2, frameon=True, edgecolor=INK, fancybox=False)
frame(fig, "Dự đoán sát thực tế đến đâu?", "502 học sinh lớp 9 · dự đoán kiểm định chéo (mô hình chưa thấy điểm lớp 9 của em đó) · HK2 = (3 × Cả năm − HK1)/2")
fig.savefig(f"{OUT}/04_do_sat_thuc_te.png", dpi=130); plt.close(fig)

# 5. Dự đoán so với thực tế (scatter) – TabPFN và XEdu-KANFormer, điểm HK2
a9 = store._actual9()
fig, axes = plt.subplots(1, 2, figsize=(12, 6.4))
fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.1, wspace=0.18)
for ax, mm, colr in ((axes[0], "TabPFN", MI), (axes[1], "XEdu-KANFormer", CO)):
    oof = store._oof(mm)
    ids = [i for i in oof.index if i in a9["L9H1"].index and i in a9["L9H2"].index]
    h1 = a9["L9H1"].loc[ids, SUBJECTS].to_numpy(float); h2 = a9["L9H2"].loc[ids, SUBJECTS].to_numpy(float)
    pr = np.clip((3 * oof.loc[ids, SUBJECTS].to_numpy(float) - h1) / 2, 0, 10)
    ok = ~np.isnan(h2)
    xs, ys = h2[ok], pr[ok]
    t = np.linspace(2, 10, 2)
    ax.fill_between(t, t - 1, t + 1, color=Y, alpha=0.35, zorder=0, label="vùng lệch ≤ 1 điểm")
    ax.fill_between(t, t - 0.5, t + 0.5, color=Y, alpha=0.8, zorder=1, label="vùng lệch ≤ 0,5 điểm")
    ax.plot(t, t, color=INK, linewidth=2, zorder=2)
    ax.scatter(xs, ys, s=11, color=colr, edgecolor=INK, linewidth=0.35, alpha=0.75, zorder=3)
    mae = np.abs(xs - ys).mean(); r2 = 1 - ((xs - ys) ** 2).sum() / ((xs - xs.mean()) ** 2).sum()
    ax.set_title(f"{mm} · MAE {c(mae)} · R² {c(r2)}", loc="left", fontsize=12.5)
    ax.set_xlim(2, 10); ax.set_ylim(2, 10)
    ax.set_xlabel("Điểm HK2 thật"); ax.set_ylabel("Điểm HK2 dự đoán")
    ax.xaxis.set_major_formatter(vn(0)); ax.yaxis.set_major_formatter(vn(0))
    ax.grid(color=LINE, linewidth=1, zorder=0)
axes[0].legend(loc="upper left", edgecolor=INK, fancybox=False)
frame(fig, "Điểm HK2 lớp 9: dự đoán so với thực tế", f"Mỗi chấm là một học sinh × một môn ({ok.sum()} điểm) · đường chéo = dự đoán trùng khớp hoàn toàn")
fig.savefig(f"{OUT}/05_du_doan_vs_thuc_te.png", dpi=130); plt.close(fig)

# 6. Diễn biến điểm trung bình cả khóa theo 8 học kỳ (small multiples)
sem = [p for p in store.SEM]
labels = [p["short"] if "short" in p else p["label"] for p in sem]
fig, axes = plt.subplots(2, 4, figsize=(14, 6.6), sharex=True)
fig.subplots_adjust(left=0.05, right=0.99, top=0.83, bottom=0.12, hspace=0.38, wspace=0.22)
pal = [CO, TO, MI, AM, LI, PI, Y, CO]
for ax, s_, colr in zip(axes.ravel(), SUBJECTS, pal):
    means = [store.rows(p["key"])[s_].mean() for p in sem]
    q1 = [store.rows(p["key"])[s_].quantile(0.25) for p in sem]; q3 = [store.rows(p["key"])[s_].quantile(0.75) for p in sem]
    x = np.arange(len(sem))
    ax.fill_between(x, q1, q3, color=colr, alpha=0.25, zorder=1)
    ax.plot(x, means, color=INK, linewidth=2.6, zorder=2)
    ax.scatter(x, means, s=46, color=colr, edgecolor=INK, linewidth=2, zorder=3)
    d = means[-1] - means[0]
    ax.set_title(f"{SVN[s_]}  {'+' if d >= 0 else '−'}{c(abs(d))}", loc="left", fontsize=12)
    ax.set_xticks(x, labels, rotation=55, fontsize=8.5)
    ax.yaxis.set_major_formatter(vn(1))
    ax.grid(axis="y", color=LINE, linewidth=1)
frame(fig, "Diễn biến điểm của cả khóa qua 8 học kỳ (lớp 6 → lớp 9)", "Đường đen = điểm trung bình khối · dải màu = 50% học sinh ở giữa (Q1–Q3) · số cạnh tên môn = thay đổi HK1 lớp 6 → HK2 lớp 9")
fig.savefig(f"{OUT}/06_dien_bien_8_hoc_ky.png", dpi=130); plt.close(fig)

# 7. Bản đồ nhiệt độ quan trọng theo học kỳ (XEdu-KANFormer, trung bình trên các môn đích)
imp = pd.read_csv("reports/importance.csv")
for mm, fn in (("TabPFN", "07_do_quan_trong_tabpfn.png"),):
    d = imp[imp["model"] == mm].groupby(["feature", "period"])["delta_rmse"].mean().unstack()
    per_order = [p for p in pd.unique(imp["period"]) if p in d.columns]
    d = d[per_order]
    d = d.loc[d.abs().sum(axis=1).sort_values(ascending=False).index]
    fig, ax = plt.subplots(figsize=(12, 6.4))
    fig.subplots_adjust(left=0.17, right=0.93, top=0.8, bottom=0.12)
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    cmap = LinearSegmentedColormap.from_list("st", [TO, WHITE, MI])
    v = np.nanmax(np.abs(d.values))
    im = ax.imshow(d.values, cmap=cmap, norm=TwoSlopeNorm(0, -v, v), aspect="auto")
    for i in range(d.shape[0]):
        for j in range(d.shape[1]):
            val = d.values[i, j]
            if not np.isnan(val) and abs(val) >= v * 0.25:
                ax.text(j, i, c(val, 3), ha="center", va="center", fontsize=8, fontweight="bold")
    ax.set_xticks(range(d.shape[1]), d.columns, rotation=30, ha="right", fontsize=9.5)
    ax.set_yticks(range(d.shape[0]), d.index, fontweight="bold")
    ax.set_xticks(np.arange(-0.5, d.shape[1]), minor=True); ax.set_yticks(np.arange(-0.5, d.shape[0]), minor=True)
    ax.grid(which="minor", color=INK, linewidth=0.8); ax.tick_params(which="minor", length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.03); cb.outline.set_linewidth(2); cb.ax.yaxis.set_major_formatter(vn(3))
    frame(fig, f"Mô hình dựa vào ô điểm nào? ({mm})", "Độ quan trọng hoán vị (RMSE tăng khi xáo trộn một ô môn × học kỳ) · học kỳ gần nhất HK1 lớp 9 chi phối dự đoán")
    fig.savefig(f"{OUT}/{fn}", dpi=130); plt.close(fig)

# 8. Ma trận mức TT22 (TabPFN)
a = acc["TabPFN"]["level"]
names = a["names"][:3]
mat = np.array(a["confusion"])[:3, :3]
fig, ax = plt.subplots(figsize=(6.6, 5.6))
fig.subplots_adjust(left=0.2, right=0.96, top=0.78, bottom=0.14)
ax.imshow(mat / mat.sum(axis=1, keepdims=True), cmap=LinearSegmentedColormap.from_list("m", [WHITE, MI]), vmin=0, vmax=1)
for i in range(3):
    for j in range(3):
        ax.text(j, i, f"{mat[i, j]}\n{c(100 * mat[i, j] / mat[i].sum(), 0)}%", ha="center", va="center", fontsize=12, fontweight="bold")
ax.set_xticks(range(3), names, fontweight="bold"); ax.set_yticks(range(3), names, fontweight="bold")
ax.set_xlabel("Mức dự đoán"); ax.set_ylabel("Mức thật")
ax.set_xticks(np.arange(-0.5, 3), minor=True); ax.set_yticks(np.arange(-0.5, 3), minor=True)
ax.grid(which="minor", color=INK, linewidth=2); ax.tick_params(which="minor", length=0)
frame(fig, "Mức học lực TT22 lớp 9 (TabPFN)", f"Suy ra từ điểm dự đoán · trùng khớp {c(a['match'], 1)}%")
fig.savefig(f"{OUT}/08_muc_tt22.png", dpi=130); plt.close(fig)

json.dump({mm: {"cn": acc[mm]["cn"], "hk2": acc[mm]["hk2"], "dtb": acc[mm]["dtb"], "exam": acc[mm]["exam"], "level": acc[mm]["level"]["match"]} for mm in MAIN},
          open(os.path.join(ROOT, "reports", "accuracy_vs_actual.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("ok", sorted(os.listdir(OUT)))
