from flask import Flask, request, jsonify
#from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint
from models import User
import hashlib
from argon2 import PasswordHasher



auth_bp = Blueprint("auth", __name__, )

ph = PasswordHasher(time_cost=4, parallelism=8, hash_len=64)

def get_allowed_emails():
    allowed_emails = set() 
    with open('studentEmails.txt', 'r') as f:
        for line in f:
            email = line.strip()
            if email:  
                allowed_emails.add(email)
    return allowed_emails


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    classID = data.get('classID')
    allowed_emails = get_allowed_emails()
    if email not in allowed_emails:
        return jsonify({'message': 'Email not allowed to register'}), 403
    if User.objects(email=email).first():
        return jsonify({'message': 'Email already exists'}), 400
    max_userID = User.objects.order_by('-userID').first().userID if User.objects.count() > 0 else 0
    next_userID = max_userID + 1
    
    hashed_password = ph.hash(password)
    user = User(userID=next_userID, email=email, password=hashed_password, role=role, classID=classID)
    user.save()
    return jsonify({'message': 'User registered successfully'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = User.objects(email=email).first()
    print(user.id)
    if user and user.password == password and user.role == "Student":
        return jsonify({'message': 'Login successful', "user_id": user.userID, "user_email": user.email, "role": user.role}), 200
    elif user and user.password != password:
        return jsonify({'message': 'Incorrect password'}), 401
    else:
        return jsonify({'error': 'Invalid email or password'}), 401

@auth_bp.route('/check_email', methods=['POST'])
def check_email():
    data = request.json
    email = data.get('email')
    allowed_emails = get_allowed_emails()
    if email in allowed_emails:
        return jsonify({'message': 'Email exists in allowed emails'}), 200
    else:
        return jsonify({'error': 'User not allowed to register for the class'}), 404
    
    
    
    
    
@auth_bp.route('/update-classID', methods=['POST'])
def update_classID():
    data = request.json
    email = data.get('email')
    classID = data.get('classID')

    if not email or not classID:
        return jsonify({'error': 'email and classID are required'}), 400

    user = User.objects(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.update(set__classID=classID)
    return jsonify({'message': 'ClassID updated successfully'}), 200

    
@auth_bp.route('/user-details', methods=['GET'])
def user_details():
    classID = request.args.get('classID')
    email = request.args.get('email')
    userID = request.args.get('userID')
    if userID:
        try:
            userID = int(userID)
        except ValueError:
            return jsonify({'error': 'Invalid userID'}), 400

    if not classID and not email and not userID:
        return jsonify({'error': 'Either classID, email, or userID is required'}), 400

    if classID:
        users = User.objects(classID=classID)
    elif email:
        users = User.objects(email=email)
    elif userID:
        users = User.objects(userID=userID)
    else:
        return jsonify({'error': 'Invalid request'}), 400

    user_details = [user.to_json() for user in users]
    return jsonify(user_details), 200