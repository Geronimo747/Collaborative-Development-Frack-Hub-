

def main():
    import App
    import string
    from random import choices
    from werkzeug.security import generate_password_hash
    from datetime import datetime
    from flask_login.login_manager import LoginManager

    app = App.create_app()
    with app.app_context():
        App.db.create_all()

    login_manager = LoginManager(app=app)

    @login_manager.user_loader
    def load_user(user_id):
        """
        Used by the flask plugin to load information about a user.
        """
        return App.Users.query.get(user_id)

    password = "".join(choices(string.ascii_letters, k=16))
    print(f"\n\nAdmin password is: {password}\n\n")

    new_user = App.Users(
        name="admin",
        email="admin@frackhub.com",
        password=generate_password_hash("CHEESE" + password, "sha256"),
        address="admin",
        postcode="admin",
        credits=0,
        dob=datetime.now(),
        user_type=2,
        verified=1
    )

    with app.app_context():
        App.add_new_user(new_user)


if __name__ == "__main__":
    main()
