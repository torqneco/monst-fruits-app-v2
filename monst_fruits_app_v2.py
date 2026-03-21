import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st
import csv
import io
CSV_HEADERS = [
    "account_id",
    "character",
    "fruit1",
    "fruit2",
    "fruit3",
    "fruit4",
    "note",
]


# -----------------------
# DB
# -----------------------
def init_db():
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS game_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        account_name TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        character TEXT NOT NULL,
        fruit1 TEXT,
        fruit2 TEXT,
        fruit3 TEXT,
        fruit4 TEXT,
        note TEXT,
        updated_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def add_account(user_id, account_name):
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO game_accounts (user_id, account_name) VALUES (?, ?)",
        (user_id, account_name)
    )

    conn.commit()
    conn.close()


def get_accounts(user_id):
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()

    c.execute(
        "SELECT id, account_name FROM game_accounts WHERE user_id = ?",
        (user_id,)
    )

    accounts = c.fetchall()
    conn.close()
    return accounts


def delete_account(account_id):
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()

    c.execute("DELETE FROM game_accounts WHERE id = ?", (account_id,))
    c.execute("DELETE FROM entries WHERE account_id = ?", (account_id,))

    conn.commit()
    conn.close()


def add_entry(account_id, character, fruit1, fruit2, fruit3, fruit4, note):
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    c.execute(
        """
        INSERT INTO entries (account_id, character, fruit1, fruit2, fruit3, fruit4, note, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (account_id, character, fruit1, fruit2, fruit3, fruit4, note, now)
    )

    conn.commit()
    conn.close()


def get_entries(account_id, char_q=None, fruit_q=None, note_q=None):
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()

    q = """
    SELECT id, character, fruit1, fruit2, fruit3, fruit4, note, updated_at
    FROM entries
    WHERE account_id = ?
    """
    params = [account_id]

    if char_q:
        q += " AND character LIKE ?"
        params.append(f"%{char_q}%")

    if fruit_q:
        q += " AND (fruit1 LIKE ? OR fruit2 LIKE ? OR fruit3 LIKE ? OR fruit4 LIKE ?)"
        params.extend([f"%{fruit_q}%"] * 4)

    if note_q:
        q += " AND note LIKE ?"
        params.append(f"%{note_q}%")

    q += " ORDER BY updated_at DESC"

    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows
def update_entry(entry_id, fruit1, fruit2, fruit3, fruit4, note):
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    c.execute(
        """
        UPDATE entries
        SET fruit1 = ?, fruit2 = ?, fruit3 = ?, fruit4 = ?, note = ?, updated_at = ?
        WHERE id = ?
        """,
        (fruit1, fruit2, fruit3, fruit4, note, now, entry_id)
    )

    conn.commit()
    conn.close()
def delete_entry(entry_id):
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()

    c.execute("DELETE FROM entries WHERE id = ?", (entry_id,))

    conn.commit()
    conn.close()
def rows_to_csv_bytes(rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_HEADERS)
    writer.writeheader()

    for r in rows:
        writer.writerow({
            "account_id": r[0],
            "character": r[1],
            "fruit1": r[2] or "",
            "fruit2": r[3] or "",
            "fruit3": r[4] or "",
            "fruit4": r[5] or "",
            "note": r[6] or "",
        })

    return output.getvalue().encode("utf-8")
def csv_file_to_rows(uploaded_file):
    text = uploaded_file.read().decode("utf-8")
    f = io.StringIO(text)
    reader = csv.DictReader(f)

    rows = []
    for row in reader:
        rows.append({
            k: (v.strip() if isinstance(v, str) else v)
            for k, v in row.items()
        })

    return rows
def insert_many(rows):
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    c.executemany(
        """
        INSERT INTO entries (account_id, character, fruit1, fruit2, fruit3, fruit4, note, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                int(r.get("account_id") or 0),
                (r.get("character") or ""),
                (r.get("fruit1") or None),
                (r.get("fruit2") or None),
                (r.get("fruit3") or None),
                (r.get("fruit4") or None),
                (r.get("note") or None),
                now,
            )
            for r in rows
            if (r.get("character") or "").strip() != ""
        ],
    )
    conn.commit()
    conn.close()

def split_fruit_and_grade(value):
    if not value:
        return "", ""
    if value.endswith("特L"):
        return value[:-2], "特L"
    if value.endswith("EL"):
        return value[:-2], "EL"
    return value, ""

