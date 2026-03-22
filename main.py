import sqlite3
import json
import os
from contextlib import contextmanager
from typing import Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

BASE_DIR = os.path.join(os.path.dirname(__file__), "إعراب_القرآن_الكريم")
IRAB_DB   = os.path.join(BASE_DIR, "irab_al_karbasi.db")
MASAQ_DB  = os.path.join(BASE_DIR, "MASAQ.db")

app = FastAPI(
    title="API إعراب القرآن الكريم",
    description="واجهة برمجية شاملة للبحث في إعراب وتحليل كلمات القرآن الكريم",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@contextmanager
def get_db(path: str):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


# ─────────────────────────────────────────────
#  الصفحة الرئيسية
# ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, tags=["عام"])
def home():
    return """
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
      <meta charset="utf-8">
      <title>API إعراب القرآن الكريم</title>
      <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 40px; }
        h1   { color: #38bdf8; font-size: 2rem; }
        h2   { color: #7dd3fc; border-bottom: 1px solid #334155; padding-bottom: 8px; }
        .card { background: #1e293b; border-radius: 12px; padding: 20px 28px; margin: 16px 0; }
        code  { background: #0f172a; color: #34d399; padding: 4px 10px; border-radius: 6px; font-size: 0.9em; }
        a     { color: #38bdf8; }
        .badge { display:inline-block; background:#1d4ed8; color:#fff; border-radius:6px; padding:2px 10px; font-size:0.8em; margin-left:6px; }
        table { width:100%; border-collapse:collapse; }
        th,td { padding:10px 14px; border-bottom:1px solid #334155; text-align:right; }
        th    { color:#7dd3fc; }
      </style>
    </head>
    <body>
      <h1>🕌 API إعراب القرآن الكريم</h1>
      <p>واجهة برمجية مجانية وشاملة للبحث في إعراب وتحليل كلمات القرآن الكريم</p>

      <div class="card">
        <h2>📚 المصادر</h2>
        <ul>
          <li><b>إعراب الكربلائي</b> — إعراب تفصيلي لجميع كلمات القرآن (66,516 كلمة)</li>
          <li><b>MASAQ Dataset</b> — تحليل صرفي ونحوي علمي (131,000+ مدخل)</li>
        </ul>
      </div>

      <div class="card">
        <h2>🔍 نقاط النهاية — Endpoints</h2>
        <table>
          <tr><th>المسار</th><th>الوصف</th></tr>
          <tr><td><code>GET /api/irab/search?q=كلمة</code></td><td>البحث في إعراب الكربلائي</td></tr>
          <tr><td><code>GET /api/irab/ayah/{سورة}/{آية}</code></td><td>إعراب آية محددة</td></tr>
          <tr><td><code>GET /api/irab/surah/{سورة}</code></td><td>جميع آيات سورة</td></tr>
          <tr><td><code>GET /api/morphology/search?q=كلمة</code></td><td>البحث في MASAQ الصرفي</td></tr>
          <tr><td><code>GET /api/morphology/ayah/{سورة}/{آية}</code></td><td>تحليل صرفي لآية</td></tr>
          <tr><td><code>GET /api/morphology/word/{سورة}/{آية}/{كلمة}</code></td><td>تحليل كلمة بعينها</td></tr>
          <tr><td><code>GET /api/morphology/surah/{سورة}</code></td><td>التحليل الصرفي لسورة</td></tr>
          <tr><td><code>GET /api/stats</code></td><td>إحصاءات قاعدة البيانات</td></tr>
          <tr><td><code>GET /docs</code></td><td>توثيق تفاعلي (Swagger)</td></tr>
        </table>
      </div>

      <div class="card">
        <h2>💡 أمثلة</h2>
        <ul>
          <li><a href="/api/irab/search?q=الله">/api/irab/search?q=الله</a></li>
          <li><a href="/api/irab/ayah/1/1">/api/irab/ayah/1/1</a> (الفاتحة - البسملة)</li>
          <li><a href="/api/irab/surah/1">/api/irab/surah/1</a> (سورة الفاتحة)</li>
          <li><a href="/api/morphology/search?q=رب">/api/morphology/search?q=رب</a></li>
          <li><a href="/api/morphology/ayah/2/255">/api/morphology/ayah/2/255</a> (آية الكرسي)</li>
          <li><a href="/api/stats">/api/stats</a></li>
        </ul>
      </div>
    </body>
    </html>
    """


# ─────────────────────────────────────────────
#  إعراب الكربلائي
# ─────────────────────────────────────────────

@app.get("/api/irab/search", tags=["إعراب الكربلائي"])
def irab_search(
    q: str = Query(..., description="الكلمة المراد البحث عنها"),
    limit: int = Query(20, ge=1, le=100, description="عدد النتائج"),
    page: int = Query(1, ge=1, description="رقم الصفحة"),
):
    """البحث في إعراب الكربلائي بالكلمة"""
    offset = (page - 1) * limit
    with get_db(IRAB_DB) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM irab_content WHERE word LIKE ? OR explanation LIKE ?",
            (f"%{q}%", f"%{q}%")
        ).fetchone()[0]

        rows = conn.execute(
            """SELECT ic.content_id, ic.word, ic.explanation,
                      am.surah_number, am.ayah_number, am.ayah_harakat
               FROM irab_content ic
               LEFT JOIN (
                   SELECT am2.surah_number, am2.ayah_number, am2.ayah_harakat, je.value AS cid
                   FROM ayah_mapping am2, json_each(am2.content_ids) je
               ) am ON am.cid = ic.content_id
               WHERE ic.word LIKE ? OR ic.explanation LIKE ?
               LIMIT ? OFFSET ?""",
            (f"%{q}%", f"%{q}%", limit, offset),
        ).fetchall()

    return {
        "query": q,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "results": [dict(r) for r in rows],
    }


