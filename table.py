import psycopg2

with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
    with conn.cursor() as cur:  # ________________________________________________________________тут
        cur.execute("""
            SELECT * FROM users
        """)
        print('users -', cur.fetchall())


with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
    with conn.cursor() as cur:  # ________________________________________________________________тут
        cur.execute("""
            SELECT * FROM words
        """)
        print('words -', cur.fetchall())



with psycopg2.connect(database="tg", user="postgres", password='2024p09114') as conn:
    with conn.cursor() as cur:  # ________________________________________________________________тут
        cur.execute("""
            SELECT * FROM user_words
        """)
        print('word_users -', cur.fetchall())