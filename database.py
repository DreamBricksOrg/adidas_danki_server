from flask_mysqldb import MySQL

mysql = MySQL()


def initialize_mysql(app):
    app.config['MYSQL_HOST'] = '18.229.132.70'
    app.config['MYSQL_USER'] = 'db'
    app.config['MYSQL_PASSWORD'] = 'UzoEuMDNrBupB5E6z8DfqKgMW'
    app.config['MYSQL_DB'] = 'adidas-prod'
    mysql.init_app(app)

    return mysql
