import os

if os.path.exists('.env'):
    print('Importing environment form .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]


from flask_script import Manager
from app import create_app, db
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)

if __name__ == '__main__':
    #manager.run()
    app.run(debug=True, port=8818, threaded=True, host='0.0.0.0')


