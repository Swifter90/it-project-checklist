from flask import Flask, render_template, request, send_file
import plotly.express as px
import pandas as pd
from weasyprint import HTML
import os
import hashlib

app = Flask(__name__)

# Список задач (22 задачи, соответствующие PMBOK 7)
tasks = [
    {"task": "Определить и вовлечь стейкхолдеров", "phase": "Заинтересованные стороны", "team": "Проектный офис, Аналитики"},
    {"task": "Разработать устав проекта", "phase": "Инициирование", "team": "Проектный офис"},
    {"task": "Создать реестр стейкхолдеров", "phase": "Заинтересованные стороны", "team": "Аналитики"},
    {"task": "Определить требования", "phase": "Планирование", "team": "Аналитики, Бизнес-аналитики"},
    {"task": "Разработать план управления проектом", "phase": "Планирование", "team": "Проектный офис"},
    {"task": "Определить бюджет проекта", "phase": "Планирование", "team": "Финансовый отдел, Проектный офис"},
    {"task": "Создать расписание проекта", "phase": "Планирование", "team": "Планировщики"},
    {"task": "Определить ресурсы", "phase": "Планирование", "team": "Ресурсный менеджер"},
    {"task": "Разработать план управления рисками", "phase": "Планирование", "team": "Риск-менеджеры"},
    {"task": "Провести кик-офф встречу", "phase": "Инициирование", "team": "Проектный офис, Команда"},
    {"task": "Разработать архитектуру решения", "phase": "Исполнение", "team": "Архитекторы"},
    {"task": "Настроить инфраструктуру", "phase": "Исполнение", "team": "DevOps"},
    {"task": "Разработать код", "phase": "Исполнение", "team": "Разработчики"},
    {"task": "Провести тестирование", "phase": "Исполнение", "team": "Тестировщики"},
    {"task": "Внедрить решение", "phase": "Исполнение", "team": "DevOps, Разработчики"},
    {"task": "Обучить пользователей", "phase": "Исполнение", "team": "Тренеры"},
    {"task": "Провести приемочное тестирование", "phase": "Контроль", "team": "Тестировщики, Заказчик"},
    {"task": "Управлять изменениями", "phase": "Контроль", "team": "Проектный офис"},
    {"task": "Мониторить риски", "phase": "Контроль", "team": "Риск-менеджеры"},
    {"task": "Подготовить отчеты", "phase": "Контроль", "team": "Аналитики"},
    {"task": "Завершить проект", "phase": "Завершение", "team": "Проектный офис"},
    {"task": "Провести ретроспективу", "phase": "Завершение", "team": "Команда"}
]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = []
        for i, task in enumerate(tasks):
            start = request.form.get(f'start_date_{i}')
            end = request.form.get(f'end_date_{i}')
            if start and end:
                try:
                    # Проверка корректности дат
                    pd.to_datetime(start)
                    pd.to_datetime(end)
                    data.append({
                        'Task': task['task'],
                        'Start': start,
                        'Finish': end,
                        'Phase': task['phase'],
                        'Team': task['team']
                    })
                except ValueError:
                    return render_template('index.html', tasks=tasks, error="Некорректный формат даты. Используйте YYYY-MM-DD.")
        if data:
            df = pd.DataFrame(data)
            # Создаём уникальный хэш для данных
            data_hash = hashlib.md5(str(data).encode()).hexdigest()
            cache_file = f'static/gantt_{data_hash}.png'
            if not os.path.exists(cache_file):
                fig = px.timeline(df, x_start='Start', x_end='Finish', y='Task', color='Phase', hover_data=['Team'])
                fig.update_layout(font=dict(size=12), margin=dict(l=20, r=20, t=40, b=20))
                fig.write_png(cache_file, width=800, height=600, scale=1)
            return render_template('gantt.html', image_file=f'/static/gantt_{data_hash}.png')
        else:
            return render_template('index.html', tasks=tasks, error="Введите хотя бы одну задачу с датами")
    return render_template('index.html', tasks=tasks)

@app.route('/download_presentation')
def download_presentation():
    image_file = request.args.get('image_file', 'static/gantt.png')
    if os.path.exists(image_file):
        try:
            HTML('templates/gantt.html').write_pdf('gantt_presentation.pdf', timeout=30)
            return send_file('gantt_presentation.pdf', as_attachment=True)
        except Exception as e:
            return f"Ошибка создания PDF: {str(e)}", 500
    else:
        return "Ошибка: Диаграмма не найдена", 500

if __name__ == '__main__':
    app.run(debug=True)
