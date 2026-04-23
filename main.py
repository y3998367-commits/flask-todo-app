import json
import os

from flask import Flask, redirect, render_template_string, request, url_for


app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE_PATH = os.path.join(BASE_DIR, "todos.json")


HTML_PAGE = """
<!doctype html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>我的待办清单</title>
    <style>
        :root {
            --bg-top: #f9f1e8;
            --bg-bottom: #eef6f1;
            --card: rgba(255, 255, 255, 0.92);
            --text: #213547;
            --muted: #6b7a89;
            --line: rgba(33, 53, 71, 0.08);
            --accent: #ff7a59;
            --accent-dark: #e56747;
            --done: #3a9d7a;
            --danger: #e14d5a;
            --shadow: 0 20px 50px rgba(33, 53, 71, 0.12);
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left, rgba(255, 122, 89, 0.18), transparent 30%),
                radial-gradient(circle at top right, rgba(58, 157, 122, 0.16), transparent 24%),
                linear-gradient(160deg, var(--bg-top), var(--bg-bottom));
            padding: 32px 16px;
        }

        .shell {
            max-width: 860px;
            margin: 0 auto;
        }

        .hero {
            background: var(--card);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.7);
            border-radius: 28px;
            box-shadow: var(--shadow);
            overflow: hidden;
        }

        .hero-top {
            padding: 32px 32px 24px;
            background:
                linear-gradient(135deg, rgba(255, 122, 89, 0.18), rgba(58, 157, 122, 0.12)),
                linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.82));
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.75);
            color: var(--accent-dark);
            font-size: 14px;
            font-weight: 600;
        }

        h1 {
            margin: 18px 0 10px;
            font-size: 38px;
            line-height: 1.1;
        }

        .subtitle {
            margin: 0;
            color: var(--muted);
            font-size: 16px;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
            margin-top: 24px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(255, 255, 255, 0.7);
            border-radius: 20px;
            padding: 18px;
        }

        .stat-label {
            margin: 0 0 8px;
            color: var(--muted);
            font-size: 14px;
        }

        .stat-value {
            margin: 0;
            font-size: 30px;
            font-weight: 700;
        }

        .content {
            padding: 28px 32px 32px;
        }

        .toolbar {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }

        .add-form {
            display: flex;
            flex: 1;
            min-width: 280px;
            gap: 12px;
        }

        .add-form input {
            flex: 1;
            min-width: 0;
            border: 1px solid var(--line);
            border-radius: 16px;
            background: #ffffff;
            padding: 14px 16px;
            font-size: 16px;
            color: var(--text);
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
        }

        .add-form input:focus {
            border-color: rgba(255, 122, 89, 0.5);
            box-shadow: 0 0 0 4px rgba(255, 122, 89, 0.12);
            transform: translateY(-1px);
        }

        .button {
            border: none;
            border-radius: 16px;
            padding: 13px 18px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.18s, box-shadow 0.18s, opacity 0.18s;
        }

        .button:hover {
            transform: translateY(-1px);
        }

        .button-primary {
            color: #ffffff;
            background: linear-gradient(135deg, var(--accent), #ff9b54);
            box-shadow: 0 12px 24px rgba(255, 122, 89, 0.24);
        }

        .button-clear {
            color: #ffffff;
            background: linear-gradient(135deg, #dc4f63, #f07d6f);
            box-shadow: 0 12px 24px rgba(220, 79, 99, 0.22);
        }

        .button-done {
            color: #ffffff;
            background: linear-gradient(135deg, var(--done), #55b792);
        }

        .button-delete {
            color: #ffffff;
            background: linear-gradient(135deg, #cf4451, #ef6f67);
        }

        .button-disabled {
            color: #ffffff;
            background: #b3b8bf;
            cursor: default;
            box-shadow: none;
        }

        .button-disabled:hover {
            transform: none;
        }

        .todo-list {
            list-style: none;
            margin: 0;
            padding: 0;
            display: grid;
            gap: 14px;
        }

        .todo-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 18px;
            border: 1px solid var(--line);
            border-radius: 22px;
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 10px 24px rgba(33, 53, 71, 0.05);
        }

        .todo-main {
            display: flex;
            align-items: center;
            gap: 14px;
            min-width: 0;
            flex: 1;
        }

        .todo-mark {
            width: 14px;
            height: 14px;
            border-radius: 999px;
            background: linear-gradient(135deg, var(--accent), #ffb46b);
            flex-shrink: 0;
        }

        .todo-text {
            margin: 0;
            font-size: 17px;
            line-height: 1.5;
            word-break: break-word;
        }

        .todo-completed .todo-mark {
            background: linear-gradient(135deg, var(--done), #7ad0af);
        }

        .todo-completed .todo-text {
            color: #98a0aa;
            text-decoration: line-through;
        }

        .actions {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 10px;
            flex-shrink: 0;
        }

        .actions form,
        .toolbar form {
            margin: 0;
        }

        .empty-state {
            text-align: center;
            padding: 54px 20px;
            border: 1px dashed rgba(33, 53, 71, 0.16);
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.55);
        }

        .empty-state h2 {
            margin: 0 0 10px;
            font-size: 24px;
        }

        .empty-state p {
            margin: 0;
            color: var(--muted);
            font-size: 15px;
        }

        @media (max-width: 700px) {
            .hero-top,
            .content {
                padding: 22px 18px;
            }

            h1 {
                font-size: 30px;
            }

            .stats {
                grid-template-columns: 1fr;
            }

            .toolbar,
            .add-form,
            .todo-item,
            .todo-main,
            .actions {
                display: flex;
                flex-direction: column;
                align-items: stretch;
            }

            .todo-main {
                gap: 10px;
            }

            .button {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="shell">
        <section class="hero">
            <div class="hero-top">
                <div class="badge">Todo App</div>
                <h1>我的待办清单</h1>
                <p class="subtitle">把今天要做的事收拢在一个清爽的小页面里，完成一项，轻松划掉一项。</p>

                <div class="stats">
                    <div class="stat-card">
                        <p class="stat-label">全部任务</p>
                        <p class="stat-value">{{ total_count }}</p>
                    </div>
                    <div class="stat-card">
                        <p class="stat-label">已完成</p>
                        <p class="stat-value">{{ completed_count }}</p>
                    </div>
                    <div class="stat-card">
                        <p class="stat-label">未完成</p>
                        <p class="stat-value">{{ pending_count }}</p>
                    </div>
                </div>
            </div>

            <div class="content">
                <div class="toolbar">
                    <form class="add-form" action="{{ url_for('add_todo_view') }}" method="post">
                        <input type="text" name="content" placeholder="输入新的待办事项..." required>
                        <button class="button button-primary" type="submit">添加</button>
                    </form>

                    {% if todos %}
                    <form action="{{ url_for('clear_todos_view') }}" method="post">
                        <button
                            class="button button-clear"
                            type="submit"
                            onclick="return confirm('确定要清空全部待办事项吗？');"
                        >
                            全部清空
                        </button>
                    </form>
                    {% endif %}
                </div>

                {% if todos %}
                <ul class="todo-list">
                    {% for todo in todos %}
                    <li class="todo-item {% if todo.completed %}todo-completed{% endif %}">
                        <div class="todo-main">
                            <span class="todo-mark"></span>
                            <p class="todo-text">{{ todo.content }}</p>
                        </div>

                        <div class="actions">
                            {% if todo.completed %}
                            <button class="button button-disabled" type="button" disabled>已完成</button>
                            {% else %}
                            <form action="{{ url_for('complete_todo_view', todo_id=todo.id) }}" method="post">
                                <button class="button button-done" type="submit">✅ 标记完成</button>
                            </form>
                            {% endif %}

                            <form action="{{ url_for('delete_todo_view', todo_id=todo.id) }}" method="post">
                                <button
                                    class="button button-delete"
                                    type="submit"
                                    onclick="return confirm('确定要删除这条任务吗？');"
                                >
                                    ❌ 删除任务
                                </button>
                            </form>
                        </div>
                    </li>
                    {% endfor %}
                </ul>
                {% else %}
                <div class="empty-state">
                    <h2>还没有待办任务</h2>
                    <p>先添加一条小目标吧，今天从这里开始推进。</p>
                </div>
                {% endif %}
            </div>
        </section>
    </div>
</body>
</html>
"""


