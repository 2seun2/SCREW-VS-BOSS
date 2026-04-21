import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 페이지 설정
st.set_page_config(page_title="스크류 설계 해석 툴", layout="wide")

# 1. 표준 스크류 데이터베이스
SCREW_DB = {
    'M2.0 (플라스틱용)': {'d_ext': 2.0, 'd_core': 1.5, 'pitch': 0.8, 'ratio': [0.75, 0.85]},
    'M2.6 (플라스틱용)': {'d_ext': 2.6, 'd_core': 1.9, 'pitch': 1.1, 'ratio': [0.75, 0.85]},
    'M3.0 (플라스틱용)': {'d_ext': 3.0, 'd_core': 2.3, 'pitch': 1.3, 'ratio': [0.75, 0.85]},
    'M4.0 (플라스틱용)': {'d_ext': 4.0, 'd_core': 3.2, 'pitch': 1.6, 'ratio': [0.75, 0.85]},
    'M3.0 (기계나사)': {'d_ext': 3.0, 'd_core': 2.5, 'pitch': 0.5},
    'M4.0 (기계나사)': {'d_ext': 4.0, 'd_core': 3.3, 'pitch': 0.7},
}

# 재질 데이터베이스
MAT_DB = {
    'ABS': {'strength': 45, 'modulus': 2300, 'poisson': 0.39},
    'PC': {'strength': 65, 'modulus': 2400, 'poisson': 0.37},
    'POM': {'strength': 60, 'modulus': 2600, 'poisson': 0.35},
}

st.title("🔩 기구설계 스크류 체결 구조 해석 툴")
st.markdown("사용자 정의 **안전율**을 기반으로 보스 파손 가능성을 정밀 검토합니다.")

# 화면 레이아웃
col_in, col_res = st.columns([1, 1.5])

with col_in:
    st.header("1. 체결 조건 입력")
    mode = st.radio("대상물 종류", ["사출물 (보스)", "금속물 (프레스)"])
    
    is_plastic = mode == "사출물 (보스)"
    screw_list = [k for k in SCREW_DB.keys() if ("플라스틱" if is_plastic else "기계나사") in k]
    selected_screw = st.selectbox("스크류 표준 규격 선택", screw_list)
    spec = SCREW_DB[selected_screw]
    
    st.divider()
    
    if is_plastic:
        mat_name = st.selectbox("보스 재질 선택", list(MAT_DB.keys()))
        mat = MAT_DB[mat_name]
        
        st.subheader("보스 상세 설계")
        rec_min = spec['d_ext'] * spec['ratio'][0]
        rec_max = spec['d_ext'] * spec['ratio'][1]
        st.caption(f"💡 {selected_screw} 권장 내경: {rec_min:.2f} ~ {rec_max:.2f} mm")
        
        boss_od = st.number_input("보스 외경 (Do) [mm]", value=spec['d_ext']*2.2, step=0.1)
        boss_id = st.number_input("보스 내경 (Di) [mm]", value=spec['d_ext']*0.8, step=0.05)
        
        # --- 안전율 설정 추가 ---
        st.divider()
        st.subheader("해석 기준 설정")
        target_sf = st.slider("목표 안전율 (Target Safety Factor)", min_value=1.0, max_value=5.0, value=2.0, step=0.1)
        st.caption(f"기준: 발생 응력 × {target_sf} < 재질 강도")

        if boss_id >= spec['d_ext']:
            st.error(f"❗ 내경이 스크류 외경({spec['d_ext']})보다 큽니다.")
            
    torque = st.number_input("체결 토크 (N·m)", value=0.5, step=0.1)
    run_btn = st.button("해석 실행", type="primary", use_container_width=True)

with col_res:
    st.header("2. 해석 결과 및 가이드")
    
    # 가이드 표
    info_df = pd.DataFrame({
        "항목": ["외경(d)", "골지름(d1)", "피치(P)", "권장 내경"],
        "치수": [f"{spec['d_ext']} mm", f"{spec['d_core']} mm", f"{spec['pitch']} mm", 
                 f"{rec_min:.2f}~{rec_max:.2f} mm" if is_plastic else "N/A"]
    })
    st.table(info_df)

    if run_btn and is_plastic:
        # --- 정밀 구조 해석 ---
        interference = (spec['d_ext'] - boss_id) / 2
        ri, ro = boss_id / 2, boss_od / 2
        
        if ro <= ri:
            st.error("보스 외경이 내경보다 작습니다.")
        elif interference <= 0:
            st.error("간섭량이 0 이하입니다.")
        else:
            E, v = mat['modulus'], mat['poisson']
            pressure = (E * interference / ri) * ((ro**2 - ri**2) / (ro**2 + ri**2 + v*(ro**2 - ri**2)))
            max_stress = pressure * ((ro**2 + ri**2) / (ro**2 - ri**2))
            
            # 계산된 실제 안전율
            calculated_sf = mat['strength'] / max_stress
            
            # 메트릭 출력
            m1, m2, m3 = st.columns(3)
            m1.metric("최대 발생 응력", f"{max_stress:.1f} MPa")
            m2.metric("실제 안전율", f"{calculated_sf:.2f}")
            m3.metric("목표 안전율", f"{target_sf}")

            # 시각화
            fig, ax = plt.subplots(1, 2, figsize=(10, 4))
            
            # 1. 응력 막대 그래프 (목표 안전율에 따른 색상 변경)
            # 재질 강도를 목표 안전율로 나눈 값이 '허용 응력'
            allowable_stress = mat['strength'] / target_sf
            
            is_safe = calculated_sf >= target_sf
            bar_colors = ['#2eb82e' if is_safe else '#ff4b4b', '#808080']
            
            ax[0].bar(['Applied Stress', 'Material Strength'], [max_stress, mat['strength']], color=bar_colors)
            # 허용 응력 라인 표시
            ax[0].axhline(allowable_stress, color='blue', linestyle='--', label='Allowable Limit')
            ax[0].set_title(f"Stress Analysis (Target SF: {target_sf})")
            ax[0].legend()

            # 2. 보스 단면 시각화
            boss_c = plt.Circle((0, 0), ro, color='#e0e0e0')
            hole_c = plt.Circle((0, 0), ri, color='white')
            screw_c = plt.Circle((0, 0), spec['d_ext']/2, color='#1f77b4', alpha=0.4)
            
            ax[1].add_patch(boss_c)
            ax[1].add_patch(hole_c)
            ax[1].add_patch(screw_c)
            limit = ro * 1.5
            ax[1].set_xlim(-limit, limit); ax[1].set_ylim(-limit, limit)
            ax[1].set_aspect('equal')
            ax[1].axis('off')
            ax[1].set_title(f"Section (Real SF: {calculated_sf:.2f})")
            
            st.pyplot(fig)

            # 결과 메시지
            if calculated_sf < 1.0:
                st.error(f"❌ **파손 확정**: 안전율이 1.0 미만({calculated_sf:.2f})입니다. 즉시 설계를 수정하십시오.")
            elif calculated_sf < target_sf:
                st.warning(f"⚠️ **기준 미달**: 안전율이 목표치({target_sf})보다 낮은 {calculated_sf:.2f}입니다. 신뢰성 보장을 위해 보스 두께를 키우는 것을 권장합니다.")
            else:
                st.success(f"✅ **설계 합격**: 안전율 {calculated_sf:.2f}로 목표치({target_sf})를 충족합니다.")
