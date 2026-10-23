import streamlit as st
from datetime import date, time, datetime, timedelta

st.set_page_config(page_title="시간 설계실", page_icon="🗓️", layout="wide")

st.title("🗓️ 시간 설계실")
st.caption("중요한 일은 놓치지 않고, 쉴 시간은 지키는 하루 계획")

st.markdown("""
<style>
.block-container {max-width: 1050px; padding-top: 2rem; padding-bottom: 3rem;}
div[data-testid="stMetric"] {background: rgba(120,120,120,.07); padding: 14px; border-radius: 12px;}
.plan-card {border: 1px solid rgba(128,128,128,.25); border-radius: 12px; padding: 14px; margin: 8px 0;}
.small-note {color: #777; font-size: .9rem;}
</style>
""", unsafe_allow_html=True)

if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"name": "가장 중요한 과제", "duration": 60, "priority": 5, "due": "오늘", "note": "집중이 필요한 핵심 작업"},
        {"name": "복습 또는 정리", "duration": 30, "priority": 3, "due": "오늘", "note": ""},
    ]

with st.sidebar:
    st.header("⚙️ 하루 설정")
    start = st.time_input("시작 시간", value=time(16, 0), step=timedelta(minutes=15))
    end = st.time_input("마칠 시간", value=time(21, 30), step=timedelta(minutes=15))
    break_min = st.number_input("일정 사이 휴식 (분)", min_value=0, max_value=60, value=10, step=5)
    buffer_min = st.number_input("여유 시간 확보 (분)", min_value=0, max_value=240, value=30, step=10)
    focus_limit = st.number_input("한 번에 집중할 최대 시간 (분)", min_value=25, max_value=120, value=50, step=5)
    st.caption("팁: 시작·종료 시간은 실제로 지킬 수 있는 범위로 설정하세요.")

st.subheader("1. 사용할 수 있는 시간")
if end <= start:
    st.error("마치는 시간은 시작 시간보다 늦어야 합니다.")
    st.stop()

