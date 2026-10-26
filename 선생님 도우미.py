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
    div[data-testid="stMetric"], .css-1r6slb0, .stExpander {
        background-color: #FFFFFF !important;
        border-radius: 16px !important;
        border: 1px solid #E1F0EE !important;
        box-shadow: 0 4px 12px rgba(54, 197, 181, 0.08) !important;
        padding: 16px !important;
    }
    
    /* 포인트 민트 컬러 커스텀 헤더 뱅크 */
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
# 2. 세션 상태(Session State) 초기화 (데이터 유지)
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
# 4. 상단 공통 헤더 (민트 감성 디자인 반영)
# -----------------------------------------------------------------------------
st.markdown(
    f"""
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
                new_st = st.selectbox(
                    "상태 변경",
                    opts,
                    index=opts.index(sch['status']),
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
            t_text = st.text_input("할 업무를 입력하세요", key="new_todo_text", placeholder="예: 생기부 작성, 가정통신문 확인
