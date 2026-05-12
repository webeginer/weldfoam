import streamlit as st
import requests
import numpy as np
import matplotlib.pyplot as plt
import json

st.set_page_config(
    page_title="WeldFOAM - Калькулятор сварочных деформаций",
    page_icon="🔥",
    layout="wide"
)

st.title("🔥 WeldFOAM - Калькулятор сварочных деформаций")
st.markdown("### Этап 1: Нагрев (предельное состояние)")

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
        h_m = st.number_input("Высота h (мм)", value=100.0, min_value=20.0, max_value=500.0, step=10.0) / 1000.0
        st.caption(f"= {h_m:.3f} м")
    with col2:
        delta_m = st.number_input("Толщина δ (мм)", value=4.0, min_value=1.0, max_value=20.0, step=1.0) / 1000.0
        st.caption(f"= {delta_m:.3f} м")
    with col3:
        L_m = st.number_input("Длина L (мм)", value=500.0, min_value=100.0, max_value=2000.0, step=50.0) / 1000.0
        st.caption(f"= {L_m:.1f} м")
    
    # ========== МАТЕРИАЛ ==========
    st.subheader("🏗️ Материал")
    material_name = st.selectbox("Марка стали", ["Ст3", "АМг6", "12Х18Н10Т"])
    
    # ========== РАСШИРЕННЫЕ НАСТРОЙКИ ==========
    with st.expander("🔧 Расширенные настройки"):
        n_points = st.slider("Количество точек по высоте", 20, 100, 50)
        
        st.divider()
        st.caption("Режим отладки: прямой ввод T(y)")
        manual_T = st.checkbox("Использовать ручной ввод температуры")
        
        if manual_T:
            T_max_manual = st.number_input("T_max на кромке (°C)", value=1200.0)
            T_min_manual = st.number_input("T_min (°C)", value=20.0)
            profile_type = st.radio("Тип профиля", ["Экспоненциальный", "Линейный"])
    
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
            "manual_T": manual_T,
            "T_max_manual": T_max_manual if manual_T else None,
            "T_min_manual": T_min_manual if manual_T else None,
            "profile_type": profile_type if manual_T else None
        }

# Основная область
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📥 Тепловой расчёт")
    
    if st.session_state.get("calculate", False):
        input_data = st.session_state.input_data
        
        # Предпросмотр температурного профиля
        if not input_data["manual_T"]:
            # Демонстрационный профиль (имитация thermal.py)
            y_mm = np.linspace(0, input_data["h_m"] * 1000, input_data["n_points"])
            # Грубая оценка T_max от тепловложения
            q = input_data["eta"] * input_data["U_V"] * input_data["I_A"]
            heat_input = q / input_data["v_ms"]
            T_max_est = 20 + min(heat_input / 1000 * 300, 1480)
            T_profile = 20 + (T_max_est - 20) * np.exp(-15 * y_mm / 1000)  # затухание
        else:
            y_mm = np.linspace(0, input_data["h_m"] * 1000, input_data["n_points"])
            if input_data["profile_type"] == "Экспоненциальный":
                T_profile = input_data["T_min_manual"] + (input_data["T_max_manual"] - input_data["T_min_manual"]) * np.exp(-0.05 * y_mm)
            else:
                T_profile = input_data["T_max_manual"] - (input_data["T_max_manual"] - input_data["T_min_manual"]) * (y_mm / (input_data["h_m"] * 1000))
        
        # График T(y)
        fig_t, ax_t = plt.subplots(figsize=(6, 5))
        ax_t.plot(T_profile, y_mm)
        ax_t.set_xlabel("Температура T (°C)")
        ax_t.set_ylabel("y (мм)")
        ax_t.set_title("🌡️ Температурный профиль T(y)")
        ax_t.grid(True, alpha=0.3)
        ax_t.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='Кромка шва')
        ax_t.axhline(y=input_data["h_m"] * 1000, color='blue', linestyle='--', alpha=0.5, label='Холодная кромка')
        ax_t.legend()
        st.pyplot(fig_t)
        
        # Информация о тепловложении
        q = input_data["eta"] * input_data["U_V"] * input_data["I_A"]
        heat_input_kJ_m = (q / input_data["v_ms"]) / 1000
        st.info(f"🔥 Тепловложение: {heat_input_kJ_m:.1f} кДж/м | T_max расч: {T_profile[0]:.0f}°C")
        
        st.session_state.T_profile = T_profile
        st.session_state.y_mm = y_mm
        st.session_state.heat_input_kJ_m = heat_input_kJ_m
        
    else:
        st.info("👈 Настройте параметры сварки и нажмите 'РАССЧИТАТЬ'")
        y_mm = np.linspace(0, 100, 50)
        T_profile = np.linspace(1000, 20, 50)
        fig_t, ax_t = plt.subplots(figsize=(6, 5))
        ax_t.plot(T_profile, y_mm)
        ax_t.set_xlabel("Температура T (°C)")
        ax_t.set_ylabel("y (мм)")
        ax_t.set_title("🌡️ Температурный профиль T(y) (пример)")
        ax_t.grid(True, alpha=0.3)
        st.pyplot(fig_t)

