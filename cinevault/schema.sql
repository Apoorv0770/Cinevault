-- ============================================================
-- CineVault — Complete Database Schema (v2)
-- Run: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS cinevault;
USE cinevault;

-- ------------------------------------------------------------
-- TABLE 1: users
-- Added: bio, avatar_url, is_admin for profile feature
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    bio           TEXT,
    avatar_url    VARCHAR(500),
    is_admin      BOOLEAN DEFAULT FALSE,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- TABLE 2: movies
-- Added: director, cast_list, language, country, box_office_gross
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movies (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    title             VARCHAR(200) NOT NULL,
    release_year      INT          NOT NULL,
    rating_pg         VARCHAR(10),
    duration_min      INT,
    imdb_score        DECIMAL(3,1),
    metascore         INT,
    plot              TEXT,
    poster_url        VARCHAR(500),
    trailer_url       VARCHAR(500),
    director          VARCHAR(200),
    cast_list         TEXT,
    language          VARCHAR(100) DEFAULT 'English',
    country           VARCHAR(100) DEFAULT 'USA',
    box_office_gross  VARCHAR(50),
    is_featured       BOOLEAN DEFAULT FALSE,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- TABLE 3: genres
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS genres (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- ------------------------------------------------------------
-- TABLE 4: movie_genres (Junction Table)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INT NOT NULL,
    genre_id INT NOT NULL,
    PRIMARY KEY (movie_id, genre_id),
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE 5: box_office
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS box_office (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    movie_id INT NOT NULL,
    rank_num INT NOT NULL,
    gross    VARCHAR(20),
    week_of  DATE,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE 6: watchlist
-- Added: status (want_to_watch / watching / completed)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS watchlist (
    id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id  INT NOT NULL,
    movie_id INT NOT NULL,
    status   ENUM('want_to_watch','watching','completed') DEFAULT 'want_to_watch',
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_watchlist (user_id, movie_id),
    FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE 7: reviews
-- Added: likes_count for upvote feature
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    movie_id    INT NOT NULL,
    rating      TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 10),
    comment     TEXT,
    likes_count INT DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY one_review_per_user (user_id, movie_id),
    FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE 8: review_likes  (NEW)
-- Tracks which user liked which review (prevents double-likes)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_likes (
    user_id   INT NOT NULL,
    review_id INT NOT NULL,
    liked_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, review_id),
    FOREIGN KEY (user_id)   REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE 9: editorials
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS editorials (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(300) NOT NULL,
    body         TEXT,
    image_url    VARCHAR(500),
    tag          VARCHAR(100),
    published_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- TABLE 10: trending  (NEW)
-- Tracks a daily trending score for each movie
-- Updated by a background job or manually
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trending (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    movie_id    INT NOT NULL UNIQUE,
    score       INT DEFAULT 0,
    view_count  INT DEFAULT 0,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- TABLE 11: movie_views  (NEW)
-- Logs each time a movie detail page is viewed
-- Used to compute trending score
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS movie_views (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    movie_id   INT NOT NULL,
    user_id    INT,
    viewed_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE SET NULL
);


-- ============================================================
-- SEED DATA
-- ============================================================

INSERT IGNORE INTO genres (name) VALUES
('Action'), ('Adventure'), ('Sci-Fi'), ('Drama'),
('Comedy'), ('Animation'), ('Horror'), ('Thriller'),
('Romance'), ('Mystery'), ('Crime'), ('Fantasy');

INSERT IGNORE INTO movies
  (id, title, release_year, rating_pg, duration_min, imdb_score, metascore,
   director, cast_list, language, country, box_office_gross, plot, is_featured)
VALUES
(1, 'Avengers: Endgame', 2019, 'PG-13', 181, 8.4, 78,
 'Anthony Russo, Joe Russo',
 'Robert Downey Jr., Chris Evans, Scarlett Johansson, Mark Ruffalo',
 'English', 'USA', '$2.798B',
 'After the devastating events of Infinity War, the Avengers assemble once more to reverse Thanos'' actions and restore the universe.',
 TRUE),

(2, 'Inside Out 2', 2024, 'PG', 100, 7.8, 73,
 'Kelsey Mann',
 'Amy Poehler, Maya Hawke, Kensington Tallman',
 'English', 'USA', '$1.7B',
 'Riley enters adolescence and her emotions face new challenges inside Headquarters as a new emotion, Anxiety, arrives.',
 FALSE),

(3, 'Bad Boys: Ride or Die', 2024, 'R', 115, 6.1, 40,
 'Adil El Arbi, Bilall Fallah',
 'Will Smith, Martin Lawrence, Vanessa Hudgens',
 'English', 'USA', '$406M',
 'The Bad Boys go on the run after Miami''s greatest detective is implicated in the murder of the chief of police.',
 FALSE),

(4, 'The Watchers', 2024, 'PG-13', 102, 5.5, 45,
 'Ishana Night Shyamalan',
 'Dakota Fanning, Georgina Campbell, Oliver Finnegan',
 'English', 'USA', '$28M',
 'An artist gets stranded in an ancient forest in western Ireland where she and three strangers are watched by mysterious creatures each night.',
 FALSE),

(5, 'The Fall Guy', 2024, 'PG-13', 126, 7.0, 63,
 'David Leitch',
 'Ryan Gosling, Emily Blunt, Aaron Taylor-Johnson',
 'English', 'USA', '$180M',
 'A stuntman is pulled out of retirement to track down a missing movie star on the set of a massive studio picture.',
 FALSE),

(6, 'Dune: Part Two', 2024, 'PG-13', 167, 8.5, 79,
 'Denis Villeneuve',
 'Timothée Chalamet, Zendaya, Rebecca Ferguson, Josh Brolin',
 'English', 'USA', '$712M',
 'Paul Atreides unites with Chani and the Fremen while seeking revenge against those who destroyed his family.',
 FALSE),

(7, 'Oppenheimer', 2023, 'R', 180, 8.3, 88,
 'Christopher Nolan',
 'Cillian Murphy, Emily Blunt, Matt Damon, Robert Downey Jr.',
 'English', 'USA', '$952M',
 'The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb during World War II.',
 FALSE),

(8, 'Poor Things', 2023, 'R', 141, 8.0, 84,
 'Yorgos Lanthimos',
 'Emma Stone, Mark Ruffalo, Willem Dafoe',
 'English', 'UK', '$118M',
 'The incredible tale of Bella Baxter, a young woman brought back to life by brilliant surgeon, who embarks on a journey across the world.',
 FALSE),

(9, 'Interstellar', 2014, 'PG-13', 169, 8.7, 74,
 'Christopher Nolan',
 'Matthew McConaughey, Anne Hathaway, Jessica Chastain',
 'English', 'USA', '$773M',
 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity''s survival.',
 FALSE),

(10, 'Parasite', 2019, 'R', 132, 8.5, 96,
 'Bong Joon-ho',
 'Kang-ho Song, Sun-kyun Lee, Yeo-jeong Jo',
 'Korean', 'South Korea', '$258M',
 'Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.',
 FALSE);

INSERT IGNORE INTO movie_genres (movie_id, genre_id) VALUES
(1,1),(1,2),(1,3),
(2,6),(2,5),(2,4),
(3,1),(3,5),(3,4),
(4,8),(4,7),(4,10),
(5,1),(5,5),(5,2),
(6,2),(6,3),(6,4),
(7,4),(7,8),(7,11),
(8,4),(8,12),(8,5),
(9,3),(9,4),(9,2),
(10,4),(10,11),(10,8);

INSERT IGNORE INTO box_office (movie_id, rank_num, gross, week_of) VALUES
(2, 1, '$100M',  '2024-06-21'),
(3, 2, '$33.8M', '2024-06-21'),
(4, 3, '$7.1M',  '2024-06-21'),
(5, 4, '$2.8M',  '2024-06-21'),
(6, 5, '$18.2M', '2024-06-21');

INSERT IGNORE INTO editorials (title, body, image_url, tag) VALUES
('The 2024 Awards Season: Everything You Need to Know',
 'From underdog stories to box office giants, we breakdown the frontrunners for the upcoming ceremony.',
 'https://lh3.googleusercontent.com/aida-public/AB6AXuBoE2EWeGhfPSlCHmO5e0jH6tC1cCGbO-plpfMfKF3808OtiOvIR6-qs7AWKLevNchkBcIb4MVhME02qS0-RsKFKmw1OWnvknEiDqaEM-6P4S83IzVI1e4L1LTHsibGaHNJazkLNfAJ16zMk7f7V7yryee6Urobspmn1ktVQ0jBt3RiT4US6g5rVRLXp4sLJ84VXCttJiNeXhebphf0LUN06YslQrnxhWKWCx2qxCksXJRCENfAx03Ic364mi-3Grfiquj0SdjQknVm',
 'Editorial Spotlight'),
('Coming Soon in July',
 'Discover 12 new titles arriving this month.',
 'https://lh3.googleusercontent.com/aida-public/AB6AXuBsrKMEnUJl6QUlNZiC4T1JX3pjUiG0FsosRgeWm-MaYQJntIjBX1G_dCILvUixnzrofWI1JeOO3KOmhPVOhmFrrkh585IL8nZCxs54h4F4g5Vn5Dz4YsbSDavqmrgz4HceGLhAUvX4_jrTfx8McW_F8VcE7UUauZ8K1tQesV9qsSXtNjaEuZy9oJwPvC1ELkSw4Eb-nx-r6VBjdLVAJOU4eCsp-IhbXgc6mOYm8EWGhod2lpUIDiDm8wX3Ar_rLTvxy_z1fRl2NYr4',
 'Coming Soon'),
('Christopher Nolan: Master of the Blockbuster Masterpiece',
 'From Memento to Oppenheimer, we trace the arc of cinema''s most ambitious filmmaker and what makes his work so enduring.',
 'https://lh3.googleusercontent.com/aida-public/AB6AXuBoE2EWeGhfPSlCHmO5e0jH6tC1cCGbO-plpfMfKF3808OtiOvIR6-qs7AWKLevNchkBcIb4MVhME02qS0-RsKFKmw1OWnvknEiDqaEM-6P4S83IzVI1e4L1LTHsibGaHNJazkLNfAJ16zMk7f7V7yryee6Urobspmn1ktVQ0jBt3RiT4US6g5rVRLXp4sLJ84VXCttJiNeXhebphf0LUN06YslQrnxhWKWCx2qxCksXJRCENfAx03Ic364mi-3Grfiquj0SdjQknVm',
 'Director Spotlight');

INSERT IGNORE INTO trending (movie_id, score, view_count) VALUES
(1,950,12400),(2,870,9800),(6,820,8500),(7,790,7200),(9,740,6100),
(10,700,5800),(8,650,4900),(3,580,3400),(5,520,2900),(4,410,1800);