def combine(fruit, grade):
    if not fruit:
        return None
    return f"{fruit}{grade}" if grade else fruit
def clear_add_inputs():
    st.session_state["character_name"] = ""
    st.session_state["fruit1_select"] = ""
    st.session_state["grade1_select"] = ""
    st.session_state["fruit2_select"] = ""
    st.session_state["grade2_select"] = ""
    st.session_state["fruit3_select"] = ""
    st.session_state["grade3_select"] = ""
    st.session_state["fruit4_select"] = ""
    st.session_state["grade4_select"] = ""
    st.session_state["note_input"] = ""
def handle_add_entry(selected_account_id, selected_account_name):
    character_name = st.session_state.get("character_name", "")
    fruit1 = st.session_state.get("fruit1_select", "")
    grade1 = st.session_state.get("grade1_select", "")
    fruit2 = st.session_state.get("fruit2_select", "")
    grade2 = st.session_state.get("grade2_select", "")
    fruit3 = st.session_state.get("fruit3_select", "")
    grade3 = st.session_state.get("grade3_select", "")
    fruit4 = st.session_state.get("fruit4_select", "")
    grade4 = st.session_state.get("grade4_select", "")
    note = st.session_state.get("note_input", "")

    fruit1_value = combine(fruit1, grade1)
    fruit2_value = combine(fruit2, grade2)
    fruit3_value = combine(fruit3, grade3)
    fruit4_value = combine(fruit4, grade4)

    if character_name.strip():
        add_entry(
            selected_account_id,
            character_name,
            fruit1_value,
            fruit2_value,
            fruit3_value,
            fruit4_value,
            note
        )
        clear_add_inputs()
        st.session_state["add_success"] = f"{selected_account_name} に {character_name} を追加した"
        st.session_state["add_error"] = ""
    else:
        st.session_state["add_error"] = "キャラ名を入れて"
        st.session_state["add_success"] = ""
def get_user_by_name(username):
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()

    c.execute(
        "SELECT id, username FROM users WHERE username = ?",
        (username,)
    )

    user = c.fetchone()
    conn.close()
    return user


def create_user(username):
    conn = sqlite3.connect("monster_app.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO users (username) VALUES (?)",
        (username,)
    )

    conn.commit()
    user_id = c.lastrowid
    conn.close()
    return user_id
def login_or_create_user(username):
    user = get_user_by_name(username)

    if user:
        return user[0]  # id
    else:
        return create_user(username)
# -----------------------
# 初期化
# -----------------------
init_db()


GRADE_OPTIONS = ["", "EL", "特L"]
FRUIT_OPTIONS = [
    "",

    # 同族系
    "同族加撃",
    "同族加命",
    "同族加命撃",
    "同族加撃速",

    # 撃種系
    "撃種加撃",
    "撃種加命",
    "撃種加命撃",
    "撃種加撃速",

    # 戦型系
    "戦型加撃",
    "戦型加命",
    "戦型加命撃",
    "戦型加撃速",

    # 火力系
    "熱き友撃",
    "速必殺",

    # HP削り
    "将命削り",
    "兵命削り",

    # 耐久系
    "ケガ減り",
    "ちび癒し",

    # 状態異常
    "毒がまん",
    "麻痺がまん",

    # 不屈系
    "不屈の必殺",
    "不屈の防御",

    # 周回系
    "学び",
    "スコア稼ぎ",
    "Sランク",
    "荒稼ぎ",

    # その他（追加されてたらここに）
]

# UI
# -----------------------
st.title("モンストアプリ v2")

if "logged_in_user_id" not in st.session_state:
    st.session_state["logged_in_user_id"] = None

if "logged_in_username" not in st.session_state:
    st.session_state["logged_in_username"] = ""

if st.session_state["logged_in_user_id"] is None:
    st.subheader("ログイン")

    login_name = st.text_input("ユーザー名", key="login_name")

    if st.button("ログイン / 新規作成", key="login_button"):
        if login_name.strip():
            user_id = login_or_create_user(login_name.strip())
            st.session_state["logged_in_user_id"] = user_id
            st.session_state["logged_in_username"] = login_name.strip()
            st.rerun()
        else:
            st.error("ユーザー名を入れて")

