
import streamlit as st
import json
import csv
import io
import math
import re
import urllib.request
import urllib.error
from datetime import date, time


# =====================================================
# 1. 페이지 설정
# =====================================================
st.set_page_config(
    page_title="PlanAI | 스마트 원형 일정표",
    page_icon="🕒",
    layout="wide",
)

COLORS = {
    "높음": "#EF4444",
    "보통": "#F59E0B",
    "낮음": "#10B981",
    "자유시간": "#94A3B8",
    "추가 활동": "#8B5CF6",
}

st.markdown("""
<style>
.block-container {max-width: 1200px; padding-top: 1.8rem;}
.hero {
    background: linear-gradient(125deg, #172554, #4338ca);
    padding: 25px;
    border-radius: 18px;
    color: white;
    margin-bottom: 20px;
}
.hero h1 {color: white;}
.hero p {color: #e0e7ff; margin-bottom: 0;}
</style>
<div class="hero">
    <h1>🕒 PlanAI</h1>
    <p>일정 · 중요도 · 빈 시간까지 자동으로 구성하는 스마트 플래너</p>
</div>
""", unsafe_allow_html=True)


# =====================================================
# 2. 시간 및 공통 함수
# =====================================================
def to_min(value):
    return value.hour * 60 + value.minute


def parse_min(value):
    parts = str(value).split(":")
    if len(parts) != 2:
        raise ValueError("시간 형식은 HH:MM이어야 합니다.")

    hour, minute = map(int, parts)
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("유효하지 않은 시간입니다.")

    return hour * 60 + minute


def clock(value):
    return f"{int(value) // 60:02d}:{int(value) % 60:02d}"


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


# =====================================================
# 3. 원형 시간표 SVG
# =====================================================
def make_clock_svg(items):
    cx, cy, radius = 190, 190, 120
    stroke = 22

    def point(minute, r):
        angle = 2 * math.pi * minute / 1440 - math.pi / 2
        return (
            cx + r * math.cos(angle),
            cy + r * math.sin(angle),
        )

    parts = [
        '<svg viewBox="0 0 380 380" '
        'xmlns="http://www.w3.org/2000/svg" '
        'role="img" aria-label="24시간 원형 일정표">',
        '<circle cx="190" cy="190" r="120" '
        'fill="none" stroke="#94A3B8" stroke-opacity=".2" '
        'stroke-width="22"/>',
    ]

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

    for item in items:
        start, end = item["start_min"], item["end_min"]
        if end <= start or start < 0 or end > 1440:
            continue

        # 같은 원 둘레에서 시작과 종료 위치를 계산한다.
        x1, y1 = point(start, radius)
        x2, y2 = point(end, radius)
        large_arc = 1 if end - start > 720 else 0
        color = item.get("color", COLORS.get(item["importance"], "#64748B"))

        parts.append(
            f'<path d="M {x1:.2f} {y1:.2f} '
            f'A {radius} {radius} 0 {large_arc} 1 '
            f'{x2:.2f} {y2:.2f}" '
            f'fill="none" stroke="{color}" stroke-width="{stroke}"/>'
        )

    for hour in [0, 6, 12, 18]:
        angle = 2 * math.pi * hour / 24 - math.pi / 2
        x, y = cx + 158 * math.cos(angle), cy + 158 * math.sin(angle) + 5
        parts.append(
            f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" '
            'font-size="12" fill="currentColor">'
            f'{hour:02d}:00</text>'
        )

    parts.extend([
        '<circle cx="190" cy="190" r="84" fill="none" '
        'stroke="#94A3B8" stroke-opacity=".18"/>',
        '<text x="190" y="178" text-anchor="middle" '
        'font-size="14" fill="currentColor">TODAY</text>',
        f'<text x="190" y="207" text-anchor="middle" '
        f'font-size="26" font-weight="700" fill="currentColor">'
        f'{len(items)}개</text>',
        '<text x="190" y="228" text-anchor="middle" '
        'font-size="12" fill="currentColor">시간 구간</text>',
        '</svg>',
    ])

    return "".join(parts)


