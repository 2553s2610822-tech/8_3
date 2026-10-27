
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
# 1. 페이지 설정
# ==================================================
st.set_page_config(
    page_title="TeacherPlan AI | 교사 업무 플래너",
    page_icon="📚",
    layout="wide",
)

COLORS = {
    "높음": "#EF4444",
    "보통": "#F59E0B",
    "낮음": "#10B981",
}

TEACHER_TASK_TYPES = [
    "수업 준비",
    "수업 진행",
    "시험·평가 출제",
    "수행평가 채점",
    "학생 상담",
    "학부모 연락",
    "생활기록부 작성",
    "교무·행정 업무",
    "교직원 회의",
    "연수·연구",
    "휴식·식사",
    "기타",
]

st.markdown("""
<style>
.block-container {max-width: 1250px; padding-top: 1.7rem;}
.hero {
    padding: 25px;
    border-radius: 18px;
    background: linear-gradient(120deg, #16324F, #276678);
    color: white;
    margin-bottom: 20px;
}
.hero h1 {color: white; margin-bottom: 8px;}
.hero p {color: #E1F2F7; margin-bottom: 0;}
</style>
<div class="hero">
    <h1>📚 TeacherPlan AI</h1>
    <p>수업부터 평가·상담·행정까지, 교사의 하루를 체계적으로 설계합니다.</p>
</div>
""", unsafe_allow_html=True)


# ==================================================
# 2. 공통 함수
# ==================================================
def to_minutes(value):
    return value.hour * 60 + value.minute


def parse_minutes(value):
    h, m = map(int, str(value).split(":"))
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("올바르지 않은 시간입니다.")
    return h * 60 + m


def hhmm(value):
    value = int(value)
    if value == 1440:
        return "24:00"
    return f"{value // 60:02d}:{value % 60:02d}"


def duration_text(value):
    hours, mins = divmod(int(value), 60)
    if hours and mins:
        return f"{hours}시간 {mins}분"
    if hours:
        return f"{hours}시간"
    return f"{mins}분"


def priority_score(value):
    return {"높음": 3, "보통": 2, "낮음": 1}.get(value, 1)


def overlaps(a, b, c, d):
    return a < d and c < b


def teacher_examples():
    """수정 가능한 교사 업무 샘플."""
    return [
        {
            "id": "T1",
            "name": "1교시 수학 수업",
            "task_type": "수업 진행",
            "subject": "수학",
            "class_name": "2학년 3반",
            "duration": 50,
            "importance": "높음",
            "earliest": "09:00",
            "deadline": "09:50",
            "fixed": True,
            "fixed_start": "09:00",
            "detail": "이차함수 개념 설명 및 형성평가",
        },
        {
            "id": "T2",
            "name": "수행평가 채점",
            "task_type": "수행평가 채점",
            "subject": "수학",
            "class_name": "2학년 3반",
            "duration": 60,
            "importance": "높음",
            "earliest": "08:00",
            "deadline": "16:30",
            "fixed": False,
            "fixed_start": "10:00",
            "detail": "평가기준표에 따라 채점하고 결과를 확인",
        },
        {
            "id": "T3",
            "name": "다음 차시 수업 자료 준비",
            "task_type": "수업 준비",
            "subject": "수학",
            "class_name": "2학년",
            "duration": 40,
            "importance": "높음",
            "earliest": "08:00",
            "deadline": "17:00",
            "fixed": False,
            "fixed_start": "10:00",
            "detail": "수업 자료와 활동지를 점검",
        },
        {
            "id": "T4",
            "name": "학생 상담",
            "task_type": "학생 상담",
            "subject": "",
            "class_name": "2학년 3반",
            "duration": 20,
            "importance": "보통",
            "earliest": "13:00",
            "deadline": "16:30",
            "fixed": False,
            "fixed_start": "14:00",
            "detail": "학습 상황과 학교생활 확인",
        },
        {
            "id": "T5",
            "name": "학부모 연락",
            "task_type": "학부모 연락",
            "subject": "",
            "class_name": "2학년 3반",
            "duration": 15,
            "importance": "보통",
            "earliest": "13:00",
            "deadline": "17:00",
            "fixed": False,
            "fixed_start": "15:00",
            "detail": "상담 일정 조율 및 학습 상황 공유",
        },
        {
            "id": "T6",
            "name": "수업 후 기록 정리",
            "task_type": "교무·행정 업무",
            "subject": "",
            "class_name": "",
            "duration": 25,
            "importance": "낮음",
            "earliest": "08:00",
            "deadline": "17:00",
            "fixed": False,
            "fixed_start": "16:00",
            "detail": "수업 내용과 다음 시간 준비 사항 기록",
        },
    ]


