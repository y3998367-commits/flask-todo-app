import json
import os
import secrets
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = Path(os.environ.get("TODO_DATA_FILE", str(BASE_DIR / "todos.json"))).resolve()
DATA_LOCK = threading.Lock()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def is_valid_code(code):
    return isinstance(code, str) and len(code) == 6 and code.isdigit()


def normalize_todo(item):
    if not isinstance(item, dict):
        return None

    todo_id = item.get("id")
    if not isinstance(todo_id, int):
        return None

    content = str(item.get("content", "")).strip()
    if not content:
        return None

    return {
        "id": todo_id,
        "content": content,
        "completed": bool(item.get("completed", False)),
    }


def normalize_space(code, space):
    if not is_valid_code(code) or not isinstance(space, dict):
        return None

    owner_token = space.get("owner_token")
    if not isinstance(owner_token, str) or not owner_token:
        return None

    todos = space.get("todos", [])
    if not isinstance(todos, list):
        todos = []

    normalized_todos = []
    max_id = 0
    for item in todos:
        todo = normalize_todo(item)
        if todo is None:
            continue
        normalized_todos.append(todo)
        if todo["id"] > max_id:
            max_id = todo["id"]

    next_id = space.get("next_id")
    if not isinstance(next_id, int) or next_id <= max_id:
        next_id = max_id + 1

    return {
        "code": code,
        "owner_token": owner_token,
        "shared": bool(space.get("shared", False)),
        "next_id": next_id,
        "todos": normalized_todos,
        "created_at": space.get("created_at") or utc_now(),
        "updated_at": space.get("updated_at") or utc_now(),
    }


def normalize_data(data):
    if not isinstance(data, dict):
        return {"spaces": {}}

    raw_spaces = data.get("spaces")
    if not isinstance(raw_spaces, dict):
        if all(isinstance(key, str) for key in data.keys()):
            raw_spaces = data
        else:
            raw_spaces = {}

    spaces = {}
    for code, space in raw_spaces.items():
        normalized = normalize_space(code, space)
        if normalized is not None:
            spaces[code] = normalized

    return {"spaces": spaces}


def load_data_unlocked():
    if not DATA_FILE.exists():
        return {"spaces": {}}

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return {"spaces": {}}

    return normalize_data(raw_data)


def save_data_unlocked(data):
    normalized = normalize_data(data)
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(DATA_FILE.parent),
        delete=False,
    ) as temp_file:
        json.dump(normalized, temp_file, ensure_ascii=False, indent=2)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_name = temp_file.name

    os.replace(temp_name, DATA_FILE)


def generate_unique_code(spaces):
    for _ in range(1000):
        code = f"{secrets.randbelow(1_000_000):06d}"
        if code not in spaces:
            return code
    raise RuntimeError("无法生成新的 6 位准入码，请稍后重试。")


def get_json_data():
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload
    return {}


def get_code_and_token():
    payload = get_json_data()
    code = str(payload.get("code", "")).strip()
    owner_token = str(payload.get("owner_token", "")).strip()
    return payload, code, owner_token


def build_space_response(space, is_owner):
    completed = sum(1 for todo in space["todos"] if todo["completed"])
    return {
        "code": space["code"],
        "shared": bool(space["shared"]),
        "is_owner": bool(is_owner),
        "todos": space["todos"],
        "stats": {
            "total": len(space["todos"]),
            "completed": completed,
            "pending": len(space["todos"]) - completed,
        },
    }


def unauthorized_private_response():
    return jsonify(
        {
            "message": "该空间尚未开启共享，只有创建该空间的设备可以访问。",
        }
    ), 403


@app.get("/")
def show_index():
    return render_template("index.html")


@app.get("/health")
def health_check():
    return "ok"


