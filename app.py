import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 페이지 설정
st.set_page_config(page_title="스크류 체결 해석 툴", layout="wide")

# 1. 스크류 표준 데이터베이스 (표준 규격 및 설계 권장치)
SCREW_DB = {
    'M2.0 (플라스틱용)': {'d_ext': 2.0, 'd_core': 1.5, 'pitch': 0.8, 'ratio': [0.75, 0.85]},
    'M2.6 (플라스틱용)': {'d_ext': 2.6, 'd_core': 1.9, 'pitch': 1.1, 'ratio': [0.75, 0.85]},
    'M3.0 (플라스틱용)': {'d_ext': 3.0, 'd_core': 2.3, 'pitch': 1.3, 'ratio': [0.75, 0.85]},
    'M4.0 (플라스틱용)': {'d_ext': 4.0, 'd_core': 3.2, 'pitch': 1.6, 'ratio': [0.75, 0.85]},
    'M3.0 (기계나사/금속)': {'d_ext': 3.0, 'd_core': 2.5, 'pitch': 0.5},
    'M4.0 (기계나사/금속)': {'d_ext': 4.0, 'd_core': 3.3, 'pitch': 0.7},
}

# 재질 데이터베이스
MAT_DB = {
    'ABS (일반)': {'strength': 45, 'modulus': 2300, 'poisson': 0.39},
    'PC (고강도)': {'strength': 65, 'modulus': 2400, 'poisson': 0.37},
    'POM (내마모)': {'strength': 60, 'modulus': 2600, 'poisson': 0.35},
}

st.title("🔩 기구설계 스크류 체결 구조 해석 툴")
st.markdown("사출 보스 및 프레스 판재의 체결 안전성을 확인합니다.")

# 화면 레이아웃 분할
col_in, col_res = st.columns([1, 1.5])

with col_in:
    st.header("입력 파라미터")
    mode = st.radio("체결 대상 재질", ["사출물 (보스)", "금속물 (프레스)"])
    
    # 모드에 따른 스크류 필터링
    screw_list = [k for k in SCREW_DB.keys() if ("플라스틱" if mode == "사출물 (보스)" else "기계나사") in k]
    selected_screw = st.selectbox("스크류 규격 선택", screw_list)
    spec = SCREW_DB[selected_screw]
    
    torque = st.number_input("설정 토크 (Nm)", value=1.0, step=0.1)
    
    if mode == "사출물 (보스)":
        mat_name = st.selectbox("보스 재질", list(MAT_DB.keys()))
        mat = MAT_DB[mat_name]
        
        st.divider()
        st.info("💡 오른쪽의 설계 가이드를 참고하여 내경/외경을 입력하세요.")
        boss_od = st.number_input("보스 외경 (Do) [mm]", value=spec['d_ext']*2.2)
        boss_id = st.number_input("보스 내경 (Di) [mm]", value=spec['d_ext']*0.8)
    
    run_btn = st.button("해석 실행", type="primary")

with col_res:
    st.header("설계 가이드 및 결과")
    
    # 1. 스크류 설계 가이드 표
    guide_data = {
        "항목": ["외경(d)", "골지름(d1)", "피치(P)", "권장 보스 내경"],
        "규격 치수": [
            f"{spec['d_ext']} mm", 
            f"{spec['d_core']} mm", 
            f"{spec['pitch']} mm",
            f"{spec.get('ratio', [0,0])[0]*spec['d_ext']:.2f} ~ {spec.get('ratio', [0,0])[1]*spec['d_ext']:.2f} mm" if mode == "사출물 (보스)" else "해당 없음"
        ]
    }
    st.table(pd.DataFrame(guide_data))

    if run_btn:
        if mode == "사출물 (보스)":
            # --- 구조 해석 로직 (후프 응력) ---
            interference = (spec['d_ext'] - boss_id) / 2  # 반경방향 겹침량
            ri, ro = boss_id / 2, boss_od / 2
            
            if ro <= ri:
                st.error("오류: 외경은 내경보다 커야 합니다.")
            else:
                # 두꺼운 원통 이론(Lame's equation) 적용
                E, v = mat['modulus'], mat['poisson']
                # 압입에 의한 내압(P) 계산
                pressure = (E * interference / ri) * ((ro**2 - ri**2) / (ro**2 + ri**2 + v*(ro**2 - ri**2)))
                # 최대 후프 응력 (내벽 발생)
                max_stress = pressure * ((ro**2 + ri**2) / (ro**2 - ri**2))
                safety_factor = mat['strength'] / max_stress
                
                # 결과 지표 출력
                c1, c2 = st.columns(2)
                c1.metric("발생 최대 응력", f"{max_stress:.1f} MPa")
                c2.metric("안전율 (SF)", f"{safety_factor:.2f}")

                # 시각화 (그래프)
                fig, ax = plt.subplots(1, 2, figsize=(10, 4))
                
                # 그래프 1: 응력 비교
                ax[0].bar(['Applied Stress', 'Material Limit'], [max_stress, mat['strength']], 
                                 color=['red' if safety_factor < 1 else 'green', 'gray'])
                ax[0].set_title("Stress Comparison")
                ax[0].set_ylabel("Stress (MPa)")

                # 그래프 2: 보스 단면 시각화
                boss_circle = plt.Circle((0, 0), ro, color='lightgray', label='Boss OD')
                hole_circle = plt.Circle((0, 0), ri, color='white')
                screw_circle = plt.Circle((0, 0), spec['d_ext']/2, color='blue', alpha=0.3, label='Screw')
                
                ax[1].add_patch(boss_circle)
                ax[1].add_patch(hole_circle)
                ax[1].add_patch(screw_circle)
                limit = ro * 1.3
                ax[1].set_xlim(-limit, limit); ax[1].set_ylim(-limit, limit)
                ax[1].set_aspect('equal')
                ax[1].axis('off')
                ax[1].set_title(f"Section View (SF: {safety_factor:.2f})")
                
                st.pyplot(fig)

                if safety_factor < 1:
                    st.error(f"⚠️ 경고: {mat_name}의 허용 강도를 초과했습니다! 보스 균열(Crack) 가능성이 매우 높습니다.")
                elif safety_factor < 1.5:
                    st.warning("⚠️ 주의: 안전율이 낮습니다. 설계 치수 변경을 검토하세요.")
                else:
                    st.success("✅ 안전: 현재 설계는 구조적으로 안정적입니다.")
        else:
            st.info("프레스(금속) 모드는 현재 준비 중입니다. 나사산 전단 강도 해석이 추가될 예정입니다.")
