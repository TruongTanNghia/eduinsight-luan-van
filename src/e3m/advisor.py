"""Tầng luật sư phạm: xếp mức theo Thông tư 22, phản thực khả thi, xu hướng, điểm sàn tuyển sinh, điểm sáng.

Mọi con số đưa cho LLM đều được tính ở đây; LLM chỉ diễn đạt lại.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import EXAM, GRADES, LEVELS, SUBJECT_VN, SUBJECTS

# Thông tư 22/2021, Điều 9: (mức, điểm sàn mọi môn, ngưỡng cao, số môn tối thiểu đạt ngưỡng cao, số môn N.xét CĐ tối đa)
_RULES = [(3, 6.5, 8.0, 6, 0), (2, 5.0, 6.5, 6, 0), (1, 3.5, 5.0, 6, 1)]
GROUPS = ["Định hướng nghề nghiệp", "Cần bứt phá", "Vững vàng thi THPT"]


def _scores(d) -> dict[str, float]:
    return {s: float(d[s]) for s in SUBJECTS if s in d and pd.notna(d[s])}


def level_tt22(scores, n_cd: int = 0) -> int:
    """Mức kết quả học tập (0 = Chưa đạt … 3 = Tốt) từ điểm TB các môn đánh giá bằng điểm số."""
    v = np.array(list(_scores(scores).values()))
    for lv, floor, high, k, max_cd in _RULES:
        if n_cd <= max_cd and (v >= floor).all() and (v >= high).sum() >= min(k, len(v)):
            return lv
    return 0


def counterfactual(scores, target_level: int, max_step: float = 1.5) -> dict:
    """Phản thực thưa nhất để đạt `target_level`: nâng ít môn nhất, mỗi môn tăng ít nhất có thể.

    Ràng buộc sư phạm: chỉ tăng điểm; mỗi môn tăng không quá `max_step` điểm thì mới coi là khả thi.
    """
    sc = _scores(scores)
    _, floor, high, k, _ = next(r for r in _RULES if r[0] == target_level)
    k = min(k, len(sc))
    goal = {s: max(v, floor) for s, v in sc.items()}                       # kéo mọi môn lên điểm sàn
    need = k - sum(v >= high for v in goal.values())
    if need > 0:                                                           # nâng các môn gần ngưỡng cao nhất
        for s in sorted((s for s in goal if goal[s] < high), key=lambda s: high - sc[s])[:need]:
            goal[s] = high
    changes = [dict(mon=SUBJECT_VN[s], ma=s, hien_tai=round(sc[s], 1), muc_tieu=goal[s], tang=round(goal[s] - sc[s], 1))
               for s in sc if goal[s] > sc[s] + 1e-9]
    changes.sort(key=lambda c: -c["tang"])
    return dict(muc_dich=LEVELS[target_level], thay_doi=changes,
                kha_thi=all(c["tang"] <= max_step for c in changes), da_dat=not changes)


def admission(total3: float, floor: float, margin: float = 1.5, lo: float | None = None, hi: float | None = None) -> dict:
    """So tổng 3 môn thi với điểm sàn/chuẩn của trường THPT mục tiêu (thang 30)."""
    gap = round(total3 - floor, 1)
    verdict = ("Khả năng cao đạt điểm sàn" if gap >= margin else
               "Sát điểm sàn, cần bứt phá" if gap > -margin else "Hiện thấp hơn điểm sàn")
    out = dict(diem_san=round(floor, 1), tong_3_mon=round(total3, 1), chenh_lech=gap, nhan_dinh=verdict)
    if lo is not None:
        out["khoang_tong_3_mon_90"] = [round(lo, 1), round(hi, 1)]
    return out


def orientation(total3: float, floor: float, margin: float) -> str:
    return GROUPS[0] if total3 < floor - margin else GROUPS[1] if total3 < floor + margin else GROUPS[2]


def trend(values: list[float], eps: float = 0.3) -> dict | None:
    """Xu hướng qua các mốc (cũ -> mới): chênh lệch mốc cuối so với mốc đầu và độ dốc trung bình mỗi năm."""
    v = [float(x) for x in values if pd.notna(x)]
    if len(v) < 2:
        return None
    slope = float(np.polyfit(range(len(v)), v, 1)[0])
    change = round(v[-1] - v[0], 1)
    label = "Tăng" if change >= eps else "Giảm" if change <= -eps else "Ổn định"
    return dict(xu_huong=label, thay_doi=change, moi_nam=round(slope, 2), so_moc=len(v))


def strengths(scores, ref: pd.DataFrame, top: int = 3, min_score: float = 6.5) -> list[dict]:
    """Điểm sáng: các môn học sinh nổi bật nhất so với bạn cùng khối (xếp theo phân vị, rồi theo điểm).

    Xếp theo phân vị thay vì điểm tuyệt đối vì mặt bằng điểm các môn rất khác nhau (GDCD thường rất cao).
    """
    out = []
    for s, v in _scores(scores).items():
        pct = float((ref[s].dropna() <= v).mean() * 100) if s in ref and ref[s].notna().any() else 50.0
        out.append(dict(mon=SUBJECT_VN[s], ma=s, diem=v, phan_vi=round(pct), la_mon_thi=s in EXAM))
    out.sort(key=lambda o: (-o["phan_vi"], -o["diem"]))
    best = [o for o in out if o["diem"] >= min_score][:top]
    return best or sorted(out, key=lambda o: -o["diem"])[:1]


def history_table(df_student: pd.DataFrame) -> pd.DataFrame:
    """Bảng theo năm của một học sinh (từ bảng dài): lớp, ĐTB các môn, tổng 3 môn thi, mức."""
    h = df_student.sort_values("lop_so")
    out = pd.DataFrame({"Lớp": h["lop_so"].values, "ĐTB": h[SUBJECTS].mean(axis=1).round(2).values,
                        "Tổng 3 môn thi": h[EXAM].sum(axis=1).round(1).values,
                        "Mức": [LEVELS[int(m)] for m in h["muc"]]})
    return out


def build_facts(latest: dict, latest_grade: int, pred9: np.ndarray, lo9: np.ndarray, hi9: np.ndarray, proba9,
                ref_latest: pd.DataFrame, floor: float, margin: float = 1.5, school: str | None = None,
                actual9: dict | None = None, history: pd.DataFrame | None = None, n_cd: int = 0,
                max_step: float = 1.5, exam_shift: float = 0.0) -> dict:
    """Gom toàn bộ dữ kiện đã tính cho một học sinh (đầu vào duy nhất của tầng ngôn ngữ).

    latest: điểm năm gần nhất đã có (thường là lớp 8); pred9/lo9/hi9: dự đoán lớp 9 và khoảng 90%;
    actual9: điểm thật lớp 9 nếu đã có; history: bảng của history_table (xu hướng tính tự động).
    """
    pred = {s: round(float(pred9[j]), 1) for j, s in enumerate(SUBJECTS)}
    use = actual9 if actual9 else pred
    src = "điểm thực tế lớp 9" if actual9 else "mô hình dự đoán từ lớp 6–8"
    exam = {s: round(min(10.0, max(0.0, use[s] + exam_shift)), 1) for s in EXAM}
    total = round(sum(exam.values()), 1)
    lv_pred = level_tt22(pred, n_cd)
    facts = dict(
        lop_gan_nhat_co_diem=latest_grade,
        diem_trung_binh_lop_gan_nhat=round(float(np.mean(list(_scores(latest).values()))), 1),
        du_doan_lop_9={SUBJECT_VN[s]: pred[s] for s in SUBJECTS},
        khoang_du_doan_90_lop_9={SUBJECT_VN[s]: [round(float(lo9[j]), 1), round(float(hi9[j]), 1)] for j, s in enumerate(SUBJECTS)},
        diem_trung_binh_du_doan_lop_9=round(float(np.mean(list(pred.values()))), 1),
        muc_ket_qua_hoc_tap_du_doan_lop_9=LEVELS[lv_pred],
        nguon_diem_3_mon=src,
        diem_3_mon_thi={SUBJECT_VN[s]: exam[s] for s in EXAM},
        tong_3_mon=total,
        nhom_dinh_huong=orientation(total, floor, margin),
        diem_sang=[dict(mon=s["mon"], diem=s["diem"], lop=latest_grade) for s in strengths(latest, ref_latest)],
        dieu_kien_tot_nghiep="Kết quả học tập và rèn luyện lớp 9 từ mức Đạt trở lên",
        du_kien_du_dieu_kien_hoc_tap_tot_nghiep=lv_pred >= 1,
    )
    if proba9 is not None:
        facts["xac_suat_muc_lop_9"] = {LEVELS[i]: round(float(proba9[i]), 2) for i in range(4) if proba9[i] >= 0.05}
    if actual9:
        facts["diem_thuc_te_lop_9"] = {SUBJECT_VN[s]: actual9[s] for s in SUBJECTS if s in actual9}
        facts["muc_ket_qua_hoc_tap_thuc_te_lop_9"] = LEVELS[level_tt22(actual9, n_cd)]
    iv = (float(sum(lo9[SUBJECTS.index(s)] for s in EXAM)), float(sum(hi9[SUBJECTS.index(s)] for s in EXAM))) if not actual9 else (None, None)
    facts["tuyen_sinh_lop_10"] = admission(total, floor, margin, *iv)
    if school:
        facts["tuyen_sinh_lop_10"]["truong"] = school
    if history is not None and len(history) >= 2:
        facts["xu_huong"] = {k: t for k, t in (("diem_trung_binh", trend(history["ĐTB"])),
                                               ("tong_3_mon_thi", trend(history["Tổng 3 môn thi"]))) if t}
        facts["xu_huong"]["cac_moc"] = [f"lớp {int(g)}" for g in history["Lớp"]]
    base9 = actual9 if actual9 else pred
    lv = level_tt22(base9, n_cd)
    if lv < 3:
        cf = counterfactual(base9, 1 if lv < 1 else lv + 1, max_step)
        facts["muc_tieu_tiep_theo"] = dict(
            muc=cf["muc_dich"], kha_thi=cf["kha_thi"], can_cu="điểm lớp 9 " + ("thực tế" if actual9 else "dự đoán"),
            can_cai_thien=[dict(mon=c["mon"], tu=c["hien_tai"], len=c["muc_tieu"]) for c in cf["thay_doi"]])
    return facts
