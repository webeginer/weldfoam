import streamlit as st
import requests
import numpy as np
import matplotlib.pyplot as plt
import json
import os


API_URL = "http://localhost:8000"

# Если запущено на Render (есть переменная окружения RENDER) — берём API_URL из окружения
if os.getenv("RENDER"):
    API_URL = os.getenv("API_URL", "https://weldfoam-ui.onrender.com")
# Если есть локальный secrets.toml — используем его для переопределения (удобно для отладки)
elif os.path.exists(".streamlit/secrets.toml"):
    try:
        API_URL = st.secrets.get("API_URL", API_URL)
    except:
        pass

# Для отладки (показывает текущий адрес API в сайдбаре)
st.sidebar.caption(f"🌐 API: {API_URL}")

st.set_page_config(
    page_title="WeldFOAM - Калькулятор сварочных деформаций",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 WeldFOAM - Калькулятор сварочных деформаций")
st.markdown("### Полный расчёт: нагрев + остывание")

# Боковая панель с параметрами
with st.sidebar:
    st.header("📊 Параметры модели")
    
    # ========== РЕЖИМ СВАРКИ ==========
    st.subheader("⚡ Режим сварки")
    col1, col2 = st.columns(2)
    with col1:
        I_A = st.number_input("Ток I (А)", value=150.0, min_value=50.0, max_value=500.0, step=10.0)
        v_ms = st.number_input("Скорость v (м/с)", value=0.003, min_value=0.001, max_value=0.02, step=0.001, format="%.4f")
        st.caption("Пример: 0.003 м/с = 0.3 см/с")
    with col2:
        U_V = st.number_input("Напряжение U (В)", value=25.0, min_value=20.0, max_value=40.0, step=1.0)
        eta = st.number_input("КПД дуги η", value=0.75, min_value=0.6, max_value=0.9, step=0.05, format="%.2f")
    
    # ========== ГЕОМЕТРИЯ ==========
    st.subheader("📐 Геометрия")
    col1, col2, col3 = st.columns(3)
    with col1:
        h_mm = st.number_input("Высота h (мм)", value=100.0, min_value=20.0, max_value=500.0, step=10.0)
        h_m = h_mm / 1000.0
        st.caption(f"= {h_m:.3f} м")
    with col2:
        delta_mm = st.number_input("Толщина δ (мм)", value=4.0, min_value=1.0, max_value=20.0, step=1.0)
        delta_m = delta_mm / 1000.0
        st.caption(f"= {delta_m:.3f} м")
    with col3:
        L_mm = st.number_input("Длина L (мм)", value=500.0, min_value=100.0, max_value=2000.0, step=50.0)
        L_m = L_mm / 1000.0
        st.caption(f"= {L_m:.1f} м")
    
    # ========== МАТЕРИАЛ ==========
    st.subheader("🏗️ Материал")
    material_name = st.selectbox("Марка стали", ["Ст3", "АМг6", "12Х18Н10Т"])
    
    # ========== ЧИСЛЕННЫЕ ПАРАМЕТРЫ ==========
    with st.expander("🔧 Численные параметры"):
        n_points = st.slider("Количество точек по высоте", 20, 100, 50)
        n_steps = st.slider("Шагов остывания", 20, 80, 40)
    
    # ========== КНОПКА РАСЧЁТА ==========
    st.divider()
    if st.button("🚀 РАССЧИТАТЬ", type="primary", use_container_width=True):
        st.session_state.calculate = True
        st.session_state.input_data = {
            "I_A": I_A,
            "U_V": U_V,
            "v_ms": v_ms,
            "eta": eta,
            "h_m": h_m,
            "delta_m": delta_m,
            "L_m": L_m,
            "material_name": material_name,
            "n_points": n_points,
            "n_steps": n_steps
        }

# Основная область
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📥 Параметры расчёта")
    
    if st.session_state.get("calculate", False):
        input_data = st.session_state.input_data
        
        # Отображение параметров
        st.write(f"**Материал:** {input_data['material_name']}")
        st.write(f"**Режим сварки:** {input_data['I_A']:.0f} А, {input_data['U_V']:.0f} В, {input_data['v_ms']*100:.2f} см/с")
        st.write(f"**Геометрия:** h={input_data['h_m']*1000:.0f} мм, δ={input_data['delta_m']*1000:.1f} мм, L={input_data['L_m']*1000:.0f} мм")
        st.write(f"**Сетка:** {input_data['n_points']} точек, {input_data['n_steps']} шагов остывания")

with col2:
    st.header("📤 Результаты")
    
    if st.session_state.get("calculate", False):
        with st.spinner("🔬 Расчёт..."):
            try:
                payload = {
                    "I_A": st.session_state.input_data["I_A"],
                    "U_V": st.session_state.input_data["U_V"],
                    "v_ms": st.session_state.input_data["v_ms"],
                    "h_m": st.session_state.input_data["h_m"],
                    "delta_m": st.session_state.input_data["delta_m"],
                    "L_m": st.session_state.input_data["L_m"],
                    "material_name": st.session_state.input_data["material_name"],
                    "n_points": st.session_state.input_data["n_points"]
                }
                
                response = requests.post(
                    f"{API_URL}/api/v1/calculate/welding-full",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    heating = result["heating"]
                    
                    # Метрики
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        st.metric("Начальная кривизна", f"{heating['curvature_1pm']:.3e} 1/м")
                        st.metric("Стрелка прогиба", f"{result['deflection_mm']:.2f} мм")
                    with col_r2:
                        st.metric("Финальная кривизна", f"{result['final_curvature_1pm']:.3e} 1/м")
                        st.metric("T_max", f"{result['T_max_C']:.0f} °C")
                    with col_r3:
                        st.metric("Тепловложение", f"{result['heat_input_kJ_per_m']:.1f} кДж/м")
                        st.metric("Шагов остывания", result['cooling_steps'])
                    
                    # Эпюра остаточных напряжений
                    st.subheader("📈 Остаточные напряжения")
                    y_coords_mm = heating['y_coords_mm']
                    residual_stresses_MPa = result['residual_stresses_MPa']
                    
                    fig_s, ax_s = plt.subplots(figsize=(6, 5))
                    ax_s.plot(residual_stresses_MPa, y_coords_mm, linewidth=2, color='darkred')
                    ax_s.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
                    ax_s.set_xlabel("Остаточное напряжение σ (МПа)")
                    ax_s.set_ylabel("y (мм)")
                    ax_s.set_title("Эпюра остаточных напряжений")
                    ax_s.grid(True, alpha=0.3)
                    st.pyplot(fig_s)
                    
                    # Сравнение эпюр
                    st.subheader("📊 Сравнение: нагрев vs остывание")
                    stresses_heating_MPa = heating['stresses_MPa']
                    
                    fig_c, ax_c = plt.subplots(figsize=(6, 5))
                    ax_c.plot(stresses_heating_MPa, y_coords_mm, linewidth=2, label='Нагрев', color='blue')
                    ax_c.plot(residual_stresses_MPa, y_coords_mm, linewidth=2, label='Остывание (остаточные)', color='darkred')
                    ax_c.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
                    ax_c.set_xlabel("Напряжение σ (МПа)")
                    ax_c.set_ylabel("y (мм)")
                    ax_c.set_title("Изменение эпюры напряжений")
                    ax_c.legend()
                    ax_c.grid(True, alpha=0.3)
                    st.pyplot(fig_c)
                    
                    # Кнопка скачивания
                    st.download_button(
                        label="💾 Скачать результаты (JSON)",
                        data=json.dumps(result, indent=2),
                        file_name="weldfoam_full_result.json",
                        mime="application/json"
                    )
                    
                else:
                    st.error(f"❌ Ошибка API: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Не удалось подключиться к серверу FastAPI. Запустите: python main.py")
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
    else:
        st.info("👈 Настройте параметры и нажмите 'РАССЧИТАТЬ'")

# Footer
st.markdown("---")
st.markdown("**WeldFOAM** | Нагрев + остывание | Остаточные напряжения | Стрелка прогиба")
