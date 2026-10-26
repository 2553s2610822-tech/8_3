import streamlit as st
import pandas as pd
from datetime import datetime, date, time

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인 (이미지 테마 스타일 적용: 민트/청록 포인트, 둥근 라운딩)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="선생님 도우미",
    page_icon="👩‍🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 첨부 이미지의 민트/에메랄드 톤과 소프트 라운딩 UI CSS 디자인
st.markdown("""
<style>
    /* 메인 배경 및 폰트 컬러 */
    .main {
        background-color: #F7FAFA;
    }
    
    /* 카드 및 박스 디자인 (라운드 코너 & 부드러운 그림자) */
    div[data-testid="stMetric"], .stExpander {
        background-color: #FFFFFF !important;
        border-radius: 16px !important;
        border: 1px solid #E1F0EE !important;
        box-shadow: 0 4px 12px rgba(54, 197, 181, 0.08) !important;
        padding: 16px !important;
    }
    
    /* 포인트 민트 컬러 커스텀 헤더 */
    .teacher-header {
        background: linear-gradient(135deg, #4CD0C0 0%, #36C5B5 100%);
        padding: 24px;
        border-radius: 20px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 6px 16px rgba(54, 197, 181, 0.2);
    }
    .teacher-header h1 {
        color: white !important;
        margin: 0;
        font-size: 28px;
        font-weight: 700;
    }
    .teacher-header p {
        color: #E6F8F6 !important;
        margin: 5px 0 0 0;
        font-size: 16px;
    }

    /* 버튼 스타일 (민트 포인트컬러) */
    .stButton>button {
        background-color: #36C5B5 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 8px 16px !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #2BAE9F !important;
        box-shadow: 0 4px 10px rgba(54, 197, 181, 0.3);
    }
    
    /* 입력창 라운딩 */
    .stTextInput input, .stSelectbox select, .stTimeInput input {
        border-radius: 10px !important;
        border: 1px solid #CDEBE6 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 세션 상태(Session State) 초기화 (데이터 보존)
# -----------------------------------------------------------------------------
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {
        'name': '김선생님',
        'dept': '3학년 2반 담임',
        'email': 'teacher@school.ed.kr',
        'noti_email': True,
        'noti_sound': False
    }

if 'schedules' not in st.session_state:
    st.session_state.schedules = [
        {"id": 1, "time": "08:40", "title": "아침 학급 조회 및 인원 점검", "location": "3학년 2반 교실", "status": "완료"},
        {"id": 2, "time": "10:00", "title": "2교시 수학 수업 (도형 단원)", "location": "3학년 2반 교실", "status": "진행중"},
        {"id": 3, "time": "14:30", "title": "전학교직원 학부모 상담 협의회", "location": "교무회의실", "status": "진행예정"},
    ]

if 'todos' not in st.session_state:
    st.session_state.todos = [
        {"id": 1, "task": "수학 수행평가 채점 및 나이스 입력", "category": "성적/평가", "priority": "높음", "done": False},
        {"id": 2, "task": "현장체험학습 가정통신문 수합 확인", "category": "학급운영", "priority": "보통", "done": True},
        {"id": 3, "task": "학부모 상담 일지 정리", "category": "상담", "priority": "높음", "done": False},
    ]

if 'notifications' not in st.session_state:
    st.session_state.notifications = [
        {"id": 1, "type": "학사일정", "message": "내일은 교직원 연수일입니다. (15:00~)", "timestamp": "08:30", "read": False},
        {"id": 2, "type": "업무알림", "message": "현장체험학습 결재 신청 마감이 오늘까지입니다.", "timestamp": "09:10", "read": False},
        {"id": 3, "type": "시스템", "message": "선생님 도우미 앱 업데이트가 완료되었습니다.", "timestamp": "08:00", "read": True},
    ]

# -----------------------------------------------------------------------------
# 3. 사이드바 (메뉴 및 선생님 프로필)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("👩‍🏫 선생님 도우미")
    st.caption("오늘도 좋은 하루 되세요 🌿")
    st.write(f"**{st.session_state.user_profile['name']}** ({st.session_state.user_profile['dept']})")
    st.divider()
    
    # 메뉴 구성
    menu = st.radio(
        "📌 Quick Menu",
        ["오늘의 일정", "할 일 목록", "통합 검색", "업무 알림", "설정"],
        index=0
    )
    
    st.divider()
    
    # 알림 개수 표시
    unread_count = sum(1 for n in st.session_state.notifications if not n['read'])
    if unread_count > 0:
        st.info(f"🔔 확인하지 않은 알림이 **{unread_count}개** 있습니다.")
    else:
        st.success("✅ 모든 알림을 확인했습니다.")

# -----------------------------------------------------------------------------
# 4. 상단 공통 헤더
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="teacher-header">
        <h1>👩‍🏫 선생님 도우미</h1>
        <p>오늘도 좋은 하루 되세요! 선생님의 효율적인 학교 업무를 응원합니다 ✨</p>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# 5. 페이지 기능 구현
# -----------------------------------------------------------------------------

# PAGE 1: 오늘의 일정
if menu == "오늘의 일정":
    st.subheader("📅 오늘의 학교 일정")
    st.write(f"오늘 날짜: **{date.today().strftime('%Y년 %m월 %d일')}**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("오늘 전체 일정", f"{len(st.session_state.schedules)}건")
    with col2:
        completed = sum(1 for s in st.session_state.schedules if s['status'] == '완료')
        st.metric("완료된 일정", f"{completed}건")
    with col3:
        st.metric("남은 일정", f"{len(st.session_state.schedules) - completed}건")
        
    st.write("")
    
    with st.expander("➕ 새 학사/수업 일정 등록"):
        with st.form("add_schedule_form", clear_on_submit=True):
            sch_time = st.time_input("시간", value=time(9, 0))
            sch_title = st.text_input("일정 내용", placeholder="예: 3교시 국어 수업, 방과후 교재 작성 등")
            sch_location = st.text_input("장소", placeholder="예: 3학년 2반 교실, 컴퓨터실")
            
            submitted = st.form_submit_button("일정 추가")
            if submitted:
                if sch_title.strip():
                    new_id = max([s['id'] for s in st.session_state.schedules], default=0) + 1
                    st.session_state.schedules.append({
                        "id": new_id,
                        "time": sch_time.strftime("%H:%M"),
                        "title": sch_title,
                        "location": sch_location if sch_location else "교실",
                        "status": "진행예정"
                    })
                    st.success("새 일정이 등록되었습니다!")
                    st.rerun()
                else:
                    st.warning("일정 내용을 입력해주세요.")

    st.subheader("📋 시간대별 일정")
    if not st.session_state.schedules:
        st.info("등록된 일정이 없습니다. 편안한 하루 보내세요!")
    else:
        sorted_schedules = sorted(st.session_state.schedules, key=lambda x: x['time'])
        for sch in sorted_schedules:
            c_time, c_info, c_status, c_del = st.columns([1.5, 4, 2, 1])
            with c_time:
                st.markdown(f"⏰ **{sch['time']}**")
            with c_info:
                st.markdown(f"**{sch['title']}**")
                st.caption(f"📍 {sch['location']}")
            with c_status:
                opts = ["진행예정", "진행중", "완료"]
                status_idx = opts.index(sch['status']) if sch['status'] in opts else 0
                new_st = st.selectbox(
                    "상태 변경",
                    opts,
                    index=status_idx,
                    key=f"sch_st_{sch['id']}",
                    label_visibility="collapsed"
                )
                if new_st != sch['status']:
                    sch['status'] = new_st
                    st.rerun()
            with c_del:
                if st.button("삭제", key=f"del_sch_{sch['id']}"):
                    st.session_state.schedules = [s for s in st.session_state.schedules if s['id'] != sch['id']]
                    st.rerun()
            st.divider()

# PAGE 2: 할 일 목록
elif menu == "할 일 목록":
    st.subheader("✅ 교무 업무 할 일 목록")
    
    with st.expander("➕ 새 할 일 추가하기", expanded=True):
        col_t1, col_t2, col_t3 = st.columns([3, 1.5, 1.5])
        with col_t1:
            t_text = st.text_input("할 업무를 입력하세요", key="new_todo_text", placeholder="예: 생기부 작성, 가정통신문 확인")
        with col_t2:
            t_cat = st.selectbox("업무 분류", ["학급운영", "성적/평가", "상담", "행정업무", "개인"], key="new_todo_cat")
        with col_t3:
            t_pri = st.selectbox("우선순위", ["높음", "보통", "낮음"], key="new_todo_pri")
            
        if st.button("할 일 추가", use_container_width=True):
            if t_text.strip():
                new_id = max([t['id'] for t in st.session_state.todos], default=0) + 1
                st.session_state.todos.append({
                    "id": new_id,
                    "task": t_text,
                    "category": t_cat,
                    "priority": t_pri,
                    "done": False
                })
                st.success("업무 할 일이 등록되었습니다!")
                st.rerun()
            else:
                st.warning("할 일 내용을 입력해주세요.")
                
    st.divider()
    
    if st.session_state.todos:
        tot = len(st.session_state.todos)
        done_cnt = sum(1 for t in st.session_state.todos if t['done'])
        prog = done_cnt / tot if tot > 0 else 0
        st.write(f"**오늘의 업무 진행률: {int(prog * 100)}%** ({done_cnt}/{tot} 완료)")
        st.progress(prog)

    st.subheader("📝 업무 체크리스트")
    for todo in st.session_state.todos:
        c1, c2, c3, c4, c5 = st.columns([0.5, 4, 1.5, 1.5, 1])
        with c1:
            chk = st.checkbox("", value=todo['done'], key=f"todo_chk_{todo['id']}")
            if chk != todo['done']:
                todo['done'] = chk
                st.rerun()
        with c2:
            if todo['done']:
                st.markdown(f"~~{todo['task']}~~")
            else:
                st.markdown(f"**{todo['task']}**")
        with c3:
            st.caption(f"📁 {todo['category']}")
        with c4:
            p_color = "🔴" if todo['priority'] == "높음" else ("🟡" if todo['priority'] == "보통" else "🟢")
            st.caption(f"{p_color} {todo['priority']}")
        with c5:
            if st.button("삭제", key=f"del_todo_{todo['id']}"):
                st.session_state.todos = [t for t in st.session_state.todos if t['id'] != todo['id']]
                st.rerun()

# PAGE 3: 통합 검색
elif menu == "통합 검색":
    st.subheader("🔍 업무 통합 검색")
    st.caption("등록된 모든 학사 일정, 할 일, 업무 알림 내용을 빠르게 검색합니다.")
    
    query = st.text_input("검색어를 입력하세요", placeholder="예: 가정통신문, 채점, 상담, 연수...").strip()
    
    if query:
        res_sch = [s for s in st.session_state.schedules if query.lower() in s['title'].lower() or query.lower() in s['location'].lower()]
        res_todo = [t for t in st.session_state.todos if query.lower() in t['task'].lower() or query.lower() in t['category'].lower()]
        res_noti = [n for n in st.session_state.notifications if query.lower() in n['message'].lower()]
        
        total_res = len(res_sch) + len(res_todo) + len(res_noti)
        
        if total_res == 0:
            st.warning("검색 결과가 없습니다.")
        else:
            st.success(f"총 {total_res}건의 검색 결과를 찾았습니다.")
            t1, t2, t3 = st.tabs([f"📅 일정 ({len(res_sch)})", f"✅ 할 일 ({len(res_todo)})", f"🔔 알림 ({len(res_noti)})"])
            
            with t1:
                if res_sch:
                    for s in res_sch:
                        st.write(f"- **[{s['time']}]** {s['title']} *(장소: {s['location']} | 상태: {s['status']})*")
                else:
                    st.write("일치하는 일정이 없습니다.")
            with t2:
                if res_todo:
                    for t in res_todo:
                        st_str = "완료" if t['done'] else "미완료"
                        st.write(f"- **[{t['category']}]** {t['task']} *(우선순위: {t['priority']} | 상태: {st_str})*")
                else:
                    st.write("일치하는 할 일이 없습니다.")
            with t3:
                if res_noti:
                    for n in res_noti:
                        st.write(f"- **[{n['type']}]** {n['message']} *(시간: {n['timestamp']})*")
                else:
                    st.write("일치하는 알림이 없습니다.")
    else:
        st.info("검색어를 입력하시면 교무 항목을 즉시 찾아드립니다.")

# PAGE 4: 업무 알림
elif menu == "업무 알림":
    st.subheader("🔔 학사 및 교무 알림")
    
    c_left, c_right = st.columns([4, 1])
    with c_right:
        if st.button("모두 읽음 처리"):
            for n in st.session_state.notifications:
                n['read'] = True
            st.rerun()
            
    st.divider()
    
    if not st.session_state.notifications:
        st.info("알림 내역이 없습니다.")
    else:
        for noti in st.session_state.notifications:
            bg = "#F7FAFA" if noti['read'] else "#E6F8F6"
            bd = "#D0EBE7" if noti['read'] else "#36C5B5"
            
            st.markdown(
                f"""
                <div style="background-color: {bg}; padding: 14px; border-radius: 12px; border-left: 5px solid {bd}; margin-bottom: 12px;">
                    <span style="font-size: 12px; color: #666;">[{noti['timestamp']}] <b>{noti['type']}</b></span><br/>
                    <span style="font-size: 15px; font-weight: {'normal' if noti['read'] else 'bold'}; color: #2C3E50;">{noti['message']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
            if not noti['read']:
                if st.button("읽음", key=f"read_n_{noti['id']}"):
                    noti['read'] = True
                    st.rerun()

# PAGE 5: 설정
elif menu == "설정":
    st.subheader("⚙️ 선생님 도우미 설정")
    
    t_prof, t_noti, t_info = st.tabs(["👤 교사 프로필", "🔔 알림 수신 설정", "ℹ️ 앱 정보"])
    
    with t_prof:
        with st.form("prof_form"):
            name = st.text_input("선생님 성함", value=st.session_state.user_profile['name'])
            dept = st.text_input("담당 학급 / 담당 과목", value=st.session_state.user_profile['dept'])
            email = st.text_input("업무용 이메일", value=st.session_state.user_profile['email'])
            
            if st.form_submit_button("프로필 저장"):
                st.session_state.user_profile['name'] = name
                st.session_state.user_profile['dept'] = dept
                st.session_state.user_profile['email'] = email
                st.success("프로필 수정이 완료되었습니다.")
                st.rerun()
                
    with t_noti:
        n_email = st.checkbox("이메일 알림 받기", value=st.session_state.user_profile['noti_email'])
        n_sound = st.checkbox("알림 소리 켜기", value=st.session_state.user_profile['noti_sound'])
        if st.button("알림 설정 저장"):
            st.session_state.user_profile['noti_email'] = n_email
            st.session_state.user_profile['noti_sound'] = n_sound
            st.success("알림 설정이 반영되었습니다.")
            
    with t_info:
        st.markdown("""
        - **앱 명칭**: 선생님 도우미 (Teacher Assistant Dashboard)
        - **디자인 테마**: 힐링 & 클린 민트/에메랄드 톤 UI
        - **기능 구성**: 오늘의 일정, 교무 할 일 목록, 통합 검색, 업무 알림, 사용자 설정
        - **배포 지원**: Streamlit Community Cloud 지원
        """)
