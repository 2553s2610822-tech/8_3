
import streamlit as st
import json
import csv
import io
import re
import urllib.request
import urllib.error
from datetime import datetime, date, time, timedelta


# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="PlanAI | AI 일정 플래너",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {max-width: 1150px; padding-top: 2rem;}
    .hero {
        padding: 1.6rem;
        border-radius: 18px;
        background: linear-gradient(120deg, #172554, #2563eb);
        color: white;
        margin-bottom: 1.2rem;
    }
    .hero h1 {color: white; margin-bottom: .4rem;}
    .hero p {color: #dbeafe; margin-bottom: 0;}
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.25);
        padding: 14px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 시간 관련 함수
# -----------------------------
def to_minutes(value):
    return value.hour * 60 + value.minute


def to_time_string(minutes):
    minutes = int(minutes)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_time(value):
    return datetime.strptime(str(value), "%H:%M").time()


def overlaps(start1, end1, start2, end2):
    return start1 < end2 and start2 < end1


def priority_value(importance):
    return {"높음": 3, "보통": 2, "낮음": 1}.get(importance, 1)


def format_duration(minutes):
    hours, mins = divmod(int(minutes), 60)
    if hours and mins:
        return f"{hours}시간 {mins}분"
    if hours:
        return f"{hours}시간"
    return f"{mins}분"


# -----------------------------
# Gemini API
# -----------------------------
def generate_with_gemini(tasks, day_start, day_end, break_minutes, requirements):
    api_key = st.secrets.get("GEMINI_API_KEY", "")

    if not api_key:
        return None, "API 키가 설정되지 않았습니다."

    task_text = json.dumps(tasks, ensure_ascii=False, indent=2)

    prompt = f"""
너는 현실적인 하루 일정표를 만드는 전문 일정 최적화 AI다.

[하루 시간 범위]
시작: {day_start}
종료: {day_end}

[일정 사이 기본 휴식 시간]
{break_minutes}분

[일정 데이터]
{task_text}

[사용자 추가 요구사항]
{requirements if requirements.strip() else "추가 요구사항 없음"}

[필수 규칙]
1. 모든 일정의 id를 정확히 한 번씩 사용한다.
2. 일정의 duration은 입력된 분 단위 소요 시간과 같아야 한다.
3. 시작 시간과 종료 시간은 HH:MM 형식으로 작성한다.
4. 모든 일정은 하루 시간 범위 안에 있어야 한다.
5. 일정끼리 겹치면 안 된다.
6. 고정 일정은 fixed_start 시간을 반드시 지킨다.
7. earliest 이후에 시작하고 deadline 이전에 끝나야 한다.
8. 중요도가 높은 일정을 우선 배치하되, 마감 시간과 고정 일정을 함께 고려한다.
9. 가능한 경우 일정 사이에 {break_minutes}분의 휴식을 확보한다.
10. 조건을 모두 만족할 수 없으면 억지로 시간을 배정하지 말고
    unscheduled 배열에 해당 id와 이유를 기록한다.
11. 사용자의 추가 요구사항을 반영하되, 위 시간 제약과 충돌하면
    시간 제약을 우선한다.

반드시 JSON 객체만 출력한다. 마크다운 코드 블록은 사용하지 않는다.
형식:
{{
  "schedule": [
    {{"id": "T1", "start": "09:00", "end": "10:00",
      "reason": "중요도가 높아 먼저 배치"}}
  ],
  "unscheduled": [
    {{"id": "T2", "reason": "마감 전 필요한 시간이 부족함"}}
  ]
}}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "gemini-2.5-flash-lite:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
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

        text = candidates[0]["content"]["parts"][0]["text"].strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        result = json.loads(text)
        if not isinstance(result, dict):
            return None, "AI 응답 형식이 올바르지 않습니다."

        return result, None

    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")[:500]
        except Exception:
            detail = ""
        return None, f"Gemini API HTTP 오류 ({e.code}): {detail}"

    except urllib.error.URLError:
        return None, "네트워크 연결에 실패했습니다."

    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None, "AI 응답을 해석하지 못했습니다."

    except Exception as e:
        return None, f"예상하지 못한 AI 오류: {str(e)[:250]}"


# -----------------------------
# AI 결과 검증
# -----------------------------
def validate_ai_result(result, tasks, day_start, day_end):
    if not isinstance(result.get("schedule"), list):
        raise ValueError("일정 목록이 없습니다.")

    task_map = {task["id"]: task for task in tasks}
    scheduled = []
    used_ids = set()

    for item in result["schedule"]:
        task_id = item.get("id")

        if task_id not in task_map or task_id in used_ids:
            raise ValueError("일정 ID가 잘못되었거나 중복되었습니다.")

        start = to_minutes(parse_time(item["start"]))
        end = to_minutes(parse_time(item["end"]))
        task = task_map[task_id]

        if end - start != int(task["duration"]):
            raise ValueError(f"'{task['name']}'의 소요 시간이 맞지 않습니다.")

        if start < day_start or end > day_end or end <= start:
            raise ValueError(f"'{task['name']}'의 시간이 범위를 벗어났습니다.")

        earliest = to_minutes(parse_time(task["earliest"]))
        deadline = to_minutes(parse_time(task["deadline"]))

        if start < earliest or end > deadline:
            raise ValueError(f"'{task['name']}'의 가능 시간 또는 마감 조건을 위반했습니다.")

        if task["fixed"] and start != to_minutes(parse_time(task["fixed_start"])):
            raise ValueError(f"'{task['name']}'의 고정 시간이 지켜지지 않았습니다.")

        scheduled.append({
            **task,
            "start_min": start,
            "end_min": end,
            "reason": str(item.get("reason", "AI가 배치한 일정")),
        })
        used_ids.add(task_id)

    scheduled.sort(key=lambda x: x["start_min"])

    for previous, current in zip(scheduled, scheduled[1:]):
        if overlaps(
            previous["start_min"], previous["end_min"],
            current["start_min"], current["end_min"],
        ):
            raise ValueError("AI 결과에서 일정 충돌이 발견되었습니다.")

    unscheduled = []
    for item in result.get("unscheduled", []):
        if not isinstance(item, dict):
            continue
        task_id = item.get("id")
        if task_id in task_map and task_id not in used_ids:
            unscheduled.append({
                **task_map[task_id],
                "reason": str(item.get("reason", "시간 배정 실패")),
            })
            used_ids.add(task_id)

    # AI가 빠뜨린 일정도 미배정으로 표시한다.
    for task in tasks:
        if task["id"] not in used_ids:
            unscheduled.append({
                **task,
                "reason": "AI가 해당 일정의 시간을 배정하지 않았습니다.",
            })

    return scheduled, unscheduled


# -----------------------------
# API 없이 사용하는 대체 일정 생성기
# -----------------------------
def generate_fallback(tasks, day_start, day_end, break_minutes):
    scheduled = []
    unscheduled = []
    occupied = []

    # 고정 일정부터 배치한다.
    fixed_tasks = sorted(
        [t for t in tasks if t["fixed"]],
        key=lambda t: to_minutes(parse_time(t["fixed_start"])),
    )

    for task in fixed_tasks:
        start = to_minutes(parse_time(task["fixed_start"]))
        end = start + int(task["duration"])
        earliest = to_minutes(parse_time(task["earliest"]))
        deadline = to_minutes(parse_time(task["deadline"]))

        valid = (
            start >= day_start
            and end <= day_end
            and start >= earliest
            and end <= deadline
            and not any(overlaps(start, end, a, b) for a, b in occupied)
        )

        if valid:
            scheduled.append({
                **task,
                "start_min": start,
                "end_min": end,
                "reason": "사용자가 지정한 고정 시간",
            })
            occupied.append((start, end))
        else:
            unscheduled.append({
                **task,
                "reason": "고정 시간이 하루 범위를 벗어나거나 다른 일정과 충돌합니다.",
            })

    # 중요도와 마감 시간 순서로 나머지 일정을 배치한다.
    flexible = sorted(
        [t for t in tasks if not t["fixed"]],
        key=lambda t: (
            -priority_value(t["importance"]),
            to_minutes(parse_time(t["deadline"])),
            -int(t["duration"]),
        ),
    )

    for task in flexible:
        earliest = max(day_start, to_minutes(parse_time(task["earliest"])))
        deadline = min(day_end, to_minutes(parse_time(task["deadline"])))
        duration = int(task["duration"])
        placed = False
        candidate = earliest

        while candidate + duration <= deadline:
            end = candidate + duration

            conflict = next(
                (
                    (a, b) for a, b in occupied
                    if overlaps(candidate, end, a, b)
                ),
                None,
            )

            if conflict:
                candidate = conflict[1] + break_minutes
                continue

            scheduled.append({
                **task,
                "start_min": candidate,
                "end_min": end,
                "reason": "중요도와 마감 시간을 고려해 자동 배치",
            })
            occupied.append((candidate, end))
            placed = True
            break

        if not placed:
            unscheduled.append({
                **task,
                "reason": "가능 시간 안에 소요 시간을 확보하지 못했습니다.",
            })

    scheduled.sort(key=lambda x: x["start_min"])
    return scheduled, unscheduled


# -----------------------------
# 화면
# -----------------------------
if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "result" not in st.session_state:
    st.session_state.result = None

if "unscheduled" not in st.session_state:
    st.session_state.unscheduled = []

if "result_mode" not in st.session_state:
    st.session_state.result_mode = ""

st.markdown("""
<div class="hero">
    <h1>🗓️ PlanAI</h1>
    <p>일정을 입력하면 우선순위와 시간 제약에 맞춰 하루 계획을 설계합니다.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 하루 계획 설정")

    plan_date = st.date_input("계획 날짜", value=date.today())
    day_start_time = st.time_input("하루 시작", value=time(8, 0), step=900)
    day_end_time = st.time_input("하루 종료", value=time(22, 0), step=900)
    break_minutes = st.slider("일정 사이 기본 휴식 (분)", 0, 30, 10, 5)

    st.divider()
    st.caption("AI 사용을 위해 Streamlit Secrets에 GEMINI_API_KEY를 등록하세요.")
    st.caption("API를 사용할 수 없어도 기본 자동 일정 생성은 가능합니다.")

day_start = to_minutes(day_start_time)
day_end = to_minutes(day_end_time)

if day_end <= day_start:
    st.error("하루 종료 시간은 시작 시간보다 늦어야 합니다.")

tab_input, tab_result = st.tabs(["✍️ 일정 설계", "📊 생성된 일정표"])

with tab_input:
    st.subheader("1. 일정 추가")

    with st.form("task_form", clear_on_submit=True):
        task_name = st.text_input(
            "일정명",
            placeholder="예: 수학 숙제, 영어 공부, 운동",
        )

        c1, c2 = st.columns(2)
        with c1:
            duration = st.number_input(
                "예상 소요 시간 (분)",
                min_value=5,
                max_value=720,
                value=60,
                step=5,
            )
            importance = st.selectbox(
                "중요도",
                ["높음", "보통", "낮음"],
                index=1,
            )
        with c2:
            earliest_time = st.time_input(
                "가장 빠른 시작 시간",
                value=time(8, 0),
                key="new_earliest",
                step=900,
            )
            deadline_time = st.time_input(
                "완료 마감 시간",
                value=time(22, 0),
                key="new_deadline",
                step=900,
            )

        fixed = st.checkbox("고정 일정 (시작 시간을 지정함)")
        fixed_start_time = st.time_input(
            "고정 시작 시간",
            value=time(9, 0),
            disabled=not fixed,
            step=900,
        )

        detail = st.text_area(
            "일정별 메모 (선택)",
            placeholder="예: 교과서 30~50쪽, 집중해서 풀기",
            max_chars=500,
        )

        submitted = st.form_submit_button(
            "＋ 일정 추가",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not task_name.strip():
                st.error("일정명을 입력하세요.")
            elif to_minutes(deadline_time) <= to_minutes(earliest_time):
                st.error("마감 시간은 가장 빠른 시작 시간보다 늦어야 합니다.")
            elif fixed and not (
                to_minutes(earliest_time)
                <= to_minutes(fixed_start_time)
                and to_minutes(fixed_start_time) + int(duration)
                <= to_minutes(deadline_time)
            ):
                st.error("고정 시작 시간과 소요 시간이 가능 시간 및 마감 범위 안에 있어야 합니다.")
            else:
                new_id = f"T{len(st.session_state.tasks) + 1}"
                st.session_state.tasks.append({
                    "id": new_id,
                    "name": task_name.strip(),
                    "duration": int(duration),
                    "importance": importance,
                    "earliest": earliest_time.strftime("%H:%M"),
                    "deadline": deadline_time.strftime("%H:%M"),
                    "fixed": fixed,
                    "fixed_start": fixed_start_time.strftime("%H:%M"),
                    "detail": detail.strip(),
                })
                st.success(f"'{task_name.strip()}' 일정을 추가했습니다.")

    st.divider()
    st.subheader(f"2. 입력한 일정 ({len(st.session_state.tasks)}개)")

    if not st.session_state.tasks:
        st.info("아직 일정이 없습니다. 위에서 첫 일정을 추가하세요.")
    else:
        for i, task in enumerate(st.session_state.tasks):
            with st.container(border=True):
                col_info, col_delete = st.columns([5, 1])
                with col_info:
                    pin = " 📌 고정" if task["fixed"] else ""
                    st.markdown(f"**{task['name']}**{pin}")
                    st.caption(
                        f"{task['duration']}분 · 중요도 {task['importance']} · "
                        f"{task['earliest']}~{task['deadline']}"
                    )
                    if task["detail"]:
                        st.write(task["detail"])
                with col_delete:
                    if st.button("삭제", key=f"del_{i}"):
                        st.session_state.tasks.pop(i)
                        st.rerun()

    st.divider()
    st.subheader("3. 추가 요구사항")

    requirements = st.text_area(
        "AI에게 원하는 계획 방식",
        placeholder=(
            "예: 수학을 오전에 배치해 줘.\n"
            "점심시간 12:00~13:00을 확보해 줘.\n"
            "집중이 필요한 공부는 50분 후 10분 쉬게 해 줘."
        ),
        height=120,
        max_chars=2000,
        key="requirements",
    )

    st.caption("식사 시간이나 외출 시간처럼 반드시 비워야 할 시간은 요구사항에 구체적으로 적어주세요.")

    b1, b2 = st.columns(2)
    with b1:
        make_ai = st.button(
            "✨ AI 일정표 생성",
            type="primary",
            use_container_width=True,
        )
    with b2:
        make_basic = st.button(
            "⚡ 기본 일정표 생성",
            use_container_width=True,
        )

    if make_ai or make_basic:
        if day_end <= day_start:
            st.error("하루 시작 및 종료 시간을 확인하세요.")
        elif not st.session_state.tasks:
            st.warning("먼저 일정을 하나 이상 추가하세요.")
        else:
            with st.spinner("일정의 우선순위와 시간 조건을 분석하고 있습니다..."):
                schedule = None
                unscheduled = []
                mode = "기본 자동 생성"

                if make_ai:
                    ai_result, error = generate_with_gemini(
                        st.session_state.tasks,
                        day_start_time.strftime("%H:%M"),
                        day_end_time.strftime("%H:%M"),
                        break_minutes,
                        requirements,
                    )

                    if ai_result is not None:
                        try:
                            schedule, unscheduled = validate_ai_result(
                                ai_result,
                                st.session_state.tasks,
                                day_start,
                                day_end,
                            )
                            mode = "Gemini AI"
                        except Exception as e:
                            st.warning(
                                f"AI 결과 검증에 실패해 기본 생성 방식으로 전환합니다. ({e})"
                            )
                    else:
                        st.warning(
                            f"{error} 기본 자동 생성 방식으로 일정을 만듭니다."
                        )

                if schedule is None:
                    schedule, unscheduled = generate_fallback(
                        st.session_state.tasks,
                        day_start,
                        day_end,
                        break_minutes,
                    )
                    mode = "기본 자동 생성"

                st.session_state.result = schedule
                st.session_state.unscheduled = unscheduled
                st.session_state.result_mode = mode
                st.session_state.plan_date = plan_date
                st.session_state.plan_requirements = requirements
                st.rerun()


with tab_result:
    st.subheader("오늘의 타임라인")
    st.caption(f"계획 날짜: {plan_date.strftime('%Y년 %m월 %d일')}")

    result = st.session_state.result

    if result is None:
        st.info("일정을 입력한 뒤 'AI 일정표 생성' 버튼을 누르세요.")
    else:
        total_minutes = sum(x["duration"] for x in result)
        free_minutes = max(0, day_end - day_start - total_minutes)
        scheduled_count = len(result)
        unscheduled_count = len(st.session_state.unscheduled)

        m1, m2, m3 = st.columns(3)
        m1.metric("배정된 일정", f"{scheduled_count}개")
        m2.metric("집중·활동 시간", format_duration(total_minutes))
        m3.metric("미배정 일정", f"{unscheduled_count}개")

        st.caption(
            f"생성 방식: {st.session_state.result_mode} · "
            f"하루 전체 시간: {format_duration(day_end - day_start)} · "
            f"미배정 시간 포함 여유 시간: {format_duration(free_minutes)}"
        )

        if result:
            st.markdown("#### 시간순 일정")

            for item in result:
                start_str = to_time_string(item["start_min"])
                end_str = to_time_string(item["end_min"])
                importance_color = {
                    "높음": "🔴",
                    "보통": "🟡",
                    "낮음": "🟢",
                }.get(item["importance"], "⚪")

                with st.container(border=True):
                    left, right = st.columns([1, 4])
                    with left:
                        st.markdown(f"**{start_str}**")
                        st.caption(end_str)
                    with right:
                        st.markdown(
                            f"**{importance_color} {item['name']}** "
                            f"`{item['duration']}분`"
                        )
                        st.caption(item.get("reason", ""))
                        if item.get("detail"):
                            st.write(item["detail"])

        if st.session_state.unscheduled:
            st.warning("아래 일정은 시간 조건을 만족하지 못해 배정되지 않았습니다.")
            for item in st.session_state.unscheduled:
                st.markdown(
                    f"- **{item['name']}** ({item['duration']}분): "
                    f"{item.get('reason', '시간 부족')}"
                )

        st.divider()
        st.subheader("CSV 다운로드")

        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow([
            "날짜", "일정명", "시작", "종료", "소요시간(분)",
            "중요도", "고정일정", "메모", "배치 이유"
        ])

        for item in result:
            writer.writerow([
                st.session_state.get("plan_date", plan_date).isoformat(),
                item["name"],
                to_time_string(item["start_min"]),
                to_time_string(item["end_min"]),
                item["duration"],
                item["importance"],
                "예" if item["fixed"] else "아니오",
                item["detail"],
                item.get("reason", ""),
            ])

        st.download_button(
            "📥 일정표 CSV 다운로드",
            data="\ufeff" + csv_buffer.getvalue(),
            file_name=f"PlanAI_{st.session_state.get('plan_date', plan_date).isoformat()}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.caption(
            "CSV 파일은 Excel이나 Google 스프레드시트에서 열 수 있습니다. "
            "시간이 바뀌면 일정표를 다시 생성하세요."
        )
