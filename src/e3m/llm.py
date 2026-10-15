"""Tầng ngôn ngữ: LLM chạy cục bộ (Ollama) diễn đạt lại dữ kiện đã tính, có hàng rào kiểm soát.

Dữ liệu không rời máy: chỉ gọi http://localhost:11434. Không gửi họ tên học sinh cho LLM.
"""
from __future__ import annotations

import json
import os
import re

import requests

_host = os.environ.get("OLLAMA_HOST", "localhost:11434").replace("0.0.0.0", "localhost")
OLLAMA = _host if _host.startswith("http") else f"http://{_host}"
BANNED = ["học kém", "yếu kém", "kém cỏi", "trượt", "rớt", "thất bại", "dốt", "đội sổ", "tệ", "đáng thất vọng",
          "không có khả năng", "vô vọng"]
# người nhận -> (câu mở đầu bắt buộc, vai người viết và cách xưng hô)
AUDIENCE = {
    "Học sinh": ("Chào em,", "Người viết là thầy cô giáo, người đọc là học sinh lớp 9. Xưng 'thầy cô', gọi người đọc là 'em'."),
    "Phụ huynh": ("Kính gửi anh/chị,", "Người viết là nhà trường, người đọc là cha mẹ học sinh. Xưng 'nhà trường', gọi người đọc là 'anh/chị', gọi học sinh là 'con'."),
    "Giáo viên chủ nhiệm": ("Kính gửi thầy/cô,", "Người viết là hệ thống hỗ trợ, người đọc là giáo viên chủ nhiệm. Gọi học sinh là 'em học sinh', nêu gợi ý hỗ trợ cụ thể."),
}
PREFERRED = ["qwen3:8b", "gemma3:4b"]

SYSTEM = """Bạn là trợ lý sư phạm của một trường THCS Việt Nam. Bạn viết thông điệp ngắn bằng tiếng Việt dựa trên DỮ KIỆN dạng JSON.

QUY TẮC BẮT BUỘC
1. Chỉ dùng số liệu có trong DỮ KIỆN. Không tự thêm điểm số, tên trường, tỉ lệ hay nhận định mới.
2. Giọng ấm áp, tôn trọng, khích lệ. Tuyệt đối không dùng các từ: học kém, yếu kém, trượt, rớt, thất bại, dốt, tệ.
3. Mở đầu bằng điểm sáng (môn học tốt nhất kèm điểm và lớp).
4. Các số trong "du_doan_lop_9" là DỰ ĐOÁN của mô hình cho cuối lớp 9 (từ điểm lớp 6–8), phải nói rõ là "dự kiến"/"dự đoán"; "diem_thuc_te_lop_9" (nếu có) là điểm thật. Nói về 3 môn thi (Toán, Ngữ văn, Tiếng Anh) như một thử thách, không phán xét.
5. Theo nhóm định hướng:
   - "Định hướng nghề nghiệp": nêu rõ thi THPT công lập không phải con đường duy nhất; trường trung cấp, cao đẳng nghề là lựa chọn tốt phù hợp thế mạnh. Nhấn mạnh mục tiêu học kỳ II là giữ vững kết quả để tốt nghiệp THCS, vì đó là điều kiện để xét tuyển học nghề.
   - "Cần bứt phá": chỉ ra môn cần ưu tiên và mức điểm mục tiêu trong DỮ KIỆN; khích lệ.
   - "Vững vàng thi THPT": ghi nhận, khuyến khích duy trì, gợi ý môn có thể nâng thêm.
6. Nếu có "muc_tieu_tiep_theo", nêu cụ thể môn và điểm mục tiêu đúng như DỮ KIỆN.
   Nếu có "tuyen_sinh_lop_10": nêu tổng 3 môn so với điểm sàn đúng theo "nhan_dinh"; không khẳng định chắc chắn đậu hay không đậu.
   Nếu có "xu_huong": nêu xu hướng Tăng / Giảm / Ổn định của điểm trung bình và của tổng 3 môn thi; xu hướng Giảm thì diễn đạt như lời nhắc nhẹ nhàng.
7. Dài 100–160 từ, đúng MỘT đoạn văn, không xuống dòng, không gạch đầu dòng, không tiêu đề, không emoji. Kết thúc bằng một câu thể hiện sự đồng hành.
8. Bắt đầu chính xác bằng CÂU MỞ ĐẦU được giao và giữ đúng cách xưng hô được giao trong toàn bộ thông điệp.

VÍ DỤ VỀ GIỌNG VĂN (chỉ tham khảo giọng, không dùng lại số liệu):
"Chào em, kết quả học tập cho thấy em có năng lực rất tốt ở môn Công nghệ và Tin học – đây là những kỹ năng thực hành tuyệt vời! Dù Toán và Tiếng Anh có thể đang là thử thách với em trong kỳ thi vào 10, em hãy nhớ rằng thi THPT không phải là con đường duy nhất. Rất nhiều trường Trung cấp và Cao đẳng nghề đang mở rộng cửa đón những học sinh có thế mạnh thực hành như em. Mục tiêu quan trọng nhất của em ở học kỳ II: tiếp tục cố gắng để tốt nghiệp THCS thật đẹp. Thầy cô luôn tin tưởng và đồng hành cùng em!"
"""


