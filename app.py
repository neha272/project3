from flask import Flask, request, jsonify
from models import db, User, Post
from datetime import datetime, timezone
import secrets
import threading

app = Flask(__name__)
lock = threading.Lock()

# Configuring the app with the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def generate_unique_id():
    return len(Post.query.all()) + 1

def generate_random_key():
    return secrets.token_urlsafe(32)

def get_current_utc_timestamp():
    return datetime.now(timezone.utc)

def get_user_by_id(user_id):
    return User.query.get(user_id)

def get_post_info(post):
    user_metadata = {}
    if post.user_id is not None:
        user = get_user_by_id(post.user_id)
        user_metadata = {'user_id': user.id, 'username': user.username} if user else {}

    return {
        'id': post.id,
        'timestamp': post.timestamp,
        'msg': post.msg,
        **user_metadata
    }

@app.route('/post', methods=['POST'])
def create_post():
    try:
        data = request.get_json()
        if not isinstance(data, dict) or 'msg' not in data or not isinstance(data['msg'], str):
            return jsonify({'error': 'Bad request'}), 400

        user_id = data.get('user_id')
        user_key = data.get('user_key')

        if user_id is not None:
            user = get_user_by_id(user_id)
            if user is None or user.key != user_key:
                return jsonify({'error': 'Forbidden'}), 403

        reply_to = data.get('reply_to')
        reply_post = Post.query.get(reply_to) if reply_to is not None else None

        with lock:
            post_id = generate_unique_id()
            post_key = generate_random_key()
            timestamp = get_current_utc_timestamp()

            post = Post(
                id=post_id,
                msg=data['msg'],
                timestamp=timestamp,
                key=post_key,
                user_id=user_id,
                reply_to=reply_to
            )

            db.session.add(post)
            db.session.commit()

        return jsonify(get_post_info(post)), 201

    except Exception as e:
        print(e)
        return jsonify({'error': f'Internal server error'}), 500

@app.route('/post/<int:post_id>', methods=['GET'])
def read_post(post_id):
    with lock:
        post = Post.query.get(post_id)

        if post is None:
            return jsonify({'error': 'Not found'}), 404

        return jsonify(get_post_info(post))

@app.route('/post/<int:post_id>/delete/<string:key>', methods=['DELETE'])
def delete_post(post_id, key):
    with lock:
        post = Post.query.get(post_id)

        if post is None:
            return jsonify({'error': 'Not found'}), 404

        if post.key != key:
            return jsonify({'error': 'Forbidden'}), 403

        db.session.delete(post)
        db.session.commit()

        return jsonify(get_post_info(post))

# Extension 1 and 2: User creation and metadata
@app.route('/user', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        if not isinstance(data, dict) or 'unique_metadata' not in data:
            return jsonify({'error': 'Bad request'}), 400

        unique_metadata = data['unique_metadata']
        non_unique_metadata = data.get('non_unique_metadata', None)
        user_key = generate_random_key()

        user = User(
            username=unique_metadata,
            email=non_unique_metadata,
            key=user_key
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({'user_id': user.id, 'user_key': user.key}), 201

    except Exception as e:
        print(e)
        return jsonify({'error': 'Internal server error'}), 500

# Extension 3: Edit user metadata
@app.route('/user/<int:user_id>/edit', methods=['PUT'])
def edit_user_metadata(user_id):
    try:
        data = request.get_json()
        if not isinstance(data, dict) or 'user_key' not in data or 'non_unique_metadata' not in data:
            return jsonify({'error': 'Bad request'}), 400

        user = get_user_by_id(user_id)

        if user is None or user.key != data['user_key']:
            return jsonify({'error': 'Forbidden'}), 403

        user.email = data['non_unique_metadata']
        db.session.commit()

        return jsonify({'user_id': user.id, 'username': user.username, 'email': user.email}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Internal server error'}), 500

# Extension 4: Threaded replies - Reading posts
@app.route('/post/<int:post_id>/replies', methods=['GET'])
def get_post_replies(post_id):
    with lock:
        post = Post.query.get(post_id)

        if post is None:
            return jsonify({'error': 'Not found'}), 404

        replies = [get_post_info(reply) for reply in post.replies]
        return jsonify({'replies': replies})

# Extension 5: Date- and time-based range queries
@app.route('/posts/range', methods=['GET'])
def get_posts_in_range():
    try:
        start_datetime = request.args.get('start_datetime')
        end_datetime = request.args.get('end_datetime')

        if not start_datetime and not end_datetime:
            return jsonify({'error': 'Bad request. At least one of start_datetime or end_datetime is required.'}), 400

        query = Post.query
        if start_datetime:
            query = query.filter(Post.timestamp >= start_datetime)
        if end_datetime:
            query = query.filter(Post.timestamp <= end_datetime)

        posts = query.all()
        result = [get_post_info(post) for post in posts]

        return jsonify({'posts': result}), 200

    except Exception as e:
        print(e)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
