from flask import Flask, session, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__, template_folder="templates", static_folder="static")

app.secret_key = '$(*@^G0K0W0B0K0D*&^T*@3272y738121@!@)'

# Database connections
# mysql://username:password@hostname:port/database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost:3307/expense_tracker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True  # Disable modification tracking

db = SQLAlchemy(app)
    
UPLOAD_FOLDER = 'static/assets'  # Update this with the actual path to your assets folder
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}  # Specify allowed file extensions

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    approved = db.Column(db.Boolean, nullable=False, default=False)
    name = db.Column(db.Text, nullable=False)
    mobile = db.Column(db.String(10), unique=True, nullable=False)
    total_budget = db.Column(db.Float, nullable=False)
    available_budget = db.Column(db.Float, nullable=False)

    expenses = db.relationship('Expenses', backref='organization', lazy=True)

    def __repr__(self):
        return f'<Organization {self.email}>'
    

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'<Admin {self.email}>'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    expenses = db.relationship('Expenses', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'
    

class Expenses(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.Boolean, nullable=False, default=True)
    date = db.Column(db.DateTime, nullable=False)
    image = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Foreign key relationships
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organization.id'), nullable=False)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
def checkSession():
    if session.get("isAdminLoggedIn"):
        return {"id": session.get("id"), "userType": "ADMIN"}
    elif session.get("isOrganizationLoggedIn"):
        organization = Organization.query.filter_by(id=session.get("id")).first()
        return {"id": session.get("id"), "userType": "ORG", "organization": organization}
    else:
        return None
    
def redirectToCorrectRoute(userData):
    if userData['userType'] == "ADMIN":
        return redirect(url_for("admin_dashboard"))
    elif userData['userType'] == "ORG":
        return redirect(url_for("org_dashboard"))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def login():
    userLoggedInCheck = checkSession()
    if userLoggedInCheck:
        return redirectToCorrectRoute(userLoggedInCheck)
    else:
        success = request.args.get("success")
        error = request.args.get("error")
        if request.method == "POST":
            email = request.form.get('email')
            password = request.form.get('password')
            selectedTab = request.form.get("selectedTab")
            if selectedTab == "admin":
                admin = Admin.query.filter_by(email=email, password=password).first()
                if admin:
                    session['id'] = admin.id
                    session['isAdminLoggedIn'] = True
                    return redirect(url_for("admin_dashboard"))
                else:
                    return render_template("index.html", error="No Admin found!")
            elif selectedTab == "organization":
                organization = Organization.query.filter_by(email=email, password=password).first()
                if organization:
                    if organization.approved:
                        session['id'] = organization.id
                        session['isOrganizationLoggedIn'] = True
                        success = "User found!"
                        return redirect(url_for("org_dashboard"))
                    else:
                        return render_template("index.html", error="Organization not approved yet, contact admin.")
                else:
                    return render_template("index.html", error="No Organization found!")
            else:
                return render_template("index.html", success=success, error=error)
        else:
            return render_template("index.html", success=success, error=error)


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("login", success="Logout Success!"))       

# Admin routes
@app.route("/admin/dashboard", methods=["GET"])
def admin_dashboard():
    if checkSession():
        success = request.args.get("success")
        all_organizations = Organization.query.all()
        return render_template("admin_dashboard.html", all_organizations=all_organizations, success=success)
    else:
        return redirect(url_for("login"))

@app.route("/create_admin", methods=["GET"])
def create_admin():
    # Example JSON data for creating a new admin
    admin_data = {
        'email': 'admin@gmail.com',
        'password': 'password123'
    }

    # Create a new admin object based on the JSON data
    new_admin = Admin(**admin_data)

    # Add the new admin object to the session and commit the changes to the database
    db.session.add(new_admin)
    db.session.commit()

    return 'Admin created successfully'

@app.route("/admin/organization/approve/<int:organization_id>/<status>", methods=["GET"])
def approveOrg(organization_id, status):
    check = checkSession()
    success = None
    if check and check['userType'] == "ADMIN":
        organization = Organization.query.filter_by(id=organization_id).first()
        if organization:
            organization.approved = status.lower() == 'true'
            db.session.commit()
            success = f'{organization.name} organization updated successfully'
    return redirect(url_for("admin_dashboard", success=success))

# Organization Routes
def create_org(org_data):
    # Create a new admin object
    new_admin = Organization(**org_data)

    # Add the new admin object to the session and commit the changes to the database
    db.session.add(new_admin)
    db.session.commit()
    return True

@app.route("/signup", methods=["GET", "POST"])
def org_signup():
    userLoggedInCheck = checkSession()
    if userLoggedInCheck:
        return redirectToCorrectRoute(userLoggedInCheck)
    else:
        if request.method == "POST":
            email = request.form.get('email')
            password = request.form.get('password')
            name = request.form.get('name')
            mobile = request.form.get('mobile')
            total_budget = request.form.get('total_budget')
            organization = Organization.query.filter( 
                or_(Organization.email == email, Organization.mobile == mobile)
                ).first()
            if organization:
                return redirect(url_for("login", error="Organization already exists with the Mobile/Email."))
            create_org({
                'email': str(email),
                'password': password,
                'name': name,
                'mobile': mobile,
                'total_budget': int(total_budget),
                'available_budget': int(total_budget),
            })
            return redirect(url_for("login", success="Organization created successfully!"))
        return render_template("signup.html")