def available_models() -> list[str]:
    try:
        tags = requests.get(f"{OLLAMA}/api/tags", timeout=2).json()
        found = [m["name"] for m in tags.get("models", [])]
        return [m for m in PREFERRED if m in found] + [m for m in found if m not in PREFERRED]
    except Exception:
        return []


def check(text: str, facts: dict, audience: str | None = None) -> list[str]:
    """Hàng rào sau sinh: từ ngữ bị cấm, số liệu không có trong dữ kiện, sai câu mở đầu, quá dài."""
    issues = [f"Có từ ngữ cần tránh: “{w}”" for w in BANNED if re.search(rf"(?<!\w){re.escape(w)}(?!\w)", text.lower())]
    allowed = {float(x) for x in re.findall(r"\d+(?:\.\d+)?", json.dumps(facts, ensure_ascii=False))} | {9, 10, 2, 3, 90}
    for raw in re.findall(r"\d+(?:[.,]\d+)?", text):
        if float(raw.replace(",", ".")) not in allowed:
            issues.append(f"Số liệu “{raw}” không có trong dữ kiện")
    if audience and not text.strip().startswith(AUDIENCE[audience][0]):
        issues.append(f"Chưa mở đầu bằng “{AUDIENCE[audience][0]}”")
    if len(text.split()) > 260:
        issues.append("Thông điệp quá dài")
    return issues


def _messages(facts: dict, audience: str) -> list[dict]:
    opening, voice = AUDIENCE[audience]
    user = (f"{voice}\nCÂU MỞ ĐẦU: {opening}\n\nDỮ KIỆN:\n{json.dumps(facts, ensure_ascii=False, indent=1)}\n\n"
            f"Hãy viết thông điệp, bắt đầu bằng “{opening}”.")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def clean(text: str) -> str:
    return " ".join(re.sub(r"<think>.*?</think>", "", text, flags=re.S).split())