with col2:
    st.header("📤 Результаты этапа 1")
    
    if st.session_state.get("calculate", False) and st.session_state.get("T_profile") is not None:
        with st.spinner("🔬 Решение методом Ньютона..."):
            try:
                # Подготовка payload в точности как WeldingInput
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
                    "http://localhost:8000/api/v1/calculate/welding",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Извлекаем результаты нагрева
                    heating = result["heating"]
                    
                    # Метрики
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        st.metric("Δ0", f"{heating['delta0']:.2e}", help="Деформация на кромке шва")
                        st.metric("Кривизна", f"{heating['curvature_1pm']:.3e} 1/м")
                    with col_r2:
                        st.metric("Δh", f"{heating['deltah']:.2e}", help="Деформация на холодной кромке")
                        st.metric("Итераций", heating['iterations'])
                    with col_r3:
                        st.metric("Max ε_pl", f"{heating['plastic_strains_compression'][0]:.2e}")
                        st.metric("Невязка", f"{heating['residual']:.1e}")
                    
                    st.info(f"🔥 Тепловложение: {result['heat_input_kJ_per_m']:.1f} кДж/м | T_max: {result['T_max_C']:.0f}°C")
                    
                    # Эпюра напряжений
                    st.subheader("📈 Эпюра напряжений")
                    y_coords_mm = heating['y_coords_mm']
                    stresses_MPa = heating['stresses_MPa']
                    
                    fig_s, ax_s = plt.subplots(figsize=(6, 5))
                    ax_s.plot(stresses_MPa, y_coords_mm, linewidth=2)
                    ax_s.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
                    ax_s.set_xlabel("Напряжение σ (МПа)")
                    ax_s.set_ylabel("y (мм)")
                    ax_s.set_title("Эпюра напряжений в момент нагрева")
                    ax_s.grid(True, alpha=0.3)
                    st.pyplot(fig_s)
                    
                    # Эпюра пластических деформаций
                    st.subheader("📉 Пластические деформации")
                    fig_p, ax_p = plt.subplots(figsize=(6, 5))
                    plastic = heating['plastic_strains_compression']
                    ax_p.plot(plastic, y_coords_mm, linewidth=2)
                    ax_p.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
                    ax_p.fill_betweenx(y_coords_mm, 0, plastic, where=(np.array(plastic)<0), alpha=0.3, color='blue', label='Сжатие')
                    ax_p.set_xlabel("Пластическая деформация ε_pl")
                    ax_p.set_ylabel("y (мм)")
                    ax_p.set_title("Накопленные пластические деформации")
                    ax_p.grid(True, alpha=0.3)
                    ax_p.legend()
                    st.pyplot(fig_p)
                    
                    # Прогиб
                    if result.get('deflection_mm'):
                        st.metric("📐 Стрелка прогиба", f"{result['deflection_mm']:.2f} мм")
                    
                    # Кнопка скачивания
                    st.download_button(
                        label="💾 Скачать результаты (JSON)",
                        data=json.dumps(result, indent=2),
                        file_name="weldfoam_stage1.json",
                        mime="application/json"
                    )
                    
                else:
                    st.error(f"❌ Ошибка API: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Не удалось подключиться к серверу FastAPI. Запустите: python main.py")
            except Exception as e:
                st.error(f"❌ Ошибка: {e}")
    elif st.session_state.get("calculate", False):
        st.info("⚙️ Настройте режим сварки и нажмите 'РАССЧИТАТЬ'")
    else:
        st.info("👈 Введите параметры и нажмите 'РАССЧИТАТЬ'")

# Footer
st.markdown("---")
st.markdown("**WeldFOAM** | Этап 1: Нагрев | Метод Ньютона | Идеальная упруго-пластичность")