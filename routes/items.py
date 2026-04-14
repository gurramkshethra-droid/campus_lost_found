import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from extensions import db
from models import Item, Match, Claim, Notification
from utils.matcher import find_matches_for_item
from utils.validators import allowed_file, allowed_description

items_bp = Blueprint('items', __name__)

CATEGORIES = ['ID Card', 'Electronics', 'Wallet', 'Keys', 'Stationery', 'Clothing', 'Other']
TYPES = ['lost', 'found']


def _create_notification(user_id, item_id, message):
    notification = Notification(user_id=user_id, item_id=item_id, message=message)
    db.session.add(notification)


def _auto_close_expired_items():
    cutoff = datetime.utcnow() - timedelta(days=30)
    updated_rows = Item.query.filter(
        Item.status == 'active',
        Item.created_at < cutoff
    ).update({'status': 'closed'}, synchronize_session=False)
    if updated_rows:
        db.session.commit()


@items_bp.route('/')
@login_required
def dashboard():
    _auto_close_expired_items()
    query = request.args.get('query', '').strip()
    item_type = request.args.get('type', '').strip().lower()
    category = request.args.get('category', '').strip()

    items = Item.query.order_by(Item.created_at.desc())
    if query:
        items = items.filter(
            Item.title.ilike(f'%{query}%') |
            Item.description.ilike(f'%{query}%') |
            Item.location.ilike(f'%{query}%')
        )
    if item_type in TYPES:
        items = items.filter_by(type=item_type)
    if category in CATEGORIES:
        items = items.filter_by(category=category)

    items = items.all()

    matches = []
    if current_user.is_authenticated:
        matches = Match.query.filter(
            or_(
                Match.lost_item.has(user_id=current_user.id),
                Match.found_item.has(user_id=current_user.id)
            )
        ).all()

    total_lost = Item.query.filter_by(type='lost').count()
    total_found = Item.query.filter_by(type='found').count()
    resolved_count = Item.query.filter(Item.status.in_(['claimed', 'closed'])).count()

    return render_template('dashboard.html', items=items, categories=CATEGORIES,
                           query=query, selected_type=item_type, selected_category=category,
                           matches=matches, total_lost=total_lost, total_found=total_found,
                           resolved_count=resolved_count)


@items_bp.route('/item/new', methods=['GET', 'POST'])
@login_required
def post_item():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        date = request.form.get('date', '').strip()
        color = request.form.get('color', '').strip()
        brand = request.form.get('brand', '').strip()
        item_type = request.form.get('type', '').strip().lower()
        image_file = request.files.get('image')

        if not title or not location or category not in CATEGORIES or item_type not in TYPES:
            flash('Please fill in the required fields.', 'danger')
            return redirect(url_for('items.post_item'))

        if category == 'ID Card':
            brand = ''

        if not allowed_description(description, image_file):
            flash('Description is required. If no image is uploaded, provide at least 20 characters.', 'danger')
            return redirect(url_for('items.post_item'))

        filename = None
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                image_file.save(save_path)
            else:
                flash('Only JPG and PNG images are allowed.', 'danger')
                return redirect(url_for('items.post_item'))

        item = Item(
            title=title,
            description=description,
            category=category,
            location=location,
            color=color,
            brand=brand,
            type=item_type,
            image=filename,
            user_id=current_user.id,
        )
        db.session.add(item)
        db.session.commit()

        find_matches_for_item(item)

        flash('Your item has been posted successfully.', 'success')
        return redirect(url_for('items.dashboard'))

    return render_template('post_item.html', categories=CATEGORIES, types=TYPES)


@items_bp.route('/item/<int:item_id>')
@login_required
def item_detail(item_id):
    _auto_close_expired_items()
    item = Item.query.get_or_404(item_id)
    owner = item.owner
    masked_email = owner.email.replace('@', ' [at] ')
    user_claim = None
    if current_user.is_authenticated:
        user_claim = Claim.query.filter_by(item_id=item.id, user_id=current_user.id).first()

    can_view_found_contact = (
        item.type == 'found'
        and (
            current_user.id == item.owner.id
            or (user_claim and user_claim.status == 'approved')
        )
    )

    return render_template(
        'item_detail.html',
        item=item,
        masked_email=masked_email,
        user_claim=user_claim,
        can_view_found_contact=can_view_found_contact
    )