# ==================================================
# 3. 원형 시간표 SVG
#    하루 24시간을 원 둘레에 표시
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
        # 24:00과 동일한 좌표가 되어 호가 사라지는 현상 방지
        visual_end = min(end, 1439.99)
        x1, y1 = point(start, radius)
        x2, y2 = point(visual_end, radius)
        large_arc = 1 if visual_end - start > 720 else 0
        return (
            f"M {x1:.2f} {y1:.2f} "
            f"A {radius} {radius} 0 {large_arc} 1 "
            f"{x2:.2f} {y2:.2f}"
        )

    parts = [
        '<svg viewBox="0 0 380 380" '
        'xmlns="http://www.w3.org/2000/svg" '
        'role="img" aria-label="교사 하루 원형 시간표">',
        '<circle cx="190" cy="190" r="120" fill="none" '
        'stroke="#94A3B8" stroke-opacity=".22" stroke-width="22"/>',
    ]

    # 시간 눈금
    for hour in range(24):
        angle = 2 * math.pi * hour / 24 - math.pi / 2
        r1 = radius + 17
        r2 = radius + (27 if hour % 6 == 0 else 21)
        x1, y1 = cx + r1 * math.cos(angle), cy + r1 * math.sin(angle)
        x2, y2 = cx + r2 * math.cos(angle), cy + r2 * math.sin(angle)

        parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" '
            f'x2="{x2:.2f}" y2="{y2:.2f}" '
            'stroke="#94A3B8" stroke-width="1.5"/>'
        )

    # 중요도별 일정 호
    for item in schedule:
        start = item["start_min"]
        end = item["end_min"]
        if end <= start:
            continue

        color = COLORS.get(item["importance"], "#64748B")
        parts.append(
            f'<path d="{arc_path(start, end)}" '
            f'fill="none" stroke="{color}" '
            f'stroke-width="{stroke_width}" stroke-linecap="butt"/>'
        )

    for hour in [0, 6, 12, 18]:
        angle = 2 * math.pi * hour / 24 - math.pi / 2
        x = cx + 158 * math.cos(angle)
        y = cy + 158 * math.sin(angle) + 5
        parts.append(
            f'<text x="{x:.2f}" y="{y:.2f}" '
            'font-size="12" text-anchor="middle" '
            'fill="currentColor">'
            f'{hour:02d}:00</text>'
        )

    parts.extend([
        '<circle cx="190" cy="190" r="83" fill="none" '
        'stroke="#94A3B8" stroke-opacity=".2"/>',
        '<text x="190" y="176" text-anchor="middle" '
        'font-size="13" fill="currentColor">TEACHER DAY</text>',
        f'<text x="190" y="207" text-anchor="middle" '
        f'font-size="26" font-weight="700" fill="currentColor">'
        f'{len(schedule)}개</text>',
        '<text x="190" y="228" text-anchor="middle" '
        'font-size="12" fill="currentColor">배정된 업무</text>',
        '</svg>',
    ])
    return "".join(parts)