@app.get("/api/irab/ayah/{surah}/{ayah}", tags=["إعراب الكربلائي"])
def irab_ayah(surah: int, ayah: int):
    """الحصول على إعراب آية محددة"""
    with get_db(IRAB_DB) as conn:
        mapping = conn.execute(
            "SELECT * FROM ayah_mapping WHERE surah_number=? AND ayah_number=?",
            (surah, ayah),
        ).fetchone()

        if not mapping:
            raise HTTPException(status_code=404, detail="الآية غير موجودة")

        content_ids = json.loads(mapping["content_ids"])
        placeholders = ",".join("?" * len(content_ids))
        words = conn.execute(
            f"SELECT * FROM irab_content WHERE content_id IN ({placeholders}) ORDER BY content_id",
            content_ids,
        ).fetchall()

    return {
        "surah": surah,
        "ayah": ayah,
        "ayah_text": mapping["ayah_harakat"],
        "words": [dict(w) for w in words],
    }


@app.get("/api/irab/surah/{surah}", tags=["إعراب الكربلائي"])
def irab_surah(surah: int, page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=50)):
    """الحصول على إعراب سورة كاملة"""
    if not (1 <= surah <= 114):
        raise HTTPException(status_code=400, detail="رقم السورة يجب أن يكون بين 1 و 114")

    offset = (page - 1) * limit
    with get_db(IRAB_DB) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM ayah_mapping WHERE surah_number=?", (surah,)
        ).fetchone()[0]

        mappings = conn.execute(
            "SELECT * FROM ayah_mapping WHERE surah_number=? ORDER BY ayah_number LIMIT ? OFFSET ?",
            (surah, limit, offset),
        ).fetchall()

        result_ayahs = []
        for m in mappings:
            content_ids = json.loads(m["content_ids"])
            placeholders = ",".join("?" * len(content_ids))
            words = conn.execute(
                f"SELECT * FROM irab_content WHERE content_id IN ({placeholders}) ORDER BY content_id",
                content_ids,
            ).fetchall()
            result_ayahs.append({
                "ayah": m["ayah_number"],
                "ayah_text": m["ayah_harakat"],
                "words": [dict(w) for w in words],
            })

    return {
        "surah": surah,
        "total_ayahs": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "ayahs": result_ayahs,
    }


