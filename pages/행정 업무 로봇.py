
import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(
    page_title="행정업무 로봇",
    page_icon="🤖",
    layout="wide"
)

# ==============================
# 1. 데이터 초기화
# ==============================
defaults = {
    "documents": [],
    "tasks": [],
    "expenses": [],
    "complaints": [],
    "total_budget": 1_000_000_000,
    "current_draft": "",
    "current_title": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ==============================
# 2. 공통 함수
# ==============================
def show_table(data):
    if data:
        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("등록된 데이터가 없습니다.")


def download_csv(data, filename):
    if data:
        csv = pd.DataFrame(data).to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "📥 CSV 다운로드",
            data=csv,
            file_name=filename,
            mime="text/csv"
        )


def reset_section(data_key, reset_id, label, extra_reset=None):
    confirm_key = f"{reset_id}_confirming"

    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False

    st.divider()
    st.subheader("🔄 초기화")

    if st.button(
        f"{label} 초기화",
        key=f"{reset_id}_button"
    ):
        st.session_state[confirm_key] = True
        st.rerun()

    if st.session_state[confirm_key]:
        st.warning(
            f"{label} 데이터를 초기화할까요? "
            "삭제한 데이터는 복구할 수 없습니다."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "네, 초기화합니다",
                key=f"{reset_id}_yes",
                type="primary"
            ):
                st.session_state[data_key] = []

                if extra_reset:
                    for key, value in extra_reset.items():
                        st.session_state[key] = value

                st.session_state[confirm_key] = False
                st.rerun()

        with col2:
            if st.button(
                "취소",
                key=f"{reset_id}_no"
            ):
                st.session_state[confirm_key] = False
                st.rerun()


def classify_complaint(text):
    categories = {
        "시설·안전": [
            "시설", "고장", "파손", "안전",
            "위험", "수리", "누수"
        ],
        "예산·회계": [
            "예산", "지출", "회계", "환불",
            "결제", "비용", "납부"
        ],
        "서류·증명": [
            "서류", "증명서", "발급",
            "신청서", "공문", "문서"
        ],
        "교육·프로그램": [
            "교육", "수업", "프로그램",
            "행사", "강의", "일정"
        ],
        "불편·서비스": [
            "불편", "문의", "불친절",
            "안내", "개선", "대기"
        ]
    }

    scores = {
        category: sum(
            keyword in text
            for keyword in keywords
        )
        for category, keywords in categories.items()
    }

    best = max(scores, key=scores.get)

    if scores[best] == 0:
        return "일반 문의"

    return best


# ==============================
# 3. 사이드바 메뉴
# ==============================
st.sidebar.title("🤖 행정업무 로봇")
st.sidebar.caption("스마트 행정 업무 관리 시스템")

page = st.sidebar.radio(
    "기능 선택",
    [
        "대시보드",
        "공문 자동 작성",
        "업무 진행률",
        "예산 사용 현황",
        "민원 종류 분류"
    ]
)


