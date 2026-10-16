
        
        st.write("### 🛠️ 데이터 필터링 기능")
        columns = df.columns.tolist()
        selected_col = st.selectbox("필터링 기준 열 선택", columns)
        unique_values = df[selected_col].unique().tolist()
        selected_val = st.selectbox("값 선택", unique_values)
        
        filtered_df = df[df[selected_col] == selected_val]
        st.write(f"Filtered Results ({len(filtered_df)}건):")
        st.dataframe(filtered_df)

# ----------------------------------------------------
# 📝 보고서 자동 생성 기능
# ----------------------------------------------------
elif choice == "📝 보고서 자동 생성":
    st.subheader("📝 공문 및 보고서 양식 자동 생성")
    
    doc_title = st.text_input("보고서 제목", "2026년도 4분기 행정 업무 보고서")
    doc_dept = st.text_input("작성 부서", "행정지원팀")
    doc_author = st.text_input("작성자", "홍길동 주무관")
    doc_content = st.text_area("주요 내용 입력", "1. 본 문서의 목적은...\n2. 주요 추진 실적은 아래와 같음...")
    
    if st.button("Word 문서 생성하기"):
        # ReportLab 대신 python-docx를 사용하여 실제 행정 서식 생성
        doc = Document()
        doc.add_heading(doc_title, level=0)
        
        p = doc.add_paragraph()
        p.add_run(f"작성부서: {doc_dept}\n").bold = True
        p.add_run(f"작성자: {doc_author}\n")
        p.add_run("-" * 40 + "\n\n")
        
        doc.add_paragraph(doc_content)
        
        # 메모리 스트림에 저장하여 바로 다운로드 가능하게 처리
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        
        st.success("보고서 문서가 성공적으로 생성되었습니다!")
        st.download_button(
            label="📄 생성된 Word 파일 다운로드",
            data=bio,
            file_name=f"{doc_title}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# ----------------------------------------------------
# 📧 대량 이메일 발송 기능
# ----------------------------------------------------
elif choice == "📧 대량 이메일 발송":
    st.subheader("📧 업무 안내 메일 자동 발송기")
    
    st.warning("⚠️ 메일을 실제로 발송하려면 SMTP 설정(보안 비밀번호 등)이 필요합니다.")
    
    # SMTP 서버 설정 입력창
    with st.expander("⚙️ SMTP 서버 설정 (발신 메일 서버)"):
        smtp_server = st.text_input("SMTP 서버 주소", "://gmail.com")
        smtp_port = st.number_input("SMTP 포트 번호", value=587)
        sender_email = st.text_input("발신 이메일 주소", "example@gmail.com")
        sender_password = st.text_input("앱 비밀번호 (Password)", type="password")

    # 메일 내용 입력창
    st.write("### ✉️ 이메일 작성")
    mail_title = st.text_input("메일 제목", "[안내] 행정 자료 제출 요청의 건")
    receiver_list = st.text_area("수신자 리스트 (쉼표로 구분)", "user1@test.com, user2@test.com")
    mail_content = st.text_area("메일 본문", "안녕하세요, 행정지원팀입니다.\n요청드린 자료를 금주 금요일까지 제출해 주시기 바랍니다.")
    
    if st.button("🚀 이메일 일괄 발송"):
        receivers = [r.strip() for r in receiver_list.split(",") if r.strip()]
        
        if not sender_email or not sender_password:
            st.error("발신자 이메일과 비밀번호를 입력해 주세요.")
        elif not receivers:
            st.error("수신자 이메일을 하나 이상 입력해 주세요.")
        else:
            success_count = 0
            progress_bar = st.progress(0)
            
            try:
                # SMTP 연결 테스트 및 발송 로직 (실제 운영 시 주석 해제하여 사용)
                # server = smtplib.SMTP(smtp_server, smtp_port)
                # server.starttls()
                # server.login(sender_email, sender_password)
                
                for idx, r_email in enumerate(receivers):
                    # msg = MIMEMultipart()
                    # msg['From'] = sender_email
                    # msg['To'] = r_email
                    # msg['Subject'] = mail_title
                    # msg.attach(MIMEText(mail_content, 'plain'))
                    # server.sendmail(sender_email, r_email, msg.as_string())
                    
                    success_count += 1
                    progress_bar.progress((idx + 1) / len(receivers))
                
                # server.quit()
                st.success(f"🎉 총 {success_count}명의 담당자에게 메일 발송 시뮬레이션 완료! (실제 발송은 코드 내 SMTP 주석을 해제해 주세요)")
                
            except Exception as e:
                st.error(f"메일 발송 중 오류 발생: {e}")
코드를 사용할 때는 주의가 필요합니다.

🔥 로컬 PC에서 실행 및 GitHub 연동 방법

1. 내 컴퓨터에서 테스트하기
	• 터미널(CMD)을 열고 필요한 라이브러리를 설치합니다.bash
pip install streamlit pandas openpyxl python-docx
코드를 사용할 때는 주의가 필요합니다.
	• 코드가 저장된 폴더 안에서 프로그램을 실행합니다.bash
streamlit run app.py
코드를 사용할 때는 주의가 필요합니다.
2. GitHub에 올리기
	• GitHub 레포지토리를 만들고 app.py와 requirements.txt를 푸시(Push)합니다.
	• Streamlit Community Cloud에 접속하여 가입 후, 본인의 GitHub 레포지토리를 연결하면 전 세계 어디서나 접속할 수 있는 웹 페이지가 무료로 생성됩니다.


# 1. 페이지 초기 설정
st.set_page_config(page_title="스마트 행정 업무 로봇", layout="wide", page_icon="🏢")

st.title("🏢 스마트 행정 종합 관리 시스템")
st.caption("공문서 초안 작성부터 예산, 진행률 관리, 민원 분류까지 하나의 대시보드에서 처리합니다.")

# 사이드바 메뉴
menu = ["✍️ 공문서 초안 자동 작성", "💰 예산 사용 현황", "📈 업무 진행률 현황", "📁 민원 종류 자동 분류"]
choice = st.sidebar.radio("행정 로봇 기능 선택", menu)

# ----------------------------------------------------
# ✍️ 기능 1: 키워드 기반 공문서 초안 자동 작성
# ----------------------------------------------------
if choice == "✍️ 공문서 초안 자동 작성":
    st.subheader("✍️ 키워드 기반 공문서 초안 생성기")
    st.write("몇 가지 키워드와 핵심 내용을 입력하면 행정 표준 서식의 공문서 초안을 생성합니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        doc_num = st.text_input("문서 번호", "행정지원과-2026-1015")
        title_keyword = st.text_input("핵심 키워드 (제목용)", "개인정보 보호 교육")
        dept_name = st.text_input("시행 부서", "행정지원과")
        receiver = st.text_input("수신자", "전 부서 및 소속 기관장")
        
        # 키워드 조합 제목 자동 제안
        default_title = f"[{공고}] 2026년도 {title_keyword} 실시 안내 및 협조 요청"
        final_title = st.text_input("최종 공문 제목", default_title)
        
    with col2:
        main_summary = st.text_area("공문 핵심 내용 (요약)", "1. 관련: 국가정보화 기본법 제15조\n2. 행정 안전성 확보를 위해 아래와 같이 전 직원 대상 교육을 실시하고자 하오니 협조 바랍니다.\n- 일시: 2026. 11. 02.(월)\n- 대상: 전 직원\n- 방법: 비대면 온라인 송출")
        sign_off = st.text_input("발신 명의", "행 정 지 원 과 장 (직인생략)")

    if st.button("📄 공문서 초안(Word) 빌드"):
        doc = Document()
        
        # 행정 문서 스타일 적용
        doc.add_paragraph(f"문서번호: {doc_num}\t\t 시행일자: {datetime.date.today().strftime('%Y. %m. %d.')}")
        doc.add_paragraph(f"수 신 자: {receiver}")
        doc.add_paragraph("-" * 60)
        
        # 제목
        title_p = doc.add_paragraph()
        title_p.add_run(f"제    목: {final_title}").bold = True
        doc.add_paragraph("-" * 60)
        
        # 본문
        doc.add_paragraph(main_summary)
        
        # 끝 표시 및 명의
        doc.add_paragraph("\n\n붙임  개인정보 보호 교육 계획서 1부.  끝.")
        
        footer_p = doc.add_paragraph(f"\n\n{sign_off}")
        footer_p.alignment = 2 # 우측 정렬
        
        # 메모리 다운로드 처리
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        
        st.success("행정 공문서 초안 작성이 완료되었습니다!")
        st.download_button(
            label="📥 공문서(.docx) 다운로드",
            data=bio,
            file_name=f"{title_keyword}_공문초안.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# ----------------------------------------------------
# 💰 기능 2: 예산 사용 현황 모니터링 (차트)
# ----------------------------------------------------
elif choice == "💰 예산 사용 현황":
    st.subheader("💰 분기별 예산 집행 및 사용 현황")
    
    # 예시 예산 데이터 구성
    budget_data = pd.DataFrame({
        "목항": ["인건비", "일반운영비", "여비", "사업추진비", "자산취득비"],
        "총 예산": [50000000, 20000000, 5000000, 15000000, 10000000],
        "집행 금액": [35000000, 12000000, 4200000, 8500000, 2000000]
    })
    budget_data["잔여 예산"] = budget_data["총 예산"] - budget_data["집행 금액"]
    budget_data["집행률(%)"] = (budget_data["집행 금액"] / budget_data["총 예산"] * 100).round(1)

    # 데이터 프레임 보여주기
    st.write("### 📊 목별 예산 명세표")
    st.dataframe(budget_data.style.format({
        "총 예산": "{:,}원", "집행 금액": "{:,}원", "잔여 예산": "{:,}원", "집행률(%)": "{}%"
    }))
    
    # Plotly 시각화 차트
    st.write("### 📊 예산 집행 비율 시각화")
    fig = px.bar(budget_data, x="목항", y=["집행 금액", "잔여 예산"], 
                 title="목목별 예산 집행 vs 잔여 현황",
                 barmode="stack",
                 labels={"value": "금액 (원)", "variable": "구분"})
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# 📈 기능 3: 업무 진행률 표시
# ----------------------------------------------------
elif choice == "📈 업무 진행률 현황":
    st.subheader("📈 부서 핵심 과제 업무 진행률")
    
    # 세부 과제 리스트와 기본 진행률 설정
    tasks = {
        "1. 하반기 보안 정기 감사": 85,
        "2. 청사 시설물 안전 보수 작업": 40,
        "3. 지자체 합동 행정 혁신 평가 준비": 100,
        "4. 신임 공직자 직무 교육 프로그래밍": 15
    }
    
    st.write("각 행정 업무의 현재 진척 상황입니다.")
    
    for task_name, progress_val in tasks.items():
        col_t, col_p = st.columns([3, 7])
        with col_t:
            st.write(f"**{task_name}**")
        with col_p:
            # 프로그레스 바 표시
            st.progress(progress_val / 100)
            if progress_val == 100:
                st.caption(f"✅ 완료 (100%)")
            else:
                st.caption(f"⏳ 진행 중 ({progress_val}%)")
        st.divider()

# ----------------------------------------------------
# 📁 기능 4: 민원 종류 자동 분류 (AI/규칙 기반)
# ----------------------------------------------------
elif choice == "📁 민원 종류 자동 분류":
    st.subheader("📁 접수 민원 내용 자동 카테고리 분류기")
    st.write("접수된 민원 텍스트의 키워드를 분석하여 소관 부서 및 민원 종류를 자동 식별합니다.")
    
    complaint_text = st.text_area(
        "민원 내용을 입력하거나 복사해 넣으세요.",
        placeholder="예: 집 앞 도로에 불법 주차된 차량 때문에 출근길 통행이 너무 어렵습니다. 단속 좀 해주세요."
    )
    
    if st.button("🔍 민원 유형 분류하기"):
        if not complaint_text.strip():
            st.warning("민원 내용을 입력해 주세요.")
        else:
            # 키워드 기반 분류 매핑 알고리즘
            category = "기타 일반 행정 민원"
            assigned_dept = "종합민원실"
            badge_color = "blue"
            
            if any(k in complaint_text for k in ["주차", "불법주차", "도로", "신호등", "교통", "버스"]):
                category = "교통 및 도로 민원"
                assigned_dept = "교통지도과 / 건설과"
                badge_color = "🔴"
            elif any(k in complaint_text for k in ["쓰레기", "악취", "소음", "공사현장", "매연", "폐기물"]):
                category = "환경 및 소음 민원"
                assigned_dept = "환경위생과"
                badge_color = "🟢"
            elif any(k in complaint_text for k in ["세금", "재산세", "고지서", "환급", "취득세"]):
                category = "세무 및 재산 민원"
                assigned_dept = "세무과"
                badge_color = "🟡"
            elif any(k in complaint_text for k in ["보조금", "지원금", "기초생활", "복지", "아동", "노인"]):
                category = "복지 및 보건 민원"
                assigned_dept = "사회복지과 / 보건소"
                badge_color = "🟣"
                
            # 결과 출력
            st.success("민원 분석 및 자동 분류가 완료되었습니다.")
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric(label="분류된 민원 유형", value=f"{badge_color} {category}")
            with c2:
                st.metric(label="지정 소관 부서", value=assigned_dept)
                
            st.write("---")
            st.write("**[접수 분석 로그]**")
            st.code(f"접수 일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n내용 요약: {complaint_text[:30]}...\n시스템 판단: 담당 부서 이관 안내 자동 문자 발송 대기 상태.")
코드를 사용할 때는 주의가 필요합니다.

💡 추가 구현 가이드

1. 위 코드를 기존 app.py에 덮어쓰거나 붙여넣으시면 사이드바 선택에 따라 4가지 기능을 즉시 테스트하실 수 있습니다.
2. 민원 분류 기능 고도화: 만약 현재 코드의 텍스트 매칭(any(k in...)) 방식을 넘어 실제 AI 모델을 활용하고 싶다면, OpenAI API 키나 HuggingFace 허브를 연동하여 더욱 정밀한 의미 기반(Semantic) 분류로 확장할 수 있습니다.
작성된 코드의 기능 레이아웃은 마음에 드시나요? 혹시 예산 사용 현황 데이터를 엑셀 파일(CSV)로 직접 업로드해서 차트에 반영하도록 수정하고 싶으시거나, 공문서 서식에 행정 고유 로고 이미지를 삽입하는 코드가 필요하시면 말씀해 주세요!
AI 대답에는 오류가 있을 수 있습니다. 자세히 알아보기

내가 메인 페이지가아니라 세부적으로 들어가 있는 페이지야

아, 메인 페이지(app.py)가 아니라 별도의 파일로 분리된 서브(세부) 페이지 구조로 개발 중이시군요!
Streamlit에서 여러 페이지를 구성할 때는 주로 1) 신형 st.navigation 구조 또는 2) 구형 pages/ 폴더 구조를 사용합니다.
현재 담당하시는 세부 페이지 파일(예: pages/admin_robot.py 또는 별도 스크립트)에 바로 적용할 수 있도록, 메인 메뉴 없이 기능들만 깔끔하게 레이아웃된 세부 페이지 전용 코드를 제공해 드립니다.

💻 세부 페이지용 코드 (admin_robot.py)

기존 메인 파일에서 불필요한 사이드바 메뉴(st.sidebar.radio)를 제거하고, 사용자가 세부 페이지에 들어왔을 때 탭(Tabs) 형태로 4가지 기능을 상단에서 깔끔하게 전환하며 볼 수 있도록 직관적으로 수정했습니다.
python
import streamlit as st
import pandas as pd
from docx import Document
import io
import plotly.express as px
import datetime

# 1. 세부 페이지 상단 타이틀 설정 (메인 앱과 독립된 세부 페이지 레이아웃)
st.title("🤖 행정 업무 자동화 시스템 (세부 기능)")
st.caption("공문서 초안 작성, 예산 관리, 과제 진척도 모니터링, 민원 분류 업무를 지원하는 세부 페이지입니다.")

# 2. 상단 탭을 이용한 기능 분리 (세부 페이지 안에서 깔끔한 UI 제공)
tab1, tab2, tab3, tab4 = st.tabs([
    "✍️ 공문서 초안 작성", 
    "💰 예산 사용 현황", 
    "📈 업무 진행률", 
    "📁 민원 자동 분류"
])

# ----------------------------------------------------
# ✍️ 탭 1: 키워드 기반 공문서 초안 자동 작성
# ----------------------------------------------------
with tab1:
    st.subheader("✍️ 키워드 기반 공문서 초안 생성")
    st.info("몇 가지 행정 키워드를 입력하시면 규격화된 표준 공문서 초안(.docx) 파일이 생성됩니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        doc_num = st.text_input("문서 번호", "행정지원과-2026-1015", key="doc_num")
        title_keyword = st.text_input("핵심 키워드 (제목용)", "개인정보 보호 교육", key="keyword")
        dept_name = st.text_input("시행 부서", "행정지원과", key="dept")
        receiver = st.text_input("수신자", "전 부서 및 소속 기관장", key="receiver")
        
        default_title = f"[{dept_name} 공고] 2026년도 {title_keyword} 실시 안내 및 협조 요청"
        final_title = st.text_input("최종 공문 제목", default_title, key="final_title")
        
    with col2:
        main_summary = st.text_area("공문 핵심 내용 (요약)", "1. 관련: 국가정보화 기본법 제15조\n2. 행정 안전성 확보를 위해 아래와 같이 전 직원 대상 교육을 실시하고자 하오니 협조 바랍니다.\n- 일시: 2026. 11. 02.(월)\n- 대상: 전 직원\n- 방법: 비대면 온라인 송출", key="summary")
        sign_off = st.text_input("발신 명의", "행 정 지 원 과 장 (직인생략)", key="sign_off")

    if st.button("📄 공문서 초안 빌드", key="btn_doc"):
        doc = Document()
        doc.add_paragraph(f"문서번호: {doc_num}\t\t 시행일자: {datetime.date.today().strftime('%Y. %m. %d.')}")
        doc.add_paragraph(f"수 신 자: {receiver}")
        doc.add_paragraph("-" * 60)
        
        title_p = doc.add_paragraph()
        title_p.add_run(f"제    목: {final_title}").bold = True
        doc.add_paragraph("-" * 60)
        
        doc.add_paragraph(main_summary)
        doc.add_paragraph("\n\n붙임  개인정보 보호 교육 계획서 1부.  끝.")
        
        footer_p = doc.add_paragraph(f"\n\n{sign_off}")
        footer_p.alignment = 2
        
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        
        st.success("행정 공문서 초안 작성이 완료되었습니다!")
        st.download_button(
            label="📥 공문서(.docx) 다운로드",
            data=bio,
            file_name=f"{title_keyword}_공문초안.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

# ----------------------------------------------------
# 💰 탭 2: 예산 사용 현황 모니터링 (차트)
# ----------------------------------------------------
with tab2:
    st.subheader("💰 분기별 예산 집행 및 사용 현황")
    
    budget_data = pd.DataFrame({
        "목항": ["인건비", "일반운영비", "여비", "사업추진비", "자산취득비"],
        "총 예산":,
        "집행 금액": [42000000, 18000000, 45000000, 12000000, 5000000]
    })
    budget_data["잔여 예산"] = budget_data["총 예산"] - budget_data["집행 금액"]
    budget_data["집행률(%)"] = (budget_data["집행 금액"] / budget_data["총 예산"] * 100).round(1)

    st.write("### 📊 목별 예산 명세표")
    st.dataframe(budget_data.style.format({
        "총 예산": "{:,}원", "집행 금액": "{:,}원", "잔여 예산": "{:,}원", "집행률(%)": "{}%"
    }), use_container_width=True)
    
    st.write("### 📊 예산 집행 비율 시각화")
    fig = px.bar(budget_data, x="목항", y=["집행 금액", "잔여 예산"], 
                 barmode="stack",
                 labels={"value": "금액 (원)", "variable": "구분"})
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# 📈 탭 3: 업무 진행률 표시
# ----------------------------------------------------
with tab3:
    st.subheader("📈 부서 핵심 과제 업무 진행률")
    st.write("실시간 과제 진척도 현황입니다.")
    
    tasks = {
        "1. 하반기 보안 정기 감사": 85,
        "2. 청사 시설물 안전 보수 작업": 40,
        "3. 지자체 합동 행정 혁신 평가 준비": 100,
        "4. 신임 공직자 직무 교육 프로그래밍": 15
    }
    
    for task_name, progress_val in tasks.items():
        col_t, col_p = st.columns([2, 3])
        with col_t:
            st.write(f"**{task_name}**")
        with col_p:
            st.progress(progress_val / 100)
            if progress_val == 100:
                st.caption(f"✅ 완료 (100%)")
            else:
                st.caption(f"⏳ 진행 중 ({progress_val}%)")
        st.divider()

# ----------------------------------------------------
# 📁 탭 4: 민원 종류 자동 분류
# ----------------------------------------------------
with tab4:
    st.subheader("📁 접수 민원 내용 자동 카테고리 분류기")
    
    complaint_text = st.text_area(
        "민원 내용을 입력하거나 복사해 넣으세요.",
        placeholder="예: 집 앞 도로에 불법 주차된 차량 때문에 출근길 통행이 너무 어렵습니다.",
        key="complaint"
    )
    
    if st.button("🔍 민원 유형 분류하기", key="btn_complaint"):
        if not complaint_text.strip():
            st.warning("민원 내용을 입력해 주세요.")
        else:
            category = "기타 일반 행정 민원"
            assigned_dept = "종합민원실"
            badge_color = "🔵"
            
            if any(k in complaint_text for k in ["주차", "불법주차", "도로", "교통"]):
                category = "교통 및 도로 민원"
                assigned_dept = "교통지도과 / 건설과"
                badge_color = "🔴"
            elif any(k in complaint_text for k in ["쓰레기", "악취", "소음", "폐기물"]):
                category = "환경 및 소음 민원"
                assigned_dept = "환경위생과"
                badge_color = "🟢"
            elif any(k in complaint_text for k in ["세금", "재산세", "고지서", "환급"]):
                category = "세무 및 재산 민원"
                assigned_dept = "세무과"
                badge_color = "🟡"
            elif any(k in complaint_text for k in ["보조금", "지원금", "복지", "아동"]):
                category = "복지 및 보건 민원"
                assigned_dept = "사회복지과 / 보건소"
                badge_color = "🟣"
                
            st.success("민원 분석 및 자동 분류가 완료되었습니다.")
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric(label="분류된 민원 유형", value=f"{badge_color} {category}")
            with c2:
                st.metric(label="지정 소관 부서", value=assigned_dept)
