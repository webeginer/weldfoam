import streamlit as st
import requests
import numpy as np
import matplotlib.pyplot as plt
import json
import os


API_URL = "http://localhost:8000"

# Если запущено на Render (есть переменная окружения RENDER) — берём API_URL из окружения
if os.getenv("RENDER"):
    API_URL = os.getenv("API_URL", "https://weldfoam-core-api.onrender.com")
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
        I_A = st.number_input("Ток I (А)", value=150, min_value=50, max_value=500, step=10, format="%d")
        v_mms = st.number_input("Скорость v (мм/с)", value=3.0, min_value=1.0, max_value=20.0, step=1.0, format="%.0f")
        v_ms = v_mms / 1000.0
    with col2:
        U_V = st.number_input("Напряжение U (В)", value=25, min_value=20, max_value=40, step=1, format="%d")
        eta = st.number_input("КПД дуги η", value=0.75, min_value=0.6, max_value=0.9, step=0.05, format="%.2f")
    
    # ========== ГЕОМЕТРИЯ ==========
    st.subheader("📐 Геометрия")
    col1, col2, col3 = st.columns(3)
    with col1:
        L_mm = st.number_input("Длина L (мм)", value=500, min_value=100, max_value=2000, step=50, format="%d")
        L_m = L_mm / 1000.0
    with col2:
        b_mm = st.number_input("Ширина b (мм)", value=100, min_value=20, max_value=500, step=10, format="%d")
        b_m = b_mm / 1000.0
    with col3:
        delta_mm = st.number_input("Толщина δ (мм)", value=4, min_value=1, max_value=20, step=1, format="%d")
        delta_m = delta_mm / 1000.0
    
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
            "b_m": b_m,
            "delta_m": delta_m,
            "L_m": L_m,
            "material_name": material_name,
            "n_points": n_points,
            "n_steps": n_steps
        }

# Основная область (только результаты)
st.header("📤 Результаты")

if st.session_state.get("calculate", False):
    with st.spinner("🔬 Расчёт..."):
        try:
            payload = {
                "I_A": st.session_state.input_data["I_A"],
                "U_V": st.session_state.input_data["U_V"],
                "v_ms": st.session_state.input_data["v_ms"],
                "h_m": st.session_state.input_data["b_m"],
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
                
                # Пересчёт кривизны из 1/м в 1/мм
                curvature_heating_1pmm = heating['curvature_1pm'] / 1000.0
                curvature_final_1pmm = result['final_curvature_1pm'] / 1000.0
                
                # Форматирование с запятой (русская локаль)
                curvature_heating_str = f"{curvature_heating_1pmm:,.6f}".replace('.', ',')
                curvature_final_str = f"{curvature_final_1pmm:,.6f}".replace('.', ',')
                deflection_str = f"{result['deflection_mm']:,.2f}".replace('.', ',')
                heat_input_str = f"{result['heat_input_kJ_per_m']:,.1f}".replace('.', ',')
                tmax_str = str(int(result['T_max_C']))
                
                # Первая строка метрик (3 колонки)
                col_r1, col_r2, col_r3 = st.columns(3)
                
                with col_r1:
                    st.metric(
                        label="Кривизна при t = max",
                        value=curvature_heating_str
                    )
                    st.caption("(1/мм)")
                
                with col_r2:
                    st.metric(
                        label="Кривизна при t = 20°C",
                        value=curvature_final_str
                    )
                    st.caption("(1/мм)")
                
                with col_r3:
                    st.metric(
                        label="Стрела прогиба",
                        value=deflection_str
                    )
                    st.caption("(мм)")
                
                # Вторая строка метрик (3 колонки)
                col_r4, col_r5, col_r6 = st.columns(3)
                
                with col_r4:
                    st.metric(
                        label="Максимальная температура",
                        value=tmax_str
                    )
                    st.caption("(°C)")
                
                with col_r5:
                    st.metric(
                        label="Тепловложение",
                        value=heat_input_str
                    )
                    st.caption("(кДж/м)")
                
                with col_r6:
                    st.metric(
                        label="Шагов остывания",
                        value=result['cooling_steps']
                    )
                
                # Предупреждение о перегреве
                if result.get('warning'):
                    st.warning(result['warning'])
                elif heating.get('warning'):
                    st.warning(heating['warning'])
                
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
    st.info("👈 Настройте параметры в боковой панели и нажмите 'РАССЧИТАТЬ'")

# Footer
st.markdown("---")
st.markdown("**WeldFOAM** | Нагрев + остывание | Остаточные напряжения | Стрела прогиба")