from flask import Flask, request, render_template, send_file
import plotly.express as px
import pandas as pd
from datetime import datetime
import io
import kaleido  # Для экспорта в PDF

app = Flask(__name__)

# Обновленный чек-лист
checklist = [
    {"task": "Определить бизнес-цели и границы проекта", "phase": "Инициация", "team": "Аналитики, Проектный офис"},
    {"task": "Составить список стейкхолдеров и назначить роли", "phase": "Инициация", "team": "Проектный офис"},
    {"task": "Провести анализ рисков и разработать устав проекта", "phase": "Инициация", "team": "Аналитики, Проектный офис"},
    {"task": "Pроверить отсутствие конфликтов с проектами", "phase": "Инициация", "team": "Проектный офис"},
    {"task": "Провести техническую оценку и составить ТЗ", "phase": "Инициация", "team": "IT (Продакты)"},
    {"task": "Оценить потребности в обучении", "phase": "Инициация", "team": "Обучение"},
    {"task": "Назначить координаторов на дарксторах", "phase": "Инициация", "team": "Операции"},
    {"task": "Проанализировать текущие процессы дарксторов", "phase": "Инициация", "team": "Аналитики"},
    {"task": "Разработать план проекта и бюджет", "phase": "Планирование", "team": "Проектный офис, Аналитики"},
    {"task": "Разработать план коммуникаций", "phase": "Планирование", "team": "Проектный офис"},
    {"task": "Определить стек технологий и ресурсы", "phase": "Планирование", "team": "IT (Продакты, Разработка)"},
    {"task": "Разработать план обучения", "phase": "Планирование", "team": "Обучение"},
    {"task": "Согласовать участие в тестировании и обучении", "phase": "Планирование", "team": "Операции"},
    {"task": "Разработать метрики мониторинга", "phase": "Планирование", "team": "Аналитики"},
    {"task": "Провести кик-офф встречу", "phase": "Исполнение", "team": "Проектный офис"},
    {"task": "Реализовать разработку и тестирование", "phase": "Исполнение", "team": "IT (Разработка)"},
    {"task": "Подготовить и провести обучение", "phase": "Исполнение", "team": "Обучение"},
    {"task": "Участвовать в пилотном тестировании", "phase": "Исполнение", "team": "Операции"},
    {"task": "Мониторить прогресс", "phase": "Исполнение", "team": "Аналитики"},
    {"task": "Отслеживать выполнение плана и управлять изменениями", "phase": "Мониторинг и контроль", "team": "Проектный офис"},
    {"task": "Собирать обратную связь", "phase": "Мониторинг и контроль", "team": "Проектный офис, Аналитики"},
    {"task": "Контролировать качество", "phase": "Мониторинг и контроль", "team": "IT (Разработка)"},
    {"task": "Оценить эффективность обучения", "phase": "Мониторинг и контроль", "team": "Обучение"},
    {"task": "Контролировать пилотное внедрение", "phase": "Мониторинг и контроль", "team": "Операции"},
    {"task": "Анализировать промежуточные результаты", "phase": "Мониторинг и контроль", "team": "Аналитики"},
    {"task": "Провести полное внедрение", "phase": "Завершение", "team": "Проектный офис, Операции"},
    {"task": "Оценить результаты и провести ретроспективу", "phase": "Завершение", "team": "Проектный офис, Аналитики"},
    {"task": "Закрыть проект и архивировать данные", "phase": "Завершение", "team": "Проектный офис"},
    {"task": "Передать решение в поддержку", "phase": "Завершение", "team": "IT (Разработка)"},
    {"task": "Завершить обучение", "phase": "Завершение", "team": "Обучение"},
    {"task": "Подтвердить готовность к эксплуатации", "phase": "Завершение", "team": "Операции"},
    {"task": "Подготовить финальный отчет", "phase": "Завершение", "team": "Аналитики"}
]

@app.route('/', methods=['GET', 'POST'])
def index():
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

        # Создание DataFrame
        df = pd.DataFrame(tasks)
        
        # Построение диаграммы Ганта
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Phase",
                         title="Диаграмма Ганта: Запуск IT-проекта",
                         labels={"Task": "Задача", "Phase": "Фаза", "Team": "Команда"},
                         hover_data=["Team"])
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(showlegend=True, template="plotly_white")

        # Сохранение диаграммы в PDF
        pdf_buffer = io.BytesIO()
        fig.write_image(pdf_buffer, format="pdf", engine="kaleido")
        pdf_buffer.seek(0)

        graph = fig.to_html(full_html=False)
        return render_template('index.html', checklist=checklist, graph=graph, pdf_available=True)

    return render_template('index.html', checklist=checklist)

@app.route('/download_pdf')
def download_pdf():
    tasks = []
    for item in checklist:
        start_date = request.args.get(f'start_{item["task"]}')
        end_date = request.args.get(f'end_{item["task"]}')
        if start_date and end_date:
            tasks.append({
                'Task': item['task'],
                'Phase': item['phase'],
                'Team': item['team'],
                'Start': start_date,
                'Finish': end_date
            })

    if not tasks:
        return "Ошибка: нет данных для экспорта", 400

    df = pd.DataFrame(tasks)
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Phase",
                     title="Диаграмма Ганта: Запуск IT-проекта")
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=True, template="plotly_white")

    pdf_buffer = io.BytesIO()
    fig.write_image(pdf_buffer, format="pdf", engine="kaleido")
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, download_name="gantt_chart.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
