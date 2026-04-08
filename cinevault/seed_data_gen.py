import mysql.connector
import random
from datetime import datetime, timedelta

def insert_seed_data(host, user, password, database):
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        
        # 1. Create fake users
        users = [
            ("cine_fanatic", "fan@example.com", "randomhash1", "I love all movies!"),
            ("kritik_k", "kritik@example.com", "randomhash2", "Film school grad."),
            ("casual_viewer", "casual@example.com", "randomhash3", "Just here for blockbusters."),
            ("sci_fi_geek", "scifi@example.com", "randomhash4", "Space and beyond."),
            ("rom_com_queen", "romcom@example.com", "randomhash5", "Love is in the air.")
        ]
        
        cursor.executemany("""
            INSERT IGNORE INTO users (username, email, password_hash, bio)
            VALUES (%s, %s, %s, %s)
        """, users)
        
        # 2. Get user ids
        cursor.execute("SELECT id, username FROM users")
        user_records = cursor.fetchall()
        user_ids = [row[0] for row in user_records]
        
        # 3. Get movie ids
        cursor.execute("SELECT id FROM movies")
        movie_ids = [row[0] for row in cursor.fetchall()]
        
        # 4. Insert Reviews
        reviews = []
        for uid in user_ids:
            # Randomly select a few movies to review
            num_reviews = random.randint(2, 5)
            reviewed_movies = random.sample(movie_ids, num_reviews)
            for mid in reviewed_movies:
                rating = random.randint(5, 10)
                comment = f"A great movie! Giving it a solid {rating} out of 10."
                reviews.append((uid, mid, rating, comment, random.randint(0, 10)))
        
        cursor.executemany("""
            INSERT IGNORE INTO reviews (user_id, movie_id, rating, comment, likes_count)
            VALUES (%s, %s, %s, %s, %s)
        """, reviews)
        
        # 5. Insert Watchlists
        watchlists = []
        statuses = ['want_to_watch', 'watching', 'completed']
        for uid in user_ids:
            num_lists = random.randint(3, 7)
            listed_movies = random.sample(movie_ids, num_lists)
            for mid in listed_movies:
                watchlists.append((uid, mid, random.choice(statuses)))
                
        cursor.executemany("""
            INSERT IGNORE INTO watchlist (user_id, movie_id, status)
            VALUES (%s, %s, %s)
        """, watchlists)
        
        conn.commit()
        print("Successfully inserted additional mock users, reviews, and watchlists.")
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")

if __name__ == '__main__':
    # Can be run after DB is setup
    pass
