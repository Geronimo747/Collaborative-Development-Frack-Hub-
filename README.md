# Collaborative-Development-Frack-Hub-
Collaborative Development Frack Hub Project


You need the **set_up_database.py** and **main.py** files and the **App folder** with everything inside it.\
(*I advise you create a python virtual enviroment for this; but it's not required.*)\
You also need ffmpeg (https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) \
Unpack the zip file then move the Bin folder containing the ffmpeg binaries next to the files listed above.\

You need to install 4 python packages:
- flask
- flask-login
- Flask-SQLAlchemy
- validators

### pip install *package*

## Initial setup, take note of the administrator password in the console.
Account for admin is admin@frackhub.com, then the password displayed in console.\
(*If you lose it you need to delete then reinitialise the database*).
```
python set_up_database.py
```

## Done, now to run the actual app.
In a terminal, command prompt for windows, make sure you're in the same directory as the app.py file.
Then run it with python, for example:
```
python main.py
```
