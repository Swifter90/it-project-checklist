from flask import Flask, request, render_template, send_file, session, jsonify
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
            new_task = {
                'task': request.form.get('task_name'),
                'phase': request.form.get('phase', 'Без фазы'),
                'team': request.form.get('team', 'Без команды'),
                'dependencies': request.form.getlist('dependencies'),
                'is_milestone': request.form.get('is_milestone') == 'on'  # Флаг вехи
            }
            tasks.append(new_task)
            session['tasks'] = tasks
        elif action == 'delete_task':
            task_index = int(request.form.get('task_index'))
            tasks.pop(task_index)
            session['tasks'] = tasks
        elif action == 'build_gantt':
            project_name = request.form.get('project_name', 'Запуск IT-проекта')
            session['project_name'] = project_name
            task_data = []
            for i, item in enumerate(tasks):
                start_date = request.form.get(f'start_{i}')
                end_date = request.form.get(f'end_{i}' if not item.get('is_milestone') else f'start_{i}')
                if start_date and (end_date or item.get('is_milestone')):
                    task_data.append({
                        'Task': item['task'],
                        'Phase': item['phase'],
                        'Team': item['team'],
                        'Start': start_date,
                        'Finish': start_date if item.get('is_milestone') else end_date,
                        'Dependencies': item.get('dependencies', []),
                        'IsMilestone': item.get('is_milestone', False)
                    })

            if not task_data:
                return render_template('index.html', checklist=tasks, error="Введите даты для хотя бы одной задачи", project_name=project_name, graph=None)

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

            graph = fig.to_html(full_html=False)
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
