import os
import matplotlib.pyplot as plt
from flask import request, render_template, redirect, url_for, Flask
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'h2.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
db = SQLAlchemy(app)
categories=['AC repair', 'Electrician', 'Plumber', 'Saloon','House cleaning']
#---------------------------------------------#
# Models
#---------------------------------------------#
# Login Model
class Login(db.Model):
    __tablename__ = 'login'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# Customer Model
class Customer(db.Model):
    __tablename__ = 'Customer'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    login_id = db.Column(db.Integer, db.ForeignKey('login.id'), nullable=False)  # Foreign key
    fullname = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    number = db.Column(db.Integer, nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=True)

hidden_requests = db.Table('hidden_requests',
    db.Column('request_id', db.Integer, db.ForeignKey('request.id'), primary_key=True),
    db.Column('professional_id', db.Integer, db.ForeignKey('Professional.id'), primary_key=True)
)
# Professional Model
class Professional(db.Model):
    __tablename__ = 'Professional'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    login_id = db.Column(db.Integer, db.ForeignKey('login.id'), nullable=False)  # Foreign key
    fullname = db.Column(db.String(150), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)  # Foreign key
    experience = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(250), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    number = db.Column(db.Integer, nullable=False, unique=True)
    service = db.relationship('Service', backref='Professionals')
    status = db.Column(db.String(20), nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    
# New Service
class Request(db.Model):
    __tablename__ = 'request'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('Customer.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('Professional.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    remarks = db.Column(db.String(600), nullable=True)
    hidden_from_professionals = db.relationship('Professional', secondary=hidden_requests, backref='hidden_requests')
    # Relationships 
    customer = db.relationship('Customer', backref='requests')
    professional = db.relationship('Professional', backref='requests')
    service = db.relationship('Service', backref='requests')

class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False)
    categorie = db.Column(db.String(255), nullable=False)

#-----------------------------------#
# Routes
#-----------------------------------#

# Home/Login Page
@app.route('/')
def home():
    return redirect(url_for('login'))

#------------------------------------#
# Login Action
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Login.query.filter_by(email=email)
        if user is None:
            return render_template('login.html',error="You have not registered") 
        if user.password != password:
            if not user.check_password(password):
                return render_template('login.html', error="Wrong Password")
        professional = Professional.query.filter_by(login_id=user.id)
        customer = Customer.query.filter_by(login_id=user.id)
        if professional :
            if professional.status == 'Active':
                return redirect(url_for('P_DashBoard', P_id=professional.id)) 
            elif professional.status == 'pending':
                    return render_template('login.html',error="Your account is not active")
            elif professional.status == 'Blocked':
                    return render_template('login.html',error="Your account is Blocked")
            else:
                return render_template('login.html',error="Your account is rejected")
        elif customer:
            if customer.status=='Blocked':
                return render_template('login.html',error="Your account is Blocked")
            return redirect(url_for('C_DashBoard', C_id=customer.id))  
        return redirect(url_for('Dash_Board'))  
    return render_template('login.html')
#-------------- Customer Signup Page----------------------#

@app.route('/register_customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'GET':
        return render_template('register_customer.html')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        fullname = request.form['fullname']
        address = request.form['address']
        pincode = request.form['pincode']
        number = request.form['number']  
        user = Login.query.filter_by(email=email).first()
        if user:
            return render_template('register_customer.html', error="Email already exists")
        new_login = Login(email=email)
        new_login.set_password(password)
        db.session.add(new_login)
        db.session.commit()
        status='Active'
        customer = Customer(fullname=fullname, address=address, pincode=pincode, login_id=new_login.id,number=number,status=status)
        db.session.add(customer)
        db.session.commit()

        return redirect(url_for('login'))

#---------------Professional Signup Page---------------------#
@app.route('/register_professional', methods=['GET', 'POST'])
def register_professional():
    if request.method == 'POST':
        # Fetch form data
        email = request.form['email']
        password = request.form['password']
        fullname = request.form['fullname']
        service = request.form.get('service')  
        experience = request.form['experience']
        address = request.form['address']
        pincode = request.form['pincode']
        number = request.form['number'] 
        user = Login.query.filter_by(email=email).first()
        if user:
            return render_template('register_professional.html', email_exists=True, services=categories)
        new_login = Login(email=email)
        new_login.set_password(password)
        db.session.add(new_login)
        db.session.commit()
        service = Service.query.filter_by(name=service).first()
        professional = Professional( fullname=fullname, service_id=service.id,experience=experience, address=address
                                ,pincode=pincode,login_id=new_login.id,number=number, status='pending')
        db.session.add(professional)
        db.session.commit()
        return redirect(url_for('login'))
    categories = [service.name for service in Service.query.all()] 
    return render_template('register_professional.html', services=categories)

# ------------------------------------------------Admin Dashboard-----------------------------------------------------------------------------------------------------
@app.route("/DashBoard", methods=["GET", "POST"])
def Dash_Board():
    services = Service.query.all()
    prof= Professional.query.all()
    requests = Request.query.all()
    return render_template("ad_dash.html",services=services,prof=prof,requests=requests)

#-------------------Update Service-------------------#
@app.route("/update_service/<int:id>", methods=["GET", "POST"])
def update_service(id):
    service = Service.query.get(id)
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price")
        service.name = name
        service.description = description
        service.price = price
        db.session.commit()
        return redirect(url_for("Dash_Board"))

    return render_template("ad_serviceEdit.html", service=service)
#-------------------Delete Service-------------------#
@app.route("/delete_service/<int:id>", methods=["GET", "POST"])
def delete_service(id):
    request = Request.query.filter_by(service_id=id).all()
    for r in request:
        db.session.delete(r)
    service = Service.query.get(id)
    db.session.delete(service)
    db.session.commit()
    return redirect(url_for("Dash_Board"))
#-------------------Accept Professional-------------------#
@app.route("/accept_professional/<int:id>", methods=["GET", "POST"])
def accept_professional(id):
    professional = Professional.query.get(id)
    professional.status = 'Active'
    db.session.commit()
    return redirect(url_for("Dash_Board"))
#-------------------Reject Professional-------------------#
@app.route("/reject_professional/<int:id>", methods=["GET", "POST"])
def reject_professional(id):
    professional = Professional.query.get(id)
    professional.status = 'Rejected'
    db.session.commit()
    return redirect(url_for("Dash_Board"))
#------------------New Service------------------#
@app.route("/New_Service", methods=["GET", "POST"])
def New_Service():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        price = request.form.get("price")
        cat = request.form.get('query')
        if Service.query.filter_by(name=name).first():
            return render_template("new_service.html", categories=categories, error="Service already exists")
        try:
            price = float(price) 
            if price < 0:
                raise ValueError("Price cannot be negative.")
        except ValueError as e:
            return render_template("new_service.html", categories=categories, error=str(e))
        
        new_service = Service(name=name, description=description, price=price, categorie=cat)
        db.session.add(new_service)
        db.session.commit()
        return redirect(url_for("Dash_Board"))
    return render_template("new_service.html", categories=categories)
#-------------------Check professional details-------------------#
@app.route("/check_professional/<int:id>", methods=["GET"])
def check_professional(id):
    professional = Professional.query.get(id)
    return render_template("A_CheckProfile.html", professional=professional)
#-------------------Block Professional-------------------#
@app.route("/block_professional/<int:id>")
def block_professional(id):
    professional = Professional.query.get(id)
    professional.status = 'Blocked'
    services = Request.query.filter_by(professional_id=id).all()
    for service in services:
        if service.status == 'close it':
            service.status = 'Professional Blocked'
    db.session.commit()
    return redirect(url_for("Dash_Board"))
#--------------------Unblock Professional-------------------#
@app.route("/unblock_professional/<int:id>")
def Unblock_professional(id):
    professional = Professional.query.get(id)
    professional.status = 'Active'
    db.session.commit()
    return redirect(url_for("Dash_Board"))
#-------------------Check Customer details-------------------#
@app.route("/check_Customer/<int:id>", methods=["GET"])
def check_Customer(id):
    ustomer = Customer.query.get(id)
    return render_template("A_CustomerProfile.html", C=ustomer)
#-------------------Block Customer-------------------#
@app.route("/block_customer/<int:id>")
def block_Customer(id):
    Customer1 = Customer.query.get(id)
    Customer1.status = 'Blocked'
    services = Request.query.filter_by(customer_id=id).all()
    for service in services:
        if service.status == 'close it':
            service.status = 'Customer Blocked'
    db.session.commit()
    return redirect(url_for("Dash_Board"))
#--------------------Unblock Customer-------------------#
@app.route("/unblock_customer/<int:id>")
def Unblock_Customer(id):
    Customer1 = Customer.query.get(id)
    Customer1.status = 'Active'
    db.session.commit()
    return redirect(url_for("Dash_Board"))
#-------------------Check Request-------------------#
@app.route("/check_Request/<int:id>", methods=["GET"])
def check_Request(id):
    r = Request.query.get(id)
    return render_template("A_RequestDetails.html", r=r)
#----------------Admin Search--------------------#
@app.route('/ad_Search', methods=['GET', 'POST'])
def admin_search():
    if request.method == 'POST':
        category = request.form.get('category')
        query = request.form.get('query').lower()
        if query==None:
            return render_template('ad_search.html', error="Please enter a search query")
        if category == 'service':
            if query=='closed':
                results = Request.query.filter(Request.status=='closed').all()
            elif query=='open':
                results = Request.query.filter(Request.status=='close it' or Request.status=='Requested').all()
        elif category == 'customers':
            results=Customer.query.filter(Customer.fullname.ilike(f'%{query}%')).all()
        elif category == 'professionals':
            results = Professional.query.filter(Professional.fullname.ilike(f'%{query}%')).all()
        return render_template('ad_Search.html', results=results, category=category)
    return render_template('ad_search.html')
#-----------Admin Summary---------------------------#
@app.route('/ad_summary')
def ad_summary():

# Sample data for students and marks
    students = ["S1", "S2", "S3", "S4", "S5"]  # replace with actual student IDs
    marks = [75, 85, 90, 60, 88]               # replace with actual marks

    # Create the bar graph
    plt.bar(students, marks, color="blue", width=0.3)
    plt.xlabel("Student IDs")
    plt.ylabel("Marks")
    plt.title("Marks scored by students in FAT")

    # Save the plot as an image file
    plt.savefig("images/image.jpg", dpi=100)

    # Display the plot (optional)
    plt.show()

    total_customers = Customer.query.count()
    total_professionals = Request.query.count()
    total_services = Service.query.count()
    total_service_requests = {
        'Requested': Request.query.count(),
        'Closed': db.session.query(Request).filter_by(status='closed').count(),
        'Accepted': db.session.query(Request).filter_by(status='close it').count()
    }
    customer_ratings = {
        'positive': db.session.query(Request).filter(Request.rating >= 4).count(),
        'neutral': db.session.query(Request).filter(Request.rating == 3).count(),
        'negative': db.session.query(Request).filter(Request.rating <= 2).count()
    }
    
    return render_template('A_summary.html',total_customers=total_customers,total_professionals=total_professionals,
        total_services=total_services,total_service_requests=total_service_requests,customer_ratings=customer_ratings
    )
#--------------------------------------------Customer Dashboard------------------------------------------------------------------------------------------#
@app.route("/C_DashBoard/<int:C_id>", methods=["GET", "POST"])
def C_DashBoard(C_id):
    history = Request.query.filter_by(customer_id=C_id).all()
    return render_template("C_DashBoard.html", service1=categories, history=history,C_id=C_id)

#------------Booking--------------------#
@app.route("/C_Booking/<int:C_id>/<string:cato>", methods=["GET", "POST"])
def Booking(C_id, cato):
    results = Service.query.filter_by(categorie=cato).all()
    results = [s for s in results if Professional.query.filter_by(service_id=s.id).first()]
    if request.method == "POST":
        id = request.form.get("id")
        service = Service.query.get(id)
        if Request.query.filter_by(customer_id=C_id, service_id=service.id,status='requested').first():
            return redirect(url_for('C_DashBoard', C_id=C_id))
        new_request = Request(customer_id=C_id, service_id=service.id, status="requested")
        db.session.add(new_request)
        db.session.commit()
        return redirect(url_for('C_DashBoard', C_id=C_id))
    return render_template("C_Booking.html", C_id=C_id, cato=cato, services=results)

#------------------service Remarks--------------------#
@app.route("/service_remarks/<int:C_id>/<int:request_id>", methods=["GET", "POST"])
def service_remarks(C_id, request_id):
    service= Request.query.get(request_id)
    if request.method == "POST":
        service1= Service.query.get(service.service_id)
        rating = request.form.get("rating")
        remarks = request.form.get("remarks")
        service.rating = rating
        service.remarks = remarks
        if service1.rating is None:
            service1.rating = rating
        else:
            service1.rating =(service1.rating + int(rating))/2 
        service.status = "closed"
        db.session.commit()
        return redirect(url_for('C_DashBoard', C_id=C_id))
    
    return render_template("cu_remarks.html", service=service, C_id=C_id)

#-----------Customer Profile----------------#
@app.route('/C_Search/<int:C_id>', methods=['GET', 'POST'])
def C_search(C_id):
    if request.method == 'POST':
        category = request.form.get('category')
        query = request.form.get('query').lower()
        results = None
        if category == 'service':
            results = Service.query.filter(Service.name.ilike(f'%{query}%')).all()
            results = [s for s in results if Professional.query.filter_by(service_id=s.id).first()]
        elif category == 'pin':
            results = Professional.query.filter_by(pincode=int(query)).all()
            results = [Service.query.filter_by(id=s.service_id).first() for s in results if Professional.query.filter_by(service_id=s.id).first()]
        elif category == 'category':
            results = Service.query.filter(Service.categorie.ilike(f'%{query}%')).all()
            results = [s for s in results if Professional.query.filter_by(service_id=s.id).first()]
        return render_template('C_search.html', C_id=C_id, services=results)
    return render_template('C_search.html', C_id=C_id, new=True)

#--------------customer Summary----------------#
@app.route('/C_summary/<int:C_id>', methods=['GET'])
def C_summary(C_id):
    custmoer = Customer.query.get(C_id)
    total_service_requests = {
        'Requested': Request.query.filter_by(customer_id=C_id).count(),
        'Closed': Request.query.filter_by(customer_id=C_id, status='closed').count(),
        'Accepted': Request.query.filter_by(customer_id=C_id, status='close it').count()
    }
    return render_template('C_summary.html', C_id=C_id, total_service_requests=total_service_requests)


#--------------------------------------------Professional Dashboard---------------------------------------------------------------------------------------#
@app.route("/P_DashBoard/<int:P_id>", methods=["GET", "POST"])
def P_DashBoard(P_id):
    prof = Professional.query.get(P_id)
    service_id = prof.service_id
    if service_id == None:
        return redirect(url_for('P_Profile', P_id=P_id,service="Your service not found. Please select a service"))
    requests = Request.query.filter( Request.service_id == service_id,Request.status == 'requested',
        ~Request.hidden_from_professionals.contains(prof)
    ).all()
    closed = Request.query.filter(Request.service_id == service_id,Request.status == 'closed',
        ~Request.hidden_from_professionals.contains(prof)
    ).all()
    Accepted = Request.query.filter(Request.service_id == service_id,Request.status == 'close it',
        ~Request.hidden_from_professionals.contains(prof)
    ).all()
    closed.extend(Accepted)
    
    return render_template("P_dash.html", requests=requests, P_id=P_id, closed=closed)
#------------Professional Profile----------------#
@app.route("/P_Profile/<int:P_id>", methods=["GET", "POST"])
def P_Profile(P_id):
    professional = Professional.query.get(P_id)
    if request.method == "POST":
        professional.fullname = request.form.get("name")
        professional.pincode = request.form.get("pincode")
        professional.number = request.form.get("number")
        professional.experience = request.form.get("experience")
        professional.address = request.form.get("address")
        service = request.form.get('service')
        service = Service.query.filter_by(name=service).first()
        professional.service_id = service.id
        db.session.commit()
        return redirect(url_for('P_DashBoard', P_id=P_id))
    services = [service.name for service in Service.query.all()] 
    return render_template("P_profile.html", professional=professional, P_id=P_id,services=services)

#------------------Professional Accept request----------------#
@app.route("/P_Accept/<int:P_id>/<int:request_id>", methods=["GET", "POST"])
def P_Accept(P_id, request_id):
    request = Request.query.get(request_id)
    request.professional_id = P_id
    request.status = "close it"
    db.session.commit()
    return redirect(url_for('P_DashBoard', P_id=P_id))
#------------------Professional Reject request----------------#
@app.route("/P_Reject/<int:P_id>/<int:request_id>", methods=["GET", "POST"])
def P_Reject(P_id, request_id):
    request = Request.query.get(request_id)
    professional = Professional.query.get(P_id)
    if professional not in request.hidden_from_professionals:
        request.hidden_from_professionals.append(professional)
        db.session.commit()
    all_professionals = Professional.query.filter_by(service_id=request.service_id).all()
    all_rejected = all(pro in request.hidden_from_professionals for pro in all_professionals)
    if all_rejected:
        request.status = "rejected"
        db.session.commit()
    return redirect(url_for('P_DashBoard', P_id=P_id))

#--------------Professional Search----------------#
@app.route('/P_Search/<int:P_id>', methods=['GET', 'POST'])
def P_search(P_id):
    professional = Professional.query.get(P_id)
    service_id = professional.service_id
    hidden_request_ids = db.session.query(hidden_requests.c.request_id).filter(hidden_requests.c.professional_id == P_id)
    if request.method == 'POST':
        category = request.form.get('category')
        query = request.form.get('query').lower()
        if category == 'location':
            results = Request.query.join(Customer).filter(Request.service_id == service_id,Request.status == 'requested', 
                Customer.address.ilike(f'%{query}%'),~Request.id.in_(hidden_request_ids)).all()
        elif category == 'pincode':
            results = Request.query.join(Customer).filter(Request.service_id == service_id,Request.status == 'requested',
                    Customer.pincode.ilike(f'%{query}%'),~Request.id.in_(hidden_request_ids) ).all()

        return render_template('P_search.html', results=results, P_id=P_id)
    return render_template('P_search.html', P_id=P_id, new=True)

#-------------------------Professional Summary----------------#
@app.route('/P_summary/<int:P_id>', methods=['GET'])
def P_summary(P_id):
    total_service_requests = {
        'Requested': Request.query.filter_by(professional_id=P_id).count(),
        'Closed': Request.query.filter_by(professional_id=P_id, status='closed').count(),
        'Accepted': Request.query.filter_by(professional_id=P_id, status='close it').count()
    }
    customer_ratings = {
        'positive': Request.query.filter(Request.rating >= 4, Request.professional_id==P_id).count(),
        'neutral': Request.query.filter(Request.rating == 3, Request.professional_id==P_id).count(),
        'negative': Request.query.filter(Request.rating <= 2, Request.professional_id==P_id).count()
    }
    
    return render_template('P_summary.html', P_id=P_id, total_service_requests=total_service_requests, customer_ratings=customer_ratings)




# Run the ap
if __name__ == '__main__':
    app.run(debug=True)
