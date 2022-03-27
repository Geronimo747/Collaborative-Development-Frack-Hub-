# Collaborative-Development-Frack-Hub-
Collaborative Development Frack Hub Project


You need the app.py file and the templates folder with everything inside.
(I advise you create a python virtual enviroment for this; but it's not required.)

You need to install 3 packages:
- flask
- flask-login
- Flask-SQLAlchemy

*pip install [package]*

## Run the following python script, either standalone or in a terminal *In the same directory as the App folder.*:
```
import App
app = App.create_app()
with app.app_context():
    App.db.create_all()
```

## Done, now to run the actual app.
In a terminal, command prompt for windows, make sure you're in the same directory as the app.py file.
Then run it with python, for example:
```
python app.py
```
