import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 폰트 설정 (Colab/Docker 환경 대응, 필요시 로컬 폰트 경로 지정)
plt.rcParams['font.family'] = 'NanumGothic' # 또는 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 1. 표준 스크류 데이터 및 설계 권장치 (예시 데이터)
# 실제 프로젝트에서는 인터넷에서 수집한 ISO/JIS 규격 테이블을 CSV로 불러와서 사용하세요.
screw_data = {
    'M2.6 (Plastic Tapping)': {'d_ext': 2.6, 'd_core': 1.9, 'pitch': 1.1, 'rec_boss_id_ratio': [0.75, 0.85]},
    'M3 (Plastic Tapping)': {'d_ext': 3.0, 'd_core': 2.3, 'pitch': 1.3, 'rec_boss_id_ratio': [0.75, 0.85]},
    'M3.5 (Plastic Tapping)': {'d_ext': 3.5, 'd_core': 2.7, 'pitch': 1.4, 'rec_boss_id_ratio': [0.75, 0.85]},
    'M4 (Plastic Tapping)': {'d_ext': 4.0, 'd_core': 3.2, 'pitch': 1.6, 'rec_boss_id_ratio': [0.75, 0.85]},
    'M3 (Machine Screw)': {'d_ext': 3.0, 'd_core': 2.5, 'pitch': 0.5},
    'M4 (Machine Screw)': {'d_ext': 4.0, 'd_core': 3.3, 'pitch': 0.7},
}

# 재질 물성 데이터
material_data = {
    'ABS': {'strength': 45, 'modulus': 2300, 'poisson': 0.39},
    'PC': {'strength': 65, 'modulus': 2400, 'poisson': 0.37},
    'POM': {'strength': 60, 'modulus': 2600, 'poisson': 0.35},
}

st.set_page_config(layout="wide") # 와이드 모드로 설정

st.title("🔩 기구설계 스크류 체결 파손 해석 및 시각화 Tool")
st.markdown("---")

# 레이아웃 분할: 왼쪽 (입력), 오른쪽 (가이드 및 결과)
col_in, col_guide = st.columns([1, 1.2])

# ==========================================
# 왼쪽 사이드바: 입력 설정
# ==========================================
with col_in:
    st.header("1. 체결 조건 입력")
    target_material_type = st.radio("체결 대상물 구분", ["플라스틱(사출 보스)", "프레스(금속 판재)"])
    
    # 1. 스크류 선택
    st.subheader("스크류 선택")
    if target_material_type == "플라스틱(사출 보스)":
        plastic_screws = [k for k in screw_data.keys() if 'Plastic' in k]
        selected_screw = st.selectbox("스크류 규격 (TAP)", plastic_screws)
    else:
        metal_screws = [k for k in screw_data.keys() if 'Machine' in k]
        selected_screw = st.selectbox("스크류 규격 (Machine)", metal_screws)
        
    screw_info = screw_data[selected_screw]

    # 2. 상세 치수 및 물성 설정 (사출물일 때)
    st.subheader("상세 설계 치수 및 물성")
    input_torque = st.number_input("체결 토크 (N·m)", min_value=0.01, value=1.0, step=0.05)
    
    if target_material_type == "플라스틱(사출 보스)":
        plastic_mat = st.selectbox("보스 재질", list(material_data.keys()))
        mat_info = material_data[plastic_mat]
        
        # 사용자가 직접 입력하는 설계 치수
        st.write("---")
        st.markdown("**사용자 설계 입력:**")
        boss_od = st.number_input("보스 외경 (mm) - [Do]", value=screw_info['d_ext'] * 2.2, step=0.1)
        
        # 가이드를 보고 입력하게 유도
        st.info(f"👉 오른쪽 가이드의 권장 내경 범위를 참고하여 입력하세요.")
        boss_id = st.number_input("보스 내경 (mm) - [Di]", value=screw_info['d_ext'] * 0.8, step=0.05)
        
    # 해석 실행 버튼
    run_analysis = st.button("해석 및 시각화 실행")

