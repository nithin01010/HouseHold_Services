class Login(db.Model):
    __tablename__ = 'login'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
  
# Customer Model
class Customer(db.Model):
    __tablename__ = 'Customer'
    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.Integer, db.ForeignKey('login.id'), nullable=False)  # Foreign key
    fullname = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    number = db.Column(db.Integer, nullable=False, unique=True)

hidden_requests = db.Table('hidden_requests',
    db.Column('request_id', db.Integer, db.ForeignKey('request.id'), primary_key=True),
    db.Column('professional_id', db.Integer, db.ForeignKey('Professional.id'), primary_key=True)
)
# Professional Model
class Professional(db.Model):
    __tablename__ = 'Professional'
    id = db.Column(db.Integer, primary_key=True)
    login_id = db.Column(db.Integer, db.ForeignKey('login.id'), nullable=False)  # Foreign key
    fullname = db.Column(db.String(150), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)  # Foreign key
    experience = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(250), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    number = db.Column(db.Integer, nullable=False, unique=True)
    service = db.relationship('Service', backref='Professionals')
    status = db.Column(db.String(20), nullable=False)
# New Service
class Request(db.Model):
    __tablename__ = 'request'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('Professional.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    remarks = db.Column(db.String(600), nullable=True)
    hidden_from_professionals = db.relationship('Professional', secondary=hidden_requests, backref='hidden_requests')
    # Relationships to access associated models directly
    customer = db.relationship('Customer', backref='requests')
    professional = db.relationship('Professional', backref='requests')
    service = db.relationship('Service', backref='requests')

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    categorie = db.Column(db.String(255), nullable=False)
    rating = db.Column(db.Integer, nullable=True)