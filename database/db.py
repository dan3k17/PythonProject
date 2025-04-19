import psycopg2
from psycopg2 import pool
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

db_pool = None

def create_db_pool():
    global db_pool
    db_pool = psycopg2.pool.SimpleConnectionPool(
        1, 20,  # Минимальное и максимальное количество соединений
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return db_pool

def create_table():
    conn = db_pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        age INTEGER NOT NULL,
                        gender TEXT NOT NULL,
                        weight REAL NOT NULL,
                        height INTEGER NOT NULL,
                        allergies TEXT,
                        goal TEXT NOT NULL,
                        timeframe TEXT NOT NULL
                    );
                """)
                conn.commit()
        print("✅ Таблица 'users' готова!")
    finally:
        db_pool.putconn(conn)

def save_user_to_db(user_data):
    conn = db_pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (user_id, name, age, gender, weight, height, allergies, goal, timeframe)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        age = EXCLUDED.age,
                        gender = EXCLUDED.gender,
                        weight = EXCLUDED.weight,
                        height = EXCLUDED.height,
                        allergies = EXCLUDED.allergies,
                        goal = EXCLUDED.goal,
                        timeframe = EXCLUDED.timeframe;
                """, (
                    user_data["user_id"], user_data["name"], user_data["age"], user_data["gender"],
                    user_data["weight"], user_data["height"], user_data["allergies"],
                    user_data["goal"], user_data["timeframe"]
                ))
                conn.commit()
    finally:
        db_pool.putconn(conn)

def delete_user_from_db(user_id):
    conn = db_pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE user_id = %s;", (user_id,))
                conn.commit()
    finally:
        db_pool.putconn(conn)

def get_user_data(user_id):
    conn = db_pool.getconn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, name, age, gender, weight, height, allergies, goal, timeframe 
                    FROM users WHERE user_id = %s;
                """, (user_id,))
                result = cur.fetchone()
                if result:
                    return {
                        "user_id": result[0],
                        "name": result[1],
                        "age": result[2],
                        "gender": result[3],
                        "weight": result[4],
                        "height": result[5],
                        "allergies": result[6],
                        "goal": result[7],
                        "timeframe": result[8]
                    }
                return None
    finally:
        db_pool.putconn(conn)

def on_startup():
    global db_pool
    db_pool = create_db_pool()
    create_table()
def on_shutdown():
    global db_pool
    if db_pool:
        db_pool.closeall()
        print("⛔ Соединение с БД закрыто.")