# ==================================================
# 4. 기본 일정 생성기
# ==================================================
def fallback_schedule(tasks, day_start, day_end, break_min):
    scheduled, unscheduled, occupied = [], [], []

    def place(task, start):
        end = start + task["duration"]
        scheduled.append({
            **task,
            "start_min": start,
            "end_min": end,
            "reason": (
                "교사가 지정한 고정 시간"
                if task["fixed"]
                else "중요도와 마감 시간을 고려한 자동 배치"
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
                "reason": "고정 교시가 하루 범위를 벗어나거나 다른 일정과 충돌합니다.",
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
                "reason": "가능 시간 안에 업무 시간을 확보하지 못했습니다.",
            })

    scheduled.sort(key=lambda x: x["start_min"])
    return scheduled, unscheduled


# ==================================================
# 5. Gemini AI
# ==================================================
def call_gemini(tasks, day_start, day_end, break_min, requirements):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key = ""

    if not api_key:
        return None, "GEMINI_API_KEY가 설정되지 않았습니다."

    prompt = f"""
너는 학교 현장과 교사 업무를 이해하는 일정 최적화 AI다.
교사의 수업과 교육 활동을 우선 고려해 실행 가능한 하루 계획을 작성한다.

[근무 시간]
시작: {hhmm(day_start)}
종료: {hhmm(day_end)}
일정 사이 기본 여유 시간: {break_min}분

[교사 업무 데이터]
{json.dumps(tasks, ensure_ascii=False, indent=2)}

[교사의 별도 요구사항]
{requirements if requirements.strip() else "추가 요구사항 없음"}

[필수 규칙]
1. 각 업무의 id를 정확히 한 번만 사용한다.
2. importance(높음/보통/낮음)를 반드시 고려한다.
3. 수업 진행과 고정 교시는 반드시 지정된 시간에 배치한다.
4. 소요 시간, earliest, deadline을 준수한다.
5. 일정 간 충돌을 만들지 않는다.
6. 수업 준비, 평가 채점, 학생 상담, 학부모 연락,
   생활기록부 및 행정 업무의 성격을 고려한다.
7. 수업과 평가 마감이 임박한 업무는 우선적으로 고려한다.
8. 휴식과 식사 시간을 포함한 요구사항을 가능한 한 반영한다.
9. 고정 일정과 충돌하는 요구사항은 임의로 시간을 변경하지 않는다.
10. 조건을 만족할 수 없는 업무는 미배정 사유를 기록한다.
11. 학생의 민감한 개인정보를 추측하거나 추가하지 않는다.
12. reason에는 해당 업무를 그 시간에 배치한 이유를 구체적으로 쓴다.

반드시 JSON 객체만 반환한다. 마크다운 코드 블록은 쓰지 않는다.

형식:
{{
  "schedule": [
    {{"id":"T1","start":"09:00","end":"09:50",
      "reason":"고정된 1교시 수업"}}
  ],
  "unscheduled": [
    {{"id":"T2","reason":"수업 시간과 충돌하여 배정할 수 없음"}}
  ]
}}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash-lite:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

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
# 6. AI 응답 검증
# ==================================================
def validate_result(result, tasks, day_start, day_end):
    if not isinstance(result.get("schedule"), list):
        raise ValueError("일정 목록이 없습니다.")

    task_map = {t["id"]: t for t in tasks}
    scheduled, used = [], set()

    for item in result["schedule"]:
        task_id = item.get("id")
        if task_id not in task_map or task_id in used:
            raise ValueError("업무 ID가 잘못되었거나 중복되었습니다.")

        task = task_map[task_id]
        start = parse_minutes(item["start"])
        end = parse_minutes(item["end"])

        if end - start != task["duration"]:
            raise ValueError(f"{task['name']}의 소요 시간이 맞지 않습니다.")

        if start < day_start or end > day_end or end <= start:
            raise ValueError(f"{task['name']}의 근무 시간 범위를 벗어났습니다.")

        if start < parse_minutes(task["earliest"]):
            raise ValueError(f"{task['name']}의 시작 가능 시간을 위반했습니다.")

        if end > parse_minutes(task["deadline"]):
            raise ValueError(f"{task['name']}의 마감 시간을 위반했습니다.")

        if task["fixed"] and start != parse_minutes(task["fixed_start"]):
            raise ValueError(f"{task['name']}의 고정 시간이 지켜지지 않았습니다.")

        scheduled.append({
            **task,
            "start_min": start,
            "end_min": end,
            "reason": str(item.get("reason", "AI가 자동 배치")),
        })
        used.add(task_id)

    scheduled.sort(key=lambda x: x["start_min"])

    for previous, current in zip(scheduled, scheduled[1:]):
        if overlaps(
            previous["start_min"], previous["end_min"],
            current["start_min"], current["end_min"],
        ):
            raise ValueError("일정 충돌이 발견되었습니다.")

    unscheduled = []
    for item in result.get("unscheduled", []):
        if isinstance(item, dict):
            task_id = item.get("id")
            if task_id in task_map and task_id not in used:
                unscheduled.append({
                    **task_map[task_id],
                    "reason": str(item.get("reason", "업무 배정 실패")),
                })
                used.add(task_id)

    for task in tasks:
        if task["id"] not in used:
            unscheduled.append({
                **task,
                "reason": "AI가 배정하지 않은 업무입니다.",
            })

    return scheduled, unscheduled


# ==================================================
# 7. 세션 상태
# ==================================================
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "schedule" not in st.session_state:
    st.session_state.schedule = None
if "unscheduled" not in st.session_state:
    st.session_state.unscheduled = []
if "mode" not in st.session_state:
    st.session_state.mode = ""
if "demo_loaded" not in st.session_state:
    st.session_state.demo_loaded = False
if "plan_date" not in st.session_state:
    st.session_state.plan_date = date.today()
if "saved_day_start" not in st.session_state:
    st.session_state.saved_day_start = 8 * 60
if "saved_day_end" not in st.session_state:
    st.session_state.saved_day_end = 17 * 60


# ==================================================
# 8. 사이드바
# ==================================================
with st.sidebar:
    st.header("🏫 근무일 설정")
    plan_date = st.date_input("계획 날짜", value=date.today())
    start_time = st.time_input("근무 시작", value=time(8, 0), step=900)
    end_time = st.time_input("근무 종료", value=time(17, 0), step=900)
    break_min = st.slider("일정 충돌 후 여유 시간 (분)", 0, 30, 10, 5)

day_start = to_minutes(start_time)
day_end = to_minutes(end_time)

st.caption(
    "예시 업무는 학교별 실제 시간표와 다를 수 있습니다. "
    "수업 교시와 업무 시간은 직접 수정해 사용하세요."
)

if day_end <= day_start:
    st.error("근무 종료 시간은 시작 시간보다 늦어야 합니다.")


# ==================================================
# 9. 탭
# ==================================================
input_tab, result_tab = st.tabs(["📝 업무 입력", "🕒 교사 원형 시간표"])

with input_tab:
    st.subheader("1. 교사 업무 등록")

    if st.button("📚 교사 업무 예시 불러오기"):
        st.session_state.tasks = teacher_examples()
        st.session_state.schedule = None
        st.session_state.unscheduled = []
        st.session_state.demo_loaded = True
        st.success("교사 업무 예시 6개를 불러왔습니다.")
        st.rerun()

    with st.form("teacher_task_form", clear_on_submit=True):
        name = st.text_input(
            "업무명",
            placeholder="예: 3학년 영어 수행평가 채점",
        )

        task_type = st.selectbox("업무 유형", TEACHER_TASK_TYPES)
        c1, c2 = st.columns(2)

        with c1:
            subject = st.text_input(
                "과목 (선택)",
                placeholder="예: 수학, 국어, 영어",
            )
            class_name = st.text_input(
                "학년·학급 (선택)",
                placeholder="예: 2학년 3반",
            )
            duration = st.number_input(
                "예상 소요 시간 (분)", 5, 720, 50, 5
            )

        with c2:
            importance = st.selectbox(
                "이 업무의 중요도",
                ["높음", "보통", "낮음"],
                index=1,
            )
            earliest = st.time_input(
                "가장 빠른 시작 시간",
                value=time(8, 0),
                key="teacher_earliest",
            )
            deadline = st.time_input(
                "완료 마감 시간",
                value=time(17, 0),
                key="teacher_deadline",
            )

        fixed = st.checkbox("고정 교시 또는 고정 업무")
        fixed_start = st.time_input(
            "고정 시작 시간",
            value=time(9, 0),
            disabled=not fixed,
            key="teacher_fixed_start",
        )

        detail = st.text_area(
            "세부 사항",
            placeholder=(
                "예: 채점 기준표 확인, 평가 결과 입력, "
                "수업 자료 인쇄, 학생 상담 기록 정리"
            ),
            max_chars=1000,
        )

        add = st.form_submit_button(
            "＋ 교사 업무 추가",
            type="primary",
            use_container_width=True,
        )

        if add:
            if not name.strip():
                st.error("업무명을 입력하세요.")
            elif to_minutes(deadline) <= to_minutes(earliest):
                st.error("마감 시간은 시작 가능 시간보다 늦어야 합니다.")
            elif fixed and not (
                to_minutes(earliest) <= to_minutes(fixed_start)
                and to_minutes(fixed_start) + int(duration) <= to_minutes(deadline)
            ):
                st.error("고정 시작 시간과 소요 시간을 확인하세요.")
            else:
                # 삭제 후 ID가 재사용되지 않도록 현재 최대 번호를 사용
                existing_numbers = []
                for task in st.session_state.tasks:
                    match = re.fullmatch(r"T(\d+)", task["id"])
                    if match:
                        existing_numbers.append(int(match.group(1)))
                new_id = f"T{max(existing_numbers, default=0) + 1}"

                st.session_state.tasks.append({
                    "id": new_id,
                    "name": name.strip(),
                    "task_type": task_type,
                    "subject": subject.strip(),
                    "class_name": class_name.strip(),
                    "duration": int(duration),
                    "importance": importance,
                    "earliest": earliest.strftime("%H:%M"),
                    "deadline": deadline.strftime("%H:%M"),
                    "fixed": fixed,
                    "fixed_start": fixed_start.strftime("%H:%M"),
                    "detail": detail.strip(),
                })
                st.session_state.schedule = None
                st.success("교사 업무를 추가했습니다.")
                st.rerun()

    st.divider()
    st.subheader(f"2. 등록된 업무 ({len(st.session_state.tasks)}개)")

    for i, task in enumerate(st.session_state.tasks):
        color = COLORS[task["importance"]]
        with st.container(border=True):
            left, right = st.columns([5, 1])

            with left:
                st.markdown(
                    f'<span style="color:{color};font-size:20px">●</span> '
                    f'**{task["name"]}**',
                    unsafe_allow_html=True,
                )
                st.caption(
                    f'{task["task_type"]} · {task["duration"]}분 · '
                    f'중요도 {task["importance"]}'
                )

                extra = " · ".join(
                    x for x in [task["subject"], task["class_name"]] if x
                )
                if extra:
                    st.write(extra)

                if task["fixed"]:
                    st.write(f'📌 고정 시간: {task["fixed_start"]}')

                st.caption(
                    f'{task["earliest"]}부터 {task["deadline"]}까지'
                )

                if task["detail"]:
                    st.write(task["detail"])

            with right:
                if st.button("삭제", key=f"teacher_delete_{i}"):
                    st.session_state.tasks.pop(i)
                    st.session_state.schedule = None
                    st.rerun()

    st.divider()
    st.subheader("3. 교사 맞춤 요구사항")

    requirements = st.text_area(
        "AI에게 전달할 추가 지시",
        placeholder=(
            "예: 1교시 수업 전에 수업 자료를 점검해 줘.\n"
            "점심시간은 12:00~13:00에 확보해 줘.\n"
            "수행평가 마감 업무를 우선 배치해 줘.\n"
            "학생 상담은 수업이 끝난 뒤 배치해 줘."
        ),
        max_chars=3000,
        key="teacher_requirements",
    )

    st.caption(
        "점심·회의 등 반드시 비워야 할 시간은 요구사항에 구체적으로 작성하세요. "
        "기본 생성기는 자연어 요구를 자동 해석하지 않습니다."
    )

    a, b = st.columns(2)
    with a:
        ai_button = st.button(
            "✨ AI 일정표 생성",
            type="primary",
            use_container_width=True,
        )
    with b:
        basic_button = st.button(
            "⚡ 기본 일정표 생성",
            use_container_width=True,
        )

    if ai_button or basic_button:
        if day_end <= day_start:
            st.error("근무 시간 범위를 확인하세요.")
        elif not st.session_state.tasks:
            st.warning("업무를 하나 이상 등록하세요.")
        else:
            schedule = None
            unscheduled = []
            mode = "기본 자동 생성"

            if ai_button:
                with st.spinner("교사 업무의 중요도와 마감 시간을 분석 중입니다..."):
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
                            f"AI 결과 검증 실패: {e} 기본 생성으로 전환합니다."
                        )
                else:
                    st.warning(f"{error} 기본 생성으로 전환합니다.")

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
            st.session_state.plan_date = plan_date
            st.session_state.saved_day_start = day_start
            st.session_state.saved_day_end = day_end
            st.session_state.saved_requirements = requirements
            st.rerun()


# ==================================================
# 10. 원형 시간표와 상세 결과
# ==================================================
with result_tab:
    schedule = st.session_state.schedule

    if schedule is None:
        st.info(
            "업무를 등록하고 일정표를 생성하세요. "
            "교사 업무 예시를 불러오면 바로 테스트할 수 있습니다."
        )
    else:
        total = sum(item["duration"] for item in schedule)
        unscheduled_count = len(st.session_state.unscheduled)
        day_length = (
            st.session_state.saved_day_end
            - st.session_state.saved_day_start
        )
        free = max(0, day_length - total)

        st.caption(
            f'계획 날짜: {st.session_state.plan_date.isoformat()} · '
            f'생성 방식: {st.session_state.mode}'
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("배정된 업무", f"{len(schedule)}개")
        m2.metric("업무 시간", duration_text(total))
        m3.metric("미배정 업무", f"{unscheduled_count}개")

        st.divider()

        chart_col, info_col = st.columns([1.15, 1])

        with chart_col:
            st.subheader("하루 원형 시간표")
            svg = make_clock_svg(schedule)
            st.markdown(
                f'<div style="max-width:430px;margin:auto">{svg}</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                "원 둘레는 24시간입니다. 색상 구간은 각 업무의 "
                "실제 시작·종료 시각을 표시합니다."
            )

        with info_col:
            st.subheader("중요도 범례")
            for level in ["높음", "보통", "낮음"]:
                st.markdown(
                    f'<span style="color:{COLORS[level]};font-size:20px">●</span> '
                    f'**{level} 중요도**',
                    unsafe_allow_html=True,
                )

            st.divider()
            st.subheader("업무 배분 요약")
            st.write(f"근무 시간 범위: **{duration_text(day_length)}**")
            st.write(f"배정된 업무: **{duration_text(total)}**")
            st.write(f"미배정 시간: **{duration_text(free)}**")

            high_count = sum(
                1 for item in schedule if item["importance"] == "높음"
            )
            st.write(f"높은 중요도의 배정 업무: **{high_count}개**")

        st.divider()
        st.subheader("업무별 세부 일정")

        for item in schedule:
            color = COLORS.get(item["importance"], "#64748B")

            with st.container(border=True):
                st.markdown(
                    f'<span style="color:{color};font-size:20px">●</span> '
                    f'**{item["name"]}**',
                    unsafe_allow_html=True,
                )

                st.write(
                    f'🕒 {hhmm(item["start_min"])}–{hhmm(item["end_min"])} · '
                    f'{item["duration"]}분'
                )
                st.write(
                    f'업무 유형: {item["task_type"]} · '
                    f'중요도: {item["importance"]}'
                )

                extra = " · ".join(
                    x for x in [item["subject"], item["class_name"]] if x
                )
                if extra:
                    st.write(f"과목·학급: {extra}")

                st.caption(
                    "배치 이유: " + item.get("reason", "자동 배치")
                )

                if item.get("detail"):
                    st.write(f'세부 사항: {item["detail"]}')

        if st.session_state.unscheduled:
            st.warning("아래 업무는 시간 조건을 만족하지 못했습니다.")
            for item in st.session_state.unscheduled:
                st.write(
                    f'- **{item["name"]}** ({item["duration"]}분): '
                    f'{item["reason"]}'
                )

        st.divider()
        st.subheader("업무 일정표 다운로드")

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "날짜", "업무명", "업무 유형", "과목", "학년·학급",
            "시작", "종료", "소요시간(분)", "중요도",
            "고정 일정", "세부 사항", "배치 이유",
        ])

        for item in schedule:
            writer.writerow([
                st.session_state.plan_date.isoformat(),
                item["name"],
                item["task_type"],
                item["subject"],
                item["class_name"],
                hhmm(item["start_min"]),
                hhmm(item["end_min"]),
                item["duration"],
                item["importance"],
                "예" if item["fixed"] else "아니오",
                item["detail"],
                item.get("reason", ""),
            ])

# 원형 시간표와 일정 목록을 좌우로 배치
chart_col, list_col = st.columns([1.05, 1])

# 왼쪽: 기존 원형 시간표
with chart_col:
    st.subheader("🕒 24시간 원형 시간표")

    # 기존 코드에서 원형 SVG를 표시하던 줄을 여기에 그대로 유지
    st.markdown(
        make_clock_svg(schedule),
        unsafe_allow_html=True,
    )

    st.caption("색상은 일정의 중요도를 나타냅니다.")
    st.markdown("🔴 높음　🟠 보통　🟢 낮음")

# 오른쪽: 시간순 일정 목록
with list_col:
    st.subheader("📋 오늘의 일정")

    importance_style = {
        "높음": "🔴",
        "보통": "🟠",
        "낮음": "🟢",
    }

    sorted_schedule = sorted(
        schedule,
        key=lambda item: item["start_min"],
    )

    if not sorted_schedule:
        st.info("배정된 일정이 없습니다.")

    for item in sorted_schedule:
        start = hhmm(item["start_min"])
        end = hhmm(item["end_min"])
        importance = item.get("importance", "보통")
        icon = importance_style.get(importance, "⚪")

        with st.container(border=True):
            st.markdown(
                f"**{icon} {start} – {end}**"
            )
            st.markdown(f"**{item['name']}**")
            st.caption(
                f"{item.get('task_type', '기타')} · "
                f"{item.get('duration', 0)}분 · "
                f"중요도 {importance}"
            )

            if item.get("subject"):
                st.caption(f"과목: {item['subject']}")

            if item.get("class_name"):
                st.caption(f"학급: {item['class_name']}")

            if item.get("reason"):
                st.write(f"배정 이유: {item['reason']}")
        
        st.download_button(
            "📥 교사 업무표 CSV 다운로드",
            data="\ufeff" + buffer.getvalue(),
            file_name=f"TeacherPlan_{st.session_state.plan_date.isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
