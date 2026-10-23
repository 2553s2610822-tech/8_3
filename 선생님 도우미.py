import streamlit as st
import pandas as pd
from datetime import datetime, date, time

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정 및 스타일 지정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="스마트 워크스페이스 Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS로 깔끔한 디자인 적용
st.markdown("""
<style>
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e9ecef;
    }
    .status-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 세션 상태(Session State) 초기화 (데이터 보존용)
# -----------------------------------------------------------------------------
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {
        'name': '홍길동',
        'dept': '디지털혁신팀',
        'email': 'hong@example.com',
        'noti_email': True,
        'noti_sound': False
    }

if 'schedules' not in st.session_state:
    st.session_state.schedules = [
        {"id": 1, "time": "09:30", "title": "주간 팀 스크럼 회의", "location": "회의실 A", "status": "진행예정"},
        {"id": 2, "time": "14:00", "title": "클라이언트 Q3 프로젝트 리뷰", "location": "온라인 (Zoom)", "status": "진행예정"},
        {"id": 3, "time": "16:30", "title": "신규 기능 서비스 데모 시연", "location": "대회의실", "status": "진행예정"},
    ]

if 'todos' not in st.session_state:
    st.session_state.todos = [
        {"id": 1, "task": "주간 보고서 작성 및 결재", "category": "업무", "priority": "높음", "done": False},
        {"id": 2, "task": "스프린트 백로그 정제", "category": "기획", "priority": "보통", "done": True},
        {"id": 3, "task": "코드 리뷰 참여 (PR #42)", "category": "개발", "priority": "높음", "done": False},
    ]

if 'notifications' not in st.session_state:
    st.session_state.notifications = [
        {"id": 1, "type": "일정", "message": "30분 뒤 '주간 팀 스크럼 회의'가 시작됩니다.", "timestamp": "09:00", "read": False},
        {"id": 2, "type": "할일", "message": "마감 임박: '주간 보고서 작성' 할 일이 남아있습니다.", "timestamp": "10:15", "read": False},
        {"id": 3, "type": "시스템", "message": "새로운 대시보드 업데이트가 반영되었습니다.", "timestamp": "08:30", "read": True},
    ]

# -----------------------------------------------------------------------------
# 3. 사이드바 (메뉴 이동 및 사용자 정보)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("💼 Smart Workspace")
    
    # 사용자 프로필 요약 표시
    st.caption(f"👤 {st.session_state.user_profile['name']} ({st.session_state.user_profile['dept']})")
    
    st.divider()
    
    # 사이드바 메뉴 선택
    menu = st.radio(
        "📌 메뉴 선택",
        ["오늘의 일정", "할 일 목록", "통합 검색", "업무 알림", "설정"],
        index=0
    )
    
    st.divider()
    
    # 미읽은 알림 배지 표시
    unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
    if unread_count > 0:
        st.info(f"🔔 읽지 않은 알림이 **{unread_count}개** 있습니다.")
    else:
        st.success("✅ 모든 알림을 확인했습니다.")

# -----------------------------------------------------------------------------
# 4. 페이지별 구현
# -----------------------------------------------------------------------------

# ----------------------------------------------------
# PAGE 1: 오늘의 일정
# ----------------------------------------------------
if menu == "오늘의 일정":
    st.header("📅 오늘의 일정")
    st.write(f"오늘 날짜: **{date.today().strftime('%Y년 %m월 %d일')}**")
    
    # 상단 요약 지표
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 일정 수", f"{len(st.session_state.schedules)}개")
    with col2:
        completed_sch = sum(1 for s in st.session_state.schedules if s['status'] == '완료')
        st.metric("완료된 일정", f"{completed_sch}개")
    with col3:
        st.metric("남은 일정", f"{len(st.session_state.schedules) - completed_sch}개")
        
    st.divider()
    
    # 일정 추가 폼
    with st.expander("➕ 새 일정 추가하기"):
        with st.form("add_schedule_form", clear_on_submit=True):
            sch_time = st.time_input("시간", value=time(9, 0))
            sch_title = st.text_input("일정 제목", placeholder="예: 주간 회의")
            sch_location = st.text_input("장소", placeholder="예: 회의실 B 또는 Zoom")
            
            submitted = st.form_submit_button("일정 추가")
            if submitted:
                if sch_title.strip():
                    new_id = max([s['id'] for s in st.session_state.schedules], default=0) + 1
                    st.session_state.schedules.append({
                        "id": new_id,
                        "time": sch_time.strftime("%H:%M"),
                        "title": sch_title,
                        "location": sch_location if sch_location else "미정",
                        "status": "진행예정"
                    })
                    st.success("일정이 추가되었습니다!")
                    st.rerun()
                else:
                    st.warning("일정 제목을 입력해주세요.")

    # 일정 목록 출력 및 상태 변경/삭제
    st.subheader("📋 일정 목록")
    if not st.session_state.schedules:
        st.info("등록된 일정이 없습니다.")
    else:
        # 시간순 정렬
        sorted_schedules = sorted(st.session_state.schedules, key=lambda x: x['time'])
        for idx, sch in enumerate(sorted_schedules):
            col_time, col_info, col_status, col_action = st.columns([1.5, 4, 2, 1.5])
            
            with col_time:
                st.markdown(f"🕒 **{sch['time']}**")
            with col_info:
                st.markdown(f"**{sch['title']}**")
                st.caption(f"📍 {sch['location']}")
            with col_status:
                status_options = ["진행예정", "진행중", "완료"]
                new_status = st.selectbox(
                    "상태", 
                    status_options, 
                    index=status_options.index(sch['status']),
                    key=f"sch_status_{sch['id']}",
                    label_visibility="collapsed"
                )
                if new_status != sch['status']:
                    sch['status'] = new_status
                    st.rerun()
            with col_action:
                if st.button("삭제", key=f"del_sch_{sch['id']}"):
                    st.session_state.schedules = [s for s in st.session_state.schedules if s['id'] != sch['id']]
                    st.rerun()
            st.divider()

# ----------------------------------------------------
# PAGE 2: 할 일 목록
# ----------------------------------------------------
elif menu == "할 일 목록":
    st.header("✅ 할 일 목록 (To-Do List)")
    
    # 새 할 일 추가
    with st.expander("➕ 새 할 일 추가하기", expanded=True):
        col_in1, col_in2, col_in3 = st.columns([3, 1.5, 1.5])
        with col_in1:
            task_text = st.text_input("할 일 내용을 입력하세요", key="new_todo_text")
        with col_in2:
            task_cat = st.selectbox("카테고리", ["업무", "기획", "개발", "개인"], key="new_todo_cat")
        with col_in3:
            task_pri = st.selectbox("우선순위", ["높음", "보통", "낮음"], key="new_todo_pri")
            
        if st.button("할 일 추가", use_container_width=True):
            if task_text.strip():
                new_id = max([t['id'] for t in st.session_state.todos], default=0) + 1
                st.session_state.todos.append({
                    "id": new_id,
                    "task": task_text,
                    "category": task_cat,
                    "priority": task_pri,
                    "done": False
                })
                st.success("새 할 일이 추가되었습니다!")
                st.rerun()
            else:
                st.warning("할 일 내용을 입력해주세요.")

    st.divider()
    
    # 진행 상황 프로그레스 바
    if st.session_state.todos:
        total = len(st.session_state.todos)
        dones = sum(1 for t in st.session_state.todos if t['done'])
        progress = dones / total
        st.write(f"**진행률: {int(progress * 100)}%** ({dones}/{total} 완료)")
        st.progress(progress)

    st.subheader("📝 Task List")
    
    if not st.session_state.todos:
        st.info("등록된 할 일이 없습니다.")
    else:
        for todo in st.session_state.todos:
            c1, c2, c3, c4, c5 = st.columns([0.5, 4, 1.5, 1.5, 1])
            
            with c1:
                is_done = st.checkbox("", value=todo['done'], key=f"todo_check_{todo['id']}")
                if is_done != todo['done']:
                    todo['done'] = is_done
                    st.rerun()
            
            with c2:
                if todo['done']:
                    st.markdown(f"~~{todo['task']}~~")
                else:
                    st.markdown(f"**{todo['task']}**")
            
            with c3:
                st.caption(f"📁 {todo['category']}")
                
            with c4:
                color = "🔴" if todo['priority'] == "높음" else ("🟡" if todo['priority'] == "보통" else "🟢")
                st.caption(f"{color} {todo['priority']}")
                
            with c5:
                if st.button("삭제", key=f"del_todo_{todo['id']}"):
                    st.session_state.todos = [t for t in st.session_state.todos if t['id'] != todo['id']]
                    st.rerun()

# ----------------------------------------------------
# PAGE 3: 통합 검색
# ----------------------------------------------------
elif menu == "통합 검색":
    st.header("🔍 통합 검색")
    st.caption("일정, 할 일, 알림 데이터를 한 번에 검색합니다.")
    
    search_query = st.text_input("검색어를 입력하세요", placeholder="예: 회의, 보고서, 프로젝트...").strip()
    
    if search_query:
        st.subheader(f"'{search_query}' 검색 결과")
        
        # 1. 일정 검색 결과
        matched_schedules = [s for s in st.session_state.schedules if search_query.lower() in s['title'].lower() or search_query.lower() in s['location'].lower()]
        
        # 2. 할 일 검색 결과
        matched_todos = [t for t in st.session_state.todos if search_query.lower() in t['task'].lower() or search_query.lower() in t['category'].lower()]
        
        # 3. 알림 검색 결과
        matched_notis = [n for n in st.session_state.notifications if search_query.lower() in n['message'].lower()]
        
        total_results = len(matched_schedules) + len(matched_todos) + len(matched_notis)
        
        if total_results == 0:
            st.warning("검색 결과가 없습니다.")
        else:
            st.success(f"총 {total_results}건의 항목을 찾았습니다.")
            
            tab1, tab2, tab3 = st.tabs([f"📅 일정 ({len(matched_schedules)})", f"✅ 할 일 ({len(matched_todos)})", f"🔔 알림 ({len(matched_notis)})"])
            
            with tab1:
                if matched_schedules:
                    for s in matched_schedules:
                        st.write(f"- **[{s['time']}]** {s['title']} *(장소: {s['location']} | 상태: {s['status']})*")
                else:
                    st.write("일치하는 일정이 없습니다.")
                    
            with tab2:
                if matched_todos:
                    for t in matched_todos:
                        status_str = "완료" if t['done'] else "미완료"
                        st.write(f"- **[{t['category']}]** {t['task']} *(우선순위: {t['priority']} | 상태: {status_str})*")
                else:
                    st.write("일치하는 할 일이 없습니다.")
                    
            with tab3:
                if matched_notis:
                    for n in matched_notis:
                        st.write(f"- **[{n['type']}]** {n['message']} *(시간: {n['timestamp']})*")
                else:
                    st.write("일치하는 알림이 없습니다.")
    else:
        st.info("상단 입력창에 검색어를 입력하시면 관련 항목들을 바로 찾아드립니다.")

# ----------------------------------------------------
# PAGE 4: 업무 알림
# ----------------------------------------------------
elif menu == "업무 알림":
    st.header("🔔 업무 알림 센터")
    
    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.caption("시스템 및 주요 업무 관련 알림을 확인할 수 있습니다.")
    with col_b:
        if st.button("모두 읽음 처리"):
            for n in st.session_state.notifications:
                n['read'] = True
            st.rerun()
            
    st.divider()
    
    if not st.session_state.notifications:
        st.info("새로운 알림이 없습니다.")
    else:
        for noti in st.session_state.notifications:
            card_color = "#f0f2f6" if noti['read'] else "#e8f4f8"
            border_color = "#ccc" if noti['read'] else "#0066cc"
            
            st.markdown(
                f"""
                <div style="background-color: {card_color}; padding: 12px; border-radius: 8px; border-left: 5px solid {border_color}; margin-bottom: 10px;">
                    <span style="font-size: 12px; color: #666;">[{noti['timestamp']}] <b>{noti['type']}</b></span><br/>
                    <span style="font-size: 15px; font-weight: {'normal' if noti['read'] else 'bold'};">{noti['message']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            col_btn1, col_btn2 = st.columns([1, 8])
            with col_btn1:
                if not noti['read']:
                    if st.button("읽음", key=f"read_noti_{noti['id']}"):
                        noti['read'] = True
                        st.rerun()
            st.write("")

# ----------------------------------------------------
# PAGE 5: 설정
# ----------------------------------------------------
elif menu == "설정":
    st.header("⚙️ 앱 설정")
    
    tab_user, tab_noti, tab_info = st.tabs(["👤 사용자 정보", "🔔 알림 설정", "ℹ️ 앱 기본 정보"])
    
    # 1. 사용자 정보
    with tab_user:
        st.subheader("사용자 프로필 수정")
        with st.form("user_profile_form"):
            name = st.text_input("이름", value=st.session_state.user_profile['name'])
            dept = st.text_input("부서", value=st.session_state.user_profile['dept'])
            email = st.text_input("이메일", value=st.session_state.user_profile['email'])
            
            save_user = st.form_submit_button("프로필 저장")
            if save_user:
                st.session_state.user_profile['name'] = name
                st.session_state.user_profile['dept'] = dept
                st.session_state.user_profile['email'] = email
                st.success("프로필 정보가 수정되었습니다!")
                st.rerun()

    # 2. 알림 설정
    with tab_noti:
        st.subheader("알림 수신 설정")
        noti_email = st.checkbox("이메일 알림 받기", value=st.session_state.user_profile['noti_email'])
        noti_sound = st.checkbox("소리 알림 켜기", value=st.session_state.user_profile['noti_sound'])
        
        if st.button("알림 설정 저장"):
            st.session_state.user_profile['noti_email'] = noti_email
            st.session_state.user_profile['noti_sound'] = noti_sound
            st.success("알림 설정이 저장되었습니다.")

    # 3. 앱 기본 정보
    with tab_info:
        st.subheader("애플리케이션 정보")
        st.markdown("""
        - **앱 이름**: Smart Workspace Dashboard
        - **버전**: v1.0.0
        - **프레임워크**: Streamlit
        - **배포 환경**: Streamlit Community Cloud
        - **설명**: 업무 일정, 할 일, 검색 및 알림을 통합 관리하는 개인 대시보드 앱입니다.
        """)
