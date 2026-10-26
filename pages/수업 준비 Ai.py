
import streamlit as st
from google import genai

st.set_page_config(
    page_title="수업준비 AI",
    page_icon="📚",
    layout="wide"
)

st.title("📚 수업준비 AI")
st.write("AI와 대화하며 수업을 개선하고 학습 자료를 만들어 보세요.")

# API 키 확인
try:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    api_key = ""

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""

# 사이드바 설정
with st.sidebar:
    st.header("수업 설정")

    grade = st.selectbox(
        "학년",
        ["유치원", "초등학교 1~2학년", "초등학교 3~4학년",
         "초등학교 5~6학년", "중학교", "고등학교"]
    )

    subject = st.selectbox(
        "과목",
        ["통합", "국어", "수학", "영어", "과학",
         "사회", "음악", "미술", "체육", "기타"]
    )

    lesson_time = st.selectbox(
        "수업 시간",
        ["20분", "40분", "45분", "50분", "직접 설정"]
    )

    lesson_style = st.selectbox(
        "수업 방식",
        ["AI 추천", "토론 중심", "놀이·체험 중심",
         "모둠 활동", "개별 활동", "설명 중심"]
    )

    extra_request = st.text_area(
        "추가 요청",
        placeholder="예: 준비물이 적고 재미있는 수업"
    )

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_question = ""
        st.rerun()

# 추천 질문
st.subheader("💡 추천 질문")

recommendations = [
    "새로운 수업 계획안을 만들어 줘.",
    "기존 수업안을 수정하고 개선해 줘.",
    "학생용 학습지를 만들어 줘.",
    "퀴즈와 정답을 만들어 줘.",
    "재미있는 수업 활동을 추천해 줘.",
    "수업 목표와 평가 방법을 정리해 줘."
]

columns = st.columns(3)

for index, question in enumerate(recommendations):
    with columns[index % 3]:
        if st.button(
            question,
            key=f"recommend_{index}",
            use_container_width=True
        ):
            st.session_state.pending_question = question
            st.rerun()

st.divider()

# 기존 대화 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 질문 입력
user_input = st.chat_input("수업에 관해 무엇이든 질문하세요.")

if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = ""

# AI 답변 생성
if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    answer = ""

    with st.chat_message("assistant"):
        if not api_key:
            answer = (
                "🔑 Gemini API 키가 설정되지 않았습니다.\n\n"
                "Streamlit Community Cloud의 Settings → Secrets에서 "
                "GEMINI_API_KEY를 등록해 주세요."
            )
            st.warning(answer)

        else:
            try:
                client = genai.Client(api_key=api_key)

                recent_messages = st.session_state.messages[-12:]

                history = "\n\n".join(
                    ("선생님" if item["role"] == "user" else "AI")
                    + ": " + item["content"]
                    for item in recent_messages
                )

                prompt = f"""
당신은 선생님의 수업 준비를 돕는 대화형 AI입니다.

[수업 정보]
학년: {grade}
과목: {subject}
수업 시간: {lesson_time}
수업 방식: {lesson_style}
추가 요청: {extra_request or "없음"}

[해야 할 일]
1. 선생님과 자연스럽게 대화합니다.
2. 기존 수업안 개선 요청에는 기존 문제점과 개선안을 제시합니다.
3. 학습지, 퀴즈, 활동지, 수업 계획안 등을 요청에 맞게 제작합니다.
4. 퀴즈에는 정답과 간단한 해설을 포함합니다.
5. 수업 계획에는 필요에 따라 목표, 도입, 전개, 정리,
   준비물과 평가 방법을 포함합니다.
6. 학생의 학년과 발달 수준에 맞게 내용을 조정합니다.
7. 정보가 부족하면 필요한 사항을 간단히 질문합니다.
8. 결과는 읽기 쉽고 구체적으로 작성합니다.

[대화 기록]
{history}

선생님의 마지막 요청에 답변하세요.
"""

                with st.spinner("수업 자료를 만들고 있습니다..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=prompt
                    )

                answer = response.text or (
                    "답변이 비어 있습니다. 질문을 바꾸어 다시 시도해 주세요."
                )
                st.markdown(answer)

            except Exception:
                answer = (
                    "AI 응답을 생성하지 못했습니다.\n\n"
                    "API 키, 인터넷 연결, 모델 사용 권한 및 API 사용량을 "
                    "확인한 뒤 다시 시도해 주세요."
                )
                st.error(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

# 자료 다운로드
st.divider()
st.subheader("📥 수업 자료 다운로드")

if st.session_state.messages:
    last_answer = next(
        (
            item["content"]
            for item in reversed(st.session_state.messages)
            if item["role"] == "assistant"
        ),
        ""
    )

    st.download_button(
        "TXT 파일로 다운로드",
        data=last_answer,
        file_name="수업준비자료.txt",
        mime="text/plain",
        use_container_width=True
    )
else:
    st.info("AI와 대화하면 답변을 파일로 저장할 수 있습니다.")

