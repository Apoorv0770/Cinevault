import os

def generate_real_data():
    sql = """-- ============================================================
-- CineVault V2 — Real Movie Data Seed 
-- (Generated offline to bypass TMDB API auth requirements)
-- ============================================================

USE cinevault;

-- Clear previous movies
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE movies;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Insert High-Fidelity Movies
INSERT IGNORE INTO movies (id, title, release_year, director, rating_pg, duration_min, language, country, box_office_gross, imdb_score, metascore, genres, plot, poster_url, trailer_url) VALUES
(1, 'Interstellar', 2014, 'Christopher Nolan', 'PG-13', 169, 'English', 'USA', '$700M+', 8.6, 74, 'Sci-Fi, Drama, Adventure', 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity''s survival.', 'https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg', 'https://youtube.com/watch?v=zSWdZVtXT7E'),
(2, 'The Dark Knight', 2008, 'Christopher Nolan', 'PG-13', 152, 'English', 'USA', '$1.00B+', 9.0, 84, 'Action, Crime, Drama', 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.', 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg', 'https://youtube.com/watch?v=EXeTwQWrcwY'),
(3, 'Dune: Part Two', 2024, 'Denis Villeneuve', 'PG-13', 166, 'English', 'USA', '$700M+', 8.8, 79, 'Sci-Fi, Adventure', 'Paul Atreides unites with Chani and the Fremen while on a warpath of revenge against the conspirators who destroyed his family.', 'https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2JGqqUT1O.jpg', 'https://youtube.com/watch?v=U2Qp5pL3ovA'),
(4, 'Blade Runner 2049', 2017, 'Denis Villeneuve', 'R', 164, 'English', 'USA', '$259M+', 8.0, 81, 'Sci-Fi, Thriller', 'Young Blade Runner K''s discovery of a long-buried secret leads him to track down former Blade Runner Rick Deckard, who''s been missing for thirty years.', 'https://image.tmdb.org/t/p/w500/gajva2L0rPYkEWjzgFlBXCAVBE5.jpg', 'https://youtube.com/watch?v=gCcx85zbxz4'),
(5, 'Inception', 2010, 'Christopher Nolan', 'PG-13', 148, 'English', 'USA', '$836M+', 8.8, 74, 'Action, Sci-Fi', 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.', 'https://image.tmdb.org/t/p/w500/oYuLEt3zVCKq57qu2F8dT7NIa6f.jpg', 'https://youtube.com/watch?v=YoHD9XEInc0'),
(6, 'Mad Max: Fury Road', 2015, 'George Miller', 'R', 120, 'English', 'Australia', '$375M+', 8.1, 90, 'Action, Adventure, Sci-Fi', 'In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler in search for her homeland with the aid of a group of female prisoners, a psychotic worshiper, and a drifter named Max.', 'https://image.tmdb.org/t/p/w500/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg', 'https://youtube.com/watch?v=hEJnMQG9lN8'),
(7, 'Oppenheimer', 2023, 'Christopher Nolan', 'R', 180, 'English', 'USA', '$950M+', 8.4, 88, 'Biography, Drama, History', 'The story of American scientist, J. Robert Oppenheimer, and his role in the development of the atomic bomb.', 'https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg', 'https://youtube.com/watch?v=uYPbbksJxIg'),
(8, 'Spider-Man: Across the Spider-Verse', 2023, 'Joaquim Dos Santos', 'PG', 140, 'English', 'USA', '$690M+', 8.6, 86, 'Animation, Action, Adventure', 'Miles Morales catapults across the Multiverse, where he encounters a team of Spider-People charged with protecting its very existence.', 'https://image.tmdb.org/t/p/w500/8Vt6mWEReuy4Of61Lnj5Xj704m8.jpg', 'https://youtube.com/watch?v=shW9i6k8cB0'),
(9, 'Parasite', 2019, 'Bong Joon Ho', 'R', 132, 'Korean', 'South Korea', '$262M+', 8.5, 96, 'Drama, Thriller, Comedy', 'Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.', 'https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg', 'https://youtube.com/watch?v=5xH0HfJHsaY'),
(10, 'Everything Everywhere All at Once', 2022, 'Daniel Kwan', 'R', 139, 'English', 'USA', '$143M+', 7.8, 81, 'Action, Adventure, Comedy', 'An aging Chinese immigrant is swept up in an insane adventure, in which she alone can save the world by exploring other universes connecting with the lives she could have led.', 'https://image.tmdb.org/t/p/w500/w3LxiVYdWWRvEVdn5RYq6jIqkb1.jpg', 'https://youtube.com/watch?v=wxN1T1uxQ2g'),
(11, 'The Matrix', 1999, 'Lana Wachowski', 'R', 136, 'English', 'USA', '$467M+', 8.7, 73, 'Action, Sci-Fi', 'When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth--the life he knows is the elaborate deception of an evil cyber-intelligence.', 'https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg', 'https://youtube.com/watch?v=vKQi3bBA1y8'),
(12, 'Pulp Fiction', 1994, 'Quentin Tarantino', 'R', 154, 'English', 'USA', '$213M+', 8.9, 94, 'Crime, Drama', 'The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.', 'https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg', 'https://youtube.com/watch?v=s7EdQ4FqbhY');

-- Update the trending metrics so recommenders function
TRUNCATE TABLE trending;
INSERT IGNORE INTO trending (movie_id, view_count, score, last_calculated) VALUES
(1, 4500, 8500, NOW()),
(3, 8500, 9900, NOW()),
(2, 6000, 8800, NOW()),
(7, 4000, 7500, NOW()),
(8, 5500, 8200, NOW());

-- Update Editorials for the Featured Block
TRUNCATE TABLE editorials;
INSERT IGNORE INTO editorials (movie_id, author_id, headline, tag, content) VALUES
(3, 1, 'Return to Arrakis: A Masterpiece', 'Must Watch', 'Villeneuve exceeds all expectations in this stunning second chapter. A cinematic triumph that demands to be seen on the biggest screen possible.'),
(10, 1, 'The Multiverse Done Right', 'Editor Choice', 'A beautiful, chaotic dive into existentialism via martial arts and hot dog fingers.');
"""
    with open('real_data.sql', 'w', encoding='utf-8') as f:
        f.write(sql)
    print("Generated real_data.sql successfully.")

if __name__ == "__main__":
    generate_real_data()
