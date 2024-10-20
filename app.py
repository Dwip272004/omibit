from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random
import os

app = Flask(__name__)
socketio = SocketIO(app)

# In-memory storage for active users and their pairs
active_users = {}
waiting_users = set()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    user_id = data['user_id']
    waiting_users.add(user_id)
    print(f'{user_id} joined. Waiting users: {waiting_users}')

    # Notify all clients about the new user
    emit('joined', {'message': f'User {user_id} has joined', 'user_id': user_id}, broadcast=True)

    # Check if we can form a match
    try_to_match(user_id)

@socketio.on('leave')
def handle_leave(data):
    user_id = data['user_id']
    if user_id in waiting_users:
        waiting_users.remove(user_id)
        print(f'{user_id} left. Waiting users: {waiting_users}')
        emit('left', {'message': f'User {user_id} has left', 'user_id': user_id}, broadcast=True)
        # Try to match again if necessary
        try_to_match(user_id)

@socketio.on('request_match')
def handle_request_match(data):
    user_id = data['user_id']
    try_to_match(user_id)

def try_to_match(user_id):
    if len(waiting_users) >= 2:  # Need at least 2 users to form a match
        available_users = list(waiting_users - {user_id})  # Exclude the requester
        match = random.choice(available_users)
        
        # Create a pair and emit a match event
        active_users[user_id] = match
        active_users[match] = user_id

        waiting_users.remove(user_id)
        waiting_users.remove(match)

        emit('match_found', {'matched_user': match}, room=user_id)
        emit('match_found', {'matched_user': user_id}, room=match)
        
        print(f'Match found: {user_id} is matched with {match}')
        
        # Emit updated active user pairs
        emit('active_users', {'users': list(active_users.keys())}, broadcast=True)
    elif len(waiting_users) == 1:
        emit('waiting_for_match', {'message': 'Waiting for another user to join.'}, room=user_id)

@socketio.on('offer')
def handle_offer(data):
    emit('offer', data, broadcast=True, include_self=False)

@socketio.on('answer')
def handle_answer(data):
    emit('answer', data, broadcast=True, include_self=False)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    emit('ice_candidate', data, broadcast=True, include_self=False)

@socketio.on('skip_user')
def handle_skip_user(data):
    user_id = data['user_id']
    if user_id in waiting_users:
        waiting_users.remove(user_id)
        print(f'{user_id} has skipped the current user. Waiting users: {waiting_users}')
        
        # Try to match again if there are enough waiting users
        try_to_match(user_id)


@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid  # Use session ID as user identifier
    if user_id in active_users:
        matched_user = active_users[user_id]
        # Remove both users from active pairs
        active_users.pop(user_id)
        active_users.pop(matched_user, None)
        waiting_users.add(matched_user)  # Make matched user wait again

        print(f'{user_id} disconnected. Active users: {active_users}')
        emit('left', {'message': f'User {user_id} has disconnected', 'user_id': user_id}, broadcast=True)
        
        # Notify the matched user that their match has left
        emit('left', {'message': f'User {user_id} has disconnected', 'user_id': user_id}, room=matched_user)
        
        # Emit the updated list of active users
        emit('active_users', {'users': list(active_users.keys())}, broadcast=True)
        
        # Try to match remaining waiting users again
        if matched_user in waiting_users:
            try_to_match(matched_user)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Get the port from environment variables or use 5000
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