# =====================================================
# 4. Gemini AI: 일정 및 빈 시간 구성
# =====================================================
def call_gemini(tasks, day_start, day_end, break_min, requirements):
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        api_key = ""

    if not api_key:
        return None, "GEMINI_API_KEY가 설정되지 않았습니다."

    prompt = f"""
너는 일정 최적화와 빈 시간 활용을 담당하는 AI 플래너다.

하루 시작: {clock(day_start)}
하루 종료: {clock(day_end)}
일정 사이 권장 휴식: {break_min}분

사용자가 등록한 일정:
{json.dumps(tasks, ensure_ascii=False)}

사용자의 추가 요청:
{requirements.strip() if requirements.strip() else "특별한 요청 없음"}

[필수 규칙]
1. 등록된 모든 일정을 검토하고, 각 일정의 중요도·소요 시간·
   시작 가능 시간·마감 시간을 고려한다.
2. 기존 일정의 id는 정확히 한 번만 배정한다.
3. 기존 일정의 소요 시간은 변경하지 않는다.
4. fixed=true인 일정은 fixed_start를 반드시 지킨다.
5. 일정끼리 겹치면 안 된다.
6. 시작 가능 시간보다 일찍 시작하거나 마감 이후에 끝내지 않는다.
7. 조건을 만족할 수 없는 일정은 unscheduled에 이유와 함께 넣는다.
8. 등록된 일정 사이 또는 전후에 빈 시간이 있으면 추가 활동을 검토한다.
9. 추가 요청이 빈 시간에 할 활동을 지정했다면, 가능한 시간에 해당 활동을 배치한다.
10. 추가 요청이 없거나 추가 활동을 지정하지 않았다면 빈 시간은 자유시간으로 둔다.
11. 추가 활동은 기존 일정의 시간, 고정 일정, 휴식 및 명시된 요구사항과
    충돌하지 않는 경우에만 배치한다.
12. 식사, 이동, 휴식처럼 사용자가 명시한 시간 제약을 우선한다.
13. 추가 활동을 억지로 넣지 않는다. 빈 시간이 너무 짧거나 조건이 불분명하면
    그 구간은 자유시간으로 남긴다.
14. 추가 활동은 실제로 빈 시간이 있을 때만 만든다.
15. 중요도는 기존 일정에 대해서만 입력값을 유지한다.
    추가 활동의 importance는 "추가 활동"으로 표시한다.

반드시 JSON 객체만 출력하고 마크다운을 사용하지 않는다.

출력 형식:
{{
  "schedule": [
    {{
      "id": "T1",
      "start": "09:00",
      "end": "10:00",
      "reason": "중요도가 높아 먼저 배치"
    }}
  ],
  "extras": [
    {{
      "name": "영어 단어 복습",
      "start": "10:10",
      "end": "10:30",
      "reason": "사용자가 요청한 빈 시간 활용"
    }}
  ],
  "unscheduled": [
    {{
      "id": "T2",
      "reason": "시간이 부족함"
    }}
  ]
}}

extras에는 실제로 배정할 추가 활동만 넣는다.
자유시간은 직접 출력하지 않는다. 남은 빈 시간은 앱이 자유시간으로 자동 표시한다.
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
            return None, "AI 응답이 비어 있습니다."

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
        return None, "AI 응답을 읽지 못했습니다."
    except Exception as e:
        return None, f"AI 오류: {str(e)[:200]}"


# =====================================================
# 5. AI 결과 검증 및 추가 활동 처리
# =====================================================
def validate_result(result, tasks, day_start, day_end):
    if not isinstance(result.get("schedule"), list):
        raise ValueError("AI 일정 목록이 없습니다.")

    task_map = {task["id"]: task for task in tasks}
    items = []
    used_ids = set()

    for entry in result["schedule"]:
        task_id = entry.get("id")
        if task_id not in task_map or task_id in used_ids:
            raise ValueError("일정 ID가 중복되었거나 잘못되었습니다.")

        task = task_map[task_id]
        start = parse_min(entry["start"])
        end = parse_min(entry["end"])

        if end - start != task["duration"]:
            raise ValueError(f"{task['name']}의 소요 시간이 맞지 않습니다.")
        if start < day_start or end > day_end or end <= start:
            raise ValueError(f"{task['name']}의 시간이 하루 범위를 벗어났습니다.")
        if start < parse_min(task["earliest"]):
            raise ValueError(f"{task['name']}의 시작 가능 시간을 위반했습니다.")
        if end > parse_min(task["deadline"]):
            raise ValueError(f"{task['name']}의 마감 시간을 위반했습니다.")
        if task["fixed"] and start != parse_min(task["fixed_start"]):
            raise ValueError(f"{task['name']}의 고정 시간을 위반했습니다.")

        items.append({
            **task,
            "start_min": start,
            "end_min": end,
            "reason": str(entry.get("reason", "AI 자동 배치")),
            "kind": "일정",
            "color": COLORS[task["importance"]],
        })
        used_ids.add(task_id)

    unscheduled = []
    for entry in result.get("unscheduled", []):
        if not isinstance(entry, dict):
            continue
        task_id = entry.get("id")
        if task_id in task_map and task_id not in used_ids:
            unscheduled.append({
                **task_map[task_id],
                "reason": str(entry.get("reason", "시간 부족")),
            })
            used_ids.add(task_id)

    for task in tasks:
        if task["id"] not in used_ids:
            unscheduled.append({
                **task,
                "reason": "AI가 배정하지 않은 일정입니다.",
            })

    # AI가 제안한 추가 활동도 별도로 검증한다.
    extras = result.get("extras", [])
    if not isinstance(extras, list):
        extras = []

    for index, extra in enumerate(extras, start=1):
        try:
            name = str(extra.get("name", "")).strip()
            start = parse_min(extra["start"])
            end = parse_min(extra["end"])

            if not name or end <= start:
                continue
            if start < day_start or end > day_end:
                continue

            # 추가 활동이 기존 일정과 겹치면 배치하지 않는다.
            if any(
                overlaps(start, end, item["start_min"], item["end_min"])
                for item in items
            ):
                continue

            items.append({
                "id": f"EXTRA{index}",
                "name": name,
                "duration": end - start,
                "importance": "추가 활동",
                "earliest": clock(day_start),
                "deadline": clock(day_end),
                "fixed": False,
                "fixed_start": clock(start),
                "detail": "",
                "start_min": start,
                "end_min": end,
                "reason": str(extra.get("reason", "빈 시간 활용")),
                "kind": "추가 활동",
                "color": COLORS["추가 활동"],
            })
        except (ValueError, TypeError, KeyError, AttributeError):
            continue

    items.sort(key=lambda x: x["start_min"])

    for previous, current in zip(items, items[1:]):
        if overlaps(
            previous["start_min"], previous["end_min"],
            current["start_min"], current["end_min"],
        ):
            raise ValueError("일정 또는 추가 활동 간 충돌이 발견되었습니다.")

    return items, unscheduled


# =====================================================
# 6. 기본 자동 일정 생성
# =====================================================
def fallback_schedule(tasks, day_start, day_end, break_min):
    items, unscheduled, occupied = [], [], []

    fixed = sorted(
        [t for t in tasks if t["fixed"]],
        key=lambda t: parse_min(t["fixed_start"]),
    )

    for task in fixed:
        start = parse_min(task["fixed_start"])
        end = start + task["duration"]

        valid = (
            start >= day_start
            and end <= day_end
            and start >= parse_min(task["earliest"])
            and end <= parse_min(task["deadline"])
            and not any(overlaps(start, end, a, b) for a, b in occupied)
        )

        if valid:
            items.append({
                **task,
                "start_min": start,
                "end_min": end,
                "reason": "사용자가 지정한 고정 시간",
                "kind": "일정",
                "color": COLORS[task["importance"]],
            })
            occupied.append((start, end))
        else:
            unscheduled.append({
                **task,
                "reason": "고정 시간이 다른 일정 또는 시간 조건과 충돌합니다.",
            })

    flexible = sorted(
        [t for t in tasks if not t["fixed"]],
        key=lambda t: (
            -priority_score(t["importance"]),
            parse_min(t["deadline"]),
        ),
    )

    for task in flexible:
        candidate = max(day_start, parse_min(task["earliest"]))
        deadline = min(day_end, parse_min(task["deadline"]))
        placed = False

        while candidate + task["duration"] <= deadline:
            end = candidate + task["duration"]

            conflict = next(
                ((a, b) for a, b in occupied if overlaps(candidate, end, a, b)),
                None,
            )

            if conflict:
                candidate = conflict[1] + break_min
                continue

            items.append({
                **task,
                "start_min": candidate,
                "end_min": end,
                "reason": "중요도와 마감 시간을 고려해 자동 배치",
                "kind": "일정",
                "color": COLORS[task["importance"]],
            })
            occupied.append((candidate, end))
            placed = True
            break

        if not placed:
            unscheduled.append({
                **task,
                "reason": "가능 시간 안에 필요한 시간을 확보하지 못했습니다.",
            })

    items.sort(key=lambda x: x["start_min"])
    return items, unscheduled


# =====================================================
# 7. 빈 시간 자동 채우기
# =====================================================
def fill_free_time(items, day_start, day_end):
    """기존 일정과 추가 활동 사이의 모든 공백을 자유시간으로 표시."""
    result = []
    cursor = day_start

    for item in sorted(items, key=lambda x: x["start_min"]):
        start = item["start_min"]
        end = item["end_min"]

        if start > cursor:
            result.append({
                "id": f"FREE{cursor}",
                "name": "자유시간",
                "start_min": cursor,
                "end_min": start,
                "duration": start - cursor,
                "importance": "자유시간",
                "kind": "자유시간",
                "reason": "배정되지 않은 시간입니다. 휴식 또는 개인 활동에 활용하세요.",
                "detail": "",
                "color": COLORS["자유시간"],
            })

        result.append(item)
        cursor = max(cursor, end)

    if cursor < day_end:
        result.append({
            "id": f"FREE{cursor}",
            "name": "자유시간",
            "start_min": cursor,
            "end_min": day_end,
            "duration": day_end - cursor,
            "importance": "자유시간",
            "kind": "자유시간",
            "reason": "남은 시간을 자유롭게 활용할 수 있습니다.",
            "detail": "",
            "color": COLORS["자유시간"],
        })

    return [item for item in result if item["end_min"] > item["start_min"]]


# =====================================================
# 8. 세션 초기화
# =====================================================
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "schedule" not in st.session_state:
    st.session_state.schedule = None
if "unscheduled" not in st.session_state:
    st.session_state.unscheduled = []
if "mode" not in st.session_state:
    st.session_state.mode = ""


# =====================================================
# 9. 하루 설정
# =====================================================
with st.sidebar:
    st.header("⚙️ 하루 설정")
    plan_date = st.date_input("계획 날짜", value=date.today())
    start_time = st.time_input("하루 시작", value=time(6, 0), step=900)
    end_time = st.time_input("하루 종료", value=time(22, 0), step=900)
    break_min = st.slider("충돌 후 기본 여유 시간 (분)", 0, 30, 10, 5)

day_start = to_min(start_time)
day_end = to_min(end_time)

if day_end <= day_start:
    st.error("하루 종료 시간은 시작 시간보다 늦어야 합니다.")


# =====================================================
# 10. 일정 입력 화면
# =====================================================
input_tab, result_tab = st.tabs(["✍️ 일정 입력", "🕒 원형 일정표"])

with input_tab:
    st.subheader("일정 추가")

    with st.form("task_form", clear_on_submit=True):
        name = st.text_input("일정명", placeholder="예: 수학 공부")
        c1, c2 = st.columns(2)

        with c1:
            duration = st.number_input("소요 시간 (분)", 5, 720, 60, 5)
            importance = st.selectbox(
                "중요도", ["높음", "보통", "낮음"], index=1
            )

        with c2:
            earliest = st.time_input("시작 가능 시간", value=time(6, 0))
            deadline = st.time_input("완료 마감 시간", value=time(22, 0))

        fixed = st.checkbox("고정 일정")
        fixed_start = st.time_input(
            "고정 시작 시간", value=time(9, 0), disabled=not fixed
        )
        detail = st.text_area("일정 메모 (선택)", max_chars=500)

        add = st.form_submit_button(
            "＋ 일정 추가", type="primary", use_container_width=True
        )

        if add:
            if not name.strip():
                st.error("일정명을 입력하세요.")
            elif to_min(deadline) <= to_min(earliest):
                st.error("마감 시간은 시작 가능 시간보다 늦어야 합니다.")
            elif fixed and not (
                to_min(earliest) <= to_min(fixed_start)
                and to_min(fixed_start) + int(duration) <= to_min(deadline)
            ):
                st.error("고정 시작 시간과 소요 시간을 확인하세요.")
            else:
                st.session_state.tasks.append({
                    "id": f"T{len(st.session_state.tasks) + 1}",
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
    st.subheader(f"등록된 일정 ({len(st.session_state.tasks)}개)")

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
                    f'중요도 {task["importance"]} · {task["duration"]}분 · '
                    f'{task["earliest"]}~{task["deadline"]}'
                )
                if task["fixed"]:
                    st.caption(f'📌 고정 시작: {task["fixed_start"]}')
                if task["detail"]:
                    st.write(task["detail"])
            with right:
                if st.button("삭제", key=f"delete_{i}"):
                    st.session_state.tasks.pop(i)
                    st.rerun()

    st.divider()
    st.subheader("추가 요구사항")

    requirements = st.text_area(
        "빈 시간 활용 방법도 자유롭게 입력하세요.",
        placeholder=(
            "예: 점심은 12:00~13:00에 먹어 줘.\n"
            "남는 시간에는 영어 단어를 복습해 줘.\n"
            "추가 공부는 30분 이하로 배치하고,\n"
            "그 외 시간은 자유시간으로 남겨 줘."
        ),
        max_chars=2000,
        key="requirements",
    )

    st.caption(
        "AI는 추가 요청에 따라 빈 시간에 활동을 제안합니다. "
        "추가 활동이 적합하지 않으면 해당 시간은 자유시간으로 남깁니다."
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
            items = None
            unscheduled = []
            mode = "기본 자동 생성"

            if ai_button:
                with st.spinner("일정과 빈 시간을 분석하고 있습니다..."):
                    ai_result, error = call_gemini(
                        st.session_state.tasks,
                        day_start,
                        day_end,
                        break_min,
                        requirements,
                    )

                if ai_result is not None:
                    try:
                        items, unscheduled = validate_result(
                            ai_result,
                            st.session_state.tasks,
                            day_start,
                            day_end,
                        )
                        mode = "Gemini AI"
                    except Exception as e:
                        st.warning(
                            f"AI 결과 검증에 실패했습니다. 기본 생성으로 전환합니다. ({e})"
                        )
                else:
                    st.warning(f"{error} 기본 생성 방식으로 전환합니다.")

            if items is None:
                items, unscheduled = fallback_schedule(
                    st.session_state.tasks,
                    day_start,
                    day_end,
                    break_min,
                )

            # 모든 공백은 자유시간으로 채운다.
            items = fill_free_time(items, day_start, day_end)

            st.session_state.schedule = items
            st.session_state.unscheduled = unscheduled
            st.session_state.mode = mode
            st.rerun()


# =====================================================
# 11. 결과 및 CSV
# =====================================================
with result_tab:
    items = st.session_state.schedule

    if items is None:
        st.info("일정을 등록하고 생성하면 원형 시간표와 자유시간이 표시됩니다.")
    else:
        planned_items = [x for x in items if x["kind"] != "자유시간"]
        free_items = [x for x in items if x["kind"] == "자유시간"]

        activity_minutes = sum(x["duration"] for x in planned_items)
        free_minutes = sum(x["duration"] for x in free_items)
        extra_items = [x for x in items if x["kind"] == "추가 활동"]

        st.caption(
            f"계획 날짜: {plan_date.isoformat()} · 생성 방식: {st.session_state.mode}"
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("일정 및 추가 활동", f"{len(planned_items)}개")
        m2.metric("자유시간", duration_text(free_minutes))
        m3.metric("AI 추가 활동", f"{len(extra_items)}개")

        chart_col, legend_col = st.columns([1.2, 1])

        with chart_col:
            st.subheader("24시간 원형 시간표")
            svg = make_clock_svg(items)
            st.markdown(
                f'<div style="max-width:430px;margin:auto">{svg}</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                "원 둘레는 하루의 시간입니다. 색상 구간은 일정, 추가 활동, "
                "자유시간을 구분합니다."
            )

        with legend_col:
            st.subheader("색상 범례")
            for label, color in [
                ("높음 중요도", COLORS["높음"]),
                ("보통 중요도", COLORS["보통"]),
                ("낮음 중요도", COLORS["낮음"]),
                ("AI 추가 활동", COLORS["추가 활동"]),
                ("자유시간", COLORS["자유시간"]),
            ]:
                st.markdown(
                    f'<span style="color:{color};font-size:20px">●</span> '
                    f'**{label}**',
                    unsafe_allow_html=True,
                )

            st.divider()
            st.write(f"하루 계획 범위: **{duration_text(day_end - day_start)}**")
            st.write(f"일정 및 추가 활동: **{duration_text(activity_minutes)}**")
            st.write(f"자유시간 합계: **{duration_text(free_minutes)}**")

        st.divider()
        st.subheader("시간순 상세 일정")

        for item in items:
            color = item.get("color", "#64748B")

            with st.container(border=True):
                st.markdown(
                    f'<span style="color:{color};font-size:20px">●</span> '
                    f'**{item["name"]}**',
                    unsafe_allow_html=True,
                )
                st.write(
                    f'{clock(item["start_min"])} – {clock(item["end_min"])}'
                    f' · {duration_text(item["duration"])}'
                )
                st.caption(item.get("reason", ""))

                if item.get("kind") == "일정":
                    st.write(f'중요도: **{item["importance"]}**')

                if item.get("detail"):
                    st.write(item["detail"])

        if st.session_state.unscheduled:
            st.warning("배정하지 못한 일정")
            for task in st.session_state.unscheduled:
                st.write(
                    f'- **{task["name"]}** ({task["duration"]}분): '
                    f'{task["reason"]}'
                )

        st.divider()
        st.subheader("CSV 다운로드")

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "날짜", "구분", "일정명", "시작", "종료",
            "소요시간(분)", "중요도", "설명"
        ])

        for item in items:
            writer.writerow([
                plan_date.isoformat(),
                item["kind"],
                item["name"],
                clock(item["start_min"]),
                clock(item["end_min"]),
                item["duration"],
                item["importance"],
                item.get("reason", ""),
            ])

        st.download_button(
            "📥 일정표 CSV 다운로드",
            data="\ufeff" + buffer.getvalue(),
            file_name=f"PlanAI_{plan_date.isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