# ==========================================
# 오른쪽: 설계 가이드 미리보기 및 결과 시각화
# ==========================================
with col_guide:
    st.header("2. 설계 가이드 및 해석 결과")
    
    # --- 스크류 선택 시 미리보여주는 설계 가이드 ---
    st.subheader("📍 선택된 스크류 표준 규격 및 설계 권장치")
    
    # 데이터프레임으로 정리하여 표로 보여줌
    guide_df = pd.DataFrame([screw_info])
    guide_df = guide_df.rename(columns={'d_ext': '외경(d)', 'd_core': '골지름(d1)', 'pitch': '피치(P)'})
    
    if target_material_type == "플라스틱(사출 보스)":
        # 권장 보스 내경 계산 (C-수치: 보통 d_core ~ 0.85*d_ext 사이)
        rec_id_min = screw_info['d_ext'] * screw_info['rec_boss_id_ratio'][0]
        rec_id_max = screw_info['d_ext'] * screw_info['rec_boss_id_ratio'][1]
        guide_df['권장 보스 내경 (Di)'] = f"{rec_id_min:.2f} ~ {rec_id_max:.2f} mm"
        
        # 권장 보스 외경 (보통 d_ext의 2.0~2.5배)
        guide_df['권장 보스 외경 (Do)'] = f"{screw_info['d_ext']*2.0:.1f} ~ {screw_info['d_ext']*2.5:.1f} mm"
        
        st.dataframe(guide_df.style.highlight_max(axis=1), use_container_width=True)
        st.caption("※ 권장 내경은 일반적인 사출물(ABS/PC 등)에 대한 표준 지침입니다.")
    
    else:
        # 프레스물 가이드 (M-스크류)
        guide_df['유효 물림 길이 (Le, min)'] = f"2.5 * P = {screw_info['pitch']*2.5:.2f} mm"
        st.dataframe(guide_df, use_container_width=True)


    # --- 해석 결과 및 시각화 ---
    st.markdown("---")
    if run_analysis:
        if target_material_type == "플라스틱(사출 보스)":
            st.subheader("📊 플라스틱 보스 파손 해석 (구조 해석)")
            
            # [물리 모델 계산]
            # 1. 스크류 진입에 의한 내부 압력 (P) 추정 (간략화된 압입 이론 사용)
            interference = (screw_info['d_ext'] - boss_id) / 2 # 반경 방향 간섭량
            
            # 탄성학 이론에 기반한 후프 응력(Hoop Stress) 계산
            # 실제로는 재질의 탄성계수(E), 포아송비(v), 보스 외경/내경 비율에 따라 결정됨
            E = mat_info['modulus']
            v = mat_info['poisson']
            r_i = boss_id / 2
            r_o = boss_od / 2
            
            # 간략화된 압력 공식 (E-Mat 및 Do/Di 비율 고려)
            try:
                # 보스가 벌어지는 압력 P
                pressure_p = (E * interference / r_i) * ((r_o**2 - r_i**2) / (r_o**2 + r_i**2 + (v * (r_o**2 - r_i**2))))
                
                # 최대 훕 응력 (Hoop Stress, 인장) - 보스 내벽에서 발생
                max_hoop_stress = pressure_p * ((r_o**2 + r_i**2) / (r_o**2 - r_i**2))
            except ZeroDivisionError:
                max_hoop_stress = 1000 # 설계 잘못 (내경=외경)
            
            # 2. 결과 출력 및 파손 여부 판단
            col_res1, col_res2 = st.columns(2)
            
            # 안전율 계산
            safety_factor = mat_info['strength'] / max_hoop_stress
            
            with col_res1:
                st.metric("발생 최대 Hoop 응력", f"{max_hoop_stress:.1f} MPa")
                if max_hoop_stress > mat_info['strength']:
                    st.error(f"❌ 파손 위험! (안전율: {safety_factor:.2f})")
                else:
                    st.success(f"✅ 안전함 (안전율: {safety_factor:.2f})")
            
            with col_res2:
                st.metric(f"{plastic_mat} 인장 강도", f"{mat_info['strength']} MPa")
            
            # 3. 파손 여부 시각화 (그래프)
            st.markdown("**[시각화] 응력 대조 및 파손 분포**")
            
            fig, ax = plt.subplots(1, 2, figsize=(10, 4))
            
            # 그래프 1: 막대그래프로 응력 비교
            labels = ['발생 응력 (max)', f'{plastic_mat} 인장 강도']
            values = [max_hoop_stress, mat_info['strength']]
            colors = ['red' if max_hoop_stress > mat_info['strength'] else 'green', 'gray']
            
            sns.barplot(x=labels, y=values, palette=colors, ax=ax[0])
            ax[0].set_ylabel("응력 (MPa)")
            ax[0].set_title("응력 대조 확인")
            
            # 그래프 2: 보스 단면의 응력 분포 (간략 시각화)
            # radial_stress_dist = ... (실제 반경 방향 응력 분포 계산 코드가 들어갈 자리)
            # 여기서는 개념적으로만 보여줌
            circle_radius = r_o
            circle_color = 'red' if max_hoop_stress > mat_info['strength'] else 'blue'
            
            circle = plt.Circle((0, 0), circle_radius, color=circle_color, fill=False, linewidth=2)
            ax[1].add_patch(circle)
            inner_circle = plt.Circle((0, 0), r_i, color='black', fill=True)
            ax[1].add_patch(inner_circle)
            
            ax[1].set_xlim(-r_o*1.2, r_o*1.2)
            ax[1].set_ylim(-r_o*1.2, r_o*1.2)
            ax[1].set_aspect('equal', adjustable='box')
            ax[1].set_title(f"보스 단면 응력 (D={boss_od}mm)")
            ax[1].axis('off') # 축 숨기기
            
            st.pyplot(fig)

        else:
            st.subheader("🔩 프레스 금속물 해석 (개념)")
            st.info("프레스물(금속)에 대한 전단 파손 및 토크 해석 로직은 여기에 구현됩니다.")
            st.warning("이 버전에서는 사출물 파손 시각화에 집중합니다.")

