# Skill Swap Platform

A full-stack web application enabling users to connect, offer, and request skills from each other. It includes user authentication, profile management, a swap request system, and an admin panel for platform management.

## Table of Contents

-   [Description](#description)
-   [Features](#features)
-   [Technologies Used](#technologies-used)
-   [Setup Instructions](#setup-instructions)
    -   [Prerequisites](#prerequisites)
    -   [Backend Setup](#backend-setup)
    -   [Frontend Setup](#frontend-setup)
-   [How to Run](#how-to-run)
-   [Admin Credentials](#admin-credentials)
-   [API Endpoints](#api-endpoints)
-   [Database Schema](#database-schema)
-   [Future Improvements](#future-improvements)

## Description

The Skill Swap Platform is designed to foster a community where individuals can exchange knowledge and skills. Users can create profiles, list skills they can offer, and skills they wish to learn. They can browse other users' profiles, send swap requests, and provide feedback on completed swaps. An administrative interface allows for user management, monitoring swap requests, and platform-wide announcements.

## Features

* **User Authentication:** Secure signup and login for users.
* **User Profiles:**
    * Personalized profiles with name, location, bio.
    * Ability to list skills offered and skills wanted.
    * Availability settings.
    * Profile photo upload (via URL or file).
    * Option to make profile public or private.
    * AI-powered bio generation (using Gemini API).
    * Themed UI based on user preference.
* **Browse Users:** Discover other users and their skills with search and category filtering.
* **Swap Requests:** Send and manage requests to exchange skills with other users.
* **Feedback System:** Rate and comment on completed skill swaps.
* **Admin Panel:**
    * View and manage all users (ban/unban).
    * Monitor all swap requests.
    * View all feedback logs.
    * Send platform-wide announcements.
    * Download various reports (user activity, feedback, swap statistics).
* **Responsive Design:** Optimized for various screen sizes (mobile, tablet, desktop).
* **Dynamic Theming:** Users can select their preferred color theme.
* **Animated Backgrounds:** Engaging visual elements using Three.js.

## Technologies Used

* **Backend:**
    * Python 3
    * Flask: Web framework
    * SQLite3: Database
    * `werkzeug.security`: For password hashing
    * `uuid`: For generating unique IDs
    * `Flask-CORS`: For handling Cross-Origin Resource Sharing
* **Frontend:**
    * HTML5
    * CSS3 (Tailwind CSS for utility-first styling)
    * JavaScript (React for component-based UI)
    * Three.js: For interactive 3D background animations
    * Font Awesome: For icons
    * Google Fonts (Inter): For typography
    * Gemini API: For AI-powered bio generation

## Setup Instructions

Follow these steps to get the Skill Swap Platform up and running on your local machine.

### Prerequisites

* Python 3.8+
* Node.js and npm (or yarn) - if you plan to use a local build process for frontend, otherwise CDN is used.
* A web browser.

### Backend Setup

1.  **Clone the repository (or save `app.py`):**
    If you have the files locally, ensure `app.py` is in your project directory.

2.  **Create a Python virtual environment (recommended):**

    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**

    * On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```
    * On Windows:
        ```bash
        .\venv\Scripts\activate
        ```

4.  **Install backend dependencies:**

    ```bash
    pip install Flask Flask-Cors Werkzeug
    ```

5.  **Database Initialization:**
    The `init_db()` function in `app.py` will automatically create the `skill_swap.db` SQLite database and its tables when the Flask app is run for the first time. It will also create the default admin user.

6.  **Create `uploads` directory:**
    Ensure there's an `uploads` directory in the same location as `app.py` for profile pictures. The backend code will attempt to create it if it doesn't exist.

### Frontend Setup

The frontend (`index.html`) uses CDN links for React, ReactDOM, Babel, Tailwind CSS, Three.js, and Font Awesome. This means no separate `npm install` or build step is strictly required for the frontend to run.

1.  **Place `index.html`:**
    Ensure `index.html` is in a directory named `html_templates` in the same location as `app.py`. The Flask app is configured to serve static files from this folder.

    ```
    your_project_root/
    ├── app.py
    ├── uploads/
    └── html_templates/
        └── index.html
    ```

## How to Run

1.  **Start the Backend (Flask server):**
    Open your terminal, navigate to your project root directory (where `app.py` is located), activate your virtual environment, and run:

    ```bash
    python app.py
    ```
    The server will typically run on `http://127.0.0.1:5000`. You should see output indicating the server is running.

2.  **Access the Frontend:**
    Open your web browser and navigate to `http://127.0.0.1:5000/`.

    The application should load, and you will be presented with the login/signup page.

## Admin Credentials

A default admin user is automatically created when the `app.py` is run for the first time (if the database doesn't already contain a user with this name).

* **Username:** `Admin User`
* **Password:** `Adminpass`

You can log in with these credentials to access the Admin Panel.

## API Endpoints

The backend provides the following API endpoints:

**Authentication:**

* `POST /api/auth/signup`
    * **Body:** `{ "name": "string", "password": "string", "location": "string", "skillsOffered": ["string"], "skillsWanted": ["string"], "availability": ["string"], "isPublic": boolean }`
    * **Description:** Registers a new user.
* `POST /api/auth/login`
    * **Body:** `{ "name": "string", "password": "string" }`
    * **Description:** Logs in a user.

**User Profiles:**

* `GET /api/profile/<user_id>`
    * **Description:** Retrieves a specific user's profile.
* `PUT /api/profile/<user_id>`
    * **Body:** `multipart/form-data` including fields like `name`, `location`, `bio`, `skillsOffered`, `skillsWanted`, `availability`, `isPublic`, `theme`, `profilePhoto` (file) or `profilePhotoUrl` (string).
    * **Description:** Updates a user's profile.
* `GET /api/users`
    * **Query Params:** `searchTerm` (optional)
    * **Description:** Retrieves a list of public users, optionally filtered by a search term.

**Swap Requests:**

* `POST /api/swap_requests`
    * **Body:** `{ "senderId": "string", "senderName": "string", "receiverId": "string", "receiverName": "string", "skillOffered": "string", "skillWanted": "string" }`
    * **Description:** Creates a new swap request.
* `GET /api/swap_requests/<user_id>`
    * **Description:** Retrieves all swap requests (sent and received) for a user.
* `PUT /api/swap_requests/<request_id>`
    * **Body:** `{ "status": "string" }` (e.g., "accepted", "rejected", "completed")
    * **Description:** Updates the status of a swap request.
* `DELETE /api/swap_requests/<request_id>`
    * **Description:** Deletes a swap request.

**Feedback:**

* `POST /api/feedback`
    * **Body:** `{ "swapRequestId": "string", "giverId": "string", "receiverId": "string", "rating": integer (1-5), "comment": "string" }`
    * **Description:** Submits feedback for a completed swap and updates the receiver's average rating.
* `GET /api/feedback`
    * **Description:** Retrieves all feedback logs (admin only).

**Admin Endpoints:**

* `GET /api/admin/users`
    * **Description:** Retrieves all user data (admin only).
* `PUT /api/admin/users/<user_id>/ban`
    * **Body:** `{ "isBanned": integer (0 or 1) }`
    * **Description:** Bans or unbans a user (admin only).
* `GET /api/admin/platform_message`
    * **Description:** Retrieves the current platform-wide message.
* `POST /api/admin/platform_message`
    * **Body:** `{ "message": "string" }`
    * **Description:** Sets a new platform-wide message (admin only).
* `GET /api/admin/swap_requests`
    * **Description:** Retrieves all swap requests (admin only).

## Database Schema

The `skill_swap.db` SQLite database contains the following tables:

* **`users`**:
    * `id` (TEXT, PRIMARY KEY)
    * `name` (TEXT, NOT NULL, UNIQUE)
    * `password_hash` (TEXT, NOT NULL)
    * `location` (TEXT)
    * `skills_offered` (TEXT) - comma-separated string
    * `skills_wanted` (TEXT) - comma-separated string
    * `availability` (TEXT) - comma-separated string
    * `is_public` (INTEGER) - 1 for public, 0 for private
    * `is_admin` (INTEGER) - 1 for admin, 0 for regular user
    * `is_banned` (INTEGER) - 1 for banned, 0 for active
    * `profile_photo` (TEXT) - URL or path to photo
    * `bio` (TEXT)
    * `theme` (TEXT)
    * `average_rating` (REAL)
    * `rating_count` (INTEGER)
    * `created_at` (TIMESTAMP)

* **`swap_requests`**:
    * `id` (TEXT, PRIMARY KEY)
    * `sender_id` (TEXT, NOT NULL, FOREIGN KEY to `users.id`)
    * `sender_name` (TEXT, NOT NULL)
    * `receiver_id` (TEXT, NOT NULL, FOREIGN KEY to `users.id`)
    * `receiver_name` (TEXT, NOT NULL)
    * `skill_offered` (TEXT, NOT NULL)
    * `skill_wanted` (TEXT, NOT NULL)
    * `status` (TEXT) - 'pending', 'accepted', 'rejected', 'completed'
    * `created_at` (TIMESTAMP)

* **`feedback`**:
    * `id` (TEXT, PRIMARY KEY)
    * `swap_request_id` (TEXT, NOT NULL, FOREIGN KEY to `swap_requests.id`)
    * `giver_id` (TEXT, NOT NULL, FOREIGN KEY to `users.id`)
    * `receiver_id` (TEXT, NOT NULL, FOREIGN KEY to `users.id`)
    * `rating` (INTEGER, NOT NULL) - 1 to 5
    * `comment` (TEXT)
    * `created_at` (TIMESTAMP)

* **`platform_messages`**:
    * `id` (INTEGER, PRIMARY KEY AUTOINCREMENT)
    * `message` (TEXT, NOT NULL)
    * `created_at` (TIMESTAMP)

## Future Improvements

* **Real-time Notifications:** Implement WebSockets for instant notifications on new swap requests, status updates, and platform announcements.
* **Messaging System:** Add a direct messaging feature between users.
* **Advanced Search & Filtering:** More robust search capabilities, including filtering by location, specific skills, or availability.
* **Skill Categories:** Predefined categories for skills to improve discoverability.
* **User Reviews:** Allow users to leave public reviews on profiles (beyond just ratings).
* **Calendar Integration:** Allow users to link their availability to a calendar or schedule.
* **Progress Tracking:** For accepted swaps, allow users to track the progress of their skill exchange.
* **More Robust Admin Features:** Detailed analytics, moderation tools for comments/bios.
* **Password Reset:** Implement a "forgot password" functionality.
* **OAuth Integration:** Allow login via Google, Facebook, etc.
* **Deployment:** Instructions and configurations for deploying the application to a cloud platform.