if st.session_state["logged_in_user_id"] is not None:
    USER_ID = st.session_state["logged_in_user_id"]

    st.success(f"ログイン中: {st.session_state['logged_in_username']}")

    if st.button("ログアウト", key="logout_button"):
        st.session_state["logged_in_user_id"] = None
        st.session_state["logged_in_username"] = ""
        st.rerun()

    accounts = get_accounts(USER_ID)

    # -----------------------
    # アカウント管理
    # -----------------------
    st.subheader("アカウント管理")

    new_account = st.text_input("アカウント名", key="new_account")

    if st.button("アカウント追加", key="add_account_button"):
        if new_account.strip():
            add_account(USER_ID, new_account.strip())
            st.success("追加した")
            st.rerun()
        else:
            st.error("名前入れて")

    if accounts:
        st.write("### アカウント一覧")

        for acc in accounts:
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(acc[1])

            with col2:
                if st.button("削除", key=f"delete_{acc[0]}"):
                    delete_account(acc[0])
                    st.rerun()
    else:
        st.write("まだアカウントがありません")

# -----------------------
# 選択中アカウント
# -----------------------
selected_account_id = None
selected_account_name = None

if accounts:
    account_options = {acc[1]: acc[0] for acc in accounts}
    selected_account_name = st.selectbox("アカウントを選択", list(account_options.keys()))
    selected_account_id = account_options[selected_account_name]

    st.write(f"選択中: {selected_account_name} / ID: {selected_account_id}")


