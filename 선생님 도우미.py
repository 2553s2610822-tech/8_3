import streamlit as st
from datetime import datetime, date

# -------------------------------------------------------------------
# 0. 페이지 기본 설정 및 세션 초기화
# -------------------------------------------------------------------
st.set_page_config(
    page_title="선생님 업무 도우미 AI",
    page_icon="🏫",
    layout="wide"
)

# 데이터 공유용 세션 상태 초기화
if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "name": "홍길동",
        "school": "행복초등학교",
        "subject": "초등담임/수학",
        "email_notif": True,
        "push_notif": False
    }

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

# -------------------------------------------------------------------
# 1. 각 기능별 페이지 함수 (각 페이지 진입시에만 해당 제목 출력)
# -------------------------------------------------------------------

def page_schedule():
    # '오늘의 일정' 기능에 진입했을 때만 노출되는 타이틀
    st.title("📅 오늘의 일정")
    st.subheader(f"오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### 시간표 및 일정")
        if not st.session_state.events:
            st.info("등록된 일정이 없습니다.")
        for idx, event in enumerate(st.session_state.events):
            with st.expander(f"📌 {event['time']} - {event['title']}", expanded=True):
                st.write(f"일정 내용: {event['title']}")
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

def page_lesson_ai():
    st.title("📚 수업준비 AI")
    st.caption("AI를 활용해 학습 지도안, 퀴즈, 수업 자료를 빠르게 생성합니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        grade = st.selectbox("학년/학기", ["초등 3학년 1학기", "초등 4학년 1학기", "중등 1학년", "고등 1학년"])
        subject = st.text_input("과목/단원", "수학 - 분수의 계산")
    with col2:
        topic = st.text_input("수업 주제", "분수의 개념과 실생활 활용 예시")
        activity_type = st.multiselect("포함할 활동", ["개념 설명", "그룹 토의", "퀴즈/학습지", "실험/실습"], default=["개념 설명", "퀴즈/학습지"])

    if st.button("✨ 수업 자료 AI 생성하기", type="primary"):
        st.info("AI가 수업 지도안 및 평가 요소를 생성 중입니다...")
        st.markdown(f"""
        ### 📚 [{subject}] {topic} 수업안
        - **대상:** {grade}
        - **수업 목표:** {topic}의 기본 원리를 이해하고 문제를 해결할 수 있다.
        
        #### 1. 도입 (10분)
        - 흥미 유발: 피자와 빵을 나누는 실생활 상황 제시
        
        #### 2. 전개 (25분)
        - 핵심 개념 설명 및 구체물 활용 활동
        - 그룹별 분수 모형 조작 실습
        
        #### 3. 정리 및 평가 (10분)
        - AI가 추천하는 오늘의 퀴즈 3문항 풀이
        """)

def page_time_ai():
    st.title("⏳ 효율적 시간 배분 AI")
    st.caption("선생님의 업무 우선순위와 일정을 분석하여 최적의 시간표를 추천합니다.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("업무 우선순위 설정")
        urgent_tasks = st.text_area("오늘 꼭 처리해야 할 중요 업무", "1. 생활기록부 작성\n2. 수학 수업 준비\n3. 학부모 상담 전화")
        available_hours = st.slider("오늘 확보 가능한 비수업 시간 (시간)", 1, 8, 3)
        
        if st.button("📊 시간 배분 AI 분석 실행"):
            st.session_state.time_analyzed = True

    with col2:
        st.subheader("AI 추천 시간 배분 스케줄")
        if st.session_state.get("time_analyzed"):
            st.success("AI 분석 완료: 집중도가 높은 오전에 중요 업무를 배치했습니다.")
            st.markdown("""
            - **09:00 - 10:30 (집중 시간 90분):** 📝 `생활기록부 작성`
            - **10:40 - 11:30 (수업 준비 50분):** 📚 `수업준비 AI 활용`
            - **13:30 - 14:30 (행정/소통 60분):** 📞 `학부모 상담 및 공문 확인`
            - **15:00 - 16:00 (여유 시간 60분):** ☕ `기타 할 일 정돈`
            """)
        else:
            st.info("왼쪽에서 업무를 입력하고 분석 버튼을 눌러주세요.")

def page_admin_robot():
    st.title("🤖 행정업무 로봇")
    st.caption("반복되는 교무 행정 업무, 공문서 요약, 가정통신문 초안 작성을 자동화합니다.")
    
    task_type = st.tabs(["✉️ 가정통신문 생성", "📄 공문서 요약 로봇", "📊 학생 명단 정리"])
    
    with task_type[0]:
        st.subheader("가정통신문 초안 자동 작성")
        title = st.text_input("안내 주제", "봄 현장체험학습 안내")
        if st.button("가정통신문 작성 시작"):
            st.text_area("AI 생성 결과", 
f"""[가정통신문] {title}

학부모님 안녕하십니까?
{title}에 대해 아래와 같이 안내해 드리오니 확인 부탁드립니다.

1. 일시: 2026년 5월 10일(금)
2. 장소: 국립중앙박물관
3. 준비물: 개인 도시락, 개인 위생용품
4. 참가비: 무료""", height=200)

    with task_type[1]:
        st.subheader("긴 공문서 핵심 요약")
        doc_text = st.text_area("공문서 텍스트 붙여넣기", placeholder="내용을 입력하세요.")
        if st.button("공문 요약하기") and doc_text:
            st.warning("📌 [요약 결과]\n1. 제출 마감: 금요일 17:00까지\n2. 제출 서류: 붙임1 양식 엑셀 파일")

    with task_type[2]:
        st.subheader("학급 데이터 자동 정리")
        st.file_uploader("학생 데이터 파일 업로드 (xlsx, csv)", type=["xlsx", "csv"])

def page_todo():
    st.title("☑️ 할 일 목록")
    
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

    for idx, todo in enumerate(st.session_state.todos):
        col_chk, col_text, col_due, col_del = st.columns([0.5, 4, 1.5, 1])
        is_done = col_chk.checkbox("", value=todo["done"], key=f"todo_chk_{idx}")
        if is_done != todo["done"]:
            st.session_state.todos[idx]["done"] = is_done
            st.rerun()
            
        task_text = f"~~{todo['task']}~~" if todo["done"] else todo["task"]
        col_text.markdown(task_text)
        col_due.caption(f"📅 {todo['due']}")
        
        if col_del.button("삭제", key=f"todo_del_{idx}"):
            st.session_state.todos.pop(idx)
            st.rerun()

def page_search():
    st.title("🔍 통합 검색")
    query = st.text_input("검색어를 입력하세요", placeholder="검색할 일정, 할 일, 알림 입력")
    if query:
        st.write(f"**'{query}'** 에 관한 검색 결과:")
        found = False
        matching_events = [e for e in st.session_state.events if query.lower() in e["title"].lower()]
        if matching_events:
            found = True
            st.write("- 일정에서 발견:", matching_events)
        matching_todos = [t for t in st.session_state.todos if query.lower() in t["task"].lower()]
        if matching_todos:
            found = True
            st.write("- 할 일 목록에서 발견:", matching_todos)
        if not found:
            st.info("검색 결과가 없습니다.")

def page_notification():
    st.title("🔔 업무 알림")
    for n in st.session_state.notifications:
        st.info(f"[{n['type']}] {n['content']} (`{n['date']}`)")

def page_settings():
    st.title("⚙️ 설정")
    tab1, tab2 = st.tabs(["👤 사용자 정보", "🔔 알림 설정"])
    with tab1:
        st.text_input("선생님 이름", st.session_state.user_info["name"])
        st.text_input("소속 학교", st.session_state.user_info["school"])
        st.text_input("담당 과목", st.session_state.user_info["subject"])
    with tab2:
        st.toggle("이메일 알림 받기", st.session_state.user_info["email_notif"])
        st.toggle("푸시 알림 받기", st.session_state.user_info["push_notif"])

# -------------------------------------------------------------------
# 2. 메인 네비게이션 등록 및 실행
# -------------------------------------------------------------------

pg = st.navigation({
    "🤖 AI 스마트 기능": [
        st.Page(page_lesson_ai, title="수업준비 AI", icon="📚"),
        st.Page(page_time_ai, title="효율적 시간 배분 AI", icon="⏳"),
        st.Page(page_admin_robot, title="행정업무 로봇", icon="🤖"),
    ],
    "📋 교무 업무 관리": [
        st.Page(page_schedule, title="오늘의 일정", icon="📅"),
        st.Page(page_todo, title="할 일 목록", icon="☑️"),
        st.Page(page_search, title="통합 검색", icon="🔍"),
        st.Page(page_notification, title="업무 알림", icon="🔔"),
    ],
    "⚙️ 시스템": [
        st.Page(page_settings, title="설정", icon="⚙️"),
    ]
})

# 선택된 특정 페이지 1개만 실행 (독립 화면 보장)
pg.run()    
