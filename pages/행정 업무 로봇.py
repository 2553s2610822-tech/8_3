
import streamlit as st
import pandas as pd
from datetime import date

# =====================================
# 1. 기본 설정
# =====================================
st.set_page_config(
    page_title="행정업무 로봇",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 학교 행정업무 로봇")
st.caption("공문 작성 · 업무 관리 · 예산 관리 · 민원 분류")


# =====================================
# 2. 데이터 초기화
# =====================================
if "documents" not in st.session_state:
    st.session_state.documents = []

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "expenses" not in st.session_state:
    st.session_state.expenses = []

if "complaints" not in st.session_state:
    st.session_state.complaints = []

if "total_budget" not in st.session_state:
    st.session_state.total_budget = 1000000000

if "current_draft" not in st.session_state:
    st.session_state.current_draft = ""

if "current_title" not in st.session_state:
    st.session_state.current_title = ""


# =====================================
# 3. 공통 함수
# =====================================
def display_table(data):
    if len(data) > 0:
        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("등록된 내역이 없습니다.")


def download_csv(data, filename):
    if len(data) > 0:
        csv_data = pd.DataFrame(data).to_csv(
            index=False,
            encoding="utf-8-sig"
        )
        st.download_button(
            "CSV 다운로드",
            data=csv_data,
            file_name=filename,
            mime="text/csv"
        )


def classify_complaint(content):
    rules = {
        "시설·안전": [
            "시설", "고장", "안전", "화장실",
            "냉난방", "위험", "수리"
        ],
        "예산·회계": [
            "예산", "비용", "지출", "회계",
            "환불", "납부"
        ],
        "서류·증명": [
            "서류", "증명서", "발급", "신청서"
        ],
        "교육·프로그램": [
            "수업", "교육", "프로그램",
            "체험학습", "행사"
        ],
        "불편·서비스": [
            "불편", "문의", "안내", "급식"
        ]
    }

    scores = {}

    for category, keywords in rules.items():
        scores[category] = sum(
            keyword in content for keyword in keywords
        )

    best = max(scores, key=scores.get)

    if scores[best] == 0:
        return "일반 문의"

    return best


# =====================================
# 4. 메뉴
# =====================================
page = st.sidebar.selectbox(
    "기능 선택",
    [
        "대시보드",
        "공문 자동 작성",
        "업무 진행률",
        "예산 사용 현황",
        "민원 종류 분류"
    ]
)


# =====================================
# 5. 대시보드
# =====================================
if page == "대시보드":
    st.header("📊 행정업무 현황")

    total_tasks = len(st.session_state.tasks)

    completed_tasks = sum(
        task["상태"] == "완료"
        for task in st.session_state.tasks
    )

    if total_tasks > 0:
        completion_rate = completed_tasks / total_tasks * 100
    else:
        completion_rate = 0

    spent = sum(
        item["금액"] for item in st.session_state.expenses
    )

    remaining = st.session_state.total_budget - spent

    pending = sum(
        item["처리 상태"] != "처리 완료"
        for item in st.session_state.complaints
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("전체 업무", f"{total_tasks}건")
    c2.metric("업무 완료율", f"{completion_rate:.1f}%")
    c3.metric("예산 잔액", f"{remaining:,}원")
    c4.metric("미완료 민원", f"{pending}건")

    st.subheader("업무 진행 상황")

    st.progress(int(completion_rate))
    st.write(
        f"완료된 업무: {completed_tasks} / {total_tasks}건"
    )

    st.subheader("저장된 자료")
    st.write(f"공문: {len(st.session_state.documents)}건")
    st.write(f"지출: {len(st.session_state.expenses)}건")
    st.write(f"민원: {len(st.session_state.complaints)}건")


# =====================================
# 6. 공문 자동 작성
# =====================================
elif page == "공문 자동 작성":
    st.header("📝 공문 자동 작성")
    st.write("키워드를 선택해 공문 초안을 생성하세요.")

    keyword_options = [
        "체험학습", "예산", "시설관리", "안전교육",
        "행사안내", "회의개최", "교육활동", "물품구매",
        "출장신청", "급식관리", "학생지원", "학부모안내",
        "환경정비", "업무협조", "자료제출", "학교행사",
        "연수계획", "방학안내", "교직원안내", "교육자료",
        "진로교육", "안전점검", "학사일정", "급식안내",
        "가정통신문", "결과보고", "계획서제출", "수업운영"
    ]

    with st.form("make_document_form"):
        title = st.text_input(
            "공문 제목",
            placeholder="예: 현장체험학습 실시 안내"
        )

        receiver = st.text_input(
            "수신",
            placeholder="예: 전 교직원"
        )

        sender = st.text_input(
            "발신",
            placeholder="예: ○○고등학교장"
        )

        selected_keywords = st.multiselect(
            "핵심 키워드 (여러 개 선택 가능)",
            keyword_options
        )

        custom_keywords = st.text_input(
            "추가 키워드",
            placeholder="예: 수학여행, 버스 신청, 안전 점검"
        )

        purpose = st.text_area(
            "공문 목적 및 주요 내용",
            placeholder="공문에 들어갈 내용을 입력하세요."
        )

        make_button = st.form_submit_button(
            "공문 초안 생성"
        )

    if make_button:
        extra = [
            word.strip().lstrip("#")
            for word in custom_keywords.replace("，", ",").split(",")
            if word.strip().lstrip("#")
        ]

        keywords = list(dict.fromkeys(
            selected_keywords + extra
        ))

        if not title.strip():
            st.error("공문 제목을 입력해 주세요.")

        elif not keywords:
            st.error("키워드를 하나 이상 선택하거나 입력해 주세요.")

        else:
            hashtags = " ".join(
                "#" + word.replace(" ", "_")
                for word in keywords
            )

            draft = (
                f"수신: {receiver.strip() or '관련 담당자'}\n"
                f"발신: {sender.strip() or '담당 부서'}\n\n"
                f"제목: {title.strip()}\n\n"
                f"핵심 키워드:\n{hashtags}\n\n"
                f"1. 목적\n{purpose.strip() or '관련 업무를 원활하게 추진하고자 합니다.'}\n\n"
                f"2. 주요 내용\n{', '.join(keywords)}\n\n"
                "3. 협조 사항\n"
                "관련 담당자는 내용을 확인하고 필요한 업무를 진행해 주시기 바랍니다.\n\n"
                "※ 실제 발송 전 내용을 확인하고 수정해 주세요."
            )

            st.session_state.current_draft = draft
            st.session_state.current_title = title.strip()

            # 편집창이 생성되기 전에 값을 설정
            st.session_state["document_editor"] = draft

    if st.session_state.current_draft:
        st.divider()
        st.subheader("📄 공문 초안 편집")

        edited_draft = st.text_area(
            "생성된 공문을 자유롭게 수정하세요.",
            key="document_editor",
            height=320
        )

        st.subheader("🏷️ 해시태그 미리 보기")

        hashtag_lines = [
            line for line in edited_draft.splitlines()
            if "#" in line
        ]

        if hashtag_lines:
            st.write(" ".join(hashtag_lines))
        else:
            st.write("공문에 해시태그가 없습니다.")

        st.download_button(
            "공문 TXT 다운로드",
            data=edited_draft,
            file_name="공문_초안.txt",
            mime="text/plain"
        )

        if st.button("공문 내역에 저장"):
            st.session_state.documents.append({
                "저장일": str(date.today()),
                "제목": st.session_state.current_title,
                "공문 내용": edited_draft
            })
            st.success("공문을 저장했습니다.")

        if st.button("새 공문 작성"):
            st.session_state.current_draft = ""
            st.session_state.current_title = ""
            st.session_state["document_editor"] = ""
            st.rerun()

    st.divider()
    st.subheader("📚 저장된 공문")

    display_table([
        {
            "저장일": item["저장일"],
            "제목": item["제목"]
        }
        for item in st.session_state.documents
    ])

    download_csv(
        st.session_state.documents,
        "공문_내역.csv"
    )

    if st.button("공문 내역 전체 삭제"):
        st.session_state.documents = []
        st.session_state.current_draft = ""
        st.session_state.current_title = ""
        st.session_state["document_editor"] = ""
        st.rerun()


# =====================================
# 7. 업무 진행률
# =====================================
elif page == "업무 진행률":
    st.header("📈 업무 진행률 관리")

    with st.form("add_task_form"):
        task_name = st.text_input("업무명")
        manager = st.text_input("담당자")
        deadline = st.date_input("마감일", value=date.today())

        task_status = st.selectbox(
            "업무 상태",
            ["예정", "진행 중", "완료"]
        )

        add_task = st.form_submit_button("업무 등록")

    if add_task:
        if task_name.strip():
            st.session_state.tasks.append({
                "업무명": task_name.strip(),
                "담당자": manager.strip() or "미지정",
                "마감일": str(deadline),
                "상태": task_status
            })
            st.success("업무를 등록했습니다.")
            st.rerun()
        else:
            st.error("업무명을 입력해 주세요.")

    st.subheader("등록된 업무")

    if st.session_state.tasks:
        for i, task in enumerate(st.session_state.tasks):
            with st.container(border=True):
                st.write(f"**{task['업무명']}**")
                st.write(f"담당자: {task['담당자']}")
                st.write(f"마감일: {task['마감일']}")

                new_status = st.selectbox(
                    "상태",
                    ["예정", "진행 중", "완료"],
                    index=["예정", "진행 중", "완료"].index(
                        task["상태"]
                    ),
                    key=f"task_status_{i}"
                )

                st.session_state.tasks[i]["상태"] = new_status

                if st.button("이 업무 삭제", key=f"delete_task_{i}"):
                    st.session_state.tasks.pop(i)
                    st.rerun()

        total = len(st.session_state.tasks)
        done = sum(
            task["상태"] == "완료"
            for task in st.session_state.tasks
        )
        rate = done / total

        st.subheader("전체 완료율")
        st.progress(rate)
        st.write(f"{rate * 100:.1f}%")

    display_table(st.session_state.tasks)

    download_csv(
        st.session_state.tasks,
        "업무_진행률.csv"
    )

    if st.button("업무 내역 전체 삭제"):
        st.session_state.tasks = []
        st.rerun()


# =====================================
# 8. 예산 사용 현황
# =====================================
elif page == "예산 사용 현황":
    st.header("💰 예산 사용 현황")

    new_budget = st.number_input(
        "총예산 (원)",
        min_value=0,
        max_value=100_000_000_000,
        value=int(st.session_state.total_budget),
        step=1_000_000
    )

    st.session_state.total_budget = new_budget

    with st.form("add_expense_form"):
        expense_name = st.text_input(
            "지출 항목",
            placeholder="예: 교육용 물품 구매"
        )

        amount = st.number_input(
            "지출 금액 (원)",
            min_value=0,
            max_value=100_000_000_000,
            value=0,
            step=10000
        )

        add_expense = st.form_submit_button("지출 등록")

    if add_expense:
        if not expense_name.strip():
            st.error("지출 항목을 입력해 주세요.")
        elif amount <= 0:
            st.error("지출 금액을 입력해 주세요.")
        else:
            st.session_state.expenses.append({
                "등록일": str(date.today()),
                "지출 항목": expense_name.strip(),
                "금액": int(amount)
            })
            st.success("지출을 등록했습니다.")
            st.rerun()

    spent = sum(
        item["금액"] for item in st.session_state.expenses
    )

    remaining = new_budget - spent

    c1, c2, c3 = st.columns(3)
    c1.metric("총예산", f"{new_budget:,}원")
    c2.metric("총지출", f"{spent:,}원")
    c3.metric("잔액", f"{remaining:,}원")

    if new_budget > 0:
        rate = spent / new_budget
        st.subheader("예산 사용률")
        st.progress(min(rate, 1.0))
        st.write(f"{rate * 100:.1f}% 사용")

    if remaining < 0:
        st.error(f"예산을 {abs(remaining):,}원 초과했습니다.")

    st.subheader("지출 내역")
    display_table(st.session_state.expenses)

    download_csv(
        st.session_state.expenses,
        "예산_지출내역.csv"
    )

    if st.button("예산 및 지출 내역 초기화"):
        st.session_state.expenses = []
        st.session_state.total_budget = 1_000_000_000
        st.rerun()


# =====================================
# 9. 민원 종류 분류
# =====================================
elif page == "민원 종류 분류":
    st.header("📨 민원 종류 분류")

    with st.form("complaint_form"):
        complaint_text = st.text_area(
            "민원 내용",
            placeholder="예: 교실 냉난방 시설이 작동하지 않습니다."
        )

        classify_button = st.form_submit_button("민원 분류")

    if classify_button:
        if not complaint_text.strip():
            st.error("민원 내용을 입력해 주세요.")
        else:
            category = classify_complaint(complaint_text)

            st.success(f"추천 민원 유형: {category}")

            st.session_state.complaints.append({
                "접수일": str(date.today()),
                "민원 내용": complaint_text.strip(),
                "민원 유형": category,
                "처리 상태": "접수"
            })

    st.divider()
    st.subheader("접수된 민원")

    categories = [
        "시설·안전",
        "예산·회계",
        "서류·증명",
        "교육·프로그램",
        "불편·서비스",
        "일반 문의"
    ]

    statuses = ["접수", "처리 중", "처리 완료"]

    if st.session_state.complaints:
        for i, item in enumerate(st.session_state.complaints):
            with st.container(border=True):
                st.write(f"**민원 {i + 1}**")
                st.write(item["민원 내용"])
                st.caption(f"접수일: {item['접수일']}")

                category_index = (
                    categories.index(item["민원 유형"])
                    if item["민원 유형"] in categories else 5
                )

                status_index = (
                    statuses.index(item["처리 상태"])
                    if item["처리 상태"] in statuses else 0
                )

                new_category = st.selectbox(
                    "민원 유형",
                    categories,
                    index=category_index,
                    key=f"category_{i}"
                )

                new_status = st.selectbox(
                    "처리 상태",
                    statuses,
                    index=status_index,
                    key=f"status_{i}"
                )

                st.session_state.complaints[i]["민원 유형"] = new_category
                st.session_state.complaints[i]["처리 상태"] = new_status

                if st.button("민원 삭제", key=f"delete_complaint_{i}"):
                    st.session_state.complaints.pop(i)
                    st.rerun()

    display_table(st.session_state.complaints)

    download_csv(
        st.session_state.complaints,
        "민원_목록.csv"
    )

    if st.button("민원 내역 전체 삭제"):
        st.session_state.complaints = []
        st.rerun()


# =====================================
# 10. 안내
# =====================================
st.divider()
st.caption(
    "교육용 시범 프로그램입니다. 데이터는 세션에 저장되므로 "
    "앱 재시작 시 사라질 수 있습니다. 공문은 실제 발송 전 검토하세요."
)