# -----------------------
# キャラ管理
# -----------------------
if selected_account_id is not None:
    tab_manage, tab_add = st.tabs(["📋 一覧・検索・編集・バックアップ", "➕ 追加"])

    with tab_manage:
        # --- 検索 ---
        st.write("### 検索")

        col1, col2, col3 = st.columns(3)

        with col1:
            char_q = st.text_input("キャラ名", key="search_character")

        with col2:
            fruit_q = st.text_input("実", key="search_fruit")

        with col3:
            note_q = st.text_input("メモ", key="search_note")

        # --- 一覧 ---
        st.write("### キャラ一覧")

        entries = get_entries(
            selected_account_id,
            char_q=char_q.strip() or None,
            fruit_q=fruit_q.strip() or None,
            note_q=note_q.strip() or None,
        )

        if entries:
            import pandas as pd

            table_data = []
            for entry in entries:
                table_data.append({
                    "キャラ": entry[1],
                    "実1": entry[2] or "-",
                    "実2": entry[3] or "-",
                    "実3": entry[4] or "-",
                    "実4": entry[5] or "-",
                    "メモ": entry[6] or "-",
                    "更新": entry[7],
                })

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.write("まだキャラがありません")

        # --- 編集 ---
        if entries:
            st.write("### 編集")

            entry_options = {
                f"{entry[1]} / 更新: {entry[7]}": entry[0]
                for entry in entries
            }

            selected_entry_label = st.selectbox(
                "編集するキャラを選択",
                list(entry_options.keys()),
                key="edit_target"
            )
            selected_entry_id = entry_options[selected_entry_label]

            selected_entry = next(e for e in entries if e[0] == selected_entry_id)

            fruit1_name, grade1 = split_fruit_and_grade(selected_entry[2])
            fruit2_name, grade2 = split_fruit_and_grade(selected_entry[3])
            fruit3_name, grade3 = split_fruit_and_grade(selected_entry[4])
            fruit4_name, grade4 = split_fruit_and_grade(selected_entry[5])

            edit_fruit1 = st.selectbox(
                "編集 実1",
                FRUIT_OPTIONS,
                index=FRUIT_OPTIONS.index(fruit1_name) if fruit1_name in FRUIT_OPTIONS else 0,
                key="edit_fruit1"
            )
            edit_grade1 = st.selectbox(
                "編集 等級1",
                GRADE_OPTIONS,
                index=GRADE_OPTIONS.index(grade1) if grade1 in GRADE_OPTIONS else 0,
                key="edit_grade1"
            )

            edit_fruit2 = st.selectbox(
                "編集 実2",
                FRUIT_OPTIONS,
                index=FRUIT_OPTIONS.index(fruit2_name) if fruit2_name in FRUIT_OPTIONS else 0,
                key="edit_fruit2"
            )
            edit_grade2 = st.selectbox(
                "編集 等級2",
                GRADE_OPTIONS,
                index=GRADE_OPTIONS.index(grade2) if grade2 in GRADE_OPTIONS else 0,
                key="edit_grade2"
            )

            edit_fruit3 = st.selectbox(
                "編集 実3",
                FRUIT_OPTIONS,
                index=FRUIT_OPTIONS.index(fruit3_name) if fruit3_name in FRUIT_OPTIONS else 0,
                key="edit_fruit3"
            )
            edit_grade3 = st.selectbox(
                "編集 等級3",
                GRADE_OPTIONS,
                index=GRADE_OPTIONS.index(grade3) if grade3 in GRADE_OPTIONS else 0,
                key="edit_grade3"
            )

            edit_fruit4 = st.selectbox(
                "編集 実4",
                FRUIT_OPTIONS,
                index=FRUIT_OPTIONS.index(fruit4_name) if fruit4_name in FRUIT_OPTIONS else 0,
                key="edit_fruit4"
            )
            edit_grade4 = st.selectbox(
                "編集 等級4",
                GRADE_OPTIONS,
                index=GRADE_OPTIONS.index(grade4) if grade4 in GRADE_OPTIONS else 0,
                key="edit_grade4"
            )

            edit_note = st.text_area(
                "編集 メモ",
                value=selected_entry[6] or "",
                key="edit_note"
            )

            if st.button("この内容で更新", key="update_entry_button"):
                update_entry(
                    selected_entry_id,
                    combine(edit_fruit1, edit_grade1),
                    combine(edit_fruit2, edit_grade2),
                    combine(edit_fruit3, edit_grade3),
                    combine(edit_fruit4, edit_grade4),
                    edit_note
                )
                st.success("更新した")
                st.rerun()

            if st.button("このキャラを削除", key="delete_entry_button"):
                delete_entry(selected_entry_id)
                st.success("削除した")
                st.rerun()

        # --- バックアップ ---
        st.write("### バックアップ")

        backup_rows = get_entries(selected_account_id)

        csv_ready_rows = [
            (
                selected_account_id,
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
            )
            for row in backup_rows
        ]

        csv_bytes = rows_to_csv_bytes(csv_ready_rows)

        st.download_button(
            label="CSVをダウンロード",
            data=csv_bytes,
            file_name=f"{selected_account_name}_backup.csv",
            mime="text/csv",
        )

        st.write("### CSV取り込み")

        uploaded = st.file_uploader("CSVを選択", type=["csv"], key="csv_uploader")

        if uploaded is not None:
            try:
                rows_in = csv_file_to_rows(uploaded)

                if not rows_in:
                    st.error("CSVにデータがありません")
                else:
                    missing = [h for h in CSV_HEADERS if h not in rows_in[0]]

                    if missing:
                        st.error(f"CSVの列が足りない: {missing}")
                    else:
                        if st.button("取り込み実行", key="csv_import_button"):
                            insert_many(rows_in)
                            st.success(f"取り込み完了！（{len(rows_in)}件）")
                            st.rerun()

            except Exception as e:
                st.error(f"読み込み失敗: {e}")

    with tab_add:
        st.subheader("キャラ追加")

        character_name = st.text_input("キャラ名", key="character_name")

        fruit1 = st.selectbox("実1", FRUIT_OPTIONS, key="fruit1_select")
        grade1 = st.selectbox("等級1", GRADE_OPTIONS, key="grade1_select")

        fruit2 = st.selectbox("実2", FRUIT_OPTIONS, key="fruit2_select")
        grade2 = st.selectbox("等級2", GRADE_OPTIONS, key="grade2_select")

        fruit3 = st.selectbox("実3", FRUIT_OPTIONS, key="fruit3_select")
        grade3 = st.selectbox("等級3", GRADE_OPTIONS, key="grade3_select")

        fruit4 = st.selectbox("実4", FRUIT_OPTIONS, key="fruit4_select")
        grade4 = st.selectbox("等級4", GRADE_OPTIONS, key="grade4_select")

        note = st.text_area("メモ", key="note_input")

        st.button(
            "このアカウントにキャラ追加",
            key="add_entry_button",
            on_click=handle_add_entry,
            args=(selected_account_id, selected_account_name),
        )

        if st.session_state.get("add_success"):
            st.success(st.session_state["add_success"])

        if st.session_state.get("add_error"):
            st.error(st.session_state["add_error"])
