import json
import math
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, time, timedelta

import streamlit as st

st.set_page_config(
    page_title="TeacherPlan AI | 교사 일정 플래너",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# 디자인 및 기본 설정
# -----------------------------
st.markdown("""
<style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 1500px;}
    .hero {
        padding: 1.35rem 1.5rem; border-radius: 20px;
        background: linear-gradient(120deg, #172554 0%, #1e3a8a 55%, #0f766e 100%);
        color: white; margin-bottom: 1.2rem;
    }
    .hero h1 {font-size: 2rem; margin: 0 0 .35rem 0; color: white;}
    .hero p {margin: 0; color: #dbeafe; font-size: 1rem;}
    .metric-card {
        padding: 1rem; border: 1px solid rgba(128,128,128,.25);
        border-radius: 14px; min-height: 95px;
    }
    .metric-label {font-size: .85rem; opacity: .75; margin-bottom: .3rem;}
    .metric-value {font-size: 1.55rem; font-weight: 750;}
    .task-card {
        border: 1px solid rgba(128,128,128,.25); border-left: 5px solid #64748b;
        border-radius: 12px; padding: .75rem .85rem; margin-bottom: .65rem;
    }
    .task-title {font-weight: 700; font-size: 1rem; margin-bottom: .25rem;}
    .task-meta {font-size: .84rem; opacity: .78; line-height: 1.55;}
    .reason {font-size: .88rem; margin-top: .45rem; line-height: 1.5;}
    .section-note {opacity: .72; font-size: .9rem;}
    div[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.2); padding: .75rem; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

IMPORTANCE = {"높음": 3, "보통": 2, "낮음": 1}
COLORS = {"높음": "#EF4444", "보통": "#F59E0B", "낮음": "#10B981"}
TASK_TYPES = [
    "수업", "수업 준비", "시험·평가", "채점", "학생 상담", "학부모 연락",
    "생활기록부·기록", "행정 업무", "회의", "연수·자기계발", "휴식·식사", "기타"
]

def minutes_of(t):
    return t.hour * 60 + t.minute

def hhmm(value):
    return f"{value // 60:02d}:{value % 60:02d}"

def parse_hhmm(value):
    try:
        h, m = str(value).split(":")
        h, m = int(h), int(m)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h * 60 + m
    except (ValueError, TypeError):
        pass
    return None

def teacher_examples():
    return [
        {"id":"T1","name":"1교시 수학 수업","task_type":"수업","subject":"수학","class_name":"1학년 2반","duration":50,"importance":"높음","earliest":"09:00","deadline":"09:50","fixed":True,"fixed_start":"09:00","detail":"수업 자료와 출석 확인"},
        {"id":"T2","name":"수행평가 채점","task_type":"채점","subject":"수학","class_name":"2학년","duration":60,"importance":"높음","earliest":"10:00","deadline":"16:00","fixed":False,"fixed_start":"","detail":"평가 기준표에 따라 공정하게 채점"},
        {"id":"T3","name":"다음 수업 자료 준비","task_type":"수업 준비","subject":"수학","class_name":"1학년","duration":45,"importance":"높음","earliest":"10:00","deadline":"15:00","fixed":False,"fixed_start":"","detail":"활동지와 판서 계획 점검"},
        {"id":"T4","name":"학생 상담","task_type":"학생 상담","subject":"","class_name":"3학년 학생","duration":30,"importance":"보통","earliest":"13:00","deadline":"16:30","fixed":False,"fixed_start":"","detail":"상담 후 필요한 후속 조치 기록"},
        {"id":"T5","name":"학부모 연락","task_type":"학부모 연락","subject":"","class_name":"2학년 학부모","duration":20,"importance":"보통","earliest":"13:00","deadline":"17:00","fixed":False,"fixed_start":"","detail":"학생의 학습 상황과 지원 방법 공유"},
        {"id":"T6","name":"수업 후 기록 정리","task_type":"생활기록부·기록","subject":"","class_name":"1학년","duration":25,"importance":"낮음","earliest":"15:00","deadline":"17:00","fixed":False,"fixed_start":"","detail":"수업 내용과 특이사항 간단히 정리"},
    ]

def task_payload(tasks):
    return [{
        "id": t["id"], "name": t["name"], "task_type": t["task_type"],
        "subject": t.get("subject", ""), "class_name": t.get("class_name", ""),
        "duration": int(t["duration"]), "importance": t["importance"],
        "earliest": t["earliest"], "deadline": t["deadline"],
        "fixed": bool(t["fixed"]), "fixed_start": t.get("fixed_start", ""),
        "detail": t.get("detail", "")
    } for t in tasks]

def overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end

def validate_schedule(schedule, tasks, day_start, day_end):
    task_by_id = {t["id"]: t for t in tasks}
    seen = set()
    errors = []
    cleaned = []

    if not isinstance(schedule, list):
        return None, ["AI 응답이 일정 목록 형식이 아닙니다."]

    for item in schedule:
        if not isinstance(item, dict):
            errors.append("일정 항목의 형식이 올바르지 않습니다.")
            continue
        tid = str(item.get("id", ""))
        if tid not in task_by_id:
            errors.append(f"등록되지 않은 일정 ID가 포함되었습니다: {tid}")
            continue
        if tid in seen:
            errors.append(f"같은 일정이 중복 배치되었습니다: {task_by_id[tid]['name']}")
            continue
        seen.add(tid)
        task = task_by_id[tid]
        start = parse_hhmm(item.get("start"))
        end = parse_hhmm(item.get("end"))
        if start is None or end is None or end <= start:
            errors.append(f"{task['name']}: 시작/종료 시간이 올바르지 않습니다.")
            continue
        if end - start != int(task["duration"]):
            errors.append(f"{task['name']}: 입력한 소요 시간 {task['duration']}분과 배치 시간이 다릅니다.")
            continue
        if start < day_start or end > day_end:
            errors.append(f"{task['name']}: 설정한 하루 일정 시간 범위를 벗어났습니다.")
            continue
        earliest = parse_hhmm(task["earliest"])
        deadline = parse_hhmm(task["deadline"])
        if earliest is not None and start < earliest:
            errors.append(f"{task['name']}: 가능한 시작 시간보다 빠릅니다.")
            continue
        if deadline is not None and end > deadline:
            errors.append(f"{task['name']}: 마감 시간 이후에 끝납니다.")
            continue
        if task["fixed"]:
            fixed_start = parse_hhmm(task["fixed_start"])
            if fixed_start is None or start != fixed_start:
                errors.append(f"{task['name']}: 고정 일정 시간이 변경되었습니다.")
                continue
        cleaned.append({
            **task, "start_min": start, "end_min": end,
            "start": hhmm(start), "end": hhmm(end),
            "reason": str(item.get("reason", "")).strip() or "업무 조건과 중요도를 고려해 배치했습니다.",
            "advice": str(item.get("advice", "")).strip() or "완료 후 결과를 간단히 기록하세요."
        })

    for i, a in enumerate(cleaned):
        for b in cleaned[i + 1:]:
            if overlaps(a["start_min"], a["end_min"], b["start_min"], b["end_min"]):
                errors.append(f"일정이 겹칩니다: {a['name']} / {b['name']}")

    if errors:
        return None, errors

    # AI가 일부 작업을 누락하면 잘못된 완성 일정으로 취급하지 않음
    missing = [t["name"] for t in tasks if t["id"] not in seen]
    if missing:
        errors.append("배치되지 않은 일정: " + ", ".join(missing))
        return None, errors

    return sorted(cleaned, key=lambda x: x["start_min"]), []

def fallback_schedule(tasks, day_start, day_end):
    """API가 없거나 실패한 경우 사용할 간단한 제약 기반 배치."""
    fixed_tasks, flexible = [], []
    for t in tasks:
        earliest = parse_hhmm(t["earliest"])
        deadline = parse_hhmm(t["deadline"])
        if t["fixed"]:
            start = parse_hhmm(t["fixed_start"])
            if start is None:
                raise ValueError(f"{t['name']}: 고정 시작 시간을 입력해 주세요.")
            end = start + int(t["duration"])
            if start < day_start or end > day_end:
                raise ValueError(f"{t['name']}: 고정 일정이 하루 일정 시간 범위를 벗어납니다.")
            if earliest is not None and start < earliest:
                raise ValueError(f"{t['name']}: 고정 시작 시간이 가능한 시작 시간보다 빠릅니다.")
            if deadline is not None and end > deadline:
                raise ValueError(f"{t['name']}: 고정 일정이 마감 시간을 넘깁니다.")
            fixed_tasks.append({**t, "start_min":start, "end_min":end, "start":hhmm(start), "end":hhmm(end),
                                "reason":"사용자가 지정한 고정 시간을 유지했습니다.",
                                "advice":"수업·회의 등 고정 일정 직전에 필요한 자료를 확인하세요."})
        else:
            flexible.append(t)

    fixed_tasks.sort(key=lambda x: x["start_min"])
    for i, a in enumerate(fixed_tasks):
        for b in fixed_tasks[i + 1:]:
            if overlaps(a["start_min"], a["end_min"], b["start_min"], b["end_min"]):
                raise ValueError(f"고정 일정끼리 시간이 겹칩니다: {a['name']} / {b['name']}")

    flexible.sort(key=lambda t: (
        -IMPORTANCE.get(t["importance"], 1),
        parse_hhmm(t["deadline"]) if parse_hhmm(t["deadline"]) is not None else 1440,
        -int(t["duration"])
    ))
    result = fixed_tasks[:]
    for t in flexible:
        duration = int(t["duration"])
        earliest = max(day_start, parse_hhmm(t["earliest"]) or day_start)
        deadline = min(day_end, parse_hhmm(t["deadline"]) if parse_hhmm(t["deadline"]) is not None else day_end)
        if deadline - duration < earliest:
            raise ValueError(f"{t['name']}: 가능한 시간과 마감 시간 사이에 소요 시간을 확보할 수 없습니다.")
        candidate = earliest
        placed = False
        while candidate + duration <= deadline:
            collision = None
            for existing in sorted(result, key=lambda x: x["start_min"]):
                if overlaps(candidate, candidate + duration, existing["start_min"], existing["end_min"]):
                    collision = existing
                    break
            if collision is None:
                result.append({**t, "start_min":candidate, "end_min":candidate+duration,
                               "start":hhmm(candidate), "end":hhmm(candidate+duration),
                               "reason":f"{t['importance']} 중요도와 마감 시간을 고려해 가능한 이른 시간에 배치했습니다.",
                               "advice":"업무 종료 후 결과를 기록하고, 예상보다 오래 걸리면 여유 시간에 조정하세요."})
                placed = True
                break
            candidate = collision["end_min"]
        if not placed:
            raise ValueError(f"{t['name']}: 다른 일정과 겹치지 않는 시간대를 찾지 못했습니다. 소요 시간이나 마감 시간을 조정해 주세요.")
    return sorted(result, key=lambda x: x["start_min"])

def call_gemini(tasks, requirements, day_start, day_end):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key = ""
    if not api_key:
        return None, "GEMINI_API_KEY가 설정되지 않아 기본 일정 배치 기능을 사용합니다."

    prompt = f"""
당신은 교사의 하루 업무를 배치하는 일정 설계 도우미입니다.
아래 작업을 가능한 한 모두 배치하고, 업무 사이 충돌이 없도록 하세요.
- 하루 배치 가능 범위: {hhmm(day_start)}부터 {hhmm(day_end)}까지
- 우선순위: 높음 > 보통 > 낮음
- earliest는 해당 시간 이전에 시작할 수 없다는 뜻입니다.
- deadline은 해당 시간까지 작업을 끝내야 한다는 뜻입니다.
- fixed=true인 일정은 fixed_start에 반드시 시작해야 합니다.
- 각 작업의 duration(분)을 정확히 지키세요.
- 시간이 남으면 무리하게 일을 늘리지 말고 여유 시간으로 남겨두세요.
- 교사의 수업, 평가, 채점, 상담, 학부모 연락, 기록, 행정 업무의 특성을 고려하세요.
- 배치가 불가능하면 억지로 시간을 겹치지 말고 "error"에 이유를 적으세요.
추가 요구사항: {requirements or "별도 요구사항 없음"}
작업 목록:
{json.dumps(task_payload(tasks), ensure_ascii=False)}
반드시 JSON 객체만 반환하세요. 형식:
{{
 "schedule":[
  {{"id":"T1","start":"09:00","end":"09:50","reason":"배치 이유","advice":"실행 조언"}}
 ],
 "error":"불가능한 경우 이유, 가능하면 빈 문자열"
}}
"""
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?" + urllib.parse.urlencode({"key": api_key})
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }
    request = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(text)
        if result.get("error"):
            return None, "AI가 일정 배치의 어려움을 보고했습니다: " + str(result["error"])
        checked, errors = validate_schedule(result.get("schedule"), tasks, day_start, day_end)
        if errors:
            return None, "AI 결과를 검증하는 과정에서 문제가 발견되어 기본 배치 기능으로 전환합니다. " + " ".join(errors[:3])
        return checked, "Gemini AI가 교사 업무의 중요도와 시간 제약을 반영했습니다."
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8")[:300]
        except Exception:
            pass
        return None, f"Gemini API 오류({e.code}). API 키·사용 권한·할당량을 확인하세요. {detail}"
    except urllib.error.URLError:
        return None, "네트워크 연결 문제로 AI에 연결할 수 없습니다."
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None, "AI 응답을 읽을 수 없어 기본 배치 기능으로 전환합니다."
    except Exception as e:
        return None, f"AI 처리 중 예상하지 못한 오류가 발생했습니다: {e}"

def make_clock_svg(schedule, day_start, day_end):
    size, center, radius = 440, 220, 160
    def point(minute, r=radius):
        angle = (minute / 1440) * 2 * math.pi - math.pi / 2
        return center + r * math.cos(angle), center + r * math.sin(angle)
    def arc_path(start, end, r):
        x1, y1 = point(start, r)
        x2, y2 = point(end, r)
        large = 1 if end - start > 720 else 0
        return f"M {x1:.2f} {y1:.2f} A {r} {r} 0 {large} 1 {x2:.2f} {y2:.2f}"
    svg = [f'<svg viewBox="0 0 {size} {size}" width="100%" role="img" aria-label="원형 24시간 일정표">']
    svg.append(f'<circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="#94a3b8" stroke-opacity=".28" stroke-width="22"/>')
    # 시간 눈금과 라벨
    for hour in range(24):
        minute = hour * 60
        x1, y1 = point(minute, radius + 15)
        x2, y2 = point(minute, radius + (25 if hour % 6 == 0 else 19))
        svg.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#64748b" stroke-width="{2 if hour%6==0 else 1}" opacity=".8"/>')
        if hour % 3 == 0:
            tx, ty = point(minute, radius + 42)
            svg.append(f'<text x="{tx:.2f}" y="{ty+4:.2f}" text-anchor="middle" font-size="12" fill="currentColor">{hour:02d}</text>')
    # 일정은 바깥쪽 트랙에 표시. 24시를 넘지 않게 일정 검증에서 제약.
    for item in schedule:
        start, end = item["start_min"], item["end_min"]
        # 짧은 작업도 보이도록 최소 각도 폭을 보정하되 실제 시각 표시는 일정 목록을 기준으로 확인
        if end - start < 18:
            mid = (start + end) / 2
            start, end = mid - 9, mid + 9
        color = COLORS.get(item["importance"], "#64748b")
        svg.append(f'<path d="{arc_path(start, end, radius)}" fill="none" stroke="{color}" stroke-width="20" stroke-linecap="round"/>')
    svg.append(f'<circle cx="{center}" cy="{center}" r="118" fill="none" stroke="#94a3b8" stroke-opacity=".18" stroke-width="1"/>')
    svg.append(f'<text x="{center}" y="{center-18}" text-anchor="middle" font-size="18" font-weight="700" fill="currentColor">오늘의 일정</text>')
    svg.append(f'<text x="{center}" y="{center+12}" text-anchor="middle" font-size="28" font-weight="800" fill="currentColor">{len(schedule)}개</text>')
    total = sum(x["end_min"]-x["start_min"] for x in schedule)
    svg.append(f'<text x="{center}" y="{center+38}" text-anchor="middle" font-size="13" fill="currentColor">업무 {total//60}시간 {total%60}분</text>')
    svg.append('</svg>')
    return "".join(svg)

def render_schedule_cards(schedule):
    if not schedule:
        st.info("아직 배치된 일정이 없습니다. 왼쪽에서 일정을 입력하고 시간표를 생성해 주세요.")
        return
    for item in schedule:
        color = COLORS.get(item["importance"], "#64748b")
        title = item["name"]
        details = [item["task_type"]]
        if item.get("subject"): details.append(item["subject"])
        if item.get("class_name"): details.append(item["class_name"])
        details.append(f"{item['duration']}분")
        if item.get("fixed"): details.append("고정 일정")
        st.markdown(f"""
        <div class="task-card" style="border-left-color:{color}">
          <div class="task-title">{item['start']}–{item['end']}　{title}</div>
          <div class="task-meta">{' · '.join(details)}　|　중요도: {item['importance']}</div>
          <div class="reason"><b>배치 이유</b>　{item.get('reason','')}</div>
          <div class="reason"><b>실행 조언</b>　{item.get('advice','')}</div>
        </div>
        """, unsafe_allow_html=True)

def safe_text(value):
    # 텍스트가 HTML로 해석되지 않도록 기본 치환
    return (str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#x27;"))

# -----------------------------
# 헤더
# -----------------------------
st.markdown("""
<div class="hero">
  <h1>🗓️ TeacherPlan AI</h1>
  <p>교사의 수업·채점·상담·행정 업무를 한눈에 정리하는 하루 일정 플래너</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 하루 시간 설정")
    start_time = st.time_input("일정 시작 시간", value=time(8, 30), key="day_start")
    end_time = st.time_input("일정 종료 시간", value=time(17, 30), key="day_end")
    st.caption("고정 일정은 반드시 지정한 시간에 배치됩니다.")
    st.divider()
    st.markdown("**중요도 색상**")
    st.markdown("🔴 높음　🟠 보통　🟢 낮음")
    st.caption("원형 시간표는 24시간 기준이며, 오른쪽 목록에서 정확한 시간과 세부 내용을 확인할 수 있습니다.")

day_start, day_end = minutes_of(start_time), minutes_of(end_time)
if day_end <= day_start:
    st.error("종료 시간은 시작 시간보다 늦어야 합니다.")
    st.stop()

# Session state
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "schedule" not in st.session_state:
    st.session_state.schedule = []
if "schedule_note" not in st.session_state:
    st.session_state.schedule_note = ""

# Summary metrics
scheduled = st.session_state.schedule
work_minutes = sum(x["end_min"] - x["start_min"] for x in scheduled)
window_minutes = day_end - day_start
free_minutes = max(0, window_minutes - work_minutes)
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">등록된 업무</div><div class="metric-value">{len(st.session_state.tasks)}개</div></div>', unsafe_allow_html=True)
with m2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">배치된 업무 시간</div><div class="metric-value">{work_minutes//60}시간 {work_minutes%60}분</div></div>', unsafe_allow_html=True)
with m3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">설정 범위 내 여유 시간</div><div class="metric-value">{free_minutes//60}시간 {free_minutes%60}분</div></div>', unsafe_allow_html=True)

st.divider()
left, right = st.columns([1.0, 1.05], gap="large")

with left:
    st.subheader("① 교사 업무 입력")
    st.markdown('<div class="section-note">일정별 시간·중요도·마감 조건을 입력하세요.</div>', unsafe_allow_html=True)

    with st.form("task_form", clear_on_submit=True):
        task_name = st.text_input("일정 이름 *", placeholder="예: 2학년 수행평가 채점")
        c1, c2 = st.columns(2)
        with c1:
            task_type = st.selectbox("업무 종류", TASK_TYPES)
            subject = st.text_input("과목", placeholder="예: 수학")
            duration = st.number_input("예상 소요 시간(분)", min_value=5, max_value=600, value=30, step=5)
        with c2:
            importance = st.selectbox("중요도", ["높음", "보통", "낮음"])
            class_name = st.text_input("학년·학급", placeholder="예: 2학년 1반")
            earliest_time = st.time_input("가장 빠른 시작 시간", value=start_time, key="earliest_input")
        c3, c4 = st.columns(2)
        with c3:
            deadline_time = st.time_input("마감 시간", value=end_time, key="deadline_input")
        with c4:
            fixed = st.checkbox("고정 일정 (수업·회의 등)")
            fixed_time = st.time_input("고정 시작 시간", value=time(9, 0), key="fixed_input")
        detail = st.text_area("세부 내용", placeholder="예: 평가 기준표 확인 후 채점 결과 입력", height=80)
        submitted = st.form_submit_button("＋ 일정 추가", use_container_width=True)

    if submitted:
        if not task_name.strip():
            st.error("일정 이름을 입력해 주세요.")
        elif minutes_of(deadline_time) <= minutes_of(earliest_time):
            st.error("마감 시간은 가장 빠른 시작 시간보다 늦어야 합니다.")
        elif fixed and (minutes_of(fixed_time) < minutes_of(earliest_time) or minutes_of(fixed_time) + int(duration) > minutes_of(deadline_time)):
            st.error("고정 시작 시간과 소요 시간이 가능한 시간 범위 및 마감 시간 안에 들어오도록 설정해 주세요.")
        else:
            next_id = f"T{int(datetime.now().timestamp() * 1000)}"
            st.session_state.tasks.append({
                "id":next_id, "name":task_name.strip(), "task_type":task_type,
                "subject":subject.strip(), "class_name":class_name.strip(),
                "duration":int(duration), "importance":importance,
                "earliest":earliest_time.strftime("%H:%M"),
                "deadline":deadline_time.strftime("%H:%M"),
                "fixed":fixed, "fixed_start":fixed_time.strftime("%H:%M") if fixed else "",
                "detail":detail.strip()
            })
            st.success("일정을 추가했습니다.")
            st.rerun()

    ca, cb = st.columns(2)
    with ca:
        if st.button("예시 일정 불러오기", use_container_width=True):
            st.session_state.tasks = teacher_examples()
            st.session_state.schedule = []
            st.session_state.schedule_note = ""
            st.rerun()
    with cb:
        if st.button("전체 일정 비우기", use_container_width=True):
            st.session_state.tasks = []
            st.session_state.schedule = []
            st.session_state.schedule_note = ""
            st.rerun()

    st.markdown("#### 등록된 일정")
    if not st.session_state.tasks:
        st.info("예시 일정을 불러오거나 위 입력란에서 업무를 추가하세요.")
    else:
        for idx, task in enumerate(st.session_state.tasks):
            with st.container(border=True):
                c_title, c_del = st.columns([5, 1])
                with c_title:
                    st.markdown(f"**{task['name']}**")
                    extra = " · ".join(x for x in [task["task_type"], task.get("subject",""), task.get("class_name","")] if x)
                    st.caption(f"{extra} · {task['duration']}분 · 중요도 {task['importance']}")
                    st.caption(f"{task['earliest']}부터 / {task['deadline']}까지" + (f" · 고정 {task['fixed_start']}" if task["fixed"] else ""))
                with c_del:
                    if st.button("삭제", key=f"delete_{task['id']}", use_container_width=True):
                        removed_id = task["id"]
                        st.session_state.tasks = [x for x in st.session_state.tasks if x["id"] != removed_id]
                        st.session_state.schedule = []
                        st.rerun()

    st.markdown("#### 추가 요구사항")
    requirements = st.text_area(
        "AI에게 전달할 조건",
        placeholder="예: 채점 업무는 집중력이 높은 오전에 배치하고, 상담 전후 10분 여유를 두세요.",
        height=100,
        label_visibility="collapsed",
        key="requirements"
    )
    generate = st.button("✨ 하루 일정 생성", type="primary", use_container_width=True, disabled=not st.session_state.tasks)

    if generate:
        try:
            with st.spinner("업무 조건을 확인하고 일정을 구성하고 있습니다..."):
                ai_schedule, note = call_gemini(st.session_state.tasks, requirements, day_start, day_end)
                if ai_schedule is not None:
                    st.session_state.schedule = ai_schedule
                    st.session_state.schedule_note = note
                else:
                    fallback = fallback_schedule(st.session_state.tasks, day_start, day_end)
                    st.session_state.schedule = fallback
                    st.session_state.schedule_note = note + " 기본 배치 결과를 표시합니다."
            st.rerun()
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"일정 생성 중 문제가 발생했습니다: {e}")

with right:
    st.subheader("② 원형 시간표와 일정 목록")
    st.markdown('<div class="section-note">원형에서 하루 흐름을 확인하고, 바로 옆 목록에서 각 일정의 정확한 시간·배치 이유·실행 조언을 확인하세요.</div>', unsafe_allow_html=True)
    if st.session_state.schedule_note:
        st.caption("ℹ️ " + st.session_state.schedule_note)

    if st.session_state.schedule:
        # 요청한 핵심 레이아웃: 원형 시간표 바로 옆에 일정 목록
        clock_col, list_col = st.columns([0.95, 1.05], gap="medium")
        with clock_col:
            st.markdown("**24시간 흐름**")
            svg = make_clock_svg(st.session_state.schedule, day_start, day_end)
            st.markdown(svg, unsafe_allow_html=True)
            st.markdown("""
            <div style="display:flex;gap:.6rem;flex-wrap:wrap;font-size:.8rem;opacity:.85;margin-top:.25rem">
              <span>🔴 높음</span><span>🟠 보통</span><span>🟢 낮음</span>
            </div>
            """, unsafe_allow_html=True)
        with list_col:
            st.markdown("**시간순 일정 목록**")
            render_schedule_cards(st.session_state.schedule)

        st.divider()
        st.markdown("#### 시간순 전체 일정")
        table_rows = [{
            "시작":x["start"], "종료":x["end"], "일정":x["name"],
            "업무 종류":x["task_type"], "소요(분)":x["duration"],
            "중요도":x["importance"], "고정": "예" if x["fixed"] else "아니오",
            "배치 이유":x.get("reason",""), "실행 조언":x.get("advice","")
        } for x in st.session_state.schedule]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        csv_text = __import__("pandas").DataFrame(table_rows).to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ 일정표 CSV 다운로드", data=csv_text, file_name="teacher_schedule.csv",
                           mime="text/csv", use_container_width=True)
    else:
        st.markdown("""
        <div style="border:1px dashed #94a3b8;border-radius:18px;padding:2rem 1.2rem;text-align:center;opacity:.85">
          <div style="font-size:2.4rem">🕒</div>
          <h3>아직 생성된 시간표가 없습니다</h3>
          <p>왼쪽에서 업무를 입력하거나 예시 일정을 불러온 다음<br> <b>하루 일정 생성</b> 버튼을 눌러주세요.</p>
          <p>생성 후에는 원형 시간표와 상세 일정 목록이 나란히 표시됩니다.</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.caption("TeacherPlan AI · AI가 제안한 일정은 실제 수업 시간표·학교 규정·긴급 업무와 대조한 뒤 사용하세요.")
