
import streamlit as st
import json
import csv
import io
import math
import re
import urllib.request
import urllib.error
from datetime import date, time


# ==================================================
# 1. 페이지 설정 및 디자인
# ==================================================
st.set_page_config(
    page_title="PlanAI | 원형 일정 플래너",
    page_icon="🕒",
    layout="wide",
)

st.markdown("""
<style>
.block-container {
    max-width: 1250px;
    padding-top: 1.8rem;
}
.hero {
    background: linear-gradient(125deg, #172554, #4338ca);
    padding: 26px;
    border-radius: 20px;
    color: white;
    margin-bottom: 22px;
}
.hero h1 { color: white; margin-bottom: 7px; }
.hero p { color: #e0e7ff; margin-bottom: 0; }
.task-card {
    border: 1px solid rgba(128,128,128,.3);
    border-radius: 12px;
    padding: 12px 15px;
    margin: 8px 0;
}
.small-muted { color: #777; font-size: .88rem; }
</style>

<div class="hero">
    <h1>🕒 PlanAI</h1>
    <p>중요도를 분석하고 하루를 원형 시간표로 설계하는 AI 플래너</p>
</div>
""", unsafe_allow_html=True)


# ==================================================
# 2. 공통 함수
# ==================================================
COLORS = {
    "높음": "#EF4444",
    "보통": "#F59E0B",
    "낮음": "#10B981",
}

def minutes(value):
    return value.hour * 60 + value.minute


def parse_minutes(value):
    h, m = map(int, str(value).split(":"))
    return h * 60 + m


def hhmm(value):
    return f"{int(value) // 60:02d}:{int(value) % 60:02d}"


def duration_text(value):
    h, m = divmod(int(value), 60)
    if h and m:
        return f"{h}시간 {m}분"
    if h:
        return f"{h}시간"
    return f"{m}분"


def priority_score(value):
    return {"높음": 3, "보통": 2, "낮음": 1}.get(value, 1)


def overlaps(a, b, c, d):
    return a < d and c < b


# ==================================================
# 3. 원형 시간표 SVG
#    하루 24시간을 시계 형태로 표현
# ==================================================
def make_clock_svg(schedule):
    cx, cy = 190, 190
    radius = 120
    stroke_width = 22

    def point(minute, r):
        angle = 2 * math.pi * minute / 1440 - math.pi / 2
        return (
            cx + r * math.cos(angle),
            cy + r * math.sin(angle),
        )

    def arc_path(start, end):
        # 24:00 경계를 넘지 않는 하루 단위 일정
        x1, y1 = point(start, radius)
        x2, y2 = point(end, radius)
        large_arc = 1 if end - start > 720 else 0
        return (
            f"M {x1:.2f} {y1:.2f} "
            f"A {radius} {radius} 0 {large_arc} 1 "
            f"{x2:.2f} {y2:.2f}"
        )

    parts = [
        f'<svg viewBox="0 0 380 380" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="24시간 원형 일정표">',
        '<rect width="380" height="380" rx="24" fill="transparent"/>',
        # 하루 전체를 나타내는 원
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
        'fill="none" stroke="#94A3B8" stroke-opacity=".2" '
        f'stroke-width="{stroke_width}"/>',
    ]

    # 24시간 눈금
    for hour in range(24):
        angle = 2 * math.pi * hour / 24 - math.pi / 2
        inner = radius + 17
        outer = radius + (27 if hour % 6 == 0 else 21)

        x1 = cx + inner * math.cos(angle)
        y1 = cy + inner * math.sin(angle)
        x2 = cx + outer * math.cos(angle)
        y2 = cy + outer * math.sin(angle)

        parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" '
            f'x2="{x2:.2f}" y2="{y2:.2f}" '
            'stroke="#94A3B8" stroke-width="1.5"/>'
        )

    # 일정별 색상 구간
    for item in schedule:
        start = item["start_min"]
        end = item["end_min"]

        if end <= start:
            continue

        color = COLORS.get(item["importance"], "#64748B")

        parts.append(
            f'<path d="{arc_path(start, end)}" '
            f'fill="none" stroke="{color}" '
            f'stroke-width="{stroke_width}" '
            'stroke-linecap="butt"/>'
        )

    # 00, 06, 12, 18시 라벨
    for hour in [0, 6, 12, 18]:
        angle = 2 * math.pi * hour / 24 - math.pi / 2
        r = 158
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle) + 5

        parts.append(
            f'<text x="{x:.2f}" y="{y:.2f}" '
            'font-size="12" text-anchor="middle" '
            'fill="currentColor">'
            f'{hour:02d}:00</text>'
        )

    parts.extend([
        f'<circle cx="{cx}" cy="{cy}" r="84" '
        'fill="none" stroke="#94A3B8" stroke-opacity=".18"/>',
        f'<text x="{cx}" y="178" text-anchor="middle" '
        'font-size="14" fill="currentColor">TODAY</text>',
        f'<text x="{cx}" y="207" text-anchor="middle" '
        'font-size="26" font-weight="700" fill="currentColor">'
        f'{len(schedule)}개</text>',
        f'<text x="{cx}" y="228" text-anchor="middle" '
        'font-size="12" fill="currentColor">배정된 일정</text>',
        '</svg>',
    ])

    return "".join(parts)


