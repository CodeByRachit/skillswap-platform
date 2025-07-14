import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__, static_folder='html_templates')
CORS(app) # Enable CORS for all routes

DATABASE = 'skill_swap.db'
UPLOAD_FOLDER = 'uploads' # Folder to store uploaded profile pictures
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

def init_db():
    """Initializes the database by creating necessary tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            location TEXT,
            skills_offered TEXT, -- Stored as comma-separated string
            skills_wanted TEXT,  -- Stored as comma-separated string
            availability TEXT,   -- Stored as comma-separated string
            is_public INTEGER DEFAULT 1,
            is_admin INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            profile_photo TEXT, -- URL or path to profile photo
            bio TEXT,           -- User biography
            theme TEXT DEFAULT 'indigo', -- User's chosen theme
            average_rating REAL DEFAULT 0.0, -- Average rating received by the user
            rating_count INTEGER DEFAULT 0,  -- Number of ratings received
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create swap_requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS swap_requests (
            id TEXT PRIMARY KEY,
            sender_id TEXT NOT NULL,
            sender_name TEXT NOT NULL,
            receiver_id TEXT NOT NULL,
            receiver_name TEXT NOT NULL,
            skill_offered TEXT NOT NULL,
            skill_wanted TEXT NOT NULL,
            status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'rejected', 'completed'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    ''')

    # Create feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            swap_request_id TEXT NOT NULL,
            giver_id TEXT NOT NULL,    -- The user giving the feedback
            receiver_id TEXT NOT NULL, -- The user receiving the feedback (who completed the swap)
            rating INTEGER NOT NULL,   -- Rating from 1 to 5
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (swap_request_id) REFERENCES swap_requests (id),
            FOREIGN KEY (giver_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    ''')

    # Create platform_messages table for admin announcements
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS platform_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add a default admin user if one doesn't already exist
    admin_username = "Admin User"
    admin_password = "Adminpass" # In a real application, this should be an environment variable or more securely managed

    cursor.execute("SELECT id FROM users WHERE name = ?", (admin_username,))
    existing_admin = cursor.fetchone()

    if not existing_admin:
        admin_id = str(uuid.uuid4())
        admin_password_hash = generate_password_hash(admin_password)
        cursor.execute(
            "INSERT INTO users (id, name, password_hash, is_admin, skills_offered, skills_wanted, availability, is_public, bio, theme, average_rating, rating_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (admin_id, admin_username, admin_password_hash, 1, '', '', '', 1, 'Platform Administrator', 'purple', 0.0, 0)
        )
        print(f"Default admin user '{admin_username}' created.")
    else:
        print(f"Admin user '{admin_username}' already exists.")


    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

def allowed_file(filename):
    """Checks if a file's extension is allowed for upload."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def serve_index():
    """Serves the main HTML file."""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/uploads/<filename>')
