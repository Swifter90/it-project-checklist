from flask import Flask, request, render_template, send_file, session
import plotly.express as px
import pandas as pd
import io
import networkx as nx
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key'

@app.route('/', methods=['GET', 'POST'])
def index():
    project_name = session.get('project_name', 'Запуск IT-проекта')
    tasks = session.get('tasks', [])
    graph = session.get('graph', None)

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_task':
            task_name = request.form.get('task_name', '').strip()
            if not task_name:
                return render_template('index.html', checklist=tasks, error="Название задачи не может быть пустым", project_name=project_name, graph=graph, pdf_available=bool(graph))
            new_task = {
                'task': task_name,
                'phase': request.form.get('phase', 'Без фазы'),
                'team': request.form.get('team', 'Без команды'),
                'dependencies': request.form.getlist('dependencies'),
                'is_milestone': request.form.get('is_milestone') == 'on',
                'start_date': request.form.get('start_date'),
                'end_date': request.form.get('end_date') if not request.form.get('is_milestone') else request.form.get('start_date')
            }
            if new_task['start_date'] and new_task['end_date'] and not new_task['is_milestone']:
                start = datetime.strptime(new_task['start_date'], '%Y-%m-%d')
                end = datetime.strptime(new_task['end_date'], '%Y-%m-%d')
                if end < start:
                    return render_template('index.html', checklist=tasks, error="Дата окончания не может быть раньше даты начала", project_name=project_name, graph=graph, pdf_available=bool(graph))
            tasks.append(new_task)
            session['tasks'] = tasks
        elif action == 'delete_task':
            task_index = int(request.form.get('task_index'))
            tasks.pop(task_index)
            session['tasks'] = tasks
        elif action == 'update_project_name':
            project_name = request.form.get('project_name', 'Запуск IT-проекта').strip()
            if not project_name:
                project_name = 'Запуск IT-проекта'
            session['project_name'] = project_name
        elif action == 'build_gantt':
            task_data = []
            for item in tasks:
                if item['start_date'] and (item['end_date'] or item['is_milestone']):
                    task_data.append({
                        'Task': item['task'],
                        'Phase': item['phase'],
                        'Team': item['team'],
                        'Start': item['start_date'],
                        'Finish': item['start_date'] if item['is_milestone'] else item['end_date'],
                        'Dependencies': item.get('dependencies', []),
                        'IsMilestone': item.get('is_milestone', False)
                    })

            if not task_data:
                return render_template('index.html', checklist=tasks, error="Введите даты для хотя бы одной задачи", project_name=project_name, graph=graph, pdf_available=bool(graph))

            session['task_data'] = task_data

            # Расчет критического пути
            df, critical_path = calculate_critical_path(task_data)
            fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Phase",
                             title=f"Диаграмма Ганта: {project_name}",
                             labels={"Task": "Задача", "Phase": "Фаза", "Team": "Команда"},
                             hover_data=["Team"])
            fig.update_yaxes(autorange="reversed")
            fig.update_layout(showlegend=True, template="plotly_white",
                             plot_bgcolor='#F5F6F5', paper_bgcolor='#FFFFFF',
                             colorway=['#005BFF', '#FF5C00', '#1E3A8A', '#F97316'])

            # Выделение критического пути
            for task in critical_path:
                fig.add_shape(type="rect", x0=df.loc[df['Task'] == task, 'Start'].iloc[0],
                              x1=df.loc[df['Task'] == task, 'Finish'].iloc[0],
                              y0=df.index[df['Task'] == task].tolist()[0] - 0.4,
                              y1=df.index[df['Task'] == task].tolist()[0] + 0.4,
                              fillcolor="rgba(255, 92, 0, 0.3)", line=dict(color="#FF5C00"))

            # Добавление вех
            for i, row in df.iterrows():
                if row['IsMilestone']:
                    fig.add_shape(type="path",
                                  path=f"M {fig.layout.xaxis.tickvals[0]} {i-0.4} L {fig.layout.xaxis.tickvals[0]} {i+0.4} L {fig.layout.xaxis.tickvals[0]+5} {i} Z",
                                  fillcolor="#FF5C00", line=dict(color="#FF5C00"))

            graph = fig.to_html(full_html=False, include_plotlyjs='cdn')
            session['graph'] = graph
            return render_template('index.html', checklist=tasks, graph=graph, project_name=project_name, pdf_available=True)

    return render_template('index.html', checklist=tasks, project_name=project_name, graph=graph, pdf_available=bool(graph))

def calculate_critical_path(tasks):
    G = nx.DiGraph()
    for task in tasks:
        start = datetime.strptime(task['Start'], '%Y-%m-%d')
        end = datetime.strptime(task['Finish'], '%Y-%m-%d')
        duration = 0 if task['IsMilestone'] else (end - start).days
        G.add_node(task['Task'], duration=duration, start=start, finish=end)
        for dep in task.get('Dependencies', []):
            G.add_edge(dep, task['Task'])

    critical_path = nx.dag_longest_path(G, weight='duration')
    df = pd.DataFrame(tasks)
    df['Start'] = pd.to_datetime(df['Start'])
    df['Finish'] = pd.to_datetime(df['Finish'])
    return df, critical_path

@app.route('/download_pdf', methods=['GET'])
def download_pdf():
    tasks = session.get('task_data', [])
    project_name = session.get('project_name', 'Запуск IT-проекта')
    if not tasks:
        return "Ошибка: нет данных для экспорта.", 400

    df = pd.DataFrame(tasks)
    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Phase",
                     title=f"Диаграмма Ганта: {project_name}",
                     labels={"Task": "Задача", "Phase": "Фаза", "Team": "Команда"},
                     hover_data=["Team"])
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(showlegend=True, template="plotly_white",
                     plot_bgcolor='#F5F6F5', paper_bgcolor='#FFFFFF',
                     colorway=['#005BFF', '#FF5C00', '#1E3A8A', '#F97316'])

    # Выделение критического пути
    _, critical_path = calculate_critical_path(tasks)
    for task in critical_path:
        fig.add_shape(type="rect", x0=df.loc[df['Task'] == task, 'Start'].iloc[0],
                      x1=df.loc[df['Task'] == task, 'Finish'].iloc[0],
                      y0=df.index[df['Task'] == task].tolist()[0] - 0.4,
                      y1=df.index[df['Task'] == task].tolist()[0] + 0.4,
                      fillcolor="rgba(255, 92, 0, 0.3)", line=dict(color="#FF5C00"))

    # Добавление вех
    for i, row in df.iterrows():
        if row['IsMilestone']:
            fig.add_shape(type="path",
                          path=f"M {fig.layout.xaxis.tickvals[0]} {i-0.4} L {fig.layout.xaxis.tickvals[0]} {i+0.4} L {fig.layout.xaxis.tickvals[0]+5} {i} Z",
                          fillcolor="#FF5C00", line=dict(color="#FF5C00"))

    pdf_buffer = io.BytesIO()
    fig.write_image(pdf_buffer, format="pdf", engine="kaleido")
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, download_name="gantt_chart.pdf", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
