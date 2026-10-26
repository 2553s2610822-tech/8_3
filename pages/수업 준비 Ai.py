
import streamlit as st
from google import genai

st.set_page_config(
    page_title="수업준비 AI",
    page_icon="📚",
    layout="wide"
)

# ---------- 화면 디자인 ----------
st.title("📚 수업준비 AI")
st.caption("대화로 수업을 개선하고, 필요한 자료까지 만들어 보세요.")

# ---------- API 키 확인 ----------
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    API_KEY = ""

# ---------- 대화 기록 ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "download_text" not in st.session_state:
    st.session_state.download_text = ""

# ---------- 사이드바 설정 ----------
with st.sidebar:
    st.header("⚙️ 수업 설정")

    grade = st.selectbox(
        "대상 학년",
        [
            "유치원", "초등학교 1~2학년",
            "초등학교 3~4학년", "초등학교 5~6학년",
            "중학교", "고등학교"
        ]
    )

    subject = st.selectbox(
        "과목",
        [
            "통합", "국어", "수학", "영어", "과학",
            "사회", "음악", "미술", "체육", "기타"
        ]
    )

    duration = st.selectbox(
        "수업 시간",
        ["20분", "40분", "45분", "50분", "자유 설정"]
    )

    teaching_style = st.selectbox(
        "수업 방식",
        ["자유롭게 추천", "토론 중심", "놀이·체험 중심",
         "강의 중심", "모둠 활동 중심", "개별 활동 중심"]
    )

    extra_info = st.text_area(
        "추가 요청 사항",
        placeholder="예: 준비물이 적고 학생 참여가 많은 수업"
    )

    st.divider()

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.download_text = ""
        st.rerun()

# ---------- 추천 질문 ----------
st.subheader("💡 무엇을 도와드릴까요?")

suggestions = [
    "새로운 수업 계획안을 만들어 줘.",
    "기존 수업안을 수정하고 개선해 줘.",
    "수업에 사용할 학습지를 만들어 줘.",
    "객관식 퀴즈와 정답을 만들어 줘.",
    "학생 참여 활동을 추천해 줘.",
    "수업 목표와 평가 방법을 정리해 줘."
]

if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""

cols = st.columns(3)

for i, question in enumerate(suggestions):
    with cols[i % 3]:
        if st.button(
            question,
            key=f"suggestion_{i}",
            use_container_width=True
        ):
            st.session_state.selected_question = question

st.divider()

# ---------- 기존 대화 표시 ----------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------- 채팅 입력 ----------
user_input = st.chat_input(
    "수업에 대해 질문하거나 수정할 내용을 입력하세요."
)

# 추천 질문 버튼을 누른 경우
if st.session_state.selected_question:
    user_input = st.session_state.selected_question
    st.session_state.selected_question = ""

# ---------- AI 응답 생성 ----------
if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    answer = ""

    with st.chat_message("assistant"):
        if not API_KEY:
            answer = (
                "🔑 Gemini API 키가 설정되지 않았어요.\n\n"
                "Streamlit Community Cloud의 앱 설정에서 "
                "Secrets에 GEMINI_API_KEY를 등록해 주세요."
            )
            st.warning(answer)

        else:
            try:
                client = genai.Client(api_key=API_KEY)

                # 최근 대화 최대 12개를 참고
                history = st.session_state.messages[-12:]

                conversation = "\n\n".join(
                    ("선생님" if item["role"] == "user" else "AI")
                    + ": " + item["content"]
                    for item in history
                )

                prompt = f"""
당신은 선생님의 수업 준비를 돕는 전문적인 교육 보조 AI입니다.

[수업 설정]
대상 학년: {grade}
과목: {subject}
수업 시간: {duration}
수업 방식: {teaching_style}
추가 요청: {extra_info or "없음"}

[주요 역할]
1. 선생님과 자연스러운 대화 형식으로 소통합니다.
2. 기존 수업안을 받으면 잘된 점, 개선할 점,
   수정한 수업안을 구분해서 제공합니다.
3. 자료 제작 요청에는 학년에 맞는 학습지, 퀴즈,
   활동지, 수업 계획안 등을 작성합니다.
4. 퀴즈를 만들 때는 정답과 간단한 해설도 제공합니다.
5. 수업 계획은 필요에 따라 도입, 전개, 정리,
   학습 목표, 준비물, 평가 방법으로 구성합니다.
6. 학년과 과목, 수업 시간에 맞게 내용을 조절합니다.
7. 요청이 모호하면 필요한 내용을 간단히 질문합니다.
8. 실제로 확인하지 않은 교육과정이나 사실을
   확정적으로 말하지 않습니다.
9. 읽기 쉽게 제목과 목록을 사용하고,
   불필요하게 긴 설명은 피합니다.

[최근 대화]
{conversation}

선생님의 마지막 요청에 맞춰 구체적으로 답변하세요.
"""

                with st.spinner("수업 자료를 준비하고 있어요..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=prompt
                    )

                answer = response.text or (
                    "답변을 생성하지 못했어요. "
                    "질문을 조금 바꾸어 다시 시도해 주세요."
                )

                st.markdown(answer)

            except Exception:
                answer = (
                    "죄송해요. AI 답변을 만드는 중 문제가 발생했어요.\n\n"
                    "다음 사항을 확인해 주세요.\n"
                    "- Secrets에 API 키가 올바르게 등록되었는지\n"
                    "- Gemini API 키와 모델 사용이 가능한지\n"
                    "- API 사용량 또는 연결에 문제가 없는지\n\n"
                    "설정을 확인한 후 다시 질문해 주세요."
                )
                st.error(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    # 마지막 답변을 다운로드할 자료로 저장
    st.session_state.download_text = answer

# ---------- 자료 다운로드 ----------
st.divider()
st.subheader("📥 수업 자료 저장")

if st.session_state.download_text:
    st.download_button(
        label="📄 마지막 AI 답변 다운로드 (.txt)",
        data=st.session_state.download_text,
        file_name="수업준비자료.txt",
        mime="text/plain",
        use_container_width=True
    )
else:
    st.info("AI에게 질문하면 마지막 답변을 파일로 저장할 수 있어요.")

st.caption(
    "수업준비 AI는 수업 준비를 돕는 보조 도구입니다. "
    "실제 수업에 사용하기 전에 자료의 정확성과 적절성을 확인해 주세요."
)