@items_bp.route('/claim/<int:item_id>', methods=['POST'])
@login_required
def claim_item(item_id):
    item = Item.query.get_or_404(item_id)

    if item.type != 'found':
        flash('Claims are allowed only for found items.', 'danger')
        return redirect(url_for('items.item_detail', item_id=item_id))

    if item.user_id == current_user.id:
        flash('You cannot claim your own found item post.', 'danger')
        return redirect(url_for('items.item_detail', item_id=item_id))

    if item.status != 'active':
        flash('This item is no longer open for claims.', 'warning')
        return redirect(url_for('items.item_detail', item_id=item_id))

    existing_claim = Claim.query.filter_by(item_id=item_id, user_id=current_user.id).first()
    if existing_claim:
        flash('You have already submitted a claim for this item.', 'info')
        return redirect(url_for('items.item_detail', item_id=item_id))

    message = request.form.get('message', '').strip()
    if not message:
        flash('Unique detail / proof is required to submit a claim.', 'danger')
        return redirect(url_for('items.item_detail', item_id=item_id))

    claim = Claim(
        item_id=item_id,
        user_id=current_user.id,
        location=request.form.get('location', '').strip(),
        color=request.form.get('color', '').strip(),
        brand=request.form.get('brand', '').strip(),
        message=message
    )

    db.session.add(claim)
    _create_notification(
        user_id=item.user_id,
        item_id=item.id,
        message=f"New claim received for your item: {item.title}"
    )
    db.session.commit()

    flash('Claim submitted!', 'success')
    return redirect(url_for('items.item_detail', item_id=item_id))

# ===== CLAIM APPROVE / REJECT =====

@items_bp.route('/claim/<int:claim_id>/approve')
@login_required
def approve_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    item = claim.item

    if item.type != 'found' or item.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('items.dashboard'))

    if item.status != 'active':
        flash('This item is already resolved.', 'info')
        return redirect(url_for('items.item_detail', item_id=item.id))

    claim.status = 'approved'
    item.status = 'claimed'
    Claim.query.filter(
        Claim.item_id == item.id,
        Claim.id != claim.id,
        Claim.status == 'pending'
    ).update({'status': 'rejected'}, synchronize_session=False)
    _create_notification(
        user_id=claim.user_id,
        item_id=item.id,
        message=f"Your claim was approved for: {item.title}"
    )
    db.session.commit()
    flash('Claim approved and item marked as claimed.', 'success')

    return redirect(url_for('items.item_detail', item_id=item.id))


@items_bp.route('/claim/<int:claim_id>/reject')
@login_required
def reject_claim(claim_id):
    claim = Claim.query.get_or_404(claim_id)

    if claim.item.type != 'found' or claim.item.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('items.dashboard'))

    if claim.status != 'pending':
        flash('This claim is already processed.', 'info')
        return redirect(url_for('items.item_detail', item_id=claim.item_id))

    claim.status = 'rejected'
    db.session.commit()

    flash('Claim rejected.', 'info')
    return redirect(url_for('items.item_detail', item_id=claim.item_id))

# ===== MARK LOST ITEM AS FOUND =====
@items_bp.route('/mark_found/<int:item_id>')
@login_required
def mark_found(item_id):
    item = Item.query.get_or_404(item_id)

    if item.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('items.dashboard'))

    if item.type != 'lost':
        flash('Only lost items can be marked as found from this action.', 'danger')
        return redirect(url_for('items.item_detail', item_id=item.id))

    item.status = 'claimed'
    db.session.commit()

    flash('Item marked as found/resolved.', 'success')
    return redirect(url_for('items.item_detail', item_id=item.id))


@items_bp.route('/notifications/read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)

    if notification.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('items.dashboard'))

    notification.is_read = True
    db.session.commit()

    if notification.item_id:
        return redirect(url_for('items.item_detail', item_id=notification.item_id))
    return redirect(url_for('items.dashboard'))


@items_bp.route('/notifications/read-all')
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update(
        {'is_read': True},
        synchronize_session=False
    )
    db.session.commit()
    return redirect(request.referrer or url_for('items.dashboard'))