def get_file_path():
    file_path = os.environ.get("TODO_FILE_PATH", DEFAULT_FILE_PATH)
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    return file_path


def load_todos():
    file_path = get_file_path()

    if not os.path.exists(file_path):
        save_todos([])
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            todos = json.load(file)
            if isinstance(todos, list):
                return todos
    except (json.JSONDecodeError, OSError):
        pass

    save_todos([])
    return []


def save_todos(todos):
    file_path = get_file_path()
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(todos, file, ensure_ascii=False, indent=2)


def get_next_id(todos):
    if not todos:
        return 1
    return max(todo["id"] for todo in todos) + 1


def get_counts(todos):
    total_count = len(todos)
    completed_count = sum(1 for todo in todos if todo["completed"])
    pending_count = total_count - completed_count
    return total_count, completed_count, pending_count


def show_index():
    todos = load_todos()
    total_count, completed_count, pending_count = get_counts(todos)
    return render_template_string(
        HTML_PAGE,
        todos=todos,
        total_count=total_count,
        completed_count=completed_count,
        pending_count=pending_count,
    )


def add_todo():
    content = request.form.get("content", "").strip()
    if content:
        todos = load_todos()
        todo = {
            "id": get_next_id(todos),
            "content": content,
            "completed": False,
        }
        todos.append(todo)
        save_todos(todos)
    return redirect(url_for("index"))


def complete_todo(todo_id):
    todos = load_todos()
    for todo in todos:
        if todo["id"] == todo_id:
            todo["completed"] = True
            break
    save_todos(todos)
    return redirect(url_for("index"))


def delete_todo(todo_id):
    todos = load_todos()
    todos = [todo for todo in todos if todo["id"] != todo_id]
    save_todos(todos)
    return redirect(url_for("index"))


def clear_todos():
    save_todos([])
    return redirect(url_for("index"))


def health_check():
    return "ok"


app.add_url_rule("/", "index", show_index, methods=["GET"])
app.add_url_rule("/add", "add_todo_view", add_todo, methods=["POST"])
app.add_url_rule("/complete/<int:todo_id>", "complete_todo_view", complete_todo, methods=["POST"])
app.add_url_rule("/delete/<int:todo_id>", "delete_todo_view", delete_todo, methods=["POST"])
app.add_url_rule("/clear", "clear_todos_view", clear_todos, methods=["POST"])
app.add_url_rule("/health", "health_check", health_check, methods=["GET"])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
