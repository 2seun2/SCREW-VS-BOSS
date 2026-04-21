import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 페이지 설정
st.set_page_config(page_title="스크류 설계 해석 툴", layout="wide")

# 1. 표준 스크류 데이터베이스 (표준 규격 및 설계 권장치)
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
st.markdown("사출 보스의 **파손 가능성** 및 **응력 분포**를 정밀하게 시뮬레이션합니다.")

# 화면 레이아웃
col_in, col_res = st.columns([1, 1.5])

with col_in:
    st.header("1. 체결 조건 입력")
    mode = st.radio("대상물 종류", ["사출물 (보스)", "금속물 (프레스)"])
    
    # 스크류 필터링
    is_plastic = mode == "사출물 (보스)"
    screw_list = [k for k in SCREW_DB.keys() if ("플라스틱" if is_plastic else "기계나사") in k]
    selected_screw = st.selectbox("스크류 표준 규격 선택", screw_list)
    spec = SCREW_DB[selected_screw]
    
    st.divider()
    
    if is_plastic:
        mat_name = st.selectbox("보스 재질 선택", list(MAT_DB.keys()))
        mat = MAT_DB[mat_name]
        
        # 보스 설계 치수 입력
        st.subheader("보스 상세 설계")
        # 가이드라인 제시
        rec_min = spec['d_ext'] * spec['ratio'][0]
        rec_max = spec['d_ext'] * spec['ratio'][1]
        st.caption(f"💡 {selected_screw} 권장 내경: {rec_min:.2f} ~ {rec_max:.2f} mm")
        
        boss_od = st.number_input("보스 외경 (Do) [mm]", value=spec['d_ext']*2.2, step=0.1)
        boss_id = st.number_input("보스 내경 (Di) [mm]", value=spec['d_ext']*0.8, step=0.05)
        
        # 에러 체크 로직
        if boss_id >= spec['d_ext']:
            st.error(f"❗ 내경({boss_id})이 스크류 외경({spec['d_ext']})보다 큽니다. 체결이 불가능합니다.")
        elif boss_id <= spec['d_core']:
            st.warning(f"⚠️ 내경이 너무 작습니다. 스크류 골지름({spec['d_core']})보다 커야 조립이 용이합니다.")
            
    torque = st.number_input("체결 토크 (N·m)", value=0.5, step=0.1)
    run_btn = st.button("해석 실행", type="primary", use_container_width=True)

with col_res:
    st.header("2. 해석 결과 및 가이드")
    
    # 스크류 정보 표
    info_df = pd.DataFrame({
        "항목": ["외경(d)", "골지름(d1)", "피치(P)", "권장 내경 범위"],
        "치수": [f"{spec['d_ext']} mm", f"{spec['d_core']} mm", f"{spec['pitch']} mm", 
                 f"{rec_min:.2f}~{rec_max:.2f} mm" if is_plastic else "N/A"]
    })
    st.table(info_df)

    if run_btn and is_plastic:
        # --- 정밀 구조 해석 (Lame's Thick Cylinder Theory) ---
        interference = (spec['d_ext'] - boss_id) / 2 # 반경 방향 겹침량
        ri, ro = boss_id / 2, boss_od / 2
        
        if ro <= ri:
            st.error("보스 외경이 내경보다 작습니다. 치수를 확인하세요.")
        elif interference <= 0:
            st.error("간섭량이 0 이하입니다. 스크류가 보스에 박히지 않습니다.")
        else:
            # 탄성학 수식 적용
            E, v = mat['modulus'], mat['poisson']
            # 내압 P 계산
            pressure = (E * interference / ri) * ((ro**2 - ri**2) / (ro**2 + ri**2 + v*(ro**2 - ri**2)))
            # 최대 후프 응력 (내벽에서 발생)
            max_stress = pressure * ((ro**2 + ri**2) / (ro**2 - ri**2))
            safety_factor = mat['strength'] / max_stress
            
            # 메트릭 출력
            m1, m2, m3 = st.columns(3)
            m1.metric("최대 발생 응력", f"{max_stress:.1f} MPa")
            m2.metric("재질 허용 강도", f"{mat['strength']} MPa")
            m3.metric("안전율", f"{safety_factor:.2f}")

            # 시각화
            fig, ax = plt.subplots(1, 2, figsize=(10, 4))
            
            # 1. 응력 막대 그래프
            colors = ['#ff4b4b' if safety_factor < 1.2 else '#2eb82e', '#808080']
            ax[0].bar(['Applied', 'Limit'], [max_stress, mat['strength']], color=colors)
            ax[0].set_title("Stress vs Strength")
            ax[0].set_ylabel("Stress (MPa)")

            # 2. 보스 단면 시각화
            boss_c = plt.Circle((0, 0), ro, color='#e0e0e0', label='Boss')
            hole_c = plt.Circle((0, 0), ri, color='white')
            screw_c = plt.Circle((0, 0), spec['d_ext']/2, color='#1f77b4', alpha=0.4, label='Screw')
            
            ax[1].add_patch(boss_c)
            ax[1].add_patch(hole_c)
            ax[1].add_patch(screw_c)
            limit = ro * 1.5
            ax[1].set_xlim(-limit, limit); ax[1].set_ylim(-limit, limit)
            ax[1].set_aspect('equal')
            ax[1].axis('off')
            ax[1].set_title(f"Section View (Safety: {safety_factor:.2f})")
            
            st.pyplot(fig)

            # 결과 리포트
            if safety_factor < 1.0:
                st.error(f"❌ **파손 위험 매우 높음**: 발생 응력이 재질 강도를 초과했습니다. 보스 외경을 키우거나 내경을 넓히십시오.")
            elif safety_factor < 1.5:
                st.warning(f"⚠️ **주의**: 안전율이 {safety_factor:.2f}로 낮습니다. 사출 조건에 따라 균열이 발생할 수 있습니다.")
            else:
                st.success(f"✅ **안전**: 설계 치수가 적절합니다. 안정적인 체결이 예상됩니다.")
                
    elif run_btn and not is_plastic:
        st.info("금속 프레스 판재 해석 모드는 준비 중입니다. (나사산 전단 강도 로직 적용 예정)")
