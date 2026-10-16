import streamlit as st
from datetime import datetime, date

# 페이지 기본 설정
st.set_page_config(
    page_title="선생님 업무 도우미",
    page_icon="🏫",
    layout="wide"
)

# 세션 상태 초기화 (데이터 저장용)
if "todos" not in st.session_state:
    st.session_state.todos = [
        {"task": "수학 수행평가 채점하기", "done": False, "due": str(date.today())},
        {"task": "학부모 가정통신문 발송", "done": True, "due": str(date.today())}
    ]

if "events" not in st.session_state:
    st.session_state.events = [
        {"time": "09:00 - 09:40", "title": "1교시: 3학년 1반 수학"},
        {"time": "10:00 - 10:40", "title": "2교시: 동아리 활동"},
        {"time": "14:00 - 15:00", "title": "교직원 협의회"}
    ]

if "notifications" not in st.session_state:
    st.session_state.notifications = [
        {"type": "공지", "content": "내일 교내 소방훈련 실시 안내", "date": "2026-10-16"},
        {"type": "마감", "content": "생활기록부 1차 입력 마감 D-3", "date": "2026-10-16"}
    ]

if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "name": "홍길동",
        "school": "행복초등학교",
        "subject": "초등담임/수학",
        "email_notif": True,
        "push_notif": False
    }

# 사이드바 메뉴 구성
st.sidebar.title("🏫 선생님 도우미")
st.sidebar.write(f"**{st.session_state.user_info['name']}** 선생님 환영합니다!")

menu = st.sidebar.radio(
    "메뉴 선택",
    ["📅 오늘의 일정", "☑️ 할 일 목록", "🔍 통합 검색", "🔔 업무 알림", "⚙️ 설정"]
)

st.sidebar.divider()
st.sidebar.caption("v1.0.0 | Streamlit Assistant")

# -------------------------------------------------------------------
# 1. 오늘의 일정
# -------------------------------------------------------------------
if menu == "📅 오늘의 일정":
    st.header("📅 오늘의 일정")
    st.subheader(f"오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### 시간표 및 일정")
        for idx, event in enumerate(st.session_state.events):
            with st.expander(f"📌 {event['time']} - {event['title']}", expanded=True):
                st.write(f"상세 내용: {event['title']}")
                if st.button("일정 삭제", key=f"del_evt_{idx}"):
                    st.session_state.events.pop(idx)
                    st.rerun()

    with col2:
        st.write("### 새 일정 추가")
        with st.form("add_event_form"):
            evt_time = st.text_input("시간 (예: 11:00 - 11:40)")
            evt_title = st.text_input("일정 내용")
            submit = st.form_submit_button("일정 저장")
            
            if submit and evt_time and evt_title:
                st.session_state.events.append({"time": evt_time, "title": evt_title})
                st.success("새 일정이 추가되었습니다.")
                st.rerun()

# -------------------------------------------------------------------
# 2. 할 일 목록
# -------------------------------------------------------------------
elif menu == "☑️ 할 일 목록":
    st.header("☑️ 할 일 목록 (To-Do)")
    
    # 새 할 일 추가
    col_input, col_date, col_btn = st.columns([3, 1.5, 1])
    with col_input:
        new_task = st.text_input("새로운 업무 등록", placeholder="예: 공문서 처리하기", label_visibility="collapsed")
    with col_date:
        due_date = st.date_input("마감일", date.today(), label_visibility="collapsed")
    with col_btn:
        if st.button("추가", use_container_width=True):
            if new_task:
                st.session_state.todos.append({"task": new_task, "done": False, "due": str(due_date)})
                st.rerun()

    st.divider()

    # 목록 표시 및 체크박스
    for idx, todo in enumerate(st.session_state.todos):
        col_chk, col_text, col_due, col_del = st.columns([0.5, 4, 1.5, 1])
        
        # 완료 여부 체크박스
        is_done = col_chk.checkbox("", value=todo["done"], key=f"todo_chk_{idx}")
        if is_done != todo["done"]:
            st.session_state.todos[idx]["done"] = is_done
            st.rerun()
            
        # 텍스트 스타일링 (완료 시 취소선)
        task_text = f"~~{todo['task']}~~" if todo["done"] else todo["task"]
        col_text.markdown(task_text)
        col_due.caption(f"📅 {todo['due']}")
        
        if col_del.button("삭제", key=f"todo_del_{idx}"):
            st.session_state.todos.pop(idx)
            st.rerun()

