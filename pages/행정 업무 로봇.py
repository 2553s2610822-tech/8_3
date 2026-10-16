import streamlit as st
import pandas as pd
from docx import Document
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 페이지 설정
st.set_page_app(page_title="행정 업무 자동화 로봇", layout="wide", page_icon="🤖")

st.title("🤖 행정 업무 자동화 로봇 시스템")
st.caption("반복적인 행정 업무를 웹에서 쉽고 빠르게 처리하세요.")

# 사이드바 메뉴 구성
menu = ["🏠 홈", "📊 엑셀 데이터 분석", "📝 보고서 자동 생성", "📧 대량 이메일 발송"]
choice = st.sidebar.selectbox("기능 선택", menu)

# ----------------------------------------------------
# 🏠 홈 화면
# ----------------------------------------------------
if choice == "🏠 홈":
    st.subheader("Welcome! 행정 로봇 가이드")
    st.write("이 프로그램은 공공 및 일반 기업의 행정 업무 효율화를 위해 개발되었습니다.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📊 **엑셀 데이터 분석**\n\n파일을 업로드하여 통계 및 가공된 데이터를 확인합니다.")
    with col2:
        st.info("📝 **보고서 자동 생성**\n\n내용을 입력하면 규격화된 Word 문서(.docx)로 변환합니다.")
    with col3:
        st.info("📧 **대량 이메일 발송**\n\n정해진 양식에 맞춰 여러 담당자에게 메일을 보냅니다.")

# ----------------------------------------------------
# 📊 엑셀 데이터 분석 기능
# ----------------------------------------------------
elif choice == "📊 엑셀 데이터 분석":
    st.subheader("📊 엑셀/CSV 데이터 처리기")
    
    uploaded_file = st.file_uploader("분석할 엑셀 또는 CSV 파일을 업로드하세요.", type=["xlsx", "csv"])
    
    if uploaded_file is not None:
        # 파일 확장자에 따라 읽기
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("파일 업로드 완료!")
        
        st.write("### 🔍 데이터 미리보기 (상위 5개 행)")
        st.dataframe(df.head())
        
        st.write("### 📈 데이터 기본 요약 통계")
        st.dataframe(df.describe(include='all').astype(str))
        
        # 특정 열 필터링 기능 예시
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

