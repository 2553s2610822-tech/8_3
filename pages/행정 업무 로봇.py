
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="행정업무 로봇",
    page_icon="🤖",
    layout="wide"
)

# -----------------------------
# 기본 데이터
# -----------------------------
DEFAULT_BUDGET = 1_000_000_000

defaults = {
    "documents": [],
    "tasks": [],
    "expenses": [],
    "complaints": [],
    "total_budget": DEFAULT_BUDGET,
    "budget_input": DEFAULT_BUDGET,
    "current_draft": "",
    "current_title": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -----------------------------
# 초기화 함수
# -----------------------------
def reset_documents():
    st.session_state.documents = []
    st.session_state.current_draft = ""
    st.session_state.current_title = ""
    st.session_state.document_editor = ""
    st.session_state.doc_title = ""
    st.session_state.doc_receiver = ""
    st.session_state.doc_sender = ""
    st.session_state.doc_keywords = []
    st.session_state.doc_custom_keywords = ""
    st.session_state.doc_purpose = ""


def reset_tasks():
    st.session_state.tasks = []


def reset_budget():
    st.session_state.expenses = []
    st.session_state.total_budget = DEFAULT_BUDGET
    st.session_state.budget_input = DEFAULT_BUDGET
    st.session_state.expense_name = ""
    st.session_state.expense_amount = 0
    st.session_state.expense_category = "교육활동"


def reset_complaints():
    st.session_state.complaints = []
    st.session_state.complaint_content = ""
    st.session_state.complaint_name = ""


def reset_all():
    reset_documents()
    reset_tasks()
    reset_budget()
    reset_complaints()


# -----------------------------
# 공통 함수
# -----------------------------
def show_table(data):
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("등록된 데이터가 없습니다.")


def download_csv(data, filename, key):
    if data:
        csv = pd.DataFrame(data).to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "📥 CSV 다운로드",
            data=csv,
            file_name=filename,
            mime="text/csv",
            key=key
        )
    else:
        st.info("다운로드할 데이터가 없습니다.")


def classify_complaint(content):
    text = content.lower()

    categories = {
        "시설·안전": [
            "시설", "고장", "안전", "수리", "화장실",
            "냉난방", "교실", "위험"
        ],
        "예산·회계": [
            "예산", "회계", "지출", "비용", "구매", "환불"
        ],
        "서류·증명": [
            "서류", "증명서", "발급", "신청서", "문서"
        ],
        "교육·프로그램": [
            "수업", "교육", "프로그램", "체험학습", "행사"
        ],
        "불편·서비스": [
            "불편", "문의", "불만", "서비스", "개선"
        ],
    }

    for category, keywords in categories.items():
        if any(word in text for word in keywords):
            return category

    return "일반 문의"


# -----------------------------
# 왼쪽 사이드바
# -----------------------------
st.sidebar.title("🤖 행정업무 로봇")
st.sidebar.write("관리할 기능을 선택하세요.")

page = st.sidebar.radio(
    "기능 목록",
    [
        "📊 대시보드",
        "📝 공문 자동 작성",
        "📈 업무 진행률",
        "💰 예산 사용 현황",
        "📨 민원 종류 분류",
    ],
    label_visibility="collapsed"
)

st.title("🤖 학교 행정업무 로봇")


