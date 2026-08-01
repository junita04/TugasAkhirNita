import os

from superset.app import create_app


app = create_app()
with app.app_context():
    username = os.environ["SUPERSET_ADMIN_USERNAME"]
    if app.appbuilder.sm.find_user(username=username) is None:
        role = app.appbuilder.sm.find_role("Admin")
        app.appbuilder.sm.add_user(
            username=username,
            first_name="Admin",
            last_name="User",
            email=os.environ["SUPERSET_ADMIN_EMAIL"],
            role=role,
            password=os.environ["SUPERSET_ADMIN_PASSWORD"],
        )
