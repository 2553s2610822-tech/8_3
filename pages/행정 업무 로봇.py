
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


def format_eok(amount):
    amount = int(amount)
    eok = amount // 100_000_000
    remainder = amount % 100_000_000

    if remainder == 0:
        return f"약 {eok}억원"

    parts = [f"약 {eok}억원"]

    for unit_value, unit_name in [
        (10_000_000, "천만원"),
        (1_000_000, "백만원"),
        (10_000, "만원"),
        (1, "원")
    ]:
        value = remainder // unit_value
        remainder %= unit_value

        if value:
            parts.append(f"{value}{unit_name}")

    return " ".join(parts)


def reset_section(data_key, reset_id, label, extra_reset=None):
    """
    지정된 기능의 데이터만 초기화한다.
    extra_reset에는 함께 초기화할 세션 값을 전달할 수 있다.
    """
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

st.sidebar.divider()
st.sidebar.caption("간편하고 효율적인 행정 업무")


# ==============================
# 4. 대시보드
# ==============================
if page == "대시보드":
    st.title("🤖 행정업무 로봇")
    st.write(
        "행정 업무에 필요한 문서 작성, 업무 관리, "
        "예산 확인, 민원 분류를 지원합니다."
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
    c3.metric("누적 지출", format_eok(spent))
    c4.metric("미완료 민원", f"{open_complaints}건")

    st.subheader("사용 가능한 기능")

    st.markdown("""
    - 📝 **공문 자동 작성:** 키워드를 활용해 공문 초안을 생성합니다.
    - 📌 **업무 진행률:** 담당 업무와 마감일, 처리 상태를 관리합니다.
    - 💰 **예산 사용 현황:** 예산과 지출, 잔액을 확인합니다.
    - 📨 **민원 종류 분류:** 민원을 분야별로 분류하고 처리 상태를 관리합니다.
    """)


# ==============================
# 5. 공문 자동 작성
# ==============================
elif page == "공문 자동 작성":
    st.title("📝 공문 자동 작성")
    st.write("핵심 키워드를 입력해 공문 초안을 작성하세요.")

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
            st.error("공문 제목과 핵심 키워드를 입력해 주세요.")
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

        submitted = st.form_submit_button(
            "업무 등록",
            type="primary"
        )

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

        st.subheader("업무 상태 수정")

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
    st.title("💰 예산 사용 현황")

    st.subheader("총예산 설정")

    budget = st.number_input(
        "총예산액 (원)",
        min_value=0,
        max_value=100_000_000_000,
        value=int(st.session_state.total_budget),
        step=10_000_000,
        key="budget_input"
    )

    st.session_state.total_budget = int(budget)

    st.info(f"현재 총예산: **{format_eok(budget)}**")

    st.subheader("지출 내역 등록")

    with st.form("expense_form"):
        name = st.text_input("지출 항목")

        category = st.selectbox(
            "지출 분류",
            [
                "인건비",
                "시설 관리",
                "사무용품",
                "교육·행사",
                "인쇄·홍보",
                "기타"
            ]
        )

        amount = st.number_input(
            "지출 금액 (원)",
            min_value=0,
            value=0,
            step=1_000_000
        )

        expense_date = st.date_input(
            "지출일",
            value=date.today()
        )

        submitted = st.form_submit_button(
            "지출 내역 추가",
            type="primary"
        )

    if submitted:
        if not name.strip():
            st.error("지출 항목을 입력해 주세요.")
        elif amount <= 0:
            st.error("지출 금액은 0원보다 커야 합니다.")
        else:
            st.session_state.expenses.append({
                "지출 항목": name.strip(),
                "분류": category,
                "금액": int(amount),
                "지출일": expense_date.isoformat()
            })
            st.success("지출 내역을 추가했습니다.")
            st.rerun()

    expenses = st.session_state.expenses
    spent = sum(item["금액"] for item in expenses)
    balance = int(budget) - spent
    usage = spent / budget if budget else 0

    st.subheader("예산 사용 요약")

    c1, c2, c3 = st.columns(3)

    c1.metric("총예산", format_eok(budget))
    c2.metric("누적 지출", format_eok(spent))
    c3.metric("잔액", format_eok(balance) if balance >= 0
              else f"초과 {format_eok(abs(balance))[2:]}")

    st.progress(min(usage, 1.0))
    st.write(f"예산 사용률: **{usage:.1%}**")

    if usage > 1:
        st.warning("예산을 초과했습니다.")

    st.subheader("지출 내역")
    show_table(expenses)
    download_csv(expenses, "예산지출내역.csv")

    if expenses:
        st.subheader("분류별 지출")
        chart = (
            pd.DataFrame(expenses)
            .groupby("분류")["금액"]
            .sum()
        )
        st.bar_chart(chart)

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
    st.write(
        "민원 내용을 입력하면 키워드에 따라 "
        "담당 분야를 제안합니다."
    )

    with st.form("complaint_form"):
        content = st.text_area("민원 내용")
        submitted = st.form_submit_button(
            "민원 분류 및 등록",
            type="primary"
        )

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
        st.subheader("민원 정보 수정")

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
