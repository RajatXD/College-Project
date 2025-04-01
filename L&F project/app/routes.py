from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models import User, Item, OTP, Claim
from app.forms import RegistrationForm, LoginForm, ItemForm, ClaimForm, AdminClaimReviewForm
from app.utils import generate_otp, send_otp_email
import os
from datetime import datetime, timedelta
import secrets
from PIL import Image

main = Blueprint('main', __name__)

@main.route("/")
def home():
    # Get filter parameters from URL
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    
    # Start with base query
    query = Item.query
    
    # Apply filters if they are provided
    if category:
        query = query.filter(Item.category == category)
    if status:
        query = query.filter(Item.status == status)
    
    # Get the filtered items ordered by date
    items = query.order_by(Item.date_posted.desc()).all()
    
    return render_template('items_list.html', 
                         items=items, 
                         selected_category=category,
                         selected_status=status)

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            phone=form.phone.data,
            is_verified=True
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    
    return render_template('login.html', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

def generate_reference_id():
    return secrets.token_hex(5).upper()

@main.route("/report/<type>", methods=['GET', 'POST'])
@login_required
def report_item(type):
    if type not in ['lost', 'found']:
        flash('Invalid report type!', 'danger')
        return redirect(url_for('main.home'))
    
    form = ItemForm()
    if form.validate_on_submit():
        reference_id = generate_reference_id()
        item = Item(
            reference_id=reference_id,
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            color=form.color.data,
            status=type,
            date_lost_found=form.date_lost_found.data,
            location=form.location.data,
            user_id=current_user.id,
            finder_id=current_user.id if type == 'found' else None
        )
        
        if form.image.data:
            image_file = save_image(form.image.data)
            item.image_file = image_file
            
        db.session.add(item)
        db.session.commit()
        flash(f'Your {type} item has been reported! Reference ID: {reference_id}', 'success')
        return redirect(url_for('main.home'))
    
    return render_template('report_item.html', form=form, type=type)

@main.route("/item/<reference_id>/claim", methods=['GET', 'POST'])
@login_required
def claim_item(reference_id):
    item = Item.query.filter_by(reference_id=reference_id).first_or_404()
    
    if item.is_resolved:
        flash('This item has already been resolved!', 'warning')
        return redirect(url_for('main.home'))
    
    form = ClaimForm()
    if form.validate_on_submit():
        claim = Claim(
            item=item,
            user_id=current_user.id,
            proof=form.proof.data
        )
        db.session.add(claim)
        db.session.commit()
        flash('Your claim has been submitted and is pending review.', 'success')
        return redirect(url_for('main.home'))
    
    return render_template('claim_item.html', form=form, item=item)

@main.route("/admin")
@login_required
def admin_panel():
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Access denied! Admin privileges required.', 'danger')
        return redirect(url_for('main.home'))
    
    pending_claims = Claim.query.filter_by(status='pending').all()
    unresolved_items = Item.query.filter_by(is_resolved=False).all()
    return render_template('admin/panel.html', 
                         claims=pending_claims, 
                         items=unresolved_items)

@main.route("/admin/claim/<int:claim_id>", methods=['GET', 'POST'])
@login_required
def review_claim(claim_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Access denied! Admin privileges required.', 'danger')
        return redirect(url_for('main.home'))
    
    claim = Claim.query.get_or_404(claim_id)
    form = AdminClaimReviewForm()
    
    if form.validate_on_submit():
        claim.status = form.status.data
        claim.admin_notes = form.admin_notes.data
        claim.collection_location = form.collection_location.data
        
        if form.status.data == 'approved':
            claim.item.is_resolved = True
            claim.item.is_claimed = True
            flash(f'Claim approved! The user has been notified to collect the item from {form.collection_location.data}.', 'success')
            # Reject all other claims for this item
            for other_claim in claim.item.claims:
                if other_claim.id != claim.id:
                    other_claim.status = 'rejected'
        else:
            flash('Claim has been rejected.', 'info')
        
        db.session.commit()
        return redirect(url_for('main.admin_panel'))
    
    return render_template('admin/review_claim.html', form=form, claim=claim)

def save_image(form_image):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename)
    image_fn = random_hex + f_ext
    image_path = os.path.join(current_app.root_path, 'static/uploads', image_fn)
    
    # Resize image
    output_size = (800, 800)
    i = Image.open(form_image)
    i.thumbnail(output_size)
    i.save(image_path)
    
    return image_fn 