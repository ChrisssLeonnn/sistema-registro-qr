import os
import uuid
import qrcode
from datetime import datetime
from fpdf import FPDF
from flask import Flask, render_template, request, jsonify, send_from_directory

# Import our new database components
from db_utils import db, User

# --- App Configuration ---
app = Flask(__name__, static_folder='static', template_folder='templates')

# Configure the database
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///local_database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with our app
db.init_app(app)

# --- Directories ---
QRS_DIR = 'qrs'
PASSES_DIR = 'passes'
os.makedirs(QRS_DIR, exist_ok=True)
os.makedirs(PASSES_DIR, exist_ok=True)


# --- PDF Generation Helper ---
def _create_qr_pdf(user_name, qr_code, qr_img_path):
    """Creates a PDF pass for the user."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 20, 'Pase de Entrada', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font('Arial', '', 16)
    processed_name = f'Bienvenid@,\n{user_name}'.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, processed_name, 0, 'C')
    pdf.ln(10)
    pdf.image(qr_img_path, x=(210 - 70) / 2, y=None, w=70, h=70)
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 12)
    pdf.cell(0, 10, f'Tu código: {qr_code}', 0, 1, 'C')
    pdf_filename = f"pase_{qr_code}.pdf"
    pdf_path = os.path.join(PASSES_DIR, pdf_filename)
    pdf.output(pdf_path)
    return pdf_filename

# --- Routes ---
@app.route('/')
def home():
    """Serves the main registration page."""
    return render_template('index.html')

@app.route('/qrs/<path:filename>')
def serve_qr(filename):
    """Serves the generated QR code images."""
    return send_from_directory(QRS_DIR, filename)

@app.route('/download-pass/<path:filename>')
def download_pass(filename):
    """Serves the generated PDF pass for downloading."""
    return send_from_directory(PASSES_DIR, filename, as_attachment=True)

@app.route('/registro', methods=['POST'])
def registro():
    """Handles new user registration."""
    form_data = request.form
    nombre = form_data.get('nombre', '').strip()
    correo = form_data.get('correo', '').strip()
    curp = form_data.get('curp', '').strip().upper()
    
    if not all([nombre, correo, curp]):
        return jsonify({"status": "error", "msg": "Nombre, Correo y CURP son obligatorios."}), 400

    if User.query.filter((User.correo == correo) | (User.curp == curp)).first():
        return jsonify({"status": "error", "msg": "El Correo o CURP ya ha sido registrado."}), 409

    try:
        new_user = User(
            nombre=nombre,
            correo=correo,
            curp=curp,
            edad=int(form_data.get('edad', 0)),
            genero=form_data.get('genero', ''),
            colonia=form_data.get('colonia', ''),
            telefono=form_data.get('telefono', ''),
            codigo_qr=uuid.uuid4().hex[:8].upper()
        )

        checkin_url = request.host_url + f'checkin/{new_user.codigo_qr}'
        img = qrcode.make(checkin_url)
        img_path = os.path.join(QRS_DIR, f"{new_user.codigo_qr}.png")
        img.save(img_path)

        pdf_filename = _create_qr_pdf(new_user.nombre, new_user.codigo_qr, img_path)

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "status": "ok",
            "codigo": new_user.codigo_qr,
            "checkin_url": checkin_url,
            "pdf_filename": pdf_filename
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error during registration: {e}")
        return jsonify({"status": "error", "msg": "Ocurrió un error en el servidor."}), 500

@app.route('/checkin/<codigo>')
def checkin(codigo):
    """Handles the check-in process."""
    user = User.query.filter_by(codigo_qr=codigo).first()

    if not user:
        return render_template('checkin_resultado.html', status="invalid", message="❌ Código QR no válido o no encontrado.")
    
    if user.estado_entrada == 'registrado':
        fecha_registro = user.fecha_hora_checkin.strftime('%Y-%m-%d %H:%M:%S')
        return render_template('checkin_resultado.html', status="already_registered", message=f"⚠️ Este código ya fue registrado por {user.nombre} el {fecha_registro}.")
        
    user.estado_entrada = 'registrado'
    user.fecha_hora_checkin = datetime.utcnow()
    db.session.commit()
    
    return render_template('checkin_resultado.html', status="valid", message=f"✅ ¡Acceso Concedido! Bienvenid@, {user.nombre}.")

# --- Main Execution ---
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    url = "http://127.0.0.1:5001/"
    print("="*50)
    print(f"Servidor iniciado. Abre tu navegador y ve a: {url}")
    print("Para detener el servidor, presiona CTRL+C")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5001)
