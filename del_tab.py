import psycopg2

with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
    with conn.cursor() as cur:  # ________________________________________________________________тут
        cur.execute("""
            DROP TABLE user_words
        """)
        cur.execute("""
            DROP TABLE words
        """)
        cur.execute("""
            DROP TABLE users
        """)


