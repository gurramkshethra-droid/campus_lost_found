from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import User, Item, Match

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(view):
    def wrapped_view(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access is required.', 'danger')
            return redirect(url_for('items.dashboard'))
        return view(*args, **kwargs)

    wrapped_view.__name__ = view.__name__
    return wrapped_view


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    users = User.query.order_by(User.name).all()
    items = Item.query.order_by(Item.created_at.desc()).all()
    matches = Match.query.order_by(Match.match_score.desc()).all()
    return render_template('admin.html', users=users, items=items, matches=matches)


@admin_bp.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash('Cannot delete another admin.', 'warning')
        return redirect(url_for('admin.dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.dashboard'))
