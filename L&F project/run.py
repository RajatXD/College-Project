from app import create_app, db
import os

app = create_app()

def init_db():
    # Create instance folder
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    # Create all database tables
    with app.app_context():
        db.drop_all()  # Drop all existing tables
        db.create_all()  # Create new tables
        
        # Create admin user
        from app.models import User
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        
        admin = User(
            username='admin',
            email='admin@example.com',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            role='admin',
            is_verified=True,
            phone='1234567890'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created!")

if __name__ == '__main__':
    init_db()  # Initialize database
    app.run(debug=True) 