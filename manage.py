from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from flfm import create_app, db
from config import Config

app = create_app(Config)

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
