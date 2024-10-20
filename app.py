from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random

import os
app = Flask(__name__)
socketio = SocketIO(app)

# In-memory set to store active users
active_users = set()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def handle_join(data):
    user_id = data['user_id']
    active_users.add(user_id)
    print(f'{user_id} joined. Active users: {active_users}')
    emit('joined', {'message': f'User {user_id} has joined', 'user_id': user_id}, broadcast=True)

@socketio.on('leave')
def handle_leave(data):
    user_id = data['user_id']
    active_users.discard(user_id)
    print(f'{user_id} left. Active users: {active_users}')
    emit('left', {'message': f'User {user_id} has left', 'user_id': user_id}, broadcast=True)

@socketio.on('request_match')
def handle_request_match(data):
    user_id = data['user_id']

    if len(active_users) > 1:  # There should be at least two users for a match
        available_users = list(active_users - {user_id})  # Exclude the requester
        match = random.choice(available_users)
        emit('match_found', {'matched_user': match}, room=request.sid)
    else:
        emit('no_users_available', {'message': 'No users available at the moment'}, room=request.sid)

# WebRTC signaling
@socketio.on('offer')
def handle_offer(data):
    emit('offer', data, broadcast=True, include_self=False)

@socketio.on('answer')
def handle_answer(data):
    emit('answer', data, broadcast=True, include_self=False)

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    emit('ice_candidate', data, broadcast=True, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    user_id = request.sid  # Use session ID as user identifier
    active_users.discard(user_id)
    print(f'{user_id} disconnected. Active users: {active_users}')
    emit('left', {'message': f'User {user_id} has disconnected', 'user_id': user_id}, broadcast=True)

if __name__ == '__main__': # Initialize the SQLite database
    port = int(os.environ.get('PORT', 5000))  # Get the port from environment variables or use 5000
    socketio.run(app, host='0.0.0.0', port=port, debug=True)