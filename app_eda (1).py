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
            "0. 목적 & 분석 절차",
            "1. 연도별 전체 인구 추이 그래프",
            "2. 데이터셋 설명",
            "3. 지역별 인구 변화량 순위",
            "4. 증감률 상위 지역 및 연도 도출",
            "5. 시각화"
            "6. 증감률 상위 지역 및 연도 도출 요청",
        ])


        df = pd.read_csv(uploaded)


        # 0. 목적 & 분석 절차
        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""
            **목적**: Bike Sharing Demand 데이터셋을 탐색하고,
            다양한 특성이 대여량(count)에 미치는 영향을 파악합니다.

            **절차**:
            1. 인구 트렌드 데이터 전처리
            2. 연도별 전체 인구 추이 그래프
            3. 지역별 인구 변화량 순위
            4. 증감률 상위 지역 및 연도 도출
            5. 시각화
            6. 증감률 상위 지역 및 연도 도출 요청

            """)
        # ✅ 1. 인구 트렌드 데이터 전처리
        with tabs[1]:
            st.header("👪 인구 트렌드: '세종' 지역 전처리 및 요약")

            

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
        # 3. 지역별 인구 변화량 순위
        with tabs[3]:
            # 앱 제목
            st.title("5-Year Population Change by Region")



            # 한글 -> 영문 지역명 매핑
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }

            # 전처리
            df = df[df['지역'] != '전국']
            df['Region'] = df['지역'].map(region_map)
            df['Year'] = df['연도']
            df['Population'] = df['인구'].astype(int)

            # 가장 최근 연도 및 5년 전 연도 계산
            latest_year = df['Year'].max()
            past_year = latest_year - 5

            # 최근 5년간의 시작/종료 연도별 데이터 추출
            df_latest = df[df['Year'] == latest_year][['Region', 'Population']]
            df_past = df[df['Year'] == past_year][['Region', 'Population']]

            # 병합 및 변화량/비율 계산
            merged = pd.merge(df_latest, df_past, on='Region', suffixes=('_latest', '_past'))
            merged['Change (thousands)'] = (merged['Population_latest'] - merged['Population_past']) / 1000
            merged['Change Rate (%)'] = ((merged['Population_latest'] - merged['Population_past']) / merged['Population_past']) * 100

            # 정렬
            merged.sort_values(by='Change (thousands)', ascending=False, inplace=True)

            # 그래프 스타일
            sns.set(style="whitegrid")

            # ---------- 그래프 1: 변화량 ----------
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            barplot1 = sns.barplot(
                data=merged,
                y='Region',
                x='Change (thousands)',
                palette='Blues_d',
                ax=ax1
            )
            ax1.set_title("Population Change (Last 5 Years)", fontsize=14)
            ax1.set_xlabel("Change (thousands)")
            ax1.set_ylabel("Region")

            # 막대 위에 값 표시
            for p in barplot1.patches:
                width = p.get_width()
                ax1.text(width + 1, p.get_y() + p.get_height() / 2,
                        f'{width:,.1f}', va='center')

            st.pyplot(fig1)

            # ---------- 그래프 2: 변화율 ----------
            merged.sort_values(by='Change Rate (%)', ascending=False, inplace=True)

            fig2, ax2 = plt.subplots(figsize=(10, 8))
            barplot2 = sns.barplot(
                data=merged,
                y='Region',
                x='Change Rate (%)',
                palette='coolwarm',
                ax=ax2
            )
            ax2.set_title("Population Growth Rate (%) (Last 5 Years)", fontsize=14)
            ax2.set_xlabel("Growth Rate (%)")
            ax2.set_ylabel("Region")

            # 막대 위에 값 표시
            for p in barplot2.patches:
                width = p.get_width()
                ax2.text(width + 0.2, p.get_y() + p.get_height() / 2,
                        f'{width:.2f}%', va='center')

            st.pyplot(fig2)

            # ---------- 해설 ----------
            st.markdown("### Analysis Summary")
            st.markdown("""
            The first chart shows the total population change (in thousands) over the past five years.
            Gyeonggi and Sejong stand out as regions with significant population growth in absolute terms.
            In contrast, regions such as Busan, Daegu, and Jeonbuk have experienced population decline.

            The second chart displays the percentage change in population over the same period.
            Although Sejong has a smaller population, it shows the highest growth rate, indicating rapid development or migration.
            Regions with negative growth rates may reflect aging populations or migration to metropolitan areas.
            """)

       
        # 4. 증감률 상위 지역 및 연도 도출
        with tabs[4]:
            st.header("🕒 증감률 상위 지역 및 연도 도출")
            


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
            st.header("📈 Population Trends by Region and Year")


            # 한글 -> 영문 지역명 매핑
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }

            # 전처리
            df = df[df['지역'] != '전국']  # '전국' 제외
            df['Region'] = df['지역'].map(region_map)
            df['Year'] = df['연도']
            df['Population'] = df['인구'].astype(int)

            # 피벗 테이블 생성: 연도(행) × 지역(열)
            pivot_df = df.pivot_table(index='Year', columns='Region', values='Population')

            # 누적 영역 그래프 그리기
            fig, ax = plt.subplots(figsize=(12, 6))
            pivot_df.plot.area(ax=ax, cmap='tab20', linewidth=0)
            ax.set_title("Stacked Area Chart of Population by Region", fontsize=16)
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
            plt.tight_layout()

            # 그래프 출력
            st.pyplot(fig)

            # 데이터 표 출력
            st.subheader("Population Pivot Table")
            st.dataframe(pivot_df.style.format('{:,}'))

        with tabs[6]:
            # 전처리
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }

            df = df[df['지역'] != '전국'].copy()
            df['Region'] = df['지역'].map(region_map)
            df['Year'] = df['연도']
            df['Population'] = df['인구'].astype(int)

            # 연도별 인구 증감(diff) 계산
            df.sort_values(by=['Region', 'Year'], inplace=True)
            df['Change'] = df.groupby('Region')['Population'].diff()

            # 상위 100개 증감 사례 추출
            top100 = df.dropna(subset=['Change']).copy()
            top100 = top100.sort_values(by='Change', ascending=False).head(100)

            # 숫자 포맷팅
            top100['Population_fmt'] = top100['Population'].apply(lambda x: f"{x:,}")
            top100['Change_fmt'] = top100['Change'].astype(int).apply(lambda x: f"{x:,}")

            # 시각화를 위한 데이터프레임 준비
            display_df = top100[['Year', 'Region', 'Population_fmt', 'Change_fmt']].rename(
                columns={
                    'Year': 'Year',
                    'Region': 'Region',
                    'Population_fmt': 'Population',
                    'Change_fmt': 'Change'
                }
            )

            # 컬러 스타일 함수 정의
            def highlight_change(val):
                try:
                    val = int(val.replace(',', ''))
                except:
                    return ''
                if val > 0:
                    return f'background-color: rgba(0, 120, 255, {min(val / top100["Change"].max(), 1):.5f})'
                elif val < 0:
                    return f'background-color: rgba(255, 0, 0, {min(abs(val) / abs(top100["Change"].min()), 1):.5f})'
                else:
                    return ''

            # 컬러 스타일 적용
            styled_df = display_df.style.applymap(highlight_change, subset=['Change'])

            # 제목 출력
            st.title("Top 100 Population Change Records by Region and Year")
            st.write("This table highlights the top 100 year-over-year population changes across all regions (excluding national total).")

            # 테이블 출력
            st.dataframe(styled_df, use_container_width=True)



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