# -----------------------------
# 1. 대시보드
# -----------------------------
if page == "📊 대시보드":
    st.header("📊 행정업무 대시보드")
    st.write("학교 행정업무 현황을 한눈에 확인합니다.")

    total_tasks = len(st.session_state.tasks)
    completed_tasks = sum(
        1 for task in st.session_state.tasks
        if task["상태"] == "완료"
    )

    progress = (
        completed_tasks / total_tasks
        if total_tasks > 0 else 0
    )

    total_expenses = sum(
        item["금액"] for item in st.session_state.expenses
    )

    remaining_budget = (
        st.session_state.total_budget - total_expenses
    )

    incomplete_complaints = sum(
        1 for item in st.session_state.complaints
        if item["처리 상태"] != "처리 완료"
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("전체 업무", f"{total_tasks}건")
    col2.metric("완료 업무", f"{completed_tasks}건")
    col3.metric("남은 예산", f"{remaining_budget:,}원")
    col4.metric("미완료 민원", f"{incomplete_complaints}건")

    st.subheader("업무 진행률")
    st.progress(progress)
    st.write(f"전체 업무의 {progress * 100:.1f}%가 완료되었습니다.")

    st.subheader("등록된 데이터")
    st.write(f"저장된 공문: {len(st.session_state.documents)}건")
    st.write(f"등록된 지출: {len(st.session_state.expenses)}건")
    st.write(f"접수된 민원: {len(st.session_state.complaints)}건")

    st.divider()
    st.subheader("전체 데이터 초기화")
    st.warning("초기화하면 공문, 업무, 예산 지출, 민원 데이터가 모두 삭제됩니다.")

    st.button(
        "🗑️ 전체 데이터 초기화",
        on_click=reset_all,
        key="reset_everything",
        type="primary"
    )


# -----------------------------
# 2. 공문 자동 작성
# -----------------------------
elif page == "📝 공문 자동 작성":
    st.header("📝 공문 자동 작성")
    st.write("키워드를 선택하거나 입력해 공문 초안을 만듭니다.")

    with st.form("document_form"):
        title = st.text_input(
            "공문 제목",
            key="doc_title"
        )

        receiver = st.text_input(
            "수신 기관",
            placeholder="예: 전 교직원",
            key="doc_receiver"
        )

        sender = st.text_input(
            "발신 기관",
            placeholder="예: ○○고등학교장",
            key="doc_sender"
        )

        keywords = st.multiselect(
            "관련 키워드",
            [
                "체험학습", "예산", "시설관리", "안전교육",
                "행사안내", "회의개최", "교육활동", "물품구매",
                "출장신청", "급식관리", "학생지원", "학부모안내",
                "환경정비", "업무협조", "자료제출", "학교행사",
                "연수계획", "방학안내", "교직원안내", "교육자료",
                "진로교육", "안전점검", "학사일정", "급식안내",
                "가정통신문", "결과보고", "계획서제출", "수업운영"
            ],
            key="doc_keywords"
        )

        custom_keywords = st.text_input(
            "직접 입력할 키워드",
            placeholder="예: 신청 기간, 제출 방법",
            key="doc_custom_keywords"
        )

        purpose = st.text_area(
            "공문 작성 목적 및 전달 내용",
            placeholder="공문에 포함할 내용을 입력하세요.",
            key="doc_purpose"
        )

        submitted = st.form_submit_button("공문 초안 생성")

    if submitted:
        all_keywords = list(keywords)

        if custom_keywords.strip():
            all_keywords += [
                word.strip()
                for word in custom_keywords.split(",")
                if word.strip()
            ]

        keyword_text = ", ".join(all_keywords) if all_keywords else "관련 업무"

        draft = f"""수신: {receiver or '관련 기관'}
발신: {sender or '학교장'}
제목: {title or '행정업무 관련 안내'}

1. 목적
{purpose or '관련 업무의 원활한 추진을 위해 다음과 같이 안내합니다.'}

2. 주요 내용
- 관련 키워드: {keyword_text}
- 세부 내용: {purpose or '세부 사항은 담당자 확인 후 작성합니다.'}

3. 협조 사항
- 관련 내용을 확인하고 필요한 업무를 진행해 주시기 바랍니다.
- 추가 문의 사항은 담당 부서에 문의해 주시기 바랍니다.

※ 본 문서는 자동 생성된 초안이므로 발송 전에 내용과 날짜 등을 확인하세요.
"""

        st.session_state.current_draft = draft
        st.session_state.current_title = title or "행정업무 관련 안내"

    st.subheader("공문 초안")

    edited_draft = st.text_area(
        "초안을 확인하고 수정하세요.",
        key="document_editor",
        height=350
    )

    if st.button("💾 공문 저장", key="save_document"):
        if edited_draft.strip():
            st.session_state.documents.append({
                "제목": st.session_state.current_title or "공문",
                "작성일": str(date.today()),
                "내용": edited_draft
            })
            st.success("공문이 저장되었습니다.")
        else:
            st.warning("먼저 공문 초안을 생성하거나 내용을 입력하세요.")

    st.download_button(
        "📥 공문 TXT 다운로드",
        data=edited_draft,
        file_name="공문_초안.txt",
        mime="text/plain",
        key="download_document"
    )

    st.divider()
    st.subheader("저장된 공문")
    show_table(st.session_state.documents)
    download_csv(
        st.session_state.documents,
        "저장된_공문.csv",
        "documents_csv"
    )

    st.button(
        "🗑️ 공문 데이터 초기화",
        on_click=reset_documents,
        key="reset_documents"
    )


# -----------------------------
# 3. 업무 진행률
# -----------------------------
elif page == "📈 업무 진행률":
    st.header("📈 업무 진행률 관리")

    with st.form("task_form"):
        task_name = st.text_input("업무 이름", key="task_name")
        manager = st.text_input("담당자", key="task_manager")
        deadline = st.date_input("마감일", key="task_deadline")
        status = st.selectbox(
            "진행 상태",
            ["예정", "진행 중", "완료"],
            key="task_status"
        )

        add_task = st.form_submit_button("업무 등록")

    if add_task:
        if task_name.strip():
            st.session_state.tasks.append({
                "업무": task_name,
                "담당자": manager,
                "마감일": str(deadline),
                "상태": status
            })
            st.success("업무가 등록되었습니다.")
        else:
            st.warning("업무 이름을 입력하세요.")

    st.divider()
    st.subheader("업무 목록")

    if st.session_state.tasks:
        for i, task in enumerate(st.session_state.tasks):
            with st.container(border=True):
                st.write(f"**{task['업무']}**")
                st.write(f"담당자: {task['담당자'] or '미지정'}")
                st.write(f"마감일: {task['마감일']}")

                new_status = st.selectbox(
                    "진행 상태",
                    ["예정", "진행 중", "완료"],
                    index=["예정", "진행 중", "완료"].index(task["상태"]),
                    key=f"task_status_{i}"
                )

                st.session_state.tasks[i]["상태"] = new_status

                if st.button("업무 삭제", key=f"delete_task_{i}"):
                    st.session_state.tasks.pop(i)
                    st.rerun()
    else:
        st.info("등록된 업무가 없습니다.")

    total = len(st.session_state.tasks)
    done = sum(
        1 for task in st.session_state.tasks
        if task["상태"] == "완료"
    )
    ratio = done / total if total else 0

    st.subheader("전체 업무 진행률")
    st.progress(ratio)
    st.write(f"{done} / {total}건 완료 ({ratio * 100:.1f}%)")

    download_csv(
        st.session_state.tasks,
        "업무_목록.csv",
        "tasks_csv"
    )

    st.button(
        "🗑️ 업무 데이터 초기화",
        on_click=reset_tasks,
        key="reset_tasks"
    )


# -----------------------------
# 4. 예산 사용 현황
# -----------------------------
elif page == "💰 예산 사용 현황":
    st.header("💰 예산 사용 현황")

    # 초기화 버튼의 콜백이 예산 입력 위젯 생성 전에 실행됨
    st.button(
        "🗑️ 예산 및 지출 내역 초기화",
        on_click=reset_budget,
        key="reset_budget"
    )

    st.number_input(
        "총 예산 (원)",
        min_value=0,
        step=100000,
        key="budget_input"
    )

    st.session_state.total_budget = st.session_state.budget_input

    with st.form("expense_form"):
        expense_name = st.text_input(
            "지출 항목",
            key="expense_name"
        )

        expense_amount = st.number_input(
            "지출 금액 (원)",
            min_value=0,
            step=10000,
            key="expense_amount"
        )

        expense_category = st.selectbox(
            "지출 분류",
            ["교육활동", "시설관리", "물품구매", "행사", "기타"],
            key="expense_category"
        )

        add_expense = st.form_submit_button("지출 등록")

    if add_expense:
        if expense_name.strip() and expense_amount > 0:
            st.session_state.expenses.append({
                "항목": expense_name,
                "금액": int(expense_amount),
                "분류": expense_category,
                "등록일": str(date.today())
            })
            st.success("지출이 등록되었습니다.")
        else:
            st.warning("지출 항목과 0보다 큰 금액을 입력하세요.")

    total_expenses = sum(
        item["금액"] for item in st.session_state.expenses
    )

    remaining = st.session_state.total_budget - total_expenses

    st.divider()
    col1, col2, col3 = st.columns(3)

    col1.metric("총 예산", f"{st.session_state.total_budget:,}원")
    col2.metric("총 지출", f"{total_expenses:,}원")
    col3.metric("남은 예산", f"{remaining:,}원")

    if st.session_state.total_budget > 0:
        usage = total_expenses / st.session_state.total_budget
        st.subheader("예산 사용률")
        st.progress(min(max(usage, 0.0), 1.0))
        st.write(f"{usage * 100:.1f}% 사용")
    else:
        st.info("총 예산을 입력하면 사용률이 표시됩니다.")

    if remaining < 0:
        st.warning("예산을 초과하여 지출했습니다.")

    st.subheader("지출 내역")
    show_table(st.session_state.expenses)

    download_csv(
        st.session_state.expenses,
        "예산_지출내역.csv",
        "expenses_csv"
    )


# -----------------------------
# 5. 민원 종류 분류
# -----------------------------
elif page == "📨 민원 종류 분류":
    st.header("📨 민원 종류 분류")
    st.write("민원 내용을 입력하면 관련 키워드를 기준으로 종류를 분류합니다.")

    with st.form("complaint_form"):
        complaint_name = st.text_input(
            "민원 제목",
            key="complaint_name"
        )

        complaint_content = st.text_area(
            "민원 내용",
            placeholder="예: 교실 냉난방 시설을 점검해 주세요.",
            key="complaint_content"
        )

        add_complaint = st.form_submit_button("민원 분류 및 등록")

    if add_complaint:
        if complaint_content.strip():
            category = classify_complaint(complaint_content)

            st.session_state.complaints.append({
                "제목": complaint_name or "제목 없음",
                "내용": complaint_content,
                "분류": category,
                "접수일": str(date.today()),
                "처리 상태": "접수"
            })

            st.success(f"민원이 등록되었습니다. 분류 결과: {category}")
        else:
            st.warning("민원 내용을 입력하세요.")

    st.divider()
    st.subheader("접수된 민원")

    if st.session_state.complaints:
        for i, complaint in enumerate(st.session_state.complaints):
            with st.container(border=True):
                st.write(f"**{complaint['제목']}**")
                st.write(f"내용: {complaint['내용']}")
                st.write(f"분류: {complaint['분류']}")
                st.write(f"접수일: {complaint['접수일']}")

                categories = [
                    "시설·안전", "예산·회계", "서류·증명",
                    "교육·프로그램", "불편·서비스", "일반 문의"
                ]

                complaint["분류"] = st.selectbox(
                    "분류 수정",
                    categories,
                    index=categories.index(complaint["분류"]),
                    key=f"complaint_category_{i}"
                )

                statuses = ["접수", "처리 중", "처리 완료"]

                complaint["처리 상태"] = st.selectbox(
                    "처리 상태",
                    statuses,
                    index=statuses.index(complaint["처리 상태"]),
                    key=f"complaint_status_{i}"
                )

                if st.button("민원 삭제", key=f"delete_complaint_{i}"):
                    st.session_state.complaints.pop(i)
                    st.rerun()
    else:
        st.info("접수된 민원이 없습니다.")

    download_csv(
        st.session_state.complaints,
        "민원_목록.csv",
        "complaints_csv"
    )

    st.button(
        "🗑️ 민원 데이터 초기화",
        on_click=reset_complaints,
        key="reset_complaints"
    )


# -----------------------------
# 하단 안내
# -----------------------------
st.divider()
st.caption(
    "※ 현재 데이터는 앱 실행 세션에 저장됩니다. "
    "앱이 재시작되거나 세션이 종료되면 데이터가 사라질 수 있습니다."
)