# -------------------------------------------------------------------
# 3. 통합 검색
# -------------------------------------------------------------------
elif menu == "🔍 통합 검색":
    st.header("🔍 통합 검색")
    st.caption("일정, 할 일, 업무 알림 내역을 한 번에 검색합니다.")
    
    query = st.text_input("검색어를 입력하세요", placeholder="예: 수학, 공지, 채점 등")
    
    if query:
        st.subheader(f"'{query}' 검색 결과")
        found = False
        
        # 1. 일정 검색
        matching_events = [e for e in st.session_state.events if query.lower() in e["title"].lower()]
        if matching_events:
            found = True
            st.write("**[오늘의 일정]**")
            for e in matching_events:
                st.write(f"- {e['time']} : {e['title']}")
                
        # 2. 할 일 검색
        matching_todos = [t for t in st.session_state.todos if query.lower() in t["task"].lower()]
        if matching_todos:
            found = True
            st.write("**[할 일 목록]**")
            for t in matching_todos:
                status = "완료" if t['done'] else "미완료"
                st.write(f"- [{status}] {t['task']} (마감: {t['due']})")
                
        # 3. 알림 검색
        matching_notifs = [n for n in st.session_state.notifications if query.lower() in n["content"].lower()]
        if matching_notifs:
            found = True
            st.write("**[업무 알림]**")
            for n in matching_notifs:
                st.write(f"- [{n['type']}] {n['content']} ({n['date']})")
                
        if not found:
            st.info("검색 결과가 없습니다.")

# -------------------------------------------------------------------
# 4. 업무 알림
# -------------------------------------------------------------------
elif menu == "🔔 업무 알림":
    st.header("🔔 업무 알림")
    
    for n in st.session_state.notifications:
        badge_color = "red" if n["type"] == "마감" else "blue"
        st.markdown(f":{badge_color}[[{n['type']}]] **{n['content']}** (`{n['date']}`)")
        st.divider()
        
    with st.expander("➕ 새 알림 등록 (테스트/자체 공지용)"):
        with st.form("notif_form"):
            n_type = st.selectbox("알림 종류", ["공지", "마감", "안내"])
            n_content = st.text_input("알림 내용")
            if st.form_submit_button("알림 등록") and n_content:
                st.session_state.notifications.insert(0, {
                    "type": n_type,
                    "content": n_content,
                    "date": str(date.today())
                })
                st.rerun()

# -------------------------------------------------------------------
# 5. 설정
# -------------------------------------------------------------------
elif menu == "⚙️ 설정":
    st.header("⚙️ 앱 설정")
    
    tab1, tab2, tab3 = st.tabs(["👤 사용자 정보", "🔔 알림 설정", "ℹ️ 앱 기본 정보"])
    
    with tab1:
        st.subheader("사용자 프로필 변경")
        name = st.text_input("선생님 이름", st.session_state.user_info["name"])
        school = st.text_input("소속 학교", st.session_state.user_info["school"])
        subject = st.text_input("담당 학년/과목", st.session_state.user_info["subject"])
        
        if st.button("프로필 저장"):
            st.session_state.user_info["name"] = name
            st.session_state.user_info["school"] = school
            st.session_state.user_info["subject"] = subject
            st.success("사용자 정보가 수정되었습니다.")
            st.rerun()
            
    with tab2:
        st.subheader("알림 수신 설정")
        email_notif = st.toggle("이메일 알림 받기", st.session_state.user_info["email_notif"])
        push_notif = st.toggle("브라우저 푸시 알림 받기", st.session_state.user_info["push_notif"])
        
        if st.button("알림 설정 저장"):
            st.session_state.user_info["email_notif"] = email_notif
            st.session_state.user_info["push_notif"] = push_notif
            st.success("알림 설정이 업데이트되었습니다.")
            
    with tab3:
        st.subheader("앱 기본 정보")
        st.write("- **앱 이름:** 선생님 업무 지원 웹 앱")
        st.write("- **버전:** v1.0.0")
        st.write("- **개발 프레임워크:** Python / Streamlit")
        st.write("- **배포 방식:** GitHub + Streamlit Community Cloud")