# ==================================================
# 4. 기본 일정 생성기
#    API가 없거나 실패했을 때도 작동
# ==================================================
def fallback_schedule(tasks, day_start, day_end, break_min):
    scheduled = []
    unscheduled = []
    occupied = []

    def place(task, start):
        end = start + task["duration"]
        scheduled.append({
            **task,
            "start_min": start,
            "end_min": end,
            "reason": (
                "사용자가 지정한 고정 시간"
                if task["fixed"]
                else "중요도와 마감 시간을 고려해 자동 배치"
            ),
        })
        occupied.append((start, end))

    fixed_tasks = sorted(
        [t for t in tasks if t["fixed"]],
        key=lambda t: parse_minutes(t["fixed_start"]),
    )

    for task in fixed_tasks:
        start = parse_minutes(task["fixed_start"])
        end = start + task["duration"]

        valid = (
            start >= day_start
            and end <= day_end
            and start >= parse_minutes(task["earliest"])
            and end <= parse_minutes(task["deadline"])
            and not any(overlaps(start, end, a, b) for a, b in occupied)
        )

        if valid:
            place(task, start)
        else:
            unscheduled.append({
                **task,
                "reason": "고정 시간이 다른 일정 또는 시간 제약과 충돌합니다.",
            })

    flexible = sorted(
        [t for t in tasks if not t["fixed"]],
        key=lambda t: (
            -priority_score(t["importance"]),
            parse_minutes(t["deadline"]),
        ),
    )

    for task in flexible:
        earliest = max(day_start, parse_minutes(task["earliest"]))
        deadline = min(day_end, parse_minutes(task["deadline"]))
        candidate = earliest
        placed = False

        while candidate + task["duration"] <= deadline:
            end = candidate + task["duration"]

            conflict = next(
                (
                    (a, b) for a, b in occupied
                    if overlaps(candidate, end, a, b)
                ),
                None,
            )

            if conflict:
                candidate = conflict[1] + break_min
                continue

            place(task, candidate)
            placed = True
            break

        if not placed:
            unscheduled.append({
                **task,
                "reason": "가능 시간 안에 필요한 시간을 확보하지 못했습니다.",
            })

    scheduled.sort(key=lambda x: x["start_min"])
    return scheduled, unscheduled


