import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        
        st.title("📊 Population Trends csv")
        uploaded = st.file_uploader("population_trends.csv 업로드", type="csv", key="pop_file")
        if not uploaded:
            st.info("train.csv 파일을 업로드 해주세요.")
            return


        tabs = st.tabs([
            "0. 인구 트렌드 데이터 전처리",
            "1. 목적 & 절차",
            "2. 데이터셋 설명",
            "3. 데이터 로드 & 품질 체크",
            "4. Datetime 특성 추출",
            "5. 시각화",
            "6. 상관관계 분석",
            "7. 이상치 제거",
            "8. 로그 변환"
        ])

        # ✅ 0. 인구 트렌드 데이터 전처리
        with tabs[0]:
            st.header("👪 인구 트렌드: '세종' 지역 전처리 및 요약")

            df = pd.read_csv(uploaded)

            # 1. '세종' 지역 필터링 (열 이름: '지역'이 존재한다고 가정)
            df_sejong = df[df['지역'].str.contains("세종", na=False)].copy()

            # 2. 전체 데이터에서 '-' → 0 으로 치환
            df_sejong = df_sejong.replace('-', 0)

            # 3. 지정 열을 숫자로 변환
            numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
            for col in numeric_cols:
                df_sejong[col] = pd.to_numeric(df_sejong[col], errors='coerce').fillna(0).astype(int)

            # 4-1. describe() 출력
            st.subheader("📊 데이터 요약 통계 (`describe()`)")
            st.dataframe(df_sejong.describe())

            # 4-2. info() 출력
            st.subheader("📄 데이터프레임 구조 (`info()`)")
            buffer = io.StringIO()
            df_sejong.info(buf=buffer)
            st.text(buffer.getvalue())

            # 5. 샘플 확인
            st.subheader("🔍 전처리된 '세종' 지역 데이터 (상위 5개)")
            st.dataframe(df_sejong.head())



        # 1. 목적 & 분석 절차
        with tabs[1]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""
            **목적**: Bike Sharing Demand 데이터셋을 탐색하고,
            다양한 특성이 대여량(count)에 미치는 영향을 파악합니다.

            **절차**:
            1. 데이터 구조 및 기초 통계 확인  
            2. 결측치/중복치 등 품질 체크  
            3. datetime 특성(연도, 월, 일, 시, 요일) 추출  
            4. 주요 변수 시각화  
            5. 변수 간 상관관계 분석  
            6. 이상치 탐지 및 제거  
            7. 로그 변환을 통한 분포 안정화
            """)
        with tabs[2]:
            st.header("🔭 연도별 전체 인구 추이 그래프")
            # 2. 데이터셋 설명
            df_total = df[df['지역'] == '전국'].copy()

            # 2. 결측치 '-' → 0, 필요 열 숫자 변환
            df_total.replace('-', 0, inplace=True)
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df_total[col] = pd.to_numeric(df_total[col], errors='coerce').fillna(0)

            # 3. 연도 정렬
            df_total = df_total.sort_values(by='연도')
            df_total['연도'] = pd.to_numeric(df_total['연도'], errors='coerce').astype(int)

            # 4. 최근 3년 평균 자연 증가 계산
            df_recent = df_total.tail(3)
            avg_birth = df_recent['출생아수(명)'].mean()
            avg_death = df_recent['사망자수(명)'].mean()
            avg_net_change = avg_birth - avg_death

            # 5. 2035년 인구 예측 (가장 최근 인구 기준)
            last_year = df_total['연도'].max()
            last_pop = df_total[df_total['연도'] == last_year]['인구'].values[0]
            years_to_2035 = 2035 - last_year
            pop_2035 = last_pop + avg_net_change * years_to_2035

            # 6. 그래프용 데이터프레임 생성
            df_plot = df_total[['연도', '인구']].copy()
            df_plot.loc[len(df_plot)] = [2035, pop_2035]

            # 7. 그래프 그리기
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df_plot['연도'], df_plot['인구'], marker='o', label='Observed')
            ax.axvline(2035, color='red', linestyle='--', alpha=0.5)
            ax.scatter(2035, pop_2035, color='red', zorder=5, label=f'2035 Projection')
            ax.set_title("Population Trend and 2035 Forecast")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            ax.grid(True)

            # 8. Streamlit에 그래프 출력
            st.pyplot(fig)

            # 9. 예측 정보 요약
            st.markdown(f"""
            ### 📌 2035 Population Forecast
            - Based on the average natural change (births - deaths) over the last 3 years  
            - Average annual change: `{avg_net_change:,.0f}` people  
            - Projected 2035 Population: **{pop_2035:,.0f}**
            """)
        # 3. 데이터 로드 & 품질 체크
        with tabs[3]:
            st.header("📥 데이터 로드 & 품질 체크")
            df = pd.read_csv(uploaded)
            df = df.replace('-', 0)
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)
            df['연도'] = pd.to_numeric(df['연도'], errors='coerce').fillna(0).astype(int)

            # 전국 제외
            df = df[df['지역'] != '전국']

            # 최신 연도 확인
            latest_year = df['연도'].max()
            past_year = latest_year - 5

            # 최근 5년 데이터만 추출
            df_recent = df[df['연도'].isin([past_year, latest_year])]

            # 피벗테이블로 인구 비교
            pivot = df_recent.pivot(index='지역', columns='연도', values='인구').dropna()
            pivot['Change'] = pivot[latest_year] - pivot[past_year]
            pivot['Change_thousand'] = pivot['Change'] / 1000
            pivot['Percent_change'] = (pivot['Change'] / pivot[past_year]) * 100

            # 한글 → 영어 지역명 변환 (예시, 필요시 수정 가능)
            region_english = {
                '서울특별시': 'Seoul', '부산광역시': 'Busan', '대구광역시': 'Daegu', '인천광역시': 'Incheon',
                '광주광역시': 'Gwangju', '대전광역시': 'Daejeon', '울산광역시': 'Ulsan', '세종특별자치시': 'Sejong',
                '경기도': 'Gyeonggi', '강원도': 'Gangwon', '충청북도': 'Chungbuk', '충청남도': 'Chungnam',
                '전라북도': 'Jeonbuk', '전라남도': 'Jeonnam', '경상북도': 'Gyeongbuk', '경상남도': 'Gyeongnam',
                '제주특별자치도': 'Jeju'
            }
            pivot['Region'] = pivot.index.map(region_english)

            # ------------------
            # 변화량 수평 막대그래프
            # ------------------
            st.subheader("📌 Population Change (Last 5 Years)")

            pivot_sorted = pivot.sort_values(by='Change_thousand', ascending=False)

            fig1, ax1 = plt.subplots(figsize=(10, 8))
            sns.barplot(data=pivot_sorted, y='Region', x='Change_thousand', palette='coolwarm', ax=ax1)
            ax1.set_title("Population Change (in thousands)", fontsize=14)
            ax1.set_xlabel("Change (thousands)")
            ax1.set_ylabel("Region")

            # 막대 위에 값 표시
            for i, v in enumerate(pivot_sorted['Change_thousand']):
                ax1.text(v + np.sign(v)*1, i, f"{v:.1f}", va='center', fontsize=9)

            st.pyplot(fig1)

            # ------------------
            # 변화율 수평 막대그래프
            # ------------------
            st.subheader("📌 Population Percent Change (Last 5 Years)")

            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sns.barplot(data=pivot_sorted, y='Region', x='Percent_change', palette='viridis', ax=ax2)
            ax2.set_title("Population Growth Rate (%)", fontsize=14)
            ax2.set_xlabel("Percent Change")
            ax2.set_ylabel("Region")

            for i, v in enumerate(pivot_sorted['Percent_change']):
                ax2.text(v + np.sign(v)*0.2, i, f"{v:.1f}%", va='center', fontsize=9)

            st.pyplot(fig2)

            # ------------------
            # 해설 추가
            # ------------------
            st.markdown("### 🔎 Interpretation")
            st.markdown(f"""
            - **Seoul, Busan** and other major cities show **population decrease**, indicating possible outmigration or aging.
            - **Gyeonggi**, **Sejong**, and surrounding areas show **positive growth**, reflecting urban expansion and housing development.
            - The percentage change highlights how **smaller regions** (e.g. Sejong) can have high growth rates even with small absolute population increases.
            - These trends may help guide policy decisions related to urban planning, transportation, and social services.
            """)

        # 4. Datetime 특성 추출
        with tabs[4]:
            st.header("🕒 Datetime 특성 추출")
            
            # CSV 또는 사전 처리된 데이터프레임 불러오기
            df = pd.read_csv(uploaded)  

            # 데이터 전처리 (전국 제외, 증감 계산 등)
            df = df[df['지역'] != '전국']
            df.sort_values(by=['지역', '연도'], inplace=True)
            df['인구증감'] = df.groupby('지역')['인구'].diff()
            df = df.dropna(subset=['인구증감']).sort_values(by='인구증감', ascending=False).head(100)

            # 천단위 콤마 포맷
            df['인구'] = df['인구'].astype(int).map('{:,}'.format)
            df['인구증감'] = df['인구증감'].astype(int)

            # Streamlit 앱 출력
            st.title("연도별 지역 인구 증감 Top 100")

            # 컬러맵 설정 (양수: 파랑, 음수: 빨강)
            def highlight_change(val):
                color = 'background-color: '
                if val > 0:
                    color += f'rgba(0, 100, 255, {min(val / df["인구증감"].max(), 1):.2f})'
                else:
                    color += f'rgba(255, 0, 0, {min(abs(val) / abs(df["인구증감"].min()), 1):.2f})'
                return color

            styled_df = df.style.applymap(highlight_change, subset=['인구증감']) \
                                .format({'인구증감': '{:,}'})

            st.dataframe(styled_df)

        # 5. 시각화
        with tabs[5]:
            st.header("📈 시각화")
            # by 근무일 여부
            st.subheader("근무일 여부별 시간대별 평균 대여량")
            fig1, ax1 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='workingday', data=df,
                          ax=ax1)
            ax1.set_xlabel("Hour");
            ax1.set_ylabel("Average Count")
            st.pyplot(fig1)
            st.markdown(
                "> **해석:** 근무일(1)은 출퇴근 시간(7 ~ 9시, 17 ~ 19시)에 대여량이 급증하는 반면,\n"
                "비근무일(0)은 오후(11 ~ 15시) 시간대에 대여량이 상대적으로 높게 나타납니다."
            )

            # by 요일
            st.subheader("요일별 시간대별 평균 대여량")
            fig2, ax2 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='dayofweek', data=df, ax=ax2)
            ax2.set_xlabel("Hour");
            ax2.set_ylabel("Average Count")
            st.pyplot(fig2)
            st.markdown(
                "> **해석:** 평일(월 ~ 금)은 출퇴근 피크가 두드러지고,\n"
                "주말(토~일)은 오전 중반(10 ~ 14시)에 대여량이 더 고르게 분포하는 경향이 있습니다."
            )

            # by 시즌
            st.subheader("시즌별 시간대별 평균 대여량")
            fig3, ax3 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='season', data=df, ax=ax3)
            ax3.set_xlabel("Hour");
            ax3.set_ylabel("Average Count")
            st.pyplot(fig3)
            st.markdown(
                "> **해석:** 여름(2)과 가을(3)에 전반적으로 대여량이 높고,\n"
                "겨울(4)은 전 시간대에 걸쳐 대여량이 낮게 나타납니다."
            )

            # by 날씨
            st.subheader("날씨 상태별 시간대별 평균 대여량")
            fig4, ax4 = plt.subplots()
            sns.pointplot(x='hour', y='count', hue='weather', data=df, ax=ax4)
            ax4.set_xlabel("Hour");
            ax4.set_ylabel("Average Count")
            st.pyplot(fig4)
            st.markdown(
                "> **해석:** 맑음(1)은 전 시간대에서 대여량이 가장 높으며,\n"
                "안개·흐림(2), 가벼운 비/눈(3)에선 다소 감소하고, 심한 기상(4)에서는 크게 떨어집니다."
            )

        # 6. 상관관계 분석
        with tabs[6]:
            st.header("🔗 상관관계 분석")
            # 관심 피처만 선택
            features = ['temp', 'atemp', 'casual', 'registered', 'humidity',
                        'windspeed', 'count']
            corr_df = df[features].corr()

            # 상관계수 테이블 출력
            st.subheader("📊 피처 간 상관계수")
            st.dataframe(corr_df)

            # 히트맵 시각화
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(corr_df, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
            ax.set_xlabel("")  # 축 이름 제거
            ax.set_ylabel("")
            st.pyplot(fig)
            st.markdown(
                "> **해석:**\n"
                "- `count`는 `registered` (r≈0.99) 및 `casual` (r≈0.67)와 강한 양의 상관관계를 보입니다.\n"
                "- `temp`·`atemp`와 `count`는 중간 정도의 양의 상관관계(r≈0.4~0.5)를 나타내며, 기온이 높을수록 대여량이 증가함을 시사합니다.\n"
                "- `humidity`와 `windspeed`는 약한 음의 상관관계(r≈-0.2~-0.3)를 보여, 습도·풍속이 높을수록 대여량이 다소 감소합니다."
            )

        # 7. 이상치 제거
        with tabs[7]:
            st.header("🚫 이상치 제거")
            # 평균·표준편차 계산
            mean_count = df['count'].mean()
            std_count = df['count'].std()
            # 상한치: 평균 + 3*표준편차
            upper = mean_count + 3 * std_count

            st.markdown(f"""
                        - **평균(count)**: {mean_count:.2f}  
                        - **표준편차(count)**: {std_count:.2f}  
                        - **이상치 기준**: `count` > 평균 + 3×표준편차 = {upper:.2f}  
                          (통계학의 68-95-99.7 법칙(Empirical rule)에 따라 평균에서 3σ를 벗어나는 관측치는 전체의 약 0.3%로 극단치로 간주)
                        """)
            df_no = df[df['count'] <= upper]
            st.write(f"- 이상치 제거 전: {df.shape[0]}개, 제거 후: {df_no.shape[0]}개")

        # 8. 로그 변환
        with tabs[8]:
            st.header("🔄 로그 변환")
            st.markdown("""
                **로그 변환 맥락**  
                - `count` 변수는 오른쪽으로 크게 치우친 분포(skewed distribution)를 가지고 있어,  
                  통계 분석 및 모델링 시 정규성 가정이 어렵습니다.  
                - 따라서 `Log(Count + 1)` 변환을 통해 분포의 왜도를 줄이고,  
                  중앙값 주변으로 데이터를 모아 해석력을 높입니다.
                """)

            # 변환 전·후 분포 비교
            fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))

            # 원본 분포
            sns.histplot(df['count'], kde=True, ax=axes[0])
            axes[0].set_title("Original Count Distribution")
            axes[0].set_xlabel("Count")
            axes[0].set_ylabel("Frequency")

            # 로그 변환 분포
            df['log_count'] = np.log1p(df['count'])
            sns.histplot(df['log_count'], kde=True, ax=axes[1])
            axes[1].set_title("Log(Count + 1) Distribution")
            axes[1].set_xlabel("Log(Count + 1)")
            axes[1].set_ylabel("Frequency")

            st.pyplot(fig)

            st.markdown("""
                > **그래프 해석:**  
                > - 왼쪽: 원본 분포는 한쪽으로 긴 꼬리를 가진 왜곡된 형태입니다.  
                > - 오른쪽: 로그 변환 후 분포는 훨씬 균형잡힌 형태로, 중앙값 부근에 데이터가 집중됩니다.  
                > - 극단치의 영향이 완화되어 이후 분석·모델링 안정성이 높아집니다.
                """)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()