# ─────────────────────────────────────────────
#  MASAQ — التحليل الصرفي والنحوي
# ─────────────────────────────────────────────

@app.get("/api/morphology/search", tags=["التحليل الصرفي MASAQ"])
def morphology_search(
    q: str = Query(..., description="الكلمة أو الجذر للبحث"),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    """البحث في بيانات MASAQ الصرفية"""
    offset = (page - 1) * limit
    with get_db(MASAQ_DB) as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM MASAQ WHERE Word LIKE ? OR Without_Diacritics LIKE ? OR Gloss LIKE ?",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchone()[0]

        rows = conn.execute(
            """SELECT m.*,
                      cm.Desc_Ar  AS case_mood_ar,
                      sr.Desc_Ar  AS syntactic_role_ar,
                      pf.Desc_Ar  AS phrasal_function_ar,
                      p.Desc_Ar   AS phrase_ar
               FROM MASAQ m
               LEFT JOIN case_mood cm ON m.Case_Mood = cm.Tag
               LEFT JOIN Syntactic_Role sr ON m.Syntactic_Role = sr.Tag
               LEFT JOIN Phrasal_Function pf ON m.Phrasal_Function = pf.Tag
               LEFT JOIN Phrase p ON m.Phrase = p.Tag
               WHERE m.Word LIKE ? OR m.Without_Diacritics LIKE ? OR m.Gloss LIKE ?
               LIMIT ? OFFSET ?""",
            (f"%{q}%", f"%{q}%", f"%{q}%", limit, offset),
        ).fetchall()

    return {
        "query": q,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "results": [dict(r) for r in rows],
    }


@app.get("/api/morphology/ayah/{surah}/{ayah}", tags=["التحليل الصرفي MASAQ"])
def morphology_ayah(surah: int, ayah: int):
    """التحليل الصرفي والنحوي لآية محددة"""
    with get_db(MASAQ_DB) as conn:
        rows = conn.execute(
            """SELECT m.*,
                      cm.Desc_Ar  AS case_mood_ar,
                      sr.Desc_Ar  AS syntactic_role_ar,
                      pf.Desc_Ar  AS phrasal_function_ar,
                      p.Desc_Ar   AS phrase_ar,
                      id2.Desc_Ar AS invariable_ar
               FROM MASAQ m
               LEFT JOIN case_mood cm ON m.Case_Mood = cm.Tag
               LEFT JOIN Syntactic_Role sr ON m.Syntactic_Role = sr.Tag
               LEFT JOIN Phrasal_Function pf ON m.Phrasal_Function = pf.Tag
               LEFT JOIN Phrase p ON m.Phrase = p.Tag
               LEFT JOIN invariable_declinable id2 ON m.Invariable_Declinable = id2.Tag
               WHERE m.Sura_No=? AND m.Verse_No=?
               ORDER BY m.Word_No, m.Segment_No""",
            (surah, ayah),
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="الآية غير موجودة")

    words = {}
    for r in rows:
        d = dict(r)
        wn = d["Word_No"]
        if wn not in words:
            words[wn] = {"word_no": wn, "word": d["Word"], "segments": []}
        words[wn]["segments"].append(d)

    return {
        "surah": surah,
        "ayah": ayah,
        "total_segments": len(rows),
        "words": list(words.values()),
    }


@app.get("/api/morphology/word/{surah}/{ayah}/{word_no}", tags=["التحليل الصرفي MASAQ"])
def morphology_word(surah: int, ayah: int, word_no: int):
    """التحليل الصرفي والنحوي لكلمة محددة"""
    with get_db(MASAQ_DB) as conn:
        rows = conn.execute(
            """SELECT m.*,
                      cm.Desc_Ar  AS case_mood_ar,
                      cm.Desc_Eng AS case_mood_en,
                      sr.Desc_Ar  AS syntactic_role_ar,
                      pf.Desc_Ar  AS phrasal_function_ar,
                      p.Desc_Ar   AS phrase_ar,
                      id2.Desc_Ar AS invariable_ar
               FROM MASAQ m
               LEFT JOIN case_mood cm ON m.Case_Mood = cm.Tag
               LEFT JOIN Syntactic_Role sr ON m.Syntactic_Role = sr.Tag
               LEFT JOIN Phrasal_Function pf ON m.Phrasal_Function = pf.Tag
               LEFT JOIN Phrase p ON m.Phrase = p.Tag
               LEFT JOIN invariable_declinable id2 ON m.Invariable_Declinable = id2.Tag
               WHERE m.Sura_No=? AND m.Verse_No=? AND m.Word_No=?
               ORDER BY m.Segment_No""",
            (surah, ayah, word_no),
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="الكلمة غير موجودة")

    return {
        "surah": surah,
        "ayah": ayah,
        "word_no": word_no,
        "word": rows[0]["Word"],
        "gloss": rows[0]["Gloss"],
        "segments": [dict(r) for r in rows],
    }


@app.get("/api/morphology/surah/{surah}", tags=["التحليل الصرفي MASAQ"])
def morphology_surah(surah: int, page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=50)):
    """التحليل الصرفي لسورة كاملة"""
    if not (1 <= surah <= 114):
        raise HTTPException(status_code=400, detail="رقم السورة بين 1 و 114")

    offset = (page - 1) * limit
    with get_db(MASAQ_DB) as conn:
        total_ayahs = conn.execute(
            "SELECT COUNT(DISTINCT Verse_No) FROM MASAQ WHERE Sura_No=?", (surah,)
        ).fetchone()[0]

        ayah_nums = conn.execute(
            "SELECT DISTINCT Verse_No FROM MASAQ WHERE Sura_No=? ORDER BY Verse_No LIMIT ? OFFSET ?",
            (surah, limit, offset),
        ).fetchall()

        result = []
        for (verse_no,) in ayah_nums:
            rows = conn.execute(
                """SELECT m.*, cm.Desc_Ar AS case_mood_ar, sr.Desc_Ar AS syntactic_role_ar
                   FROM MASAQ m
                   LEFT JOIN case_mood cm ON m.Case_Mood = cm.Tag
                   LEFT JOIN Syntactic_Role sr ON m.Syntactic_Role = sr.Tag
                   WHERE m.Sura_No=? AND m.Verse_No=?
                   ORDER BY m.Word_No, m.Segment_No""",
                (surah, verse_no),
            ).fetchall()
            result.append({"ayah": verse_no, "segments": [dict(r) for r in rows]})

    return {
        "surah": surah,
        "total_ayahs": total_ayahs,
        "page": page,
        "limit": limit,
        "pages": (total_ayahs + limit - 1) // limit,
        "ayahs": result,
    }


