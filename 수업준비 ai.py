
import streamlit as st
from google import genai

st.set_page_config(
    page_title="수업 준비 AI",
    page_icon="📚",
    layout="wide"
)

st.title("📚 수업 준비 AI")
st.caption("선생님의 수업 준비 시간을 줄여주는 대화형 도우미")

# API 키 확인
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    API_KEY = ""

# 사이드바: 수업 정보 설정
with st.sidebar:
    st.header("⚙️ 수업 설정")

    grade = st.selectbox(
        "학년",
        ["유치원", "초등학교 1~2학년",
         "초등학교 3~4학년", "초등학교 5~6학년",
         "중학교", "고등학교"]
    )

    subject = st.selectbox(
        "과목",
        ["통합", "국어", "수학", "영어", "과학",
         "사회", "음악", "미술", "체육", "기타"]
    )

    duration = st.selectbox(
        "수업 시간",
        ["20분", "40분", "45분", "50분", "자유 설정"]
    )

    extra_info = st.text_area(
        "추가 요청 사항",
        placeholder="예: 모둠 활동 중심, 준비물이 적은 수업"
    )

    st.divider()

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 첫 화면 안내
if not st.session_state.messages:
    st.markdown("""
    ### 안녕하세요! 수업 준비 AI입니다 👋

    수업에 필요한 자료를 함께 준비해 볼까요?

    - 📖 수업 계획과 학습 목표 만들기
    - 🎨 학생 참여 활동 추천하기
    - 📝 활동지와 평가 문제 만들기
    - 💡 수업 아이디어와 피드백 제안하기

    아래 채팅창에 원하는 내용을 입력해 주세요!
    """)

# 이전 대화 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 대화 입력
user_input = st.chat_input(
    "예: 초등학교 과학 수업 계획을 만들어 줘"
)

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        if not API_KEY:
            answer = (
                "🔑 아직 Gemini API 키가 설정되지 않았어요.\n\n"
                "GitHub에 코드를 올린 후 Streamlit Community Cloud의 "
                "앱 설정에서 Secrets에 `GEMINI_API_KEY`를 추가해 주세요. "
                "설정이 완료되면 실제 AI 대화를 사용할 수 있어요."
            )
            st.info(answer)
        else:
            try:
                client = genai.Client(api_key=API_KEY)

                # 최근 대화 내용을 포함해 문맥 유지
                history = st.session_state.messages[-12:]

                conversation = "\n".join(
                    f"{'선생님' if m['role'] == 'user' else 'AI'}: "
                    f"{m['content']}"
                    for m in history
                )

                prompt = f"""
당신은 선생님의 수업 준비를 돕는 친절하고 전문적인 AI입니다.

[수업 정보]
학년: {grade}
과목: {subject}
수업 시간: {duration}
추가 요청: {extra_info or '없음'}

[역할]
1. 선생님과 자연스러운 대화 형식으로 답변합니다.
2. 수업 목표, 진행 순서, 활동, 준비물, 평가 방법을
   필요에 따라 구체적으로 제안합니다.
3. 학생의 학년과 발달 수준에 맞게 설명합니다.
4. 요청이 모호하면 필요한 내용을 간단히 질문합니다.
5. 실제로 확인하지 않은 사실을 확정적으로 말하지 않습니다.
6. 답변은 읽기 쉽도록 제목과 목록을 활용합니다.
7. 요청하지 않은 내용을 지나치게 길게 설명하지 않습니다.

[최근 대화]
{conversation}

위 대화를 바탕으로 선생님의 마지막 메시지에 답변하세요.
"""

                with st.spinner("수업 아이디어를 생각하고 있어요..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=prompt
                    )

                answer = response.text

                if not answer:
                    answer = "답변을 받아오지 못했어요. 다시 질문해 주세요."

                st.markdown(answer)

            except Exception:
                answer = (
                    "죄송해요. AI 답변을 생성하는 중 문제가 발생했어요.\n\n"
                    "인터넷 연결, API 키 설정, Gemini API 사용 가능 여부를 "
                    "확인한 후 다시 시도해 주세요."
                )
                st.error(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
