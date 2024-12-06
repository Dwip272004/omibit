from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random
import os

app = Flask(__name__, static_folder='static')

socketio = SocketIO(app)

# In-memory dictionary to store active users as {user_id: user_name}
active_users = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/blog-single')
def blog_single():
    return render_template('blog-single.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/department')
def department():
    return render_template('department.html')

@app.route('/doctor')
def doctor():
    return render_template('doctor.html')
@app.route('/treatments')
def treatments():
    # your logic here
    return render_template('treatments.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# New route for video call
@app.route('/video-call')
def video_call():
    return render_template('video_call.html')


# New route for video booking
@app.route('/video-booking')
def video_booking():
    return render_template('video_booking.html')


@socketio.on('join')
def handle_join(data):
    user_id = data['user_id']
    user_name = data['user_name']  # Name sent from the client
    
    # Store the user's ID and name in the active_users dictionary
    active_users[user_id] = user_name
    print(f'{user_name} ({user_id}) joined. Active users: {active_users}')
    
    # Emit joined message to all clients
    emit('joined', {'message': f'{user_name} has joined', 'user_id': user_id, 'user_name': user_name}, broadcast=True)
    
    # Emit the updated list of active users to all clients
    emit('active_users', {'users': [{'user_id': uid, 'user_name': uname} for uid, uname in active_users.items()]}, broadcast=True)
    
    # Emit the user_id and user_name back to the client who joined
    emit('your_user_id', {'user_id': user_id, 'user_name': user_name}, room=request.sid)

@socketio.on('leave')
def handle_leave(data):
    user_id = data['user_id']
    user_name = active_users.get(user_id, 'Unknown User')
    
    # Remove the user from the active users list
    if user_id in active_users:
        del active_users[user_id]
    
    print(f'{user_name} ({user_id}) left. Active users: {active_users}')
    
    # Emit left message to all clients
    emit('left', {'message': f'{user_name} has left', 'user_id': user_id}, broadcast=True)
    
    # Emit the updated list of active users
    emit('active_users', {'users': [{'user_id': uid, 'user_name': uname} for uid, uname in active_users.items()]}, broadcast=True)

@socketio.on('request_match')
def handle_request_match(data):
    user_id = data['user_id']
    user_name = active_users.get(user_id, 'Unknown User')

    if len(active_users) > 1:  # There should be at least two users for a match
        available_users = [(uid, uname) for uid, uname in active_users.items() if uid != user_id]  # Exclude the requester
        match = random.choice(available_users)
        matched_user_id, matched_user_name = match
        emit('match_found', {'matched_user': matched_user_name, 'matched_user_id': matched_user_id}, room=request.sid)
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
    user_name = active_users.get(user_id, 'Unknown User')
    
    # Remove the user from the active users list
    if user_id in active_users:
        del active_users[user_id]
    
    print(f'{user_name} ({user_id}) disconnected. Active users: {active_users}')
    
    # Emit left message to all clients
    emit('left', {'message': f'{user_name} has disconnected', 'user_id': user_id}, broadcast=True)
    
    # Emit the updated list of active users
    emit('active_users', {'users': [{'user_id': uid, 'user_name': uname} for uid, uname in active_users.items()]}, broadcast=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)