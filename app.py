from flask import Flask
from sqlalchemy import inspect, text
from flask_login import current_user

from config import Config
from extensions import bcrypt, db, login_manager


def _sync_claim_table_columns():
    """Backfill claim table columns for older databases without migrations."""
    inspector = inspect(db.engine)
    if 'claim' not in inspector.get_table_names():
        return

    existing_columns = {col['name'] for col in inspector.get_columns('claim')}
    missing_sql = []

    if 'location' not in existing_columns:
        missing_sql.append("ALTER TABLE claim ADD COLUMN location VARCHAR(100)")
    if 'color' not in existing_columns:
        missing_sql.append("ALTER TABLE claim ADD COLUMN color VARCHAR(50)")
    if 'brand' not in existing_columns:
        missing_sql.append("ALTER TABLE claim ADD COLUMN brand VARCHAR(50)")
    if 'message' not in existing_columns:
        missing_sql.append("ALTER TABLE claim ADD COLUMN message TEXT")

    for stmt in missing_sql:
        db.session.execute(text(stmt))

    if missing_sql:
        db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    bcrypt.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    from models import User, Notification

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_notifications():
        if not current_user.is_authenticated:
            return {'header_notifications': [], 'unread_notifications_count': 0}

        notifications = (
            Notification.query
            .filter_by(user_id=current_user.id)
            .order_by(Notification.created_at.desc())
            .limit(6)
            .all()
        )
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return {
            'header_notifications': notifications,
            'unread_notifications_count': unread_count
        }

    from routes.auth import auth_bp
    from routes.items import items_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        _sync_claim_table_columns()

    return app


if __name__ == '__main__':
    application = create_app()
    application.run(host='0.0.0.0', port=5000, debug=True)
