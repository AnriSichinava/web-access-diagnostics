from fastapi import FastAPI, HTTPException

from app.diagnostics import run_diagnosis
from app.history import get_report, init_db, list_reports, save_report
from app.models import DiagnoseRequest, DiagnosisReport
from app.proxies import load_proxies

app = FastAPI(
    title="Web Access & API Troubleshooting Platform",
    description="Diagnoses DNS, HTTP/S, redirect, proxy, and bot-block behavior for a target URL.",
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/proxies")
def proxies() -> list[dict]:
    return [p.model_dump() for p in load_proxies()]


@app.post("/diagnose", response_model=DiagnosisReport)
def diagnose(req: DiagnoseRequest) -> DiagnosisReport:
    try:
        report = run_diagnosis(req.url, proxy_label=req.proxy, follow_redirects=req.follow_redirects)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    save_report(report)
    return report


@app.get("/history")
def history(limit: int = 50) -> list[dict]:
    return list_reports(limit=limit)


@app.get("/history/{correlation_id}")
def history_detail(correlation_id: str) -> dict:
    report = get_report(correlation_id)
    if report is None:
        raise HTTPException(status_code=404, detail="correlation_id not found")
    return report
