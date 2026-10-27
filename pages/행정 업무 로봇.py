
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(
    page_title="행정업무 로봇",
    page_icon="🤖",
    layout="wide"
)

DEFAULT_BUDGET = 1_000_000_000

# -------------------------
# 세션 데이터 초기 설정
# -------------------------
defaults = {
    "documents": [],
    "tasks": [],
    "expenses": [],
    "complaints": [],
    "total_budget": DEFAULT_BUDGET,
    "budget_input": DEFAULT_BUDGET,
    "current_title": "",
    "document_editor": "",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -------------------------
# 초기화 함수
# -------------------------
def reset_documents():
    st.session_state.documents = []
    st.session_state.current_title = ""
    st.session_state.document_editor = ""


def reset_tasks():
    st.session_state.tasks = []


def reset_budget():
    st.session_state.expenses = []
    st.session_state.total_budget = DEFAULT_BUDGET
    st.session_state.budget_input = DEFAULT_BUDGET


def reset_complaints():
    st.session_state.complaints = []


def reset_all():
    reset_documents()
    reset_tasks()
    reset_budget()
    reset_complaints()


# -------------------------
# 공통 함수
# -------------------------
def show_table(data):
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("등록된 데이터가 없습니다.")


def download_csv(data, filename, key):
    if data:
        csv = pd.DataFrame(data).to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 CSV 다운로드",
            data=csv,
            file_name=filename,
            mime="text/csv",
            key=key
        )


