import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 설정: 페이지 레이아웃 및 제목
st.set_page_config(page_title="Screw Design Tool", layout="wide")

# 1. 스크류 표준 데이터베이스
SCREW_DB = {
    'M2.0 (Plastic)': {'d_ext': 2.0, 'd_core': 1.5, 'pitch': 0.8, 'ratio': [0.75, 0.85]},
    'M2.6 (Plastic)': {'d_ext': 2.6, 'd_core': 1.9, 'pitch': 1.1, 'ratio': [0.75, 0.85]},
    'M3.0 (Plastic)': {'d_ext': 3.0, 'd_core': 2.3, 'pitch': 1.3, 'ratio': [0.75, 0.85]},
    'M4.0 (Plastic)': {'d_ext': 4.0, 'd_core': 3.2, 'pitch': 1.6, 'ratio': [0.75, 0.85]},
    'M3.0 (Machine)': {'d_ext': 3.0, 'd_core': 2.5, 'pitch': 0.5},
    'M4.0 (Machine)': {'d_ext': 4.0, 'd_core': 3.3, 'pitch': 0.7},
}

MAT_DB = {
    'ABS': {'strength': 45, 'modulus': 2300, 'poisson': 0.39},
    'PC': {'strength': 65, 'modulus': 2400, 'poisson': 0.37},
    'POM': {'strength': 60, 'modulus': 2600, 'poisson': 0.35},
}

st.title("🔩 Screw Fastening Analysis Tool")
st.markdown("Structure analysis for Plastic Boss & Press Plate")

# 레이아웃 배치
col_in, col_res = st.columns([1, 1.5])

with col_in:
    st.header("Input Parameters")
    mode = st.radio("Target Material", ["Plastic Boss", "Press Plate"])
    
    # 스크류 선택 필터링
    screw_list = [k for k in SCREW_DB.keys() if ("Plastic" if mode == "Plastic Boss" else "Machine") in k]
    selected_screw = st.selectbox("Select Screw Standard", screw_list)
    spec = SCREW_DB[selected_screw]
    
    torque = st.number_input("Torque (Nm)", value=1.0, step=0.1)
    
    if mode == "Plastic Boss":
        mat_name = st.selectbox("Material", list(MAT_DB.keys()))
        mat = MAT_DB[mat_name]
        
        st.divider()
        st.info(f"Check the Guide on the right for Boss ID/OD")
        boss_od = st.number_input("Boss Outer Diameter (Do) [mm]", value=spec['d_ext']*2.2)
        boss_id = st.number_input("Boss Inner Diameter (Di) [mm]", value=spec['d_ext']*0.8)
    
    run_btn = st.button("Run Analysis", type="primary")

with col_res:
    st.header("Design Guide & Result")
    
    # 오른쪽 상단: 스크류 가이드 표
    guide_data = {
        "Property": ["Outer Dia(d)", "Core Dia(d1)", "Pitch(P)", "Rec. Boss ID"],
        "Value": [
            f"{spec['d_ext']} mm", 
            f"{spec['d_core']} mm", 
            f"{spec['pitch']} mm",
            f"{spec.get('ratio', [0,0])[0]*spec['d_ext']:.2f} ~ {spec.get('ratio', [0,0])[1]*spec['d_ext']:.2f} mm" if mode == "Plastic Boss" else "N/A"
        ]
    }
    st.table(pd.DataFrame(guide_data))

    if run_btn:
        if mode == "Plastic Boss":
            # --- 구조 해석 로직 (Hoop Stress) ---
            interference = (spec['d_ext'] - boss_id) / 2
            ri, ro = boss_id / 2, boss_od / 2
            
            if ro <= ri:
                st.error("Error: Outer diameter must be larger than inner diameter.")
            else:
                # Lame's equation for thick-walled cylinders
                # Pressure P due to interference
                E, v = mat['modulus'], mat['poisson']
                pressure = (E * interference / ri) * ((ro**2 - ri**2) / (ro**2 + ri**2 + v*(ro**2 - ri**2)))
                max_stress = pressure * ((ro**2 + ri**2) / (ro**2 - ri**2))
                safety_factor = mat['strength'] / max_stress
                
                # 결과 출력
                c1, c2 = st.columns(2)
                c1.metric("Max Hoop Stress", f"{max_stress:.1f} MPa")
                c2.metric("Safety Factor", f"{safety_factor:.2f}")

                # 시각화
                fig, ax = plt.subplots(1, 2, figsize=(10, 4))
                
                # Bar Chart
                bars = ax[0].bar(['Applied Stress', 'Limit (Yield)'], [max_stress, mat['strength']], 
                                 color=['red' if safety_factor < 1 else 'green', 'gray'])
                ax[0].set_title("Stress Comparison")
                ax[0].set_ylabel("Stress (MPa)")

                # Cross-section visualization
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
                ax[1].set_title(f"Boss Section (SF: {safety_factor:.2f})")
                
                if safety_factor < 1:
                    st.error("⚠️ CRITICAL: Boss Crack Predicted!")
                else:
                    st.success("✅ SAFE: Design is within material limits.")
                
                st.pyplot(fig)
        else:
            st.write("Press Plate analysis logic is under development.")
