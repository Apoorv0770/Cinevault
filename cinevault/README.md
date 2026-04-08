# CineVault — DBMS Capstone Project
### Entertainment Information, Review & Recommendation Platform
**Tech Stack:** Python Flask + MySQL + HTML/Tailwind CSS | **Version: 2.0**

---

## Project Structure
```
cinevault/
├── app.py                  # Entry point — Application Factory pattern
├── config.py               # DB credentials and settings
├── extensions.py           # Shared objects (mysql, cors)
├── requirements.txt        # Python dependencies
├── schema.sql              # Complete MySQL schema + seed data (v2)
│
├── blueprints/
│   ├── __init__.py
│   ├── movies.py           # Movies, search, trending, genres, editorials
│   ├── auth.py             # Register, Login, Logout, Profile, Change Password
│   ├── watchlist.py        # Add, Get (with status filter), Update status, Remove, Check
│   ├── reviews.py          # Add, Get (paginated), Delete, Like, User reviews
│   └── recommendations.py  # Genre-based, Collaborative, Top-rated, Similar, By-director
│
└── static/
    └── index.html          # Frontend with all API integrations
```

---

## Setup Instructions

### Step 1 — Install Python packages
```bash
pip install flask flask-mysqldb flask-cors bcrypt
```

### Step 2 — Set up MySQL database
```bash
mysql -u root -p < schema.sql
```

### Step 3 — Update database password
Edit `config.py` and set your MySQL password.

### Step 4 — Run the server
```bash
python app.py
```

### Step 5 — Open in browser
```
http://localhost:5000/
```

---

## API Endpoints (v2)

### Movies
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /api/movies/ | All movies. Supports `?genre=`, `?year=`, `?sort=`, `?order=` | No |
| GET | /api/movies/search?q= | Search by title, plot, director, cast | No |
| GET | /api/movies/featured | Hero movie | No |
| GET | /api/movies/trending | Top 10 trending by view score | No |
| GET | /api/movies/boxoffice | Box office rankings | No |
| GET | /api/movies/editorials | Editorial cards | No |
| GET | /api/movies/genres | All available genres | No |
| GET | /api/movies/<id> | Single movie (also bumps trending) | No |

### Auth & Profile
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/auth/register | Create account (validates email, username) | No |
| POST | /api/auth/login | Login | No |
| POST | /api/auth/logout | Logout | Yes |
| GET | /api/auth/me | Current user | No |
| GET | /api/auth/profile/<user_id> | Public profile + stats | No |
| PUT | /api/auth/profile | Update bio / avatar_url | Yes |
| POST | /api/auth/change-password | Change password | Yes |

### Watchlist
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/watchlist/add | Add (with optional status) | Yes |
| GET | /api/watchlist/ | Get list. Supports `?status=` filter | Yes |
| PUT | /api/watchlist/status/<movie_id> | Update watch status | Yes |
| DELETE | /api/watchlist/remove/<movie_id> | Remove | Yes |
| GET | /api/watchlist/check/<movie_id> | Is movie in watchlist? | Yes |

### Reviews
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/reviews/add | Submit review | Yes |
| GET | /api/reviews/<movie_id> | Paginated reviews. Supports `?page=`, `?per_page=` | No |
| DELETE | /api/reviews/<review_id> | Delete own review | Yes |
| POST | /api/reviews/like/<review_id> | Toggle like on a review | Yes |
| GET | /api/reviews/user/<user_id> | All reviews by a user | No |
| GET | /api/reviews/my/<movie_id> | My review for a movie | Yes |

### Recommendations
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /api/recommendations/ | Smart router (auto-picks strategy) | No |
| GET | /api/recommendations/genre-based | Genre-based content filtering | Yes |
| GET | /api/recommendations/collaborative | User-based collaborative filtering | Yes |
| GET | /api/recommendations/top-rated | Top rated fallback (cold start) | No |
| GET | /api/recommendations/similar/<id> | "More Like This" | No |
| GET | /api/recommendations/by-director/<id> | More by same director | No |

---

## v2 Changes Summary

### Schema (schema.sql)
- `users` — added `bio`, `avatar_url`, `is_admin`
- `movies` — added `director`, `cast_list`, `language`, `country`, `box_office_gross`
- `watchlist` — added `status` enum (`want_to_watch` / `watching` / `completed`)
- `reviews` — added `likes_count`
- **NEW** `review_likes` — tracks per-user likes (prevents double-liking)
- **NEW** `trending` — stores score + view_count per movie
- **NEW** `movie_views` — event log for each movie page view
- Seed data expanded to 10 movies + 12 genres

### Bug Fixes
- `movie_id` and `rating` now validated as integers before DB query
- Empty JSON body no longer causes unhandled `AttributeError` (returns 400 instead)
- Login now normalises email to lowercase consistently
- `INSERT IGNORE` on watchlist replaced with `ON DUPLICATE KEY UPDATE` to properly handle status changes
- Review comment length capped at 2000 chars
- Bio length capped at 500 chars

### New Features
- **Search** — `/api/movies/search?q=` with title-priority ranking
- **Trending** — auto-updated score on every movie fetch
- **Genre filter** — `/api/movies/?genre=Action`
- **User profile** — bio, avatar, stats (reviews, avg rating, watchlist count)
- **Change password** — secure current-password verification
- **Review likes** — idempotent toggle with `review_likes` junction table
- **Watchlist status** — track want_to_watch / watching / completed
- **Watchlist check** — single fast endpoint to check membership
- **By-director recommendations** — more films by the same director
- **Paginated reviews** — `?page=` and `?per_page=` on review listing
