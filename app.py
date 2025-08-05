from flask import Flask, request, render_template, send_file, session
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import io
import kaleido

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Установите безопасный ключ для сессий

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect('gantt_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task TEXT, phase TEXT, team TEXT,
                  start TEXT, end TEXT, progress INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# Чек-лист (добавлено поле progress для процента выполнения)
checklist = [
    {"task": "Определить бизнес-цели и границы проекта", "phase": "Инициация", "team": "Аналитики, Проектный офис", "progress": 0},
    {"task": "Составить список стейкхолдеров и назначить роли", "phase": "Инициация", "team": "Проектный офис", "progress": 0},
    {"task": "Провести анализ рисков и разработать устав проекта", "phase": "Инициация", "team": "Аналитики, Проектный офис", "progress": 0},
    {"task": "Pроверить отсутствие конфликтов с проектами", "phase": "Инициация", "team": "Проектный офис", "progress": 0},
    {"task": "Провести техническую оценку и составить ТЗ", "phase": "Инициация", "team": "IT (Продакты)", "progress": 0},
    {"task": "Оценить потребности в обучении", "phase": "Инициация", "team": "Обучение", "progress": 0},
    {"task": "Назначить координаторов на дарксторах", "phase": "Инициация", "team": "Операции", "progress": 0},
    {"task": "Проанализировать текущие процессы дарксторов", "phase": "Инициация", "team": "Аналитики", "progress": 0},
    {"task": "Разработать план проекта и бюджет", "phase": "Планирование", "team": "Проектный офис, Аналитики", "progress": 0},
    {"task": "Разработать план коммуникаций", "phase": "Планирование", "team": "Проектный офис", "progress": 0},
    {"task": "Определить стек технологий и ресурсы", "phase": "Планирование", "team": "IT (Продакты, Разработка)", "progress": 0},
    {"task": "Разработать план обучения", "phase": "Планирование", "team": "Обучение", "progress": 0},
    {"task": "Согласовать участие в тестировании и обучении", "phase": "Планирование", "team": "Операции", "progress": 0},
    {"task": "Разработать метрики мониторинга", "phase": "Планирование", "team": "Аналитики", "progress": 0},
    {"task": "Провести кик-офф встречу", "phase": "Исполнение", "team": "Проектный офис", "progress": 0},
    {"task": "Реализовать разработку и тестирование", "phase": "Исполнение", "team": "IT (Разработка)", "progress": 0},
    {"task": "Подготовить и провести обучение", "phase": "Исполнение", "team": "Обучение", "progress": 0},
    {"task": "Участвовать в пилотном тестировании", "phase": "Исполнение", "team": "Операции", "progress": 0},
    {"task": "Мониторить прогресс", "phase": "Исполнение", "team": "Аналитики", "progress": 0},
    {"task": "Отслеживать выполнение плана и управлять изменениями", "phase": "Мониторинг и контроль", "team": "Проектный офис", "progress": 0},
    {"task": "Собирать обратную связь", "phase": "Мониторинг и контроль", "team": "Проектный офис, Аналитики", "progress": 0},
    {"task": "Контролировать качество", "phase": "Мониторинг и контроль", "team": "IT (Разработка)", "progress": 0},
    {"task": "Оценить эффективность обучения", "phase": "Мониторинг и контроль", "team": "Обучение", "progress": 0},
    {"task": "Контролировать пилотное внедрение", "phase": "Мониторинг и контроль", "team": "Операции", "progress": 0},
    {"task": "Анализировать промежуточные результаты", "phase": "Мониторинг и контроль", "team": "Аналитики", "progress": 0},
    {"task": "Провести полное внедрение", "phase": "Завершение", "team": "Проектный офис, Операции", "progress": 0},
    {"task": "Оценить результаты и провести ретроспективу", "phase": "Завершение", "team": "Проектный офис, Аналитики", "progress": 0},
    {"task": "Закрыть проект и архивировать данные", "phase": "Завершение", "team": "Проектный офис", "progress": 0},
    {"task": "Передать решение в поддержку", "phase": "Завершение", "team": "IT (Разработка)", "progress": 0},
    {"task": "Завершить обучение", "phase": "Завершение", "team": "Обучение", "progress": 0},
    {"task": "Подтвердить готовность к эксплуатации", "phase": "Завершение", "team": "Операции", "progress": 0},
    {"task": "Подготовить финальный отчет", "phase": "Завершение", "team": "Аналитики", "progress": 0}
]

# Зависимости между задачами (пример для критического пути)
dependencies = [
    (0, 1),  # "Определить бизнес-цели" -> "Составить список стейкхолдеров"
    (1, 2),  # "Составить список стейкхолдеров" -> "Провести анализ рисков"
    (2, 8),  # "Провести анализ рисков" -> "Разработать план проекта"
    (8, 14), # "Разработать план проекта" -> "Провести кик-офф встречу"
    (14, 15),# "Провести кик-офф встречу" -> "Реализовать разработку"
    (15, 19),# "Реализовать разработку" -> "Отслеживать выполнение плана"
    (19, 25),# "Отслеживать выполнение плана" -> "Провести полное внедрение"
    (25, 26),# "Провести полное внедрение" -> "Оценить результаты"
    (26, 27),# "Оценить результаты" -> "Закрыть проект"
]

@app.route('/', methods=['GET', 'POST'])
def index():
    # Загружаем сохраненные данные из SQLite
    conn = sqlite3.connect('gantt_data.db')
    c = conn.cursor()
    c.execute('SELECT task, start, end, progress FROM tasks')
    saved_tasks = c.fetchall()
    conn.close()

    # Подготавливаем данные для формы
    form_data = {task['task']: {'start': '', 'end': '', 'progress': 0} for task in checklist}
    for saved_task in saved_tasks:
        task_name, start, end, progress = saved_task
        form_data[task_name] = {'start': start or '', 'end': end or '', 'progress': progress or 0}

    if request.method == 'POST':
        tasks = []
        # Обновляем данные в SQLite
        conn = sqlite3.connect('gantt_data.db')
        c = conn.cursor()
        c.execute('DELETE FROM tasks')  # Очищаем старые данные
        for item in checklist:
            start_date = request.form.get(f'start_{item["task"]}')
            end_date = request.form.get(f'end_{item["task"]}')
            progress = request.form.get(f'progress_{item["task"]}', '0')
            progress = int(progress) if progress.isdigit() else 0
            if start_date and end_date:
                tasks.append({
                    'Task': item['task'],
                    'Phase': item['phase'],
                    'Team': item['team'],
                    'Start': start_date,
                    'Finish': end_date,
                    'Progress': progress
                })
                c.execute('INSERT INTO tasks (task, phase, team, start, end, progress) VALUES (?, ?, ?, ?, ?, ?)',
                          (item['task'], item['phase'], item['team'], start_date, end_date, progress))
        conn.commit()
        conn.close()

        if not tasks:
            return render_template('index.html', checklist=checklist, form_data=form_data,
                                 error="Введите даты для хотя бы одной задачи")

        # Сохраняем данные в сессии для PDF
        session['tasks'] = tasks

        # Создание DataFrame
        df = pd.DataFrame(tasks)
        
        # Построение диаграммы Ганта с улучшениями
        fig = go.Figure()
        colors = {'Инициация': '#1f77b4', 'Планирование': '#ff7f0e', 'Исполнение': '#2ca02c',
                  'Мониторинг и контроль': '#d62728', 'Завершение': '#9467bd'}
        
        for _, row in df.iterrows():
            # Основной бар задачи
            fig.add_trace(go.Bar(
                x=[(pd.to_datetime(row['Finish']) - pd.to_datetime(row['Start'])).days],
                y=[row['Task']],
                base=[pd.to_datetime(row['Start'])],
                marker=dict(color=colors[row['Phase']]),
                name=row['Phase'],
                hovertemplate=f"Задача: {row['Task']}<br>Фаза: {row['Phase']}<br>Команда: {row['Team']}<br>Начало: {row['Start']}<br>Конец: {row['Finish']}<br>Прогресс: {row['Progress']}%"
            ))
            # Индикатор прогресса
            if row['Progress'] > 0:
                progress_days = (pd.to_datetime(row['Finish']) - pd.to_datetime(row['Start'])).days * row['Progress'] / 100
                fig.add_trace(go.Bar(
                    x=[progress_days],
                    y=[row['Task']],
                    base=[pd.to_datetime(row['Start'])],
                    marker=dict(color='#000000', opacity=0.5),
                    showlegend=False,
                    hovertemplate=f"Прогресс: {row['Progress']}%"
                ))

        # Добавление зависимостей (стрелки)
        for dep in dependencies:
            if dep[0] < len(tasks) and dep[1] < len(tasks):
                start_task = tasks[dep[0]]
                end_task = tasks[dep[1]]
                fig.add_shape(
                    type="line",
                    x0=pd.to_datetime(start_task['Finish']),
                    y0=start_task['Task'],
                    x1=pd.to_datetime(end_task['Start']),
                    y1=end_task['Task'],
                    line=dict(color="black", width=2, dash="dash"),
                    xref="x", yref="y"
                )

        fig.update_layout(
            title="Диаграмма Ганта: Запуск IT-проекта",
            xaxis=dict(title="Дата", type="date"),
            yaxis=dict(title="Задача", autorange="reversed"),
            showlegend=True,
            template="plotly_white",
            barmode='overlay',
            bargap=0.1,
            height=800
        )

        # Выделение критического пути (задачи из dependencies)
        critical_tasks = set([checklist[i]['task'] for i in set(sum(dependencies, ()))])
        for trace in fig.data:
            if trace.y and trace.y[0] in critical_tasks:
                trace.marker.line = dict(width=2, color="red")

        graph = fig.to_html(full_html=False)
        return render_template('index.html', checklist=checklist, form_data=form_data,
                             graph=graph, pdf_available=True,
                             phases=list(set(item['phase'] for item in checklist)),
                             teams=list(set(item['team'] for item in checklist)))

    return render_template('index.html', checklist=checklist, form_data=form_data,
                         phases=list(set(item['phase'] for item in checklist)),
                         teams=list(set(item['team'] for item in checklist)))

@app.route('/download_pdf', methods=['GET'])
def download_pdf():
    tasks = session.get('tasks', [])
    if not tasks:
        return "Ошибка: нет данных для экспорта. Сначала постройте диаграмму.", 400

    df = pd.DataFrame(tasks)
    fig = go.Figure()
    colors = {'Инициация': '#1f77b4', 'Планирование': '#ff7f0e', 'Исполнение': '#2ca02c',
              'Мониторинг и контроль': '#d62728', 'Завершение': '#9467bd'}
    
    for _, row in df.iterrows():
        fig.add_trace(go.Bar(
            x=[(pd.to_datetime(row['Finish']) - pd.to_datetime(row['Start'])).days],
            y=[row['Task']],
            base=[pd.to_datetime(row['Start'])],
            marker=dict(color=colors[row['Phase']]),
            name=row['Phase'],
            hovertemplate=f"Задача: {row['Task']}<br>Фаза: {row['Phase']}<br>Команда: {row['Team']}<br>Начало: {row['Start']}<br>Конец: {row['Finish']}<br>Прогресс: {row['Progress']}%"
        ))
        if row['Progress'] > 0:
            progress_days = (pd.to_datetime(row['Finish']) - pd.to_datetime(row['Start'])).days * row['Progress'] / 100
            fig.add_trace(go.Bar(
                x=[progress_days],
                y=[row['Task']],
                base=[pd.to_datetime(row['Start'])],
                marker=dict(color='#000000', opacity=0.5),
                showlegend=False
            ))

    for dep in dependencies:
        if dep[0] < len(tasks) and dep[1] < len(tasks):
            start_task = tasks[dep[0]]
            end_task = tasks[dep[1]]
            fig.add_shape(
                type="line",
                x0=pd.to_datetime(start_task['Finish']),
                y0=start_task['Task'],
                x1=pd.to_datetime(end_task['Start']),
                y1=end_task['Task'],
                line=dict(color="black", width=2, dash="dash"),
                xref="x", yref="y"
            )

    fig.update_layout(
        title="Диаграмма Ганта: Запуск IT-проекта",
        xaxis=dict(title="Дата", type="date"),
        yaxis=dict(title="Задача", autorange="reversed"),
        showlegend=True,
        template="plotly_white",
        barmode='overlay',
        bargap=0.1,
        height=800
    )

    critical_tasks = set([checklist[i]['task'] for i in set(sum(dependencies, ()))])
    for trace in fig.data:
        if trace.y and trace.y[0] in critical_tasks:
            trace.marker.line = dict(width=2, color="red")

    pdf_buffer = io.BytesIO()
    fig.write_image(pdf_buffer, format="pdf", engine="kaleido", width=1200, height=800, scale=1)
    pdf_buffer.seek(0)

    return send_file(pdf_buffer, download_name="gantt_chart.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