start_dt = datetime.combine(date.today(), start)
end_dt = datetime.combine(date.today(), end)
total_min = int((end_dt - start_dt).total_seconds() // 60)
usable_min = max(0, total_min - int(buffer_min))
c1, c2, c3 = st.columns(3)
c1.metric("전체 시간", f"{total_min // 60}시간 {total_min % 60}분")
c2.metric("미리 확보한 여유", f"{int(buffer_min)}분")
c3.metric("일정 배정 가능", f"{usable_min}분")

st.subheader("2. 해야 할 일 입력")
st.write("중요도는 1(낮음)부터 5(매우 높음)까지 선택하세요. 예상 시간은 가능한 한 현실적으로 적어 주세요.")

with st.form("task_form", clear_on_submit=True):
    a, b = st.columns([2, 1])
    new_name = a.text_input("일정 이름", placeholder="예: 수학 숙제")
    new_duration = b.number_input("예상 시간 (분)", min_value=5, max_value=600, value=30, step=5)
    c, d = st.columns([1, 1])
    new_priority = c.select_slider("중요도", options=[1, 2, 3, 4, 5], value=3)
    new_due = d.selectbox("마감", ["오늘", "내일", "이번 주", "마감 여유 있음"])
    new_note = st.text_input("메모 (선택)", placeholder="예: 제출 전 풀이 검토 필요")
    add = st.form_submit_button("＋ 일정 추가", use_container_width=True)
    if add:
        if not new_name.strip():
            st.warning("일정 이름을 입력해 주세요.")
        else:
            st.session_state.tasks.append({
                "name": new_name.strip(), "duration": int(new_duration),
                "priority": int(new_priority), "due": new_due, "note": new_note.strip()
            })
            st.rerun()

if st.session_state.tasks:
    with st.expander("입력한 일정 확인 및 삭제", expanded=True):
        for i, task in enumerate(st.session_state.tasks):
            cols = st.columns([3, 1, 1, 1, 1])
            cols[0].write(f"**{task['name']}**")
            cols[1].write(f"{task['duration']}분")
            cols[2].write(f"중요도 {task['priority']}/5")
            cols[3].write(task["due"])
            if cols[4].button("삭제", key=f"del_{i}"):
                st.session_state.tasks.pop(i)
                st.rerun()
else:
    st.info("일정을 하나 이상 추가하면 시간표를 만들 수 있습니다.")

def explanation(task, assigned, was_split):
    reasons = []
    if task["priority"] >= 4:
        reasons.append("중요도가 높아 우선 배정했습니다.")
    if task["due"] == "오늘":
        reasons.append("마감이 오늘이라 미루는 위험을 줄이도록 앞쪽에 배치했습니다.")
    elif task["due"] == "내일":
        reasons.append("마감이 가까워 오늘 진행 상황을 확보하도록 배치했습니다.")
    else:
        reasons.append("긴급도보다 전체 일정의 균형을 고려해 배치했습니다.")
    advice = task["note"] or "시작 전 필요한 자료를 준비하고, 끝나면 완료 여부를 표시하세요."
    if was_split:
        advice = "작업량이 커서 집중 구간으로 나눴습니다. 각 구간 끝에 짧게 진행 상황을 확인하세요. " + advice
    if assigned < task["duration"]:
        advice = f"시간이 부족해 {assigned}분만 배정했습니다. 남은 {task['duration']-assigned}분은 다음 여유 시간에 이어가세요. " + advice
    return " ".join(reasons), advice

st.subheader("3. 시간표 만들기")
if st.button("✨ 효율적인 시간표 생성", type="primary", use_container_width=True):
    if not st.session_state.tasks:
        st.warning("먼저 일정을 하나 이상 추가해 주세요.")
    else:
        tasks = sorted(
            enumerate(st.session_state.tasks),
            key=lambda x: (-x[1]["priority"],
                           {"오늘": 0, "내일": 1, "이번 주": 2, "마감 여유 있음": 3}[x[1]["due"]],
                           x[0])
        )
        remaining = usable_min
        blocks = []
        current = start_dt
        used_task_minutes = 0
        for original_index, task in tasks:
            if remaining <= 0:
                break
            requested = int(task["duration"])
            assigned_total = min(requested, remaining)
            left = assigned_total
            first_block = True
            while left > 0:
                chunk = min(left, int(focus_limit))
                # Short final chunks are allowed to avoid wasting available time.
                block_start = current
                block_end = current + timedelta(minutes=chunk)
                blocks.append({
                    "task": task, "start": block_start, "end": block_end,
                    "minutes": chunk, "first": first_block,
                    "assigned_total": assigned_total, "requested": requested
                })
                current = block_end
                left -= chunk
                remaining -= chunk
                used_task_minutes += chunk
                first_block = False
                if left > 0 and break_min > 0 and remaining > 0:
                    pause = min(int(break_min), remaining)
                    blocks.append({"rest": True, "start": current,
                                   "end": current + timedelta(minutes=pause),
                                   "minutes": pause})
                    current += timedelta(minutes=pause)
                    remaining -= pause
        st.session_state.last_plan = {
            "blocks": blocks, "total": total_min, "buffer": int(buffer_min),
            "start": start_dt, "end": end_dt, "focus_limit": int(focus_limit),
            "break_min": int(break_min), "used": used_task_minutes
        }

if "last_plan" in st.session_state:
    plan = st.session_state.last_plan
    st.subheader("오늘의 추천 시간표")
    task_blocks = [b for b in plan["blocks"] if not b.get("rest")]
    rest_blocks = [b for b in plan["blocks"] if b.get("rest")]
    c1, c2, c3 = st.columns(3)
    c1.metric("집중 시간", f"{sum(b['minutes'] for b in task_blocks)}분")
    c2.metric("휴식 시간", f"{sum(b['minutes'] for b in rest_blocks)}분")
    c3.metric("확보한 여유", f"{plan['buffer']}분")
    if sum(b["minutes"] for b in task_blocks) == 0:
        st.warning("배정 가능한 시간이 없습니다. 여유 시간을 줄이거나 하루 종료 시간을 늦춰 보세요.")
    for block in plan["blocks"]:
        stamp = f"{block['start'].strftime('%H:%M')}–{block['end'].strftime('%H:%M')}"
        if block.get("rest"):
            st.markdown(f"""<div class="plan-card">☕ <b>{stamp} · 휴식</b><br>
            <span class="small-note">{block['minutes']}분 — 물 마시기, 가볍게 움직이기, 눈 쉬기. 쉬는 동안에는 다음 일을 미리 시작하지 않아도 됩니다.</span></div>""", unsafe_allow_html=True)
        else:
            task = block["task"]
            reason, advice = explanation(task, block["assigned_total"], block["requested"] > plan["focus_limit"])
            st.markdown(f"""<div class="plan-card">🧩 <b>{stamp} · {task['name']}</b>
            <span style="float:right">{block['minutes']}분 · 중요도 {task['priority']}/5</span><br>
            <span class="small-note">배정 이유: {reason}</span><br>
            <span class="small-note">조언: {advice}</span></div>""", unsafe_allow_html=True)

    total_requested = sum(t["duration"] for t in st.session_state.tasks)
    total_assigned = sum(b["minutes"] for b in task_blocks)
    unallocated = max(0, total_requested - total_assigned)
    st.markdown("#### 마무리 점검")
    if unallocated:
        st.warning(f"모든 일정에 필요한 시간보다 {unallocated}분이 부족합니다. 중요도가 낮거나 마감이 여유로운 일정은 다음 날로 옮기는 편이 좋습니다.")
    if plan["buffer"] >= 30:
        st.success("여유 시간을 따로 확보했습니다. 일정이 늦어져도 이 시간을 먼저 사용하고, 가능하면 휴식 시간은 지키세요.")
    else:
        st.info("여유 시간이 적습니다. 이동·준비·예상치 못한 일을 고려해 여유 시간을 30분 이상 확보하는 것을 추천합니다.")
    st.caption("이 도구는 입력값을 바탕으로 규칙 기반 일정을 계산합니다. 실제 소요 시간은 달라질 수 있으니 계획은 유연하게 조정하세요.")

    export_lines = ["오늘의 추천 시간표", ""]
    for block in plan["blocks"]:
        stamp = f"{block['start'].strftime('%H:%M')}–{block['end'].strftime('%H:%M')}"
        if block.get("rest"):
            export_lines.append(f"{stamp} | 휴식 ({block['minutes']}분)")
        else:
            export_lines.append(f"{stamp} | {block['task']['name']} ({block['minutes']}분, 중요도 {block['task']['priority']}/5)")
            reason, advice = explanation(block["task"], block["assigned_total"], block["requested"] > plan["focus_limit"])
            export_lines.append(f"  배정 이유: {reason}")
            export_lines.append(f"  조언: {advice}")
    st.download_button("⬇️ 시간표 텍스트 다운로드", data="\n".join(export_lines),
                       file_name="오늘의_추천_시간표.txt", mime="text/plain",
                       use_container_width=True)

st.divider()
st.caption("시간 설계실 · 현실적인 계획, 충분한 휴식, 지속 가능한 하루")
