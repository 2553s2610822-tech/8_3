
def reset_section(data_key, button_key, label, reset_values=None):
    if reset_values is None:
        reset_values = {}

    if st.button(f"🔄 {label} 초기화", key=f"{button_key}_reset"):
        st.session_state[button_key] = True

    if st.session_state.get(button_key, False):
        st.warning(
            f"{label} 데이터를 초기화할까요? "
            "삭제한 데이터는 복구할 수 없습니다."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "네, 초기화합니다",
                key=f"{button_key}_confirm",
                type="primary"
            ):
                st.session_state[data_key] = []

                for key, value in reset_values.items():
                    st.session_state[key] = value

                st.session_state[button_key] = False
                st.rerun()

        with col2:
            if st.button(
                "취소",
                key=f"{button_key}_cancel"
            ):
                st.session_state[button_key] = False
                st.rerun()
