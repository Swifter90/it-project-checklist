from flask import Flask, request, render_template, send_file
import plotly.express as px
import pandas as pd
from weasyprint import HTML
import os

app = Flask(__name__)

# Сокращённый чек-лист по PMBOK 7
checklist = [
    {"task": "Определить и вовлечь стейкхолдеров", "phase": "Заинтересованные стороны", "team": "Проектный офис, Аналитики"},
    {"task": "Утвердить устав проекта", "phase": "Заинтересованные стороны", "team": "Проектный офис"},
    {"task": "Сформировать команду", "phase": "Команда", "team": "Проектный офис"},
    {"task": "Согласовать роли и обязанности", "phase": "Команда", "team": "Все направления"},
    {"task": "Провести техническую оценку", "phase": "Подход к разработке", "team": "IT (Продакты)"},
    {"task": "Выбрать стек технологий", "phase": "Подход к разработке", "team": "IT (Разработка)"},
    {"task": "Разработать план проекта", "phase": "Планирование", "team": "Проектный офис"},
    {"task": "Разработать план коммуникаций", "phase": "Планирование", "team": "Проектный офис"},
    {"task": "Определить метрики успеха", "phase": "Планирование", "team": "Аналитики"},
    {"task": "Спланировать обучение", "phase": "Планирование", "team": "Обучение"},
    {"task": "Провести разработку", "phase": "Выполнение проекта", "team": "IT (Разработка)"},
    {"task": "Организовать обучение", "phase": "Выполнение проекта", "team": "Обучение"},
    {"task": "Провести пилотное тестирование", "phase": "Выполнение проекта", "team": "Операции"},
    {"task": "Внедрить решение", "phase": "Поставка", "team": "Проектный офис, Операции"},
    {"task": "Передать в поддержку", "phase": "Поставка", "team": "IT (Разработка)"},
    {"task": "Мониторить прогресс", "phase": "Измерение", "team": "Проектный офис, Аналитики"},
    {"task": "Оценить эффективность обучения", "phase": "Измерение", "team": "Обучение"},
    {"task": "Управлять рисками", "phase": "Неопределённость", "team": "Проектный офис, Аналитики"},
    {"task": "Управлять изменениями", "phase": "Неопределённость", "team": "Проектный офис"},
    {"task": "Оценить результаты", "phase": "Завершение", "team": "Проектный офис, Аналитики"},
    {"task": "Провести ретроспективу", "phase": "Завершение", "team": "Проектный офис"},
    {"task": "Закрыть проект", "phase": "Завершение", "team": "Проектный офис"}
]

@app.route('/', methods=['GET', 'POST'])
def index():
    """Обработка главной страницы с чек-листом и формой для ввода дат"""
    if request.method == 'POST':
        tasks = []
        for item in checklist:
            start_date = request.form.get(f'start_{item["task"]}')
            end_date = request.form.get(f'end_{item["task"]}')
            if start_date and end_date:
                tasks.append({
                    'Task': item['task'],
                    'Phase': item['phase'],
                    'Team': item['team'],
                    'Start': start_date,
                    'Finish': end_date
                })

        if not tasks:
            return render_template('index.html', checklist=checklist, error="Введите даты для хотя бы одной задачи")

        df = pd.DataFrame(tasks)
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Phase",
                          title="Диаграмма Ганта: Запуск IT-проекта",
                          labels={"Task": "Задача", "Phase": "Фаза", "Team": "Команда"},
                          hover_data=["Team"])
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(showlegend=True, template="plotly_white")
        graph = fig.to_html(full_html=False)

        # Сохранение диаграммы в PNG для PDF
        fig.write_image("static/gantt.png", engine="kaleido")

        # Создание PDF с помощью WeasyPrint
        HTML('templates/gantt.html').write_pdf('gantt_presentation.pdf')

        return render_template('index.html', checklist=checklist, graph=graph)
    
    return render_template('index.html', checklist=checklist)

@app.route('/download_presentation')
def download_presentation():
    """Скачивание PDF с диаграммой Ганта для презентации"""
    if not os.path.exists('gantt_presentation.pdf'):
        return "PDF не создан. Сначала постройте диаграмму.", 404
    return send_file('gantt_presentation.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)