
import streamlit as st

st.set_page_config(
    page_title="수업준비 AI",
    page_icon="📚",
    layout="wide"
)

# ---------- 기본 화면 ----------
st.title("📚 수업준비 AI")
st.write("AI와 대화하며 수업을 개선하고 자료를 만들어 보세요.")

# ---------- 세션 데이터 ----------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

# ---------- API 키 확인 ----------
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    API_KEY = ""

# ---------- 사이드바 ----------
with st.sidebar:
    st.header("⚙️ 수업 설정")

    grade = st.selectbox(
        "대상 학년",
        [
            "유치원",
            "초등학교 1~2학년",
            "초등학교 3~4학년",
            "초등학교 5~6학년",
            "중학교",
            "고등학교"
        ]
    )

    subject = st.selectbox(
        "과목",
        [
            "통합", "국어", "수학", "영어", "과학",
            "사회", "음악", "미술", "체육", "기타"
        ]
    )

    lesson_time = st.selectbox(
        "수업 시간",
        ["20분", "40분", "45분", "50분", "직접 설정"]
    )

    lesson_style = st.selectbox(
        "수업 방식",
        [
            "AI 추천", "토론 중심", "놀이·체험 중심",
            "모둠 활동", "개별 활동", "설명 중심"
        ]
    )

    extra_request = st.text_area(
        "추가 요청 사항",
        placeholder="예: 준비물이 적고 학생 참여가 많은 수업"
    )

    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_question = ""
        st.session_state.last_answer = ""
        st.rerun()

# ---------- 추천 질문 ----------
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
            key=f"question_{index}",
            use_container_width=True
        ):
            st.session_state.pending_question = question
            st.rerun()

st.divider()

# ---------- 대화 기록 표시 ----------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ---------- 사용자 입력 ----------
user_input = st.chat_input("수업에 필요한 내용을 입력하세요.")

# 추천 질문이 선택되었으면 해당 질문 사용
if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = ""

# ---------- AI 대화 ----------
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
                "Streamlit Community Cloud의 Settings → Secrets에서 "
                "GEMINI_API_KEY를 등록해 주세요."
            )
            st.warning(answer)

        else:
            try:
                # AI 라이브러리는 실제 사용할 때만 불러오기
                from google import genai

                client = genai.Client(api_key=API_KEY)

                recent_messages = st.session_state.messages[-10:]

                conversation = "\n\n".join(
                    ("선생님" if item["role"] == "user" else "AI")
                    + ": " + item["content"]
                    for item in recent_messages
                )

                prompt = f"""
당신은 선생님의 수업 준비를 돕는 친절한 교육 보조 AI입니다.

[수업 정보]
학년: {grade}
과목: {subject}
수업 시간: {lesson_time}
수업 방식: {lesson_style}
추가 요청: {extra_request or "없음"}

[기능]
1. 선생님과 자연스럽게 대화합니다.
2. 기존 수업안을 수정하고 개선점을 설명합니다.
3. 학습지, 퀴즈, 활동지, 수업 계획안을 제작합니다.
4. 퀴즈에는 정답과 간단한 해설을 포함합니다.
5. 수업 계획에는 학습 목표, 도입, 전개, 정리,
   준비물과 평가 방법을 필요에 따라 포함합니다.
6. 학년과 과목에 맞게 답변합니다.
7. 모르는 사실을 지어내지 않습니다.
8. 읽기 쉽도록 제목과 목록을 사용합니다.

[최근 대화]
{conversation}

선생님의 마지막 요청에 답변하세요.
"""

                with st.spinner("AI가 답변을 준비하고 있어요..."):
                    response = client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=prompt
                    )

                answer = (response.text or "").strip()

                if not answer:
                    answer = (
                        "답변을 받아오지 못했어요. "
                        "질문을 조금 바꾸어 다시 시도해 주세요."
                    )

                st.markdown(answer)

            except ImportError:
                answer = (
                    "필요한 AI 라이브러리를 찾을 수 없어요. "
                    "requirements.txt에 google-genai가 있는지 확인해 주세요."
                )
                st.error(answer)

            except Exception as error:
                # 상세 오류는 관리자 로그에서 확인할 수 있도록 출력
                print("Gemini API error:", repr(error))

                answer = (
                    "AI 답변을 생성하지 못했어요.\n\n"
                    "1. Secrets에 API 키가 등록되어 있는지 확인해 주세요.\n"
                    "2. API 키와 모델 사용 권한을 확인해 주세요.\n"
                    "3. API 사용량 제한이나 네트워크 상태를 확인해 주세요.\n\n"
                    "확인한 후 다시 질문해 주세요."
                )
                st.error(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.session_state.last_answer = answer

# ---------- 자료 다운로드 ----------
st.divider()
st.subheader("📥 수업 자료 다운로드")

if st.session_state.last_answer:
    st.download_button(
        label="TXT 파일로 다운로드",
        data=st.session_state.last_answer,
        file_name="수업준비자료.txt",
        mime="text/plain",
        use_container_width=True
    )
else:
    st.info("AI 답변이 생성되면 여기에서 자료를 다운로드할 수 있어요.")

st.caption(
    "AI가 만든 수업 자료는 실제 수업에 사용하기 전에 "
    "내용과 정답을 확인해 주세요."
)
