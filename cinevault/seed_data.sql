-- ============================================================
-- CineVault — Additional Realistic Seed Data
-- ============================================================

USE cinevault;

-- 1. Insert Additional Mock Users
INSERT IGNORE INTO users (id, username, email, password_hash, bio) VALUES
(1, 'cine_fanatic', 'fan@example.com', '$2b$12$R.S.eXn/gP/bVQK8eBx7g.E3F11r7A9S.QZz4c24Q1vN5bK6aD.fO', 'I love all movies! Avid watcher.'),
(2, 'kritik_k', 'kritik@example.com', '$2b$12$R.S.eXn/gP/bVQK8eBx7g.E3F11r7A9S.QZz4c24Q1vN5bK6aD.fO', 'Film school grad. Looking for the deep cut cinema.'),
(3, 'casual_viewer', 'casual@example.com', '$2b$12$R.S.eXn/gP/bVQK8eBx7g.E3F11r7A9S.QZz4c24Q1vN5bK6aD.fO', 'Just here for blockbusters and popcorn flicks.'),
(4, 'sci_fi_geek', 'scifi@example.com', '$2b$12$R.S.eXn/gP/bVQK8eBx7g.E3F11r7A9S.QZz4c24Q1vN5bK6aD.fO', 'Space, time travel, and beyond.'),
(5, 'drama_llama', 'drama@example.com', '$2b$12$R.S.eXn/gP/bVQK8eBx7g.E3F11r7A9S.QZz4c24Q1vN5bK6aD.fO', 'Tearjerkers are my favorite.');

-- 2. Insert User Reviews (Simulates active community feedback)
INSERT IGNORE INTO reviews (user_id, movie_id, rating, comment, likes_count) VALUES
(1, 1, 9, 'Avengers: Endgame is an emotional rollercoaster and a fitting conclusion. Highly recommend!', 14),
(1, 6, 8, 'Dune Part Two completely blew me away. The visuals are stunning.', 22),
(2, 7, 10, 'A cinematic masterpiece from Nolan. The sound design alone is unparalleled.', 45),
(2, 8, 9, 'Poor Things is beautifully bizarre. Emma Stone gave the performance of a lifetime.', 30),
(3, 3, 6, 'Bad Boys was fun but nowhere near the originals. It is a good time-killer.', 5),
(3, 5, 7, 'The Fall Guy had great action. Ryan Gosling is hilarious as always.', 12),
(4, 9, 10, 'Interstellar remains one of the best space movies ever created.', 55),
(4, 6, 9, 'A stunning adaptation of the book. Villeneuve crafted an immersive world.', 40),
(5, 10, 10, 'Parasite is flawlessly directed and scripted. A true modern masterpiece.', 62),
(5, 7, 9, 'Fascinating story and deeply dramatic, but very long.', 15);

-- 3. Insert Watchlists (To test ML routing branch logic)
-- User 1 (cine_fanatic): Has > 3 Watchlists -> Triggers "Content-Based Filter (Genre Overlap)"
INSERT IGNORE INTO watchlist (user_id, movie_id, status) VALUES
(1, 2, 'want_to_watch'),
(1, 5, 'completed'),
(1, 7, 'watching'),
(1, 8, 'want_to_watch');

-- User 2 (kritik_k): Has > 3 Reviews & < 3 Watchlists -> Triggers "User-Based Collaborative Filtering"
INSERT IGNORE INTO watchlist (user_id, movie_id, status) VALUES
(2, 10, 'want_to_watch');

-- User 3 (casual_viewer): Has Watchlists
INSERT IGNORE INTO watchlist (user_id, movie_id, status) VALUES
(3, 1, 'completed'),
(3, 3, 'completed'),
(3, 6, 'want_to_watch');

-- 4. Update Trending Metrics for UI 
UPDATE trending SET score = score + 500, view_count = view_count + 1500 WHERE movie_id = 7;
UPDATE trending SET score = score + 450, view_count = view_count + 1000 WHERE movie_id = 10;
