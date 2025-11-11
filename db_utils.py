from flask_sqlalchemy import SQLAlchemy

# Create the database instance. We will initialize it in our main app file.
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    curp = db.Column(db.String(18), unique=True, nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    genero = db.Column(db.String(20), nullable=False)
    colonia = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    
    codigo_qr = db.Column(db.String(8), unique=True, nullable=False)
    estado_entrada = db.Column(db.String(20), nullable=False, default='pendiente')
    fecha_hora_checkin = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<User {self.nombre}>'
