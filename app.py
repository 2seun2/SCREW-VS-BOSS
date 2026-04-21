import streamlit as st
import pandas as pd
import numpy as np

# 1. 표준 스크류 데이터 (예시)
screw_data = {
    'M3 (Plastic)': {'d_ext': 3.0, 'd_core': 2.4, 'pitch': 1.06},
    'M4 (Plastic)': {'d_ext': 4.0, 'd_core': 3.2, 'pitch': 1.34},
    'M3 (Machine)': {'d_ext': 3.0, 'd_core': 2.5, 'pitch': 0.5},
}

st.title("🔩 기구설계 스크류 체결 시뮬레이터")

# Sidebar - 입력 설정
with st.sidebar:
    st.header("입력 파라미터")
    target_material = st.selectbox("체결 대상물", ["플라스틱(사출)", "프레스(금속)"])
    screw_type = st.selectbox("스크류 선택", list(screw_data.keys()))
    torque = st.number_input("전동기 토크 (Nm)", min_value=0.1, value=1.5)
    
    if target_material == "플라스틱(사출)":
        boss_od = st.number_input("보스 외경 (mm)", value=6.0)
        boss_id = st.number_input("보스 내경 (mm)", value=2.6)
        material_strength = st.slider("재질 인장 강도 (MPa) - ABS: 40, PC: 60", 10, 100, 45)

# 2. 계산 로직 (간략화된 물리 모델)
axial_force = torque / (0.2 * screw_data[screw_type]['d_ext'] / 1000) # 간단한 토크-축력 환산 식

# 3. 결과 출력
st.subheader("📊 해석 결과")
col1, col2 = st.columns(2)

if target_material == "플라스틱(사출)":
    # 보스 내부 압력 추정 및 응력 계산
    interference = (screw_data[screw_type]['d_ext'] - boss_id) / 2
    # 간략화된 훕 응력 계산
    stress = (interference * 2000) / boss_od # 예시 계수
    
    col1.metric("발생 최대 응력", f"{round(stress, 2)} MPa")
    
    if stress > material_strength:
        st.error("⚠️ 파손 위험: 보스 외벽에 균열(Crack)이 발생할 가능성이 매우 높습니다.")
    else:
        st.success("✅ 안전: 설계 치수가 적절합니다.")

# 4. 시각화 (보스 단면도 등)
# 
