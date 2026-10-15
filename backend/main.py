"""API /api/v1 cho frontend EduInsight (Next.js). Chạy:  uvicorn backend.main:app --port 8000 --reload"""
from __future__ import annotations

import os
import shutil
import tempfile

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core import Store, llm

app = FastAPI(title="EduInsight API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
store = Store()
_uploads: dict[str, dict] = {}
V = "/api/v1"


@app.get(f"{V}/meta")
def meta():
    return store.meta()


# ----------------------------------------------------------------------------- analytics
@app.get(f"{V}/analytics/overview")
def overview(period: str | None = None, cls: str = Query("", alias="class")):
    return store.overview(period, cls)


@app.get(f"{V}/analytics/grades-by-semester")
def grades_by_semester(period: str | None = None, cls: str = Query("", alias="class")):
    return store.overview(period, cls)["series"]


@app.get(f"{V}/analytics/subject-comparison")
def subject_comparison(period: str | None = None, cls: str = Query("", alias="class")):
    o = store.overview(period, cls)
    return {"subjects": o["subjects"], "average": o["subjectAverage"]}


@app.get(f"{V}/analytics/class-comparison")
def class_comparison(period: str | None = None, cls: str = Query("", alias="class")):
    if cls and cls != "all":
        r = store.class_analysis(cls, period)
        if r is None:
            raise HTTPException(404, "Không có lớp này ở kỳ đã chọn")
        return r
    return store.overview(period, "")["classes"]


@app.get(f"{V}/analytics/student-risk")
def student_risk(period: str | None = None, cls: str = Query("", alias="class")):
    o = store.overview(period, cls)
    return {"items": o["risk"], "count": o["kpi"]["watch"], "threshold": o["threshold"]}


# ----------------------------------------------------------------------------- students
@app.get(f"{V}/students")
def students(q: str = "", cls: str = Query("", alias="class"), status: str = "", sort: str = "name", dir: str = "asc", page: int = 1, size: int = 20, grade: int | None = None, period: str | None = None):
    return store.students(q, cls, status, sort, dir, page, size, grade, period)


@app.get(f"{V}/students/{{sid}}")
def student(sid: str):
    p = store.profile(sid)
    if p is None:
        raise HTTPException(404, "Không tìm thấy học sinh")
    return p


@app.get(f"{V}/students/{{sid}}/grades")
def student_grades(sid: str):
    p = store.profile(sid)
    if p is None:
        raise HTTPException(404, "Không tìm thấy học sinh")
    return {"periods": p["periods"], "subjects": p["subjects"], "avgs": p["avgs"], "classAvgByPeriod": p["classAvgByPeriod"]}


@app.get(f"{V}/students/{{sid}}/trends")
def student_trends(sid: str):
    p = store.profile(sid)
    if p is None:
        raise HTTPException(404, "Không tìm thấy học sinh")
    return {"overall": p["overall"], "delta": p["delta"], "threshold": p["threshold"], "subjects": [{"key": s["key"], "name": s["name"], "trend": s["trend"]} for s in p["subjects"]]}


@app.get(f"{V}/students/{{sid}}/analysis")
def student_analysis(sid: str):
    p = store.profile(sid)
    if p is None:
        raise HTTPException(404, "Không tìm thấy học sinh")
    return {"analysis": p["analysis"], "remarks": p["remarks"], "evidence": p["evidence"], "strengths": p["strengths"]}


@app.get(f"{V}/students/{{sid}}/predictions")
def student_predictions(sid: str, model: str | None = None, floor: float | None = None, margin: float = 1.5, school: str | None = None):
    p = store.prediction(sid, model, floor, margin, school)
    if p is None:
        raise HTTPException(404, "Không có mô hình hoặc học sinh")
    return p


class MessageIn(BaseModel):
    audience: str = "Học sinh"
    llm_model: str | None = None
    use_llm: bool = False
    floor: float | None = None
    margin: float = 1.5
    school: str | None = None


@app.post(f"{V}/students/{{sid}}/message")
def student_message(sid: str, body: MessageIn):
    try:
        r = store.message(sid, body.audience, body.llm_model, body.use_llm, body.floor, body.margin, body.school)
    except Exception as e:
        raise HTTPException(502, f"LLM lỗi: {e}")
    if r is None:
        raise HTTPException(404, "Không dự đoán được cho học sinh này")
    return r


class ApproveIn(BaseModel):
    audience: str
    text: str
    source: str = ""


@app.post(f"{V}/students/{{sid}}/message/approve")
def approve_message(sid: str, body: ApproveIn):
    import csv
    import datetime as dt
    from backend.core import OUT_DIR
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "thong_diep_da_duyet.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["thoi_gian", "sid", "nguoi_nhan", "nguon", "thong_diep"])
        w.writerow([dt.datetime.now().isoformat(timespec="seconds"), sid, body.audience, body.source, body.text])
    return {"ok": True, "path": path}


# ----------------------------------------------------------------------------- classes
@app.get(f"{V}/classes")
def classes(period: str | None = None):
    return store.overview(period, "")["classes"]


@app.get(f"{V}/classes/{{cls}}")
def class_detail(cls: str, period: str | None = None):
    r = store.class_analysis(cls, period)
    if r is None:
        raise HTTPException(404, "Không có lớp này ở kỳ đã chọn")
    return r


# ----------------------------------------------------------------------------- ai
@app.get(f"{V}/ai/models")
def ai_models():
    return {"items": store.models_list(), "llm": llm.available_models(), "status": "awaiting_labels"}


@app.get(f"{V}/ai/accuracy")
def ai_accuracy(model: str = "XEdu-KANFormer"):
    r = store.accuracy(model)
    if r is None:
        raise HTTPException(404, "Chưa có dự đoán kiểm định chéo cho mô hình này (chạy scripts/train.bat)")
    return r


@app.get(f"{V}/ai/models/{{mid}}/metrics")
def ai_model_metrics(mid: str):
    r = store.model_metrics(mid)
    if r is None:
        raise HTTPException(404, "Chưa có báo cáo đánh giá cho mô hình này")
    return r


class PredictIn(BaseModel):
    student: str
    model: str | None = None


@app.post(f"{V}/ai/predict")
def ai_predict(body: PredictIn):
    p = store.prediction(body.student, body.model)
    if p is None:
        raise HTTPException(404, "Không dự đoán được")
    return p


# ----------------------------------------------------------------------------- schools
class SchoolIn(BaseModel):
    name: str
    year: str
    method: str = "Thi tuyển 3 môn"
    cut: float
    type: str = "Công lập"
    source: str


@app.get(f"{V}/schools")
def schools():
    return store.schools()


@app.post(f"{V}/schools")
def add_school(body: SchoolIn):
    if not body.source.strip():
        raise HTTPException(422, "Cần nguồn tham chiếu cho điểm chuẩn")
    return store.add_school(body.model_dump())


@app.delete(f"{V}/schools/{{sid}}")
def delete_school(sid: str):
    return store.delete_school(sid)


# ----------------------------------------------------------------------------- reports
class ReportIn(BaseModel):
    scope: str
    target: str
    sections: dict
    format: str = "pdf"


@app.get(f"{V}/reports")
def reports():
    return store.list_reports()


@app.post(f"{V}/reports/student")
def report_student(body: ReportIn):
    return store.create_report("student", body.target, body.sections, body.format)


@app.post(f"{V}/reports/class")
def report_class(body: ReportIn):
    return store.create_report("class", body.target, body.sections, body.format)


@app.post(f"{V}/reports")
def report_any(body: ReportIn):
    return store.create_report(body.scope, body.target, body.sections, body.format)


@app.get(f"{V}/reports/{{rid}}")
def report_get(rid: str):
    r = store.get_report(rid)
    if r is None:
        raise HTTPException(404, "Không có báo cáo")
    return r


# ----------------------------------------------------------------------------- data
@app.get(f"{V}/data/schema")
def data_schema():
    return {"schema": store.schema(), "dictionary": store.dictionary(), "version": store.version}


@app.get(f"{V}/data/import/history")
def import_history():
    return store.import_history()


@app.post(f"{V}/data/import/preview")
async def import_preview(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".xls", ".xlsx")):
        raise HTTPException(422, "Chỉ nhận .xls/.xlsx xuất từ sổ điểm")
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    if os.path.getsize(path) > 20 * 1024 * 1024:
        raise HTTPException(422, "Tệp vượt 20 MB")
    pv = store.import_preview(path, file.filename)
    token = os.path.basename(tmp)
    _uploads[token] = {"path": path, "filename": file.filename, "preview": pv}
    return {"token": token, **pv}


class ConfirmIn(BaseModel):
    token: str
    agree: bool


@app.post(f"{V}/data/import/confirm")
def import_confirm(body: ConfirmIn):
    u = _uploads.get(body.token)
    if not u:
        raise HTTPException(404, "Phiên tải lên không còn; hãy tải lại tệp")
    if not body.agree:
        raise HTTPException(422, "Cần xác nhận đã xem trước dữ liệu")
    if not u["preview"].get("ok"):
        raise HTTPException(422, "Tệp còn lỗi cấu trúc; không nhập")
    r = store.import_confirm(u["path"], u["filename"], u["preview"])
    _uploads.pop(body.token, None)
    return r
