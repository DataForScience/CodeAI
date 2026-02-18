"""Flask REST API for User management."""

from flask import Flask, request, render_template, redirect
from flask_restful import Api, Resource
from flask_cors import CORS

from config import Config
from models import db, User
from schemas import UserSchema, UserCreateSchema, UserUpdateSchema

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
CORS(app)
api = Api(app)

# Schemas
user_schema = UserSchema()
user_create_schema = UserCreateSchema()
user_update_schema = UserUpdateSchema()


def make_error_response(message, status_code):
    """Return a JSON error response."""
    return {"error": message}, status_code


class UserListResource(Resource):
    """GET /api/users - list all users with pagination. POST - create user."""

    def get(self):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", Config.DEFAULT_PAGE_SIZE, type=int)
        per_page = min(per_page, Config.MAX_PAGE_SIZE)

        if page < 1:
            return make_error_response("Page must be >= 1", 400)
        if per_page < 1:
            return make_error_response("per_page must be >= 1", 400)

        pagination = User.query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        users = pagination.items

        # Redirect browser requests to HTML view
        if request.accept_mimetypes.accept_html:
            return redirect(f"/users?page={page}&per_page={per_page}", code=302)

        return {
            "users": user_schema.dump(users, many=True),
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
            },
        }

    def post(self):
        data = request.get_json()
        if not data:
            return make_error_response("Request body must be JSON", 400)

        errors = user_create_schema.validate(data)
        if errors:
            return {"errors": errors}, 400

        if User.query.filter_by(email=data["email"]).first():
            return make_error_response("Email already in use", 400)

        user = User(
            email=data["email"].strip().lower(),
            name=data["name"].strip(),
        )
        db.session.add(user)
        db.session.commit()
        return user_schema.dump(user), 201


class UserResource(Resource):
    """GET, PUT, DELETE /api/users/:id - single user operations."""

    def get(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return make_error_response("User not found", 404)
        # Redirect browser requests to HTML view
        if request.accept_mimetypes.accept_html:
            return redirect(f"/users/{user_id}", code=302)
        return user_schema.dump(user)

    def put(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return make_error_response("User not found", 404)

        data = request.get_json()
        if not data:
            return make_error_response("Request body must be JSON", 400)

        errors = user_update_schema.validate(data, partial=True)
        if errors:
            return {"errors": errors}, 400

        if "email" in data:
            email = data["email"].strip().lower()
            existing = User.query.filter(
                User.email == email, User.id != user_id
            ).first()
            if existing:
                return make_error_response("Email already in use", 400)
            user.email = email
        if "name" in data:
            user.name = data["name"].strip()

        db.session.commit()
        return user_schema.dump(user)

    def delete(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return make_error_response("User not found", 404)
        db.session.delete(user)
        db.session.commit()
        return "", 204


# Register routes
api.add_resource(UserListResource, "/api/users")
api.add_resource(UserResource, "/api/users/<int:user_id>")


# HTML views for browser
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/users")
def users_list():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", Config.DEFAULT_PAGE_SIZE, type=int)
    per_page = min(per_page, Config.MAX_PAGE_SIZE)
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template(
        "users.html",
        users=pagination.items,
        pagination={"page": pagination.page, "pages": pagination.pages},
    )


@app.route("/users/<int:user_id>")
def user_detail(user_id):
    user = User.query.get(user_id)
    if not user:
        return render_template("404.html"), 404
    return render_template("user.html", user=user)


@app.errorhandler(404)
def not_found(e):
    return make_error_response("Not found", 404)


@app.errorhandler(400)
def bad_request(e):
    return make_error_response("Bad request", 400)


@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return make_error_response("Internal server error", 500)


def init_db():
    """Initialize database tables."""
    import os
    instance_path = os.path.join(os.path.dirname(__file__), "instance")
    os.makedirs(instance_path, exist_ok=True)
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