# ==============================
# 4. 대시보드
# ==============================
if page == "대시보드":
    st.title("🤖 행정업무 로봇")
    st.write(
        "공문 작성, 업무 관리, 예산 확인, "
        "민원 분류를 한곳에서 처리합니다."
    )

    tasks = st.session_state.tasks
    expenses = st.session_state.expenses
    complaints = st.session_state.complaints

    completed = sum(
        task["상태"] == "완료"
        for task in tasks
    )

    progress = completed / len(tasks) if tasks else 0

    spent = sum(
        item["금액"]
        for item in expenses
    )

    open_complaints = sum(
        item["처리 상태"] != "처리 완료"
        for item in complaints
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("등록 업무", f"{len(tasks)}건")
    c2.metric("업무 완료율", f"{progress:.0%}")
    c3.metric("누적 지출", f"{spent:,}원")
    c4.metric("미완료 민원", f"{open_complaints}건")

    st.subheader("기능 안내")
    st.markdown("""
    - 📝 공문 자동 작성: 키워드로 공문 초안 생성
    - 📌 업무 진행률: 담당 업무와 마감일, 상태 관리
    - 💰 예산 사용 현황: 총예산 입력 및 잔액 확인
    - 📨 민원 종류 분류: 민원 분류 및 처리 상태 관리
    """)


# ==============================
# 5. 공문 자동 작성
# ==============================
elif page == "공문 자동 작성":
    st.title("📝 공문 자동 작성")

    with st.form("document_form"):
        title = st.text_input("공문 제목")
        receiver = st.text_input("수신 기관")
        sender = st.text_input("발신 기관")
        keywords = st.text_area("핵심 키워드")
        purpose = st.text_area("작성 목적 및 추가 안내")

        submitted = st.form_submit_button(
            "공문 초안 생성",
            type="primary"
        )

    if submitted:
        if not title.strip() or not keywords.strip():
            st.error("제목과 핵심 키워드를 입력해 주세요.")
        else:
            draft = f"""수신: {receiver or '관련 부서'}
발신: {sender or '행정지원팀'}

제목: {title}

1. 관련: 해당 업무 추진 계획

2. 위와 관련하여 다음과 같이 안내하오니
협조하여 주시기 바랍니다.

  가. 주요 내용: {keywords}
  나. 작성 목적: {purpose or '세부 사항 별도 안내'}

3. 각 담당자는 내용을 확인하고 필요한 사항을
기한 내에 이행하여 주시기 바랍니다.

붙임: 필요 시 관련 자료 1부. 끝.
"""
            st.session_state.current_draft = draft
            st.session_state.current_title = title
            st.session_state["document_editor"] = draft
            st.success("공문 초안을 생성했습니다.")

    if st.session_state.current_draft:
        edited = st.text_area(
            "공문 내용 확인 및 수정",
            height=300,
            key="document_editor"
        )

        st.download_button(
            "📥 공문 TXT 다운로드",
            data=edited,
            file_name="공문_초안.txt",
            mime="text/plain"
        )

        if st.button("작성 내역에 저장"):
            st.session_state.documents.append({
                "제목": st.session_state.current_title,
                "작성일": date.today().isoformat(),
                "내용": edited
            })
            st.success("공문 작성 내역에 저장했습니다.")

    st.subheader("저장된 공문 내역")
    show_table(st.session_state.documents)
    download_csv(
        st.session_state.documents,
        "공문작성내역.csv"
    )

    reset_section(
        "documents",
        "reset_documents",
        "공문 작성 내역"
    )


# ==============================
# 6. 업무 진행률
# ==============================
elif page == "업무 진행률":
    st.title("📌 업무 진행률 관리")

    with st.form("task_form"):
        task_name = st.text_input("업무명")
        manager = st.text_input("담당자")
        deadline = st.date_input(
            "마감일",
            value=date.today() + timedelta(days=7)
        )
        status = st.selectbox(
            "진행 상태",
            ["시작 전", "진행 중", "완료", "보류"]
        )

        submitted = st.form_submit_button("업무 등록")

    if submitted:
        if not task_name.strip():
            st.error("업무명을 입력해 주세요.")
        else:
            st.session_state.tasks.append({
                "업무명": task_name.strip(),
                "담당자": manager.strip() or "미지정",
                "마감일": deadline.isoformat(),
                "상태": status
            })
            st.success("업무를 등록했습니다.")
            st.rerun()

    tasks = st.session_state.tasks

    if tasks:
        completed = sum(
            task["상태"] == "완료"
            for task in tasks
        )
        progress = completed / len(tasks)

        st.metric("전체 업무 완료율", f"{progress:.0%}")
        st.progress(progress)

        selected = st.selectbox(
            "수정할 업무",
            range(len(tasks)),
            format_func=lambda i: (
                f'{tasks[i]["업무명"]} ({tasks[i]["상태"]})'
            ),
            key="task_selected"
        )

        statuses = ["시작 전", "진행 중", "완료", "보류"]

        new_status = st.selectbox(
            "변경할 상태",
            statuses,
            index=statuses.index(tasks[selected]["상태"]),
            key="task_new_status"
        )

        if st.button("업무 상태 업데이트"):
            tasks[selected]["상태"] = new_status
            st.success("업무 상태를 변경했습니다.")
            st.rerun()

    show_table(st.session_state.tasks)
    download_csv(st.session_state.tasks, "업무목록.csv")

    reset_section(
        "tasks",
        "reset_tasks",
        "업무 목록"
    )


# ==============================
# 7. 예산 사용 현황
# ==============================
elif page == "예산 사용 현황":
    st.title("💰 예산 관리")

    # 원하는 총예산 입력
    budget = st.number_input(
        "총예산 입력 (원)",
        min_value=0,
        max_value=100_000_000_000,
        value=int(st.session_state.total_budget),
        step=1_000_000,
        key="budget_input"
    )

    st.session_state.total_budget = int(budget)

    st.subheader("지출 등록")

    with st.form("expense_form"):
        name = st.text_input("지출 항목")

        amount = st.number_input(
            "지출 금액 (원)",
            min_value=0,
            value=0,
            step=100_000
        )

        submitted = st.form_submit_button("지출 등록")

    if submitted:
        if not name.strip():
            st.error("지출 항목을 입력해 주세요.")
        elif amount <= 0:
            st.error("지출 금액은 0원보다 커야 합니다.")
        else:
            st.session_state.expenses.append({
                "지출 항목": name.strip(),
                "금액": int(amount)
            })
            st.success("지출을 등록했습니다.")
            st.rerun()

    # 남은 금액 계산
    total_spent = sum(
        item["금액"]
        for item in st.session_state.expenses
    )

    remaining = int(budget) - total_spent

    st.divider()
    st.subheader("💵 남은 예산")

    if remaining >= 0:
        st.metric(
            "사용 가능한 금액",
            f"{remaining:,}원"
        )
    else:
        st.metric(
            "예산 초과 금액",
            f"{abs(remaining):,}원"
        )
        st.warning("입력한 예산보다 지출이 많습니다.")

    st.subheader("지출 내역")
    show_table(st.session_state.expenses)
    download_csv(
        st.session_state.expenses,
        "지출내역.csv"
    )

    reset_section(
        "expenses",
        "reset_expenses",
        "예산 및 지출 내역",
        extra_reset={
            "total_budget": 1_000_000_000,
            "budget_input": 1_000_000_000
        }
    )


# ==============================
# 8. 민원 종류 분류
# ==============================
elif page == "민원 종류 분류":
    st.title("📨 민원 종류 분류")
    st.write("민원 내용을 입력하면 키워드에 따라 분야를 분류합니다.")

    with st.form("complaint_form"):
        content = st.text_area("민원 내용")
        submitted = st.form_submit_button("민원 분류 및 등록")

    if submitted:
        if len(content.strip()) < 3:
            st.error("민원 내용을 3글자 이상 입력해 주세요.")
        else:
            category = classify_complaint(content)

            st.session_state.complaints.append({
                "민원 내용": content.strip(),
                "분류": category,
                "접수일": date.today().isoformat(),
                "처리 상태": "접수"
            })

            st.success(f"민원 분류 결과: {category}")
            st.rerun()

    complaints = st.session_state.complaints

    if complaints:
        selected = st.selectbox(
            "수정할 민원",
            range(len(complaints)),
            format_func=lambda i: (
                f'{complaints[i]["분류"]} - '
                f'{complaints[i]["민원 내용"][:25]}'
            ),
            key="complaint_selected"
        )

        categories = [
            "시설·안전",
            "예산·회계",
            "서류·증명",
            "교육·프로그램",
            "불편·서비스",
            "일반 문의"
        ]

        states = ["접수", "처리 중", "처리 완료"]

        new_category = st.selectbox(
            "분류 수정",
            categories,
            index=categories.index(
                complaints[selected]["분류"]
            ),
            key="complaint_new_category"
        )

        new_state = st.selectbox(
            "처리 상태 수정",
            states,
            index=states.index(
                complaints[selected]["처리 상태"]
            ),
            key="complaint_new_state"
        )

        if st.button("민원 정보 업데이트"):
            complaints[selected]["분류"] = new_category
            complaints[selected]["처리 상태"] = new_state
            st.success("민원 정보를 업데이트했습니다.")
            st.rerun()

    show_table(st.session_state.complaints)
    download_csv(st.session_state.complaints, "민원목록.csv")

    reset_section(
        "complaints",
        "reset_complaints",
        "민원 목록"
    )


# ==============================
# 9. 하단 안내
# ==============================
st.divider()
st.caption(
    "행정업무 로봇 | 교육·시연용 프로그램입니다. "
    "데이터는 현재 세션에 저장되며, "
    "실제 행정 시스템과 연결되어 있지 않습니다."
)