# ─────────────────────────────────────────────
#  إحصاءات
# ─────────────────────────────────────────────

@app.get("/api/stats", tags=["عام"])
def stats():
    """إحصاءات قواعد البيانات"""
    with get_db(IRAB_DB) as conn:
        irab_words = conn.execute("SELECT COUNT(*) FROM irab_content").fetchone()[0]
        irab_ayahs = conn.execute("SELECT COUNT(*) FROM ayah_mapping").fetchone()[0]
        irab_surahs = conn.execute("SELECT COUNT(DISTINCT surah_number) FROM ayah_mapping").fetchone()[0]

    with get_db(MASAQ_DB) as conn:
        masaq_rows = conn.execute("SELECT COUNT(*) FROM MASAQ").fetchone()[0]
        masaq_suras = conn.execute("SELECT COUNT(DISTINCT Sura_No) FROM MASAQ").fetchone()[0]
        masaq_ayahs = conn.execute("SELECT COUNT(DISTINCT Sura_No || '-' || Verse_No) FROM MASAQ").fetchone()[0]

    return {
        "irab_al_karbasi": {
            "total_words": irab_words,
            "total_ayahs": irab_ayahs,
            "total_surahs": irab_surahs,
            "source": "إعراب الكربلائي",
        },
        "masaq": {
            "total_segments": masaq_rows,
            "total_surahs": masaq_suras,
            "total_ayahs": masaq_ayahs,
            "source": "MASAQ Dataset — Mendeley",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