def send_uploaded_file(filename):
    """Serves uploaded profile picture files."""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    """Handles user registration."""
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')
    location = data.get('location', '')
    skills_offered = ','.join(data.get('skillsOffered', [])) # Join list to string
    skills_wanted = ','.join(data.get('skillsWanted', []))   # Join list to string
    availability = ','.join(data.get('availability', []))   # Join list to string
    is_public = int(data.get('isPublic', 1)) # Convert boolean to integer

    if not name or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 409

        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)

        cursor.execute(
            "INSERT INTO users (id, name, password_hash, location, skills_offered, skills_wanted, availability, is_public, bio, theme, average_rating, rating_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, name, password_hash, location, skills_offered, skills_wanted, availability, is_public, '', 'purple', 0.0, 0) # Default bio, theme, rating
        )
        conn.commit()

        # Fetch the newly created user's profile to return
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        new_user_profile = cursor.fetchone()
        
        # Prepare user profile for frontend, converting comma-separated strings back to lists
        user_profile_dict = dict(new_user_profile)
        user_profile_dict['skills_offered'] = user_profile_dict['skills_offered'].split(',') if user_profile_dict['skills_offered'] else []
        user_profile_dict['skills_wanted'] = user_profile_dict['skills_wanted'].split(',') if user_profile_dict['skills_wanted'] else []
        user_profile_dict['availability'] = user_profile_dict['availability'].split(',') if user_profile_dict['availability'] else []
        user_profile_dict['is_public'] = bool(user_profile_dict['is_public'])
        user_profile_dict['is_admin'] = bool(user_profile_dict['is_admin'])
        user_profile_dict['is_banned'] = bool(user_profile_dict['is_banned'])


        return jsonify({
            "message": "User registered successfully",
            "userId": user_id,
            "userProfile": user_profile_dict
        }), 201
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error during signup: {str(e)}") # Debug print
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Handles user login."""
    data = request.get_json()
    name = data.get('name')
    password = data.get('password')

    if not name or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            # Prepare user profile for frontend, converting comma-separated strings back to lists
            user_profile_dict = dict(user)
            user_profile_dict['skills_offered'] = user_profile_dict['skills_offered'].split(',') if user_profile_dict['skills_offered'] else []
            user_profile_dict['skills_wanted'] = user_profile_dict['skills_wanted'].split(',') if user_profile_dict['skills_wanted'] else []
            user_profile_dict['availability'] = user_profile_dict['availability'].split(',') if user_profile_dict['availability'] else []
            user_profile_dict['is_public'] = bool(user_profile_dict['is_public'])
            user_profile_dict['is_admin'] = bool(user_profile_dict['is_admin'])
            user_profile_dict['is_banned'] = bool(user_profile_dict['is_banned'])

            return jsonify({
                "message": "Login successful",
                "userId": user['id'],
                "userProfile": user_profile_dict
            }), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except sqlite3.Error as e:
        print(f"Database error during login: {str(e)}") # Debug print
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/profile/<user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Retrieves a user's profile by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            user_profile_dict = dict(user)
            user_profile_dict['skills_offered'] = user_profile_dict['skills_offered'].split(',') if user_profile_dict['skills_offered'] else []
            user_profile_dict['skills_wanted'] = user_profile_dict['skills_wanted'].split(',') if user_profile_dict['skills_wanted'] else []
            user_profile_dict['availability'] = user_profile_dict['availability'].split(',') if user_profile_dict['availability'] else []
            user_profile_dict['is_public'] = bool(user_profile_dict['is_public'])
            user_profile_dict['is_admin'] = bool(user_profile_dict['is_admin'])
            user_profile_dict['is_banned'] = bool(user_profile_dict['is_banned'])
            return jsonify(user_profile_dict), 200
        return jsonify({"error": "User not found"}), 404
    except sqlite3.Error as e:
        print(f"Database error fetching profile: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/profile/<user_id>', methods=['PUT'])
def update_user_profile(user_id):
    """Updates a user's profile, including handling file uploads for profile photos."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get data from form (for multipart/form-data)
        name = request.form.get('name', user['name'])
        location = request.form.get('location', user['location'])
        bio = request.form.get('bio', user['bio'])
        skills_offered = request.form.get('skillsOffered', user['skills_offered'])
        skills_wanted = request.form.get('skillsWanted', user['skills_wanted'])
        availability = request.form.get('availability', user['availability'])
        is_public = int(request.form.get('isPublic', user['is_public']))
        theme = request.form.get('theme', user['theme'])

        profile_photo_url = user['profile_photo'] # Default to existing photo

        # Handle profile photo upload
        if 'profilePhoto' in request.files:
            file = request.files['profilePhoto']
            if file and allowed_file(file.filename):
                filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                profile_photo_url = f"/uploads/{filename}"
            else:
                return jsonify({"error": "Invalid file type for profile photo"}), 400
        elif 'profilePhotoUrl' in request.form:
            # If no file uploaded, check for a URL
            provided_url = request.form.get('profilePhotoUrl')
            if provided_url:
                profile_photo_url = provided_url
            else:
                # If URL is explicitly empty, clear the profile photo
                profile_photo_url = None # Or a default placeholder URL

        cursor.execute(
            """
            UPDATE users SET
                name = ?,
                location = ?,
                bio = ?,
                skills_offered = ?,
                skills_wanted = ?,
                availability = ?,
                is_public = ?,
                profile_photo = ?,
                theme = ?
            WHERE id = ?
            """,
            (name, location, bio, skills_offered, skills_wanted, availability, is_public, profile_photo_url, theme, user_id)
        )
        conn.commit()

        # Fetch the updated user profile
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        updated_user = cursor.fetchone()
        
        # Prepare updated user profile for frontend
        updated_user_dict = dict(updated_user)
        updated_user_dict['skills_offered'] = updated_user_dict['skills_offered'].split(',') if updated_user_dict['skills_offered'] else []
        updated_user_dict['skills_wanted'] = updated_user_dict['skills_wanted'].split(',') if updated_user_dict['skills_wanted'] else []
        updated_user_dict['availability'] = updated_user_dict['availability'].split(',') if updated_user_dict['availability'] else []
        updated_user_dict['is_public'] = bool(updated_user_dict['is_public'])
        updated_user_dict['is_admin'] = bool(updated_user_dict['is_admin'])
        updated_user_dict['is_banned'] = bool(updated_user_dict['is_banned'])

        return jsonify({
            "message": "Profile updated successfully",
            "userProfile": updated_user_dict
        }), 200
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error updating profile: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred during profile update: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/users', methods=['GET'])
def get_users():
    """Fetches a list of public users, optionally filtered by search term."""
    search_term = request.args.get('searchTerm', '').lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM users WHERE is_public = 1 AND is_banned = 0"
        params = []

        if search_term:
            query += " AND (name LIKE ? OR skills_offered LIKE ? OR skills_wanted LIKE ? OR location LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
        
        cursor.execute(query, params)
        users = cursor.fetchall()
        
        users_list = []
        for user in users:
            user_dict = dict(user)
            user_dict['skills_offered'] = user_dict['skills_offered'].split(',') if user_dict['skills_offered'] else []
            user_dict['skills_wanted'] = user_dict['skills_wanted'].split(',') if user_dict['skills_wanted'] else []
            user_dict['availability'] = user_dict['availability'].split(',') if user_dict['availability'] else []
            user_dict['is_public'] = bool(user_dict['is_public'])
            user_dict['is_admin'] = bool(user_dict['is_admin'])
            user_dict['is_banned'] = bool(user_dict['is_banned'])
            users_list.append(user_dict)
        
        return jsonify(users_list), 200
    except sqlite3.Error as e:
        print(f"Database error fetching users: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/swap_requests', methods=['POST'])
def create_swap_request():
    """Creates a new swap request."""
    data = request.get_json()
    sender_id = data.get('senderId')
    sender_name = data.get('senderName')
    receiver_id = data.get('receiverId')
    receiver_name = data.get('receiverName')
    skill_offered = data.get('skillOffered')
    skill_wanted = data.get('skillWanted')

    if not all([sender_id, sender_name, receiver_id, receiver_name, skill_offered, skill_wanted]):
        return jsonify({"error": "Missing required fields"}), 400
    
    if sender_id == receiver_id:
        return jsonify({"error": "Cannot send a swap request to yourself"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        request_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO swap_requests (id, sender_id, sender_name, receiver_id, receiver_name, skill_offered, skill_wanted, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (request_id, sender_id, sender_name, receiver_id, receiver_name, skill_offered, skill_wanted, 'pending')
        )
        conn.commit()
        return jsonify({"message": "Swap request sent successfully", "requestId": request_id}), 201
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error creating swap request: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/swap_requests/<user_id>', methods=['GET'])
def get_user_swap_requests(user_id):
    """Retrieves all swap requests for a given user (both sent and received)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT * FROM swap_requests WHERE sender_id = ? OR receiver_id = ? ORDER BY created_at DESC",
            (user_id, user_id)
        )
        requests = cursor.fetchall()
        return jsonify([dict(req) for req in requests]), 200
    except sqlite3.Error as e:
        print(f"Database error fetching swap requests: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/swap_requests/<request_id>', methods=['PUT'])
def update_swap_request_status(request_id):
    """Updates the status of a swap request."""
    data = request.get_json()
    new_status = data.get('status')

    if new_status not in ['accepted', 'rejected', 'completed']: # 'pending' is default
        return jsonify({"error": "Invalid status"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM swap_requests WHERE id = ?", (request_id,))
        req = cursor.fetchone()
        if not req:
            return jsonify({"error": "Swap request not found"}), 404
        
        # Only allow status change from pending
        if req['status'] != 'pending' and new_status != 'completed':
            return jsonify({"error": f"Cannot change status from '{req['status']}' to '{new_status}'"}), 400


        cursor.execute(
            "UPDATE swap_requests SET status = ? WHERE id = ?",
            (new_status, request_id)
        )
        conn.commit()
        return jsonify({"message": f"Swap request status updated to {new_status}"}), 200
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error updating swap request status: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/swap_requests/<request_id>', methods=['DELETE'])
def delete_swap_request(request_id):
    """Deletes a swap request."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM swap_requests WHERE id = ?", (request_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Swap request not found"}), 404
        return jsonify({"message": "Swap request deleted successfully"}), 200
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error deleting swap request: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submits feedback for a completed swap and updates receiver's average rating."""
    data = request.get_json()
    swap_request_id = data.get('swapRequestId')
    giver_id = data.get('giverId')
    receiver_id = data.get('receiverId')
    rating = data.get('rating')
    comment = data.get('comment', '')

    if not all([swap_request_id, giver_id, receiver_id, rating]):
        return jsonify({"error": "Missing required feedback fields"}), 400
    if not (1 <= rating <= 5):
        return jsonify({"error": "Rating must be between 1 and 5"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if feedback already exists for this swap from this giver
        cursor.execute("SELECT * FROM feedback WHERE swap_request_id = ? AND giver_id = ?", (swap_request_id, giver_id))
        existing_feedback = cursor.fetchone()
        if existing_feedback:
            return jsonify({"error": "Feedback already submitted for this swap by this user"}), 409

        feedback_id = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO feedback (id, swap_request_id, giver_id, receiver_id, rating, comment) VALUES (?, ?, ?, ?, ?, ?)",
            (feedback_id, swap_request_id, giver_id, receiver_id, rating, comment)
        )
        
        # Update receiver's average rating
        cursor.execute("SELECT average_rating, rating_count FROM users WHERE id = ?", (receiver_id,))
        receiver_profile = cursor.fetchone()

        if receiver_profile:
            current_avg = receiver_profile['average_rating']
            current_count = receiver_profile['rating_count']

            new_total_sum = (current_avg * current_count) + rating
            new_count = current_count + 1
            new_avg = new_total_sum / new_count if new_count > 0 else 0.0

            cursor.execute(
                "UPDATE users SET average_rating = ?, rating_count = ? WHERE id = ?",
                (new_avg, new_count, receiver_id)
            )
        
        conn.commit()
        return jsonify({"message": "Feedback submitted successfully"}), 201
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error submitting feedback: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/feedback', methods=['GET'])
def get_all_feedback():
    """Retrieves all feedback logs (for admin panel)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM feedback ORDER BY created_at DESC")
        feedback_logs = cursor.fetchall()
        return jsonify([dict(log) for log in feedback_logs]), 200
    except sqlite3.Error as e:
        print(f"Database error fetching feedback logs: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

# Admin Endpoints
@app.route('/api/admin/users', methods=['GET'])
def admin_get_all_users():
    """Admin: Get all users."""
    # In a real app, you'd add authentication/authorization for admin access here
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, location, skills_offered, skills_wanted, is_public, is_admin, is_banned, profile_photo, bio, theme, average_rating, rating_count, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    conn.close()
    
    users_list = []
    for user in users:
        user_dict = dict(user)
        user_dict['skills_offered'] = user_dict['skills_offered'].split(',') if user_dict['skills_offered'] else []
        user_dict['skills_wanted'] = user_dict['skills_wanted'].split(',') if user_dict['skills_wanted'] else []
        user_dict['is_public'] = bool(user_dict['is_public'])
        user_dict['is_admin'] = bool(user_dict['is_admin'])
        user_dict['is_banned'] = bool(user_dict['is_banned'])
        users_list.append(user_dict)
    
    return jsonify(users_list), 200

@app.route('/api/admin/users/<user_id>/ban', methods=['PUT'])
def admin_ban_user(user_id):
    """Admin: Ban or unban a user."""
    # In a real app, you'd add authentication/authorization for admin access here
    data = request.get_json()
    is_banned = data.get('isBanned') # Expect 0 or 1

    if is_banned is None or is_banned not in [0, 1]:
        return jsonify({"error": "isBanned field is required and must be 0 or 1"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET is_banned = ? WHERE id = ?", (is_banned, user_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "User not found"}), 404
        status_message = "banned" if is_banned else "unbanned"
        return jsonify({"message": f"User {user_id} successfully {status_message}."}), 200
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Admin: Database error banning user: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/admin/platform_message', methods=['GET'])
def admin_get_platform_message():
    """Admin: Get the latest platform-wide message."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM platform_messages ORDER BY created_at DESC LIMIT 1")
    message = cursor.fetchone()
    conn.close()
    return jsonify({"message": message['message'] if message else ""}), 200

@app.route('/api/admin/platform_message', methods=['POST'])
def admin_set_platform_message():
    """Admin: Set a new platform-wide message."""
    data = request.get_json()
    message = data.get('message')

    if message is None:
        print("Admin: Error - message content is required for platform message.") # Debug print
        return jsonify({"error": "Message content is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Clear previous messages or just add new one, for simplicity, we'll just add
        cursor.execute("INSERT INTO platform_messages (message) VALUES (?)", (message,))
        conn.commit()
        print(f"Admin: Platform message set to: {message}") # Debug print
        return jsonify({"message": "Platform message updated successfully"}), 200
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Admin: Database error setting platform message: {str(e)}") # Debug print
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

@app.route('/api/admin/swap_requests', methods=['GET'])
def admin_get_all_swap_requests():
    """Admin: Get all swap requests."""
    # In a real app, you'd add authentication/authorization for admin access here
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM swap_requests ORDER BY created_at DESC")
    requests = cursor.fetchall()
    conn.close()
    print(f"Admin: Fetched {len(requests)} total swap requests.") # Debug print
    return jsonify([dict(req) for req in requests]), 200


if __name__ == '__main__':
    # This will re-initialize the DB every time the script is run directly.
    # For production, you might want a separate script for initial setup.
    init_db()
    app.run(debug=True) # Run in debug mode for development