@app.post("/api/spaces")
def create_space():
    with DATA_LOCK:
        data = load_data_unlocked()
        code = generate_unique_code(data["spaces"])
        owner_token = secrets.token_urlsafe(24)
        timestamp = utc_now()

        space = {
            "code": code,
            "owner_token": owner_token,
            "shared": False,
            "next_id": 1,
            "todos": [],
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        data["spaces"][code] = space
        save_data_unlocked(data)

    return jsonify(
        {
            "message": "已生成新的独立空间。",
            "owner_token": owner_token,
            "space": build_space_response(space, True),
        }
    )


@app.post("/api/access")
def access_space():
    _, code, owner_token = get_code_and_token()
    if not is_valid_code(code):
        return jsonify({"message": "请输入正确的 6 位数字准入码。"}), 400

    with DATA_LOCK:
        data = load_data_unlocked()
        space = data["spaces"].get(code)
        if space is None:
            return jsonify({"message": "未找到对应的清单，请检查准入码是否正确。"}), 404

        is_owner = owner_token == space["owner_token"]
        if not (space["shared"] or is_owner):
            return unauthorized_private_response()

        return jsonify(
            {
                "message": "已进入清单。",
                "space": build_space_response(space, is_owner),
            }
        )


@app.post("/api/share")
def toggle_share():
    payload, code, owner_token = get_code_and_token()
    shared = bool(payload.get("shared", False))

    if not is_valid_code(code):
        return jsonify({"message": "请输入正确的 6 位数字准入码。"}), 400

    with DATA_LOCK:
        data = load_data_unlocked()
        space = data["spaces"].get(code)
        if space is None:
            return jsonify({"message": "未找到对应的清单。"}), 404

        is_owner = owner_token == space["owner_token"]
        if not is_owner:
            return jsonify({"message": "只有创建该空间的设备可以切换共享状态。"}), 403

        space["shared"] = shared
        space["updated_at"] = utc_now()
        save_data_unlocked(data)

        message = "已开启共享模式。" if shared else "已关闭共享模式。"
        return jsonify(
            {
                "message": message,
                "space": build_space_response(space, True),
            }
        )


@app.post("/api/todos")
def add_todo():
    payload, code, owner_token = get_code_and_token()
    content = str(payload.get("content", "")).strip()

    if not is_valid_code(code):
        return jsonify({"message": "请输入正确的 6 位数字准入码。"}), 400
    if not content:
        return jsonify({"message": "待办事项内容不能为空。"}), 400

    with DATA_LOCK:
        data = load_data_unlocked()
        space = data["spaces"].get(code)
        if space is None:
            return jsonify({"message": "未找到对应的清单。"}), 404

        is_owner = owner_token == space["owner_token"]
        if not (space["shared"] or is_owner):
            return unauthorized_private_response()

        todo = {
            "id": space["next_id"],
            "content": content,
            "completed": False,
        }
        space["next_id"] += 1
        space["todos"].append(todo)
        space["updated_at"] = utc_now()
        save_data_unlocked(data)

        return jsonify(
            {
                "message": "待办事项已添加。",
                "space": build_space_response(space, is_owner),
            }
        )


@app.post("/api/todos/<int:todo_id>/complete")
def complete_todo(todo_id):
    _, code, owner_token = get_code_and_token()

    if not is_valid_code(code):
        return jsonify({"message": "请输入正确的 6 位数字准入码。"}), 400

    with DATA_LOCK:
        data = load_data_unlocked()
        space = data["spaces"].get(code)
        if space is None:
            return jsonify({"message": "未找到对应的清单。"}), 404

        is_owner = owner_token == space["owner_token"]
        if not (space["shared"] or is_owner):
            return unauthorized_private_response()

        for todo in space["todos"]:
            if todo["id"] == todo_id:
                todo["completed"] = True
                space["updated_at"] = utc_now()
                save_data_unlocked(data)
                return jsonify(
                    {
                        "message": "任务已标记为完成。",
                        "space": build_space_response(space, is_owner),
                    }
                )

        return jsonify({"message": "未找到对应的待办事项。"}), 404


@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    _, code, owner_token = get_code_and_token()

    if not is_valid_code(code):
        return jsonify({"message": "请输入正确的 6 位数字准入码。"}), 400

    with DATA_LOCK:
        data = load_data_unlocked()
        space = data["spaces"].get(code)
        if space is None:
            return jsonify({"message": "未找到对应的清单。"}), 404

        is_owner = owner_token == space["owner_token"]
        if not (space["shared"] or is_owner):
            return unauthorized_private_response()

        original_length = len(space["todos"])
        space["todos"] = [todo for todo in space["todos"] if todo["id"] != todo_id]
        if len(space["todos"]) == original_length:
            return jsonify({"message": "未找到对应的待办事项。"}), 404

        space["updated_at"] = utc_now()
        save_data_unlocked(data)

        return jsonify(
            {
                "message": "任务已删除。",
                "space": build_space_response(space, is_owner),
            }
        )


@app.delete("/api/todos")
def clear_todos():
    _, code, owner_token = get_code_and_token()

    if not is_valid_code(code):
        return jsonify({"message": "请输入正确的 6 位数字准入码。"}), 400

    with DATA_LOCK:
        data = load_data_unlocked()
        space = data["spaces"].get(code)
        if space is None:
            return jsonify({"message": "未找到对应的清单。"}), 404

        is_owner = owner_token == space["owner_token"]
        if not (space["shared"] or is_owner):
            return unauthorized_private_response()

        space["todos"] = []
        space["updated_at"] = utc_now()
        save_data_unlocked(data)

        return jsonify(
            {
                "message": "已清空全部待办事项。",
                "space": build_space_response(space, is_owner),
            }
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