@app.route("/organization/dashboard", methods=["GET"])
def org_dashboard():
    check = checkSession()
    if check:
        categories = Category.query.all()
        expenses = Expenses.query.filter_by(organization_id=check['id']).\
        options(db.joinedload(Expenses.category)).all()
         # expenses = Expenses.query.filter_by(organization_id=check['id']).all()

        # for exp, cat_name in expenses:
        #     print(expense["name"])
        
        categories_data = [{'id': category.id, 'name': category.name} for category in categories]
        expenses_data = [{'id': expense.id, 'amount': expense.amount, "date": expense.date, 'category': expense.category.name} for expense in expenses]
        organization = Organization.query.filter_by(id=check['id']).first()
        return render_template("org_dashboard.html", organization=organization, check=check, categories=categories_data, expenses=expenses_data)
    else:
        return redirect(url_for("login"))
    
# Category routes
@app.route("/category", methods=["GET"])
def category_management():
    check = checkSession()
    if check:
        categories = Category.query.all()
        success = request.args.get("success")
        error = request.args.get("error")
        return render_template("category.html", categories=categories, success=success, error=error, check=check)
    else:
        return redirect(url_for("login"))

@app.route('/category/add', methods=["POST"])
def add_category():
    check = checkSession()
    if check:
        category_name = request.form.get('name')
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            new_category = Category(name=category_name)

            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for("category_management", success="New category added."))
        else:
            return redirect(url_for("category_management", error="Already a category exists with this name."))
    else:
        return redirect(url_for("login"))
    
    
@app.route('/category/delete/<id>/<status>', methods=["GET"])
def delete_category(id, status):
    check = checkSession()
    if check:
        category = Category.query.filter_by(id=id).first()
        if category:
            category.status = status.lower() == 'true'
            db.session.commit()
        return redirect(url_for("category_management", success="Deleted category successfully."))
    else:
        return redirect(url_for("login"))

# Expenses routes
@app.route("/expenses", methods=["GET"])
def expenses_management():
    check = checkSession()
    if check and check['userType'] == "ORG":
        expenses = Expenses.query.filter_by(organization_id=check['id']).all()
        success = request.args.get("success")
        error = request.args.get("error")
        categories = Category.query.all()
        return render_template("expenses.html",categories=categories, expenses=expenses, success=success, error=error, check=check)
    else:
        return redirect(url_for("login"))
    
@app.route('/expenses/add', methods=["POST"])
def add_expense():
    check = checkSession()
    if check and check['userType'] == "ORG" and request.method == "POST":
        
        expense_amount = float(request.form.get('amount'))
        org = Organization.query.filter_by(id=check['id']).first()
        if org.available_budget - expense_amount < 0:
            return redirect(url_for("expenses_management", error="Budget limit exceeds."))
        
        org.available_budget = org.available_budget - expense_amount

        expense_name = request.form.get('name')
        expense_date = request.form.get('date')
        expense_description = request.form.get('description')
        expense_category = request.form.get('category')
        expense_image = request.files['image']
        filename = None
        
        if 'file' in request.files and not allowed_file(expense_image.filename):
            return redirect(url_for("expenses_management", error="File not allowed!"))
        if expense_image.filename:
            filename = secure_filename(expense_image.filename)
            expense_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_expense = Expenses(
            name=expense_name,
            amount=expense_amount,
            date=expense_date,
            description=expense_description,
            image=filename,
            category_id = expense_category,
            organization_id = check['id']
        )

        db.session.add(new_expense)
        db.session.commit()
        
        return redirect(url_for("expenses_management", success="Expenses added successfully!"))
    else:
        return redirect(url_for("login"))


@app.route('/expenses/delete/<id>', methods=["GET"])
def delete_expense(id):
    check = checkSession()
    if check and check['userType'] == "ORG":
        expense = Expenses.query.filter_by(id=id).first()
        org = Organization.query.filter_by(id=check['id']).first()
        org.available_budget = org.available_budget + expense.amount
        db.session.delete(expense)
        db.session.commit()
        return redirect(url_for("expenses_management", success="Expenses deleted successfully!"))
    else:
        return redirect(url_for("login"))

@app.route('/income', methods=["GET", "POST"])
def income():    
    check = checkSession()
    if check and check['userType'] == "ORG":
        org = Organization.query.filter_by(id=check['id']).first()
        success = None
        if request.method == "POST":
            income = request.form.get('income')
            org.available_budget = org.available_budget + float(income)
            db.session.commit()
            success = f"${income} Added income successfully."
        return render_template("income.html", check=check, success=success)
    else:
        return redirect(url_for("login"))
    
@app.before_request
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    app.run(port=8000, debug=True)