def stream(facts: dict, audience: str, model: str, temperature: float = 0.4, timeout: int = 600):
    """Sinh thông điệp theo dòng (dùng cho giao diện); trả về từng mẩu văn bản."""
    body = dict(model=model, messages=_messages(facts, audience), stream=True, think=False,
                options=dict(temperature=temperature, num_predict=350))
    with requests.post(f"{OLLAMA}/api/chat", json=body, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if line:
                yield json.loads(line).get("message", {}).get("content", "")


def generate(facts: dict, audience: str, model: str, temperature: float = 0.4, retries: int = 1) -> tuple[str, list[str]]:
    """Sinh thông điệp; nếu vi phạm hàng rào thì sinh lại với nhắc nhở cụ thể."""
    msgs = _messages(facts, audience)
    text, issues = "", []
    for _ in range(retries + 1):
        r = requests.post(f"{OLLAMA}/api/chat", timeout=600, json=dict(
            model=model, messages=msgs, stream=False, think=False, options=dict(temperature=temperature, num_predict=350)))
        r.raise_for_status()
        text = clean(r.json()["message"]["content"])
        issues = check(text, facts, audience)
        if not issues:
            break
        msgs += [{"role": "assistant", "content": text},
                 {"role": "user", "content": "Bản trên vi phạm quy tắc: " + "; ".join(issues) + ". Hãy viết lại, sửa đúng các lỗi này."}]
    return text, issues


def template(facts: dict, audience: str = "Học sinh") -> str:
    """Thông điệp mẫu theo luật, dùng khi không có LLM (và làm mốc so sánh với LLM)."""
    you = {"Học sinh": "em", "Phụ huynh": "con", "Giáo viên chủ nhiệm": "em học sinh"}[audience]
    hello = {"Học sinh": "Chào em,", "Phụ huynh": "Kính gửi anh/chị,", "Giáo viên chủ nhiệm": "Kính gửi thầy/cô,"}[audience]
    best = " và ".join(f"{s['mon']} ({s['diem']})" for s in facts["diem_sang"][:2])
    exam = ", ".join(f"{k} {v}" for k, v in facts["diem_3_mon_thi"].items())
    out = [f"{hello} kết quả học tập lớp {facts['lop_gan_nhat_co_diem']} cho thấy {you} có thế mạnh rõ ở {best}."]
    if "diem_thuc_te_lop_9" not in facts:
        out.append(f"Từ điểm các lớp 6–8, mô hình dự đoán cuối lớp 9 {you} đạt điểm trung bình khoảng "
                   f"{facts['diem_trung_binh_du_doan_lop_9']} và mức {facts['muc_ket_qua_hoc_tap_du_doan_lop_9']}.")
    g = facts["nhom_dinh_huong"]
    if g == "Định hướng nghề nghiệp":
        out.append(f"Ba môn thi vào lớp 10 ({facts['nguon_diem_3_mon']}: {exam}) hiện là thử thách, nhưng thi THPT công lập không phải con đường duy nhất: "
                   f"các trường trung cấp, cao đẳng nghề luôn chào đón học sinh có thế mạnh thực hành.")
    elif g == "Cần bứt phá":
        out.append(f"Ba môn thi vào lớp 10 ({facts['nguon_diem_3_mon']}: {exam}) đang ở mức có thể bứt phá nếu ôn tập đều trong học kỳ II.")
    else:
        out.append(f"Ba môn thi vào lớp 10 ({facts['nguon_diem_3_mon']}: {exam}) đang ở mức vững vàng; hãy duy trì nhịp học hiện tại.")
    ts = facts.get("tuyen_sinh_lop_10")
    if ts:
        out.append(f"Tổng 3 môn hiện là {ts['tong_3_mon']} so với điểm sàn {ts['diem_san']}: {ts['nhan_dinh'].lower()}.")
    xh = facts.get("xu_huong", {})
    if xh:
        name = {"diem_trung_binh": "điểm trung bình", "tong_3_mon_thi": "tổng 3 môn thi"}
        out.append("Xu hướng qua các năm: " + "; ".join(f"{name[k]} {v['xu_huong'].lower()} ({v['thay_doi']:+})"
                                                        for k, v in xh.items() if k in name) + ".")
    nxt = facts.get("muc_tieu_tiep_theo")
    if nxt and nxt["can_cai_thien"]:
        todo = ", ".join(f"{c['mon']} từ {c['tu']} lên {c['len']}" for c in nxt["can_cai_thien"][:3])
        out.append(f"Mục tiêu gần nhất là mức {nxt['muc']}: {todo}.")
    if g == "Định hướng nghề nghiệp":
        out.append("Điều quan trọng nhất ở học kỳ II là giữ vững kết quả các môn để tốt nghiệp THCS, vì đây là điều kiện xét tuyển vào trường nghề.")
    out.append("Thầy cô luôn tin tưởng và đồng hành." if audience != "Phụ huynh" else "Nhà trường luôn đồng hành cùng gia đình.")
    return " ".join(out)