def classify_complaint(content):
    rules = {
        "시설·안전": [
            "시설", "고장", "안전", "수리", "냉난방", "교실"
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

    for category, words in rules.items():
        if any(word in content for word in words):
            return category

    return "일반 문의"


# -------------------------
# 공문 초안 자동 생성 함수
# -------------------------
def make_document(title, receiver, sender, keywords, purpose):
    """입력한 정보를 바탕으로 공문 초안을 생성한다."""

    title = title.strip() or "행정업무 관련 안내"
    receiver = receiver.strip() or "관련 기관"
    sender = sender.strip() or "학교장"
    purpose = purpose.strip() or "관련 업무의 원활한 추진을 위해 안내합니다."

    keyword_list = []

    if keywords:
        keyword_list.extend(keywords)

    # 중복 키워드 제거
    keyword_list = list(dict.fromkeys(
        word.strip() for word in keyword_list if word.strip()
    ))

    keyword_text = ", ".join(keyword_list) if keyword_list else "관련 업무"

    # 키워드별 안내 문구
    keyword_guides = {
        "체험학습": "체험학습의 일정, 장소, 참가 대상 및 안전 수칙을 안내합니다.",
        "예산": "예산 편성 및 사용 계획을 확인하고 관련 절차에 따라 집행합니다.",
        "시설관리": "시설 상태를 점검하고 필요한 유지·보수 사항을 확인합니다.",
        "안전교육": "교육 일정과 참여 대상을 확인하고 안전교육을 실시합니다.",
        "행사안내": "행사 일정, 장소, 참가 대상 및 준비 사항을 안내합니다.",
        "회의개최": "회의 일시, 장소, 참석 대상 및 주요 안건을 안내합니다.",
        "교육활동": "교육활동의 목적과 운영 계획을 확인하고 관련 업무를 진행합니다.",
        "물품구매": "구매 품목과 수량을 확인하고 관련 절차에 따라 구매를 진행합니다.",
        "출장신청": "출장 목적, 기간 및 관련 신청 서류를 확인합니다.",
        "급식관리": "급식 운영 상황과 위생 및 안전 관리 사항을 확인합니다.",
        "학생지원": "학생 지원 대상과 지원 내용을 확인하고 필요한 절차를 진행합니다.",
        "학부모안내": "학부모에게 안내할 내용과 전달 일정을 확인합니다.",
        "환경정비": "학교 환경을 점검하고 필요한 정비 활동을 진행합니다.",
        "업무협조": "관련 부서에서는 담당 업무가 원활히 진행될 수 있도록 협조해 주시기 바랍니다.",
        "자료제출": "제출 자료의 종류와 제출 기한을 확인하여 기한 내 제출합니다.",
        "학교행사": "학교 행사 일정과 준비 사항을 확인하고 원활한 운영을 위해 협조합니다.",
        "연수계획": "연수 목적, 일정, 대상 및 운영 방법을 확인합니다.",
        "방학안내": "방학 일정과 생활 수칙 및 관련 안내 사항을 전달합니다.",
        "진로교육": "진로교육의 운영 계획과 참여 대상 및 활동 내용을 안내합니다.",
        "안전점검": "점검 대상과 점검 일정을 확인하고 위험 요소를 확인합니다.",
        "학사일정": "학사일정의 주요 일정과 변경 사항을 안내합니다.",
        "가정통신문": "가정에 전달할 안내 사항과 필요한 확인 내용을 정리합니다.",
        "결과보고": "업무 추진 결과와 주요 성과 및 후속 조치 사항을 정리합니다.",
        "수업운영": "수업 운영 계획과 준비 사항을 확인하고 관련 내용을 안내합니다.",
    }

    guide_lines = []
    for keyword in keyword_list:
        if keyword in keyword_guides:
            guide_lines.append(f"- {keyword}: {keyword_guides[keyword]}")
        else:
            guide_lines.append(f"- {keyword}: 관련 내용을 확인하고 필요한 업무를 진행합니다.")

    if not guide_lines:
        guide_lines.append("- 관련 업무의 세부 사항을 확인하고 담당 절차에 따라 진행합니다.")

    guide_text = "\n".join(guide_lines)

    return f"""수신: {receiver}
발신: {sender}
제목: {title}

1. 목적
{purpose}

2. 주요 내용
{guide_text}

3. 협조 사항
가. 담당자는 관련 내용을 확인하고 필요한 업무를 진행해 주시기 바랍니다.
나. 업무 추진 시 관련 일정과 절차를 준수해 주시기 바랍니다.
다. 추가 확인이 필요한 사항은 담당 부서와 협의해 주시기 바랍니다.

4. 관련 키워드
{keyword_text}

붙임: 필요한 경우 관련 자료 별도 첨부. 끝.

※ 자동 생성된 초안입니다. 실제 발송 전에 기관명, 날짜, 담당 부서 및 세부 내용을 확인하세요.
"""


# -------------------------
# 사이드바
# -------------------------
st.sidebar.title("🤖 행정업무 로봇")

page = st.sidebar.radio(
    "기능 선택",
    [
        "📊 대시보드",
        "📝 공문 자동 작성",
        "📈 업무 진행률",
        "💰 예산 사용 현황",
        "📨 민원 종류 분류",
    ]
)

st.title("🤖 학교 행정업무 로봇")


# ==================================================
# 1. 대시보드
# ==================================================
if page == "📊 대시보드":
    st.header("📊 행정업무 대시보드")

    total_tasks = len(st.session_state.tasks)
    completed = sum(
        task["상태"] == "완료"
        for task in st.session_state.tasks
    )
    progress = completed / total_tasks if total_tasks else 0

    expenses = sum(
        item["금액"] for item in st.session_state.expenses
    )
    remaining = st.session_state.total_budget - expenses

    unfinished = sum(
        item["처리 상태"] != "처리 완료"
        for item in st.session_state.complaints
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 업무", f"{total_tasks}건")
    c2.metric("완료 업무", f"{completed}건")
    c3.metric("남은 예산", f"{remaining:,}원")
    c4.metric("미완료 민원", f"{unfinished}건")

    st.subheader("업무 진행률")
    st.progress(progress)
    st.write(f"{progress * 100:.1f}% 완료")

    st.write(f"저장된 공문: {len(st.session_state.documents)}건")
    st.write(f"등록된 지출: {len(st.session_state.expenses)}건")
    st.write(f"접수된 민원: {len(st.session_state.complaints)}건")

    st.divider()
    st.warning("전체 초기화 시 모든 등록 데이터가 삭제됩니다.")

    st.button(
        "🗑️ 전체 데이터 초기화",
        on_click=reset_all,
        key="reset_all"
    )


# ==================================================
# 2. 공문 자동 작성
# ==================================================
elif page == "📝 공문 자동 작성":
    st.header("📝 공문 자동 작성")
    st.write("키워드와 목적을 입력하면 공문 초안을 자동으로 생성합니다.")

    keyword_options = [
        "체험학습", "예산", "시설관리", "안전교육",
        "행사안내", "회의개최", "교육활동", "물품구매",
        "출장신청", "급식관리", "학생지원", "학부모안내",
        "환경정비", "업무협조", "자료제출", "학교행사",
        "연수계획", "방학안내", "진로교육", "안전점검",
        "학사일정", "가정통신문", "결과보고", "수업운영"
    ]

    # 폼 제출 시 입력값을 받아 초안 생성
    with st.form("document_form"):
        title = st.text_input(
            "공문 제목",
            placeholder="예: 학교 안전교육 실시 안내"
        )

        receiver = st.text_input(
            "수신 기관",
            placeholder="예: 전 교직원"
        )

        sender = st.text_input(
            "발신 기관",
            placeholder="예: ○○고등학교장"
        )

        selected_keywords = st.multiselect(
            "관련 키워드 선택",
            keyword_options
        )

        custom_keywords = st.text_input(
            "추가 키워드",
            placeholder="예: 제출 기한, 준비물, 신청 방법"
        )

        purpose = st.text_area(
            "공문 목적 및 전달 내용",
            placeholder="공문을 작성하는 이유와 전달할 내용을 입력하세요."
        )

        generate = st.form_submit_button(
            "✨ 공문 초안 생성",
            type="primary",
            use_container_width=True
        )

    # 이 부분은 편집창을 표시하기 전에 실행됨
    if generate:
        try:
            all_keywords = list(selected_keywords)

            if custom_keywords.strip():
                all_keywords.extend([
                    word.strip()
                    for word in custom_keywords.replace("，", ",").split(",")
                    if word.strip()
                ])

            generated_text = make_document(
                title=title,
                receiver=receiver,
                sender=sender,
                keywords=all_keywords,
                purpose=purpose
            )

            st.session_state.current_title = (
                title.strip() or "행정업무 관련 안내"
            )
            st.session_state.document_editor = generated_text

            st.success("공문 초안이 생성되었습니다.")

        except Exception as error:
            st.error("공문 초안 생성 중 문제가 발생했습니다.")
            st.code(str(error))

    st.subheader("생성된 공문 초안")

    edited_text = st.text_area(
        "아래에서 공문 내용을 확인하고 수정하세요.",
        key="document_editor",
        height=380,
        placeholder="위에서 정보를 입력하고 '공문 초안 생성'을 누르면 여기에 초안이 표시됩니다."
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "💾 공문 저장",
            key="save_document",
            use_container_width=True
        ):
            if edited_text.strip():
                st.session_state.documents.append({
                    "제목": st.session_state.current_title or "공문",
                    "작성일": str(date.today()),
                    "내용": edited_text
                })
                st.success("공문이 저장되었습니다.")
            else:
                st.warning("먼저 초안을 생성하거나 편집창에 내용을 입력하세요.")

    with col2:
        st.download_button(
            "📥 TXT 파일 다운로드",
            data=edited_text,
            file_name="공문_초안.txt",
            mime="text/plain",
            key="download_document",
            use_container_width=True
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


# ==================================================
# 3. 업무 진행률
# ==================================================
elif page == "📈 업무 진행률":
    st.header("📈 업무 진행률 관리")

    with st.form("task_form"):
        task_name = st.text_input("업무 이름")
        manager = st.text_input("담당자")
        deadline = st.date_input("마감일", value=date.today())
        status = st.selectbox("진행 상태", ["예정", "진행 중", "완료"])
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
                task["상태"] = new_status

                if st.button("업무 삭제", key=f"delete_task_{i}"):
                    st.session_state.tasks.pop(i)
                    st.rerun()
    else:
        st.info("등록된 업무가 없습니다.")

    total = len(st.session_state.tasks)
    done = sum(
        task["상태"] == "완료"
        for task in st.session_state.tasks
    )
    ratio = done / total if total else 0

    st.subheader("전체 업무 진행률")
    st.progress(ratio)
    st.write(f"{done}/{total}건 완료 ({ratio * 100:.1f}%)")

    download_csv(st.session_state.tasks, "업무_목록.csv", "tasks_csv")

    st.button(
        "🗑️ 업무 데이터 초기화",
        on_click=reset_tasks,
        key="reset_tasks"
    )


# ==================================================
# 4. 예산 사용 현황
# ==================================================
elif page == "💰 예산 사용 현황":
    st.header("💰 예산 사용 현황")

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
        expense_name = st.text_input("지출 항목")
        expense_amount = st.number_input(
            "지출 금액 (원)",
            min_value=0,
            step=10000
        )
        category = st.selectbox(
            "지출 분류",
            ["교육활동", "시설관리", "물품구매", "행사", "기타"]
        )
        add_expense = st.form_submit_button("지출 등록")

    if add_expense:
        if expense_name.strip() and expense_amount > 0:
            st.session_state.expenses.append({
                "항목": expense_name,
                "금액": int(expense_amount),
                "분류": category,
                "등록일": str(date.today())
            })
            st.success("지출이 등록되었습니다.")
        else:
            st.warning("지출 항목과 0보다 큰 금액을 입력하세요.")

    total_expenses = sum(
        item["금액"] for item in st.session_state.expenses
    )
    remaining = st.session_state.total_budget - total_expenses

    c1, c2, c3 = st.columns(3)
    c1.metric("총 예산", f"{st.session_state.total_budget:,}원")
    c2.metric("총 지출", f"{total_expenses:,}원")
    c3.metric("남은 예산", f"{remaining:,}원")

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
    download_csv(st.session_state.expenses, "예산_지출내역.csv", "expenses_csv")


# ==================================================
# 5. 민원 종류 분류
# ==================================================
elif page == "📨 민원 종류 분류":
    st.header("📨 민원 종류 분류")

    with st.form("complaint_form"):
        complaint_title = st.text_input("민원 제목")
        complaint_content = st.text_area(
            "민원 내용",
            placeholder="예: 교실 냉난방 시설을 점검해 주세요."
        )
        add_complaint = st.form_submit_button("민원 분류 및 등록")

    if add_complaint:
        if complaint_content.strip():
            category = classify_complaint(complaint_content)

            st.session_state.complaints.append({
                "제목": complaint_title or "제목 없음",
                "내용": complaint_content,
                "분류": category,
                "접수일": str(date.today()),
                "처리 상태": "접수"
            })

            st.success(f"민원이 등록되었습니다. 분류: {category}")
        else:
            st.warning("민원 내용을 입력하세요.")

    st.subheader("접수된 민원")

    if st.session_state.complaints:
        categories = [
            "시설·안전", "예산·회계", "서류·증명",
            "교육·프로그램", "불편·서비스", "일반 문의"
        ]
        statuses = ["접수", "처리 중", "처리 완료"]

        for i, item in enumerate(st.session_state.complaints):
            with st.container(border=True):
                st.write(f"**{item['제목']}**")
                st.write(item["내용"])

                item["분류"] = st.selectbox(
                    "민원 분류",
                    categories,
                    index=categories.index(item["분류"]),
                    key=f"complaint_category_{i}"
                )

                item["처리 상태"] = st.selectbox(
                    "처리 상태",
                    statuses,
                    index=statuses.index(item["처리 상태"]),
                    key=f"complaint_status_{i}"
                )

                if st.button("민원 삭제", key=f"delete_complaint_{i}"):
                    st.session_state.complaints.pop(i)
                    st.rerun()
    else:
        st.info("접수된 민원이 없습니다.")

    download_csv(st.session_state.complaints, "민원_목록.csv", "complaints_csv")

    st.button(
        "🗑️ 민원 데이터 초기화",
        on_click=reset_complaints,
        key="reset_complaints"
    )


st.divider()
st.caption(
    "※ 공문 초안은 입력한 정보를 바탕으로 규칙에 따라 자동 작성됩니다. "
    "실제 발송 전에는 내용을 확인해야 합니다. "
    "데이터는 현재 실행 세션에 저장됩니다."
)
