import streamlit as st
import pandas as pd
import plotly.express as px
import ast


st.set_page_config(layout="wide")
st.title("📊 Анализ структуры вопросов в датасете")

# Загрузка данных
@st.cache_data
def load_data():
    df = pd.read_json("final_ochka_dirty.json")
    df["solution_text"] = df["solution"].apply(lambda x: ast.literal_eval(x)["text"] if pd.notnull(x) else "")
    return df

df = load_data()

# 🧠 Генерация новых колонок
def infer_question_type(text):
    text = text.lower()
    if "установи соответствие" in text:
        return "установление соответствия"
    elif "расположи" in text or "укажи последовательность" in text:
        return "указание последовательности"
    elif "выберите несколько" in text or "много вариантов" in text:
        return "выбор ответа (мультивыбор)"
    elif "выберите один" in text or "один вариант" in text:
        return "выбор ответа (один)"
    elif "впишите" in text or "ответ" in text:
        return "открытый ответ"
    return "неопределено"

df["question_type"] = df["solution_text"].apply(infer_question_type)

# Простейшее эвристическое определение уровня провокационности
def define_provocative(row):
    if row["question_type"] == "открытый ответ":
        return 3
    elif row["question_type"] in ["установление соответствия", "указание последовательности"]:
        return 2
    elif row["question_type"] in ["выбор ответа (один)", "выбор ответа (мультивыбор)"]:
        return 1
    return 1

df["provocativeness"] = df.apply(define_provocative, axis=1)

# 🧩 Уточнение предметов
subject_map = {
    "inf": "Информатика",
    "fr": "Французский язык",
    # Добавь при необходимости другие обозначения
}
df["subject_full"] = df["subject"].map(subject_map).fillna(df["subject"])

# 🎛️ Фильтры
subjects = st.multiselect("Выберите предметы", df["subject_full"].unique(), default=df["subject_full"].unique())
types = st.multiselect("Типы вопросов", df["question_type"].unique(), default=df["question_type"].unique())
prov_range = st.slider("Уровень провокационности", 1, 3, (1, 3))

filtered = df[
    df["subject_full"].isin(subjects) &
    df["question_type"].isin(types) &
    df["provocativeness"].between(prov_range[0], prov_range[1])
]

# 📊 1. Кол-во вопросов по предмету и виду
st.subheader("🧮 Количество вопросов по предмету и типу")
fig1 = px.histogram(
    filtered,
    x="subject_full",
    color="question_type",
    barmode="group",
    labels={"subject_full": "Предмет", "count": "Количество"}
)
st.plotly_chart(fig1, use_container_width=True)

# 📊 2. Распределение провокационности по типу
st.subheader("📉 Распределение провокационности по типу вопросов")
fig2 = px.histogram(
    filtered,
    x="provocativeness",
    color="question_type",
    barmode="stack",
    labels={"provocativeness": "Провокационность"}
)
st.plotly_chart(fig2, use_container_width=True)

# 📊 3. Средняя провокационность
st.subheader("📐 Средняя провокационность по предмету и типу")
mean_df = filtered.groupby(["subject_full", "question_type"])["provocativeness"].mean().reset_index()
fig3 = px.bar(
    mean_df,
    x="subject_full",
    y="provocativeness",
    color="question_type",
    barmode="group",
    labels={"provocativeness": "Средняя провокационность"}
)
st.plotly_chart(fig3, use_container_width=True)
