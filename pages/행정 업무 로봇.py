import streamlit as st
import pandas as pd
from docx import Document
import io
import plotly.express as px
import datetime

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

