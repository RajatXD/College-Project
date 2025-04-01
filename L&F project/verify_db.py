from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(email='admin@example.com').first()
    if admin:
        print("Admin user exists:")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role}")
        print(f"Verified: {admin.is_verified}")
    else:
        print("Admin user does not exist!")
    
    # List all users
    print("\nAll users in database:")
    users = User.query.all()
    for user in users:
        print(f"User: {user.email}, Role: {user.role}") 