# ==================================================
# 5. Gemini API
# ==================================================
def call_gemini(tasks, day_start, day_end, break_min, requirements):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key = ""

    if not api_key:
        return None, "GEMINI_API_KEY가 설정되지 않았습니다."

    prompt = f"""
너는 일정 최적화 전문 AI다. 현실적인 하루 시간표를 만들어라.

하루 시작: {hhmm(day_start)}
하루 종료: {hhmm(day_end)}
일정 사이 기본 휴식: {break_min}분

일정 데이터:
{json.dumps(tasks, ensure_ascii=False)}

추가 요구사항:
{requirements if requirements.strip() else "없음"}

규칙:
- 모든 일정은 중요도, 소요 시간, 가능 시작 시간, 마감 시간을 고려한다.
- importance 값은 높음, 보통, 낮음 중 하나다.
- 각 일정 ID는 한 번만 배정한다.
- 입력된 소요 시간을 정확하게 지킨다.
- 일정이 겹치면 안 된다.
- fixed가 true인 일정은 fixed_start를 반드시 지킨다.
- earliest 이전에 시작하거나 deadline 이후에 끝내지 않는다.
- 시간이 부족하면 억지로 배정하지 않고 미배정 사유를 적는다.
- 가능한 한 일정 사이 휴식과 여유 시간을 확보한다.
- 추가 요구사항을 가능한 한 반영한다.
- 결과는 JSON만 반환한다.

JSON 형식:
{{
  "schedule": [
    {{"id":"T1","start":"09:00","end":"10:00",
      "reason":"중요도가 높아 먼저 배치"}}
  ],
  "unscheduled": [
    {{"id":"T2","reason":"시간 부족"}}
  ]
}}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash-lite:generateContent"
        f"?key={api_key}"
    )

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))

        candidates = data.get("candidates", [])
        if not candidates:
            return None, "AI가 결과를 반환하지 않았습니다."

        raw = candidates[0]["content"]["parts"][0]["text"].strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)
        if not isinstance(result, dict):
            return None, "AI 응답 형식이 올바르지 않습니다."

        return result, None

    except urllib.error.HTTPError as e:
        return None, f"Gemini API HTTP 오류: {e.code}"
    except urllib.error.URLError:
        return None, "네트워크 연결에 실패했습니다."
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None, "AI 응답을 해석하지 못했습니다."
    except Exception as e:
        return None, f"예상하지 못한 오류: {str(e)[:200]}"


# ==================================================
# 6. AI 결과 검증
# ==================================================
def validate_result(result, tasks, day_start, day_end):
    if not isinstance(result.get("schedule"), list):
        raise ValueError("일정 목록이 없습니다.")

    task_map = {t["id"]: t for t in tasks}
    scheduled = []
    used = set()

    for item in result["schedule"]:
        task_id = item.get("id")

        if task_id not in task_map or task_id in used:
            raise ValueError("일정 ID가 중복되었거나 잘못되었습니다.")

        task = task_map[task_id]
        start = parse_minutes(item["start"])
        end = parse_minutes(item["end"])

        if end - start != task["duration"]:
            raise ValueError(f"{task['name']}의 소요 시간이 맞지 않습니다.")

        if start < day_start or end > day_end or end <= start:
            raise ValueError(f"{task['name']}의 하루 시간 범위를 벗어났습니다.")

        if start < parse_minutes(task["earliest"]):
            raise ValueError(f"{task['name']}의 시작 가능 시간 위반입니다.")

        if end > parse_minutes(task["deadline"]):
            raise ValueError(f"{task['name']}의 마감 시간을 위반했습니다.")

        if task["fixed"] and start != parse_minutes(task["fixed_start"]):
            raise ValueError(f"{task['name']}의 고정 시간을 위반했습니다.")

        scheduled.append({
            **task,
            "start_min": start,
            "end_min": end,
            "reason": str(item.get("reason", "AI 자동 배치")),
        })
        used.add(task_id)

    scheduled.sort(key=lambda x: x["start_min"])

    for a, b in zip(scheduled, scheduled[1:]):
        if overlaps(a["start_min"], a["end_min"], b["start_min"], b["end_min"]):
            raise ValueError("일정 간 충돌이 발견되었습니다.")

    unscheduled = []
    for item in result.get("unscheduled", []):
        if isinstance(item, dict):
            task_id = item.get("id")
            if task_id in task_map and task_id not in used:
                unscheduled.append({
                    **task_map[task_id],
                    "reason": str(item.get("reason", "배정 실패")),
                })
                used.add(task_id)

    for task in tasks:
        if task["id"] not in used:
            unscheduled.append({
                **task,
                "reason": "AI가 배정하지 않은 일정입니다.",
            })

    return scheduled, unscheduled


# ==================================================
# 7. 앱 상태
# ==================================================
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "schedule" not in st.session_state:
    st.session_state.schedule = None
if "unscheduled" not in st.session_state:
    st.session_state.unscheduled = []
if "mode" not in st.session_state:
    st.session_state.mode = ""
if "requirements_saved" not in st.session_state:
    st.session_state.requirements_saved = ""


# ==================================================
# 8. 사이드바
# ==================================================
with st.sidebar:
    st.header("⚙️ 하루 설정")
    plan_date = st.date_input("계획 날짜", value=date.today())
    start_time = st.time_input("하루 시작 시간", value=time(6, 0), step=900)
    end_time = st.time_input("하루 종료 시간", value=time(22, 0), step=900)
    break_min = st.slider("일정 충돌 후 기본 여유 시간 (분)", 0, 30, 10, 5)

day_start = minutes(start_time)
day_end = minutes(end_time)

if day_end <= day_start:
    st.error("종료 시간은 시작 시간보다 늦어야 합니다.")


# ==================================================
# 9. 일정 입력
# ==================================================
input_tab, result_tab = st.tabs(["✍️ 일정 입력", "🕒 원형 일정표"])

with input_tab:
    st.subheader("일정 추가")

    with st.form("add_task", clear_on_submit=True):
        name = st.text_input("일정명", placeholder="예: 수학 공부")
        c1, c2 = st.columns(2)

        with c1:
            duration = st.number_input(
                "예상 소요 시간 (분)", 5, 720, 60, 5
            )
            importance = st.selectbox(
                "이 일정의 중요도",
                ["높음", "보통", "낮음"],
                index=1,
            )

        with c2:
            earliest = st.time_input(
                "시작 가능 시간", value=time(6, 0), key="earliest"
            )
            deadline = st.time_input(
                "완료 마감 시간", value=time(22, 0), key="deadline"
            )

        fixed = st.checkbox("고정 일정")
        fixed_start = st.time_input(
            "고정 시작 시간",
            value=time(9, 0),
            disabled=not fixed,
        )
        detail = st.text_area("일정 메모 (선택)", max_chars=500)

        add = st.form_submit_button(
            "＋ 일정 추가", type="primary", use_container_width=True
        )

        if add:
            if not name.strip():
                st.error("일정명을 입력하세요.")
            elif minutes(deadline) <= minutes(earliest):
                st.error("마감 시간은 시작 가능 시간보다 늦어야 합니다.")
            elif fixed and not (
                minutes(earliest) <= minutes(fixed_start)
                and minutes(fixed_start) + int(duration) <= minutes(deadline)
            ):
                st.error("고정 시작 시간과 소요 시간을 확인하세요.")
            else:
                new_id = f"T{len(st.session_state.tasks) + 1}"
                st.session_state.tasks.append({
                    "id": new_id,
                    "name": name.strip(),
                    "duration": int(duration),
                    "importance": importance,
                    "earliest": earliest.strftime("%H:%M"),
                    "deadline": deadline.strftime("%H:%M"),
                    "fixed": fixed,
                    "fixed_start": fixed_start.strftime("%H:%M"),
                    "detail": detail.strip(),
                })
                st.success("일정을 추가했습니다.")

    st.divider()
    st.subheader(f"등록된 일정 {len(st.session_state.tasks)}개")

    for i, task in enumerate(st.session_state.tasks):
        color = COLORS[task["importance"]]
        pin = " · 📌 고정" if task["fixed"] else ""

        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(
                    f'<span style="color:{color};font-size:20px">●</span> '
                    f'**{task["name"]}**',
                    unsafe_allow_html=True,
                )
                st.caption(
                    f'중요도: {task["importance"]} · '
                    f'{task["duration"]}분 · '
                    f'{task["earliest"]}~{task["deadline"]}{pin}'
                )
                if task["detail"]:
                    st.write(task["detail"])
            with right:
                if st.button("삭제", key=f"delete_{i}"):
                    st.session_state.tasks.pop(i)
                    st.rerun()

    st.divider()
    requirements = st.text_area(
        "별도 요구사항",
        placeholder=(
            "예: 점심은 12:00~13:00에 먹고 싶어.\n"
            "중요한 공부는 오전에 배치해 줘.\n"
            "공부 50분마다 10분 쉬게 해 줘."
        ),
        max_chars=2000,
        key="requirements",
    )

    a, b = st.columns(2)
    with a:
        ai_button = st.button(
            "✨ AI 일정표 생성", type="primary", use_container_width=True
        )
    with b:
        basic_button = st.button(
            "⚡ 기본 일정표 생성", use_container_width=True
        )

    if ai_button or basic_button:
        if day_end <= day_start:
            st.error("하루 시간 범위를 확인하세요.")
        elif not st.session_state.tasks:
            st.warning("일정을 하나 이상 추가하세요.")
        else:
            schedule = None
            unscheduled = []
            mode = "기본 자동 생성"

            if ai_button:
                with st.spinner("AI가 일정을 최적화하고 있습니다..."):
                    ai_result, error = call_gemini(
                        st.session_state.tasks,
                        day_start,
                        day_end,
                        break_min,
                        requirements,
                    )

                if ai_result is not None:
                    try:
                        schedule, unscheduled = validate_result(
                            ai_result,
                            st.session_state.tasks,
                            day_start,
                            day_end,
                        )
                        mode = "Gemini AI"
                    except Exception as e:
                        st.warning(
                            f"AI 결과 검증 실패. 기본 생성 방식으로 전환합니다: {e}"
                        )
                else:
                    st.warning(f"{error} 기본 생성 방식으로 전환합니다.")

            if schedule is None:
                schedule, unscheduled = fallback_schedule(
                    st.session_state.tasks,
                    day_start,
                    day_end,
                    break_min,
                )

            st.session_state.schedule = schedule
            st.session_state.unscheduled = unscheduled
            st.session_state.mode = mode
            st.session_state.requirements_saved = requirements
            st.rerun()


# ==================================================
# 10. 원형 일정표 및 결과
# ==================================================
with result_tab:
    schedule = st.session_state.schedule

    if schedule is None:
        st.info("일정을 등록하고 일정표를 생성하면 여기에 원형 그래프가 표시됩니다.")
    else:
        total = sum(item["duration"] for item in schedule)
        unscheduled_count = len(st.session_state.unscheduled)

        st.caption(
            f"계획 날짜: {plan_date.isoformat()} · "
            f"생성 방식: {st.session_state.mode}"
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("배정된 일정", f"{len(schedule)}개")
        m2.metric("활동 시간", duration_text(total))
        m3.metric("미배정 일정", f"{unscheduled_count}개")

        st.divider()

        chart_col, legend_col = st.columns([1.2, 1])

        with chart_col:
            st.subheader("하루 원형 시간표")
            svg = make_clock_svg(schedule)
            st.markdown(
                f'<div style="max-width:430px;margin:auto">{svg}</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                "원 둘레는 00:00부터 24:00까지의 시간입니다. "
                "색상 구간은 각 일정이 차지하는 시간입니다."
            )

        with legend_col:
            st.subheader("중요도 범례")
            for level in ["높음", "보통", "낮음"]:
                st.markdown(
                    f'<span style="color:{COLORS[level]};font-size:20px">●</span> '
                    f'**{level} 중요도**',
                    unsafe_allow_html=True,
                )

            st.divider()
            st.subheader("시간 활용")

            day_length = max(0, day_end - day_start)
            free = max(0, day_length - total)

            st.write(f"하루 계획 범위: **{duration_text(day_length)}**")
            st.write(f"배정된 활동: **{duration_text(total)}**")
            st.write(f"미배정 여유 시간: **{duration_text(free)}**")

        st.divider()
        st.subheader("일정별 상세 정보")

        for item in schedule:
            color = COLORS.get(item["importance"], "#64748B")
            start = hhmm(item["start_min"])
            end = hhmm(item["end_min"])

            with st.container(border=True):
                st.markdown(
                    f'<span style="color:{color};font-size:20px">●</span> '
                    f'**{item["name"]}**',
                    unsafe_allow_html=True,
                )
                st.write(f"🕒 {start} – {end} · {item['duration']}분")
                st.write(f"중요도: **{item['importance']}**")
                st.caption(item.get("reason", "자동 배치"))
                if item.get("detail"):
                    st.write(item["detail"])

        if st.session_state.unscheduled:
            st.warning("시간을 배정하지 못한 일정이 있습니다.")
            for item in st.session_state.unscheduled:
                st.write(
                    f"- **{item['name']}** ({item['duration']}분): "
                    f"{item['reason']}"
                )

        st.divider()
        st.subheader("CSV 다운로드")

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "일정명", "시작", "종료", "소요시간(분)",
            "중요도", "고정 일정", "메모", "배치 이유"
        ])

        for item in schedule:
            writer.writerow([
                item["name"],
                hhmm(item["start_min"]),
                hhmm(item["end_min"]),
                item["duration"],
                item["importance"],
                "예" if item["fixed"] else "아니오",
                item["detail"],
                item.get("reason", ""),
            ])

        st.download_button(
            "📥 일정표 CSV 다운로드",
            data="\ufeff" + buffer.getvalue(),
            file_name=f"PlanAI_{plan_date.isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
