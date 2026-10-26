
# ------------------------------
# 4. 예산 사용 현황
# ------------------------------
elif page == "예산 사용 현황":
    st.title("💰 예산 사용 현황")

    DEFAULT_BUDGET = 1_000_000_000  # 10억원

    if "total_budget" not in st.session_state:
        st.session_state.total_budget = DEFAULT_BUDGET

    if "budget_reset_confirm" not in st.session_state:
        st.session_state.budget_reset_confirm = False

    def format_eok(amount):
        eok = amount // 100_000_000
        remainder = amount % 100_000_000

        if remainder == 0:
            return f"약 {eok}억원"

        cheonman = remainder // 10_000_000
        remainder %= 10_000_000

        baekman = remainder // 1_000_000
        remainder %= 1_000_000

        result = f"약 {eok}억원"

        if cheonman:
            result += f" {cheonman}천만원"
        if baekman:
            result += f" {baekman}백만원"
        if remainder:
            result += f" {remainder:,}원"

        return result

    st.subheader("총예산 설정")

    budget = st.number_input(
        "총예산액 (원)",
        min_value=0,
        max_value=100_000_000_000,
        value=int(st.session_state.total_budget),
        step=10_000_000,
        format="%d"
    )

    st.session_state.total_budget = int(budget)

    st.info(f"현재 총예산: **{format_eok(int(budget))}**")

    st.divider()
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
    usage = spent / budget if budget > 0 else 0

    st.divider()
    st.subheader("예산 사용 요약")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "총예산",
        format_eok(int(budget))
    )

    c2.metric(
        "누적 지출",
        format_eok(spent),
        help=f"{spent:,}원"
    )

    c3.metric(
        "잔액",
        format_eok(abs(balance)) if balance >= 0
        else f"초과 {format_eok(abs(balance))[2:]}",
        help=f"{balance:,}원"
    )

    st.progress(min(usage, 1.0))
    st.write(f"예산 사용률: **{usage:.1%}**")

    if usage > 1:
        st.warning("예산을 초과했습니다.")

    st.divider()
    st.subheader("지출 내역")

    if expenses:
        st.dataframe(
            pd.DataFrame(expenses),
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "지출 내역 CSV 다운로드",
            data=pd.DataFrame(expenses).to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="예산지출내역.csv",
            mime="text/csv"
        )

        st.subheader("분류별 지출")
        chart = (
            pd.DataFrame(expenses)
            .groupby("분류")["금액"]
            .sum()
        )
        st.bar_chart(chart)
    else:
        st.info("등록된 지출 내역이 없습니다.")

    st.divider()
    st.subheader("🔄 예산 초기화")

    st.write(
        "초기화하면 등록된 지출 내역이 삭제되고 "
        "총예산이 10억원으로 돌아갑니다."
    )

    if not st.session_state.budget_reset_confirm:
        if st.button("예산 초기화", type="secondary"):
            st.session_state.budget_reset_confirm = True
            st.rerun()
    else:
        st.warning(
            "정말 초기화할까요? "
            "삭제한 지출 내역은 복구할 수 없습니다."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("네, 초기화합니다", type="primary"):
                st.session_state.expenses = []
                st.session_state.total_budget = DEFAULT_BUDGET
                st.session_state.budget_reset_confirm = False
                st.success("예산과 지출 내역을 초기화했습니다.")
                st.rerun()

        with col2:
            if st.button("취소"):
                st.session_state.budget_reset_confirm = False
                st.rerun()
