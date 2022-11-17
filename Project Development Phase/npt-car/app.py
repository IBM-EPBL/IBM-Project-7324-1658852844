from flask import Flask, render_template, redirect, Response,  url_for, request, jsonify
from flask_bootstrap import Bootstrap
# from flask_wtf import FlaskForm 
# from wtforms import StringField, PasswordField, BooleanField
# from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user  
from sklearn.preprocessing import LabelEncoder
import pandas as pd
import numpy as np
import os


import requests

# NOTE: you must manually set API_KEY below using information retrieved from your IBM Cloud account.
API_KEY = "C6cCIcP5VNHJr8YrK_X9dcCqNtb-IDwe6t0BHtU3qPJo"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
 API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}


app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thisisatopsecretmissiontopredictcarresalevalues!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Data/ResaleDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'False'
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True )
    created = db.Column(db.DateTime(timezone=False), server_default=func.now())
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    userpassword = db.Column(db.String(80))

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True )
    created = db.Column(db.DateTime(timezone=False), server_default=func.now())
    username = db.Column(db.String(15))
    rating = db.Column(db.Integer)
    comment = db.Column(db.String(1000))

class ResaleQuery(db.Model):
    __tablename__ = 'resalequery'
    id = db.Column(db.Integer, primary_key=True )
    created = db.Column(db.DateTime(timezone=False), server_default=func.now())
    cars_name = db.Column(db.String(25))
    cars_brand = db.Column(db.String(15))
    model = db.Column(db.String(15))
    model_year = db.Column(db.String(4))
    car_type = db.Column(db.String(15))
    kms = db.Column(db.String(15))
    owner = db.Column(db.String(2))
    gasoliene_type = db.Column(db.String(10))
    city = db.Column(db.String(15))
    state = db.Column(db.String(15)) 
    price = db.Column(db.Float)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('Index.html') 

@app.route('/register', methods = ["GET"])  
def register(): 
    return render_template('Register.html') 

@app.route('/login', methods = ["GET"])  
def login(): 
    return render_template('Login.html') 

@app.route('/registeruser', methods = ["POST","GET"])  
def registeruser():
    msg=""
    if request.method == "POST":  
        name = request.form["username"]  
        email = request.form["email"]  
        password = request.form["userpassword"]        
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=name, email=email, userpassword=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        # msg=DBHelper.save(name, email, hashed_password)
        msg="New User Registered"
        return jsonify(result=msg)
    else:
        return jsonify(result="Error")

@app.route('/loginuser', methods = ["POST"])  
def loginuser():
    if request.method == "POST":  
        useremail = request.form["useremail"]  
        userpassword = request.form["userpassword"]
        user = User.query.filter_by(email=useremail).first()
        if user:
            if check_password_hash(user.userpassword, userpassword):
                if request.form["remember"]=='':
                    rem = True
                else:
                    rem = False
                login_user(user, remember=rem)
                return jsonify(result="Login Successfull")
            return jsonify(result="Invalid Password")
        else:
            return jsonify(result="Invalid User Emaiil")
    else:
        return jsonify(result="Error")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/feedback', methods = ["POST"])
@login_required
def feedback():
    feedback = request.form.get('feedback')  
    comment = request.form.get('comment') 
    newfeedback = Feedback(username=current_user.username.upper(),rating=feedback, comment=comment)
    db.session.add(newfeedback)
    db.session.commit()
    return jsonify(result="Thanks")

@app.route('/dashboard')
@login_required
def dashboard():
    formdata = { 'name':current_user.username, 'sourcecount':'3592', 
                'usercount': db.session.query(User.id).count(), 
                'feedbackcount':db.session.query(Feedback.id).count(), 
                'searchcount':db.session.query(ResaleQuery.id).count() } 
    resalequeries = ResaleQuery.query
    return render_template('dashboard.html', data=formdata, enquiries=resalequeries)

@app.route('/feedbacklist')
@login_required
def feedbacklist():     
    feedbacks = Feedback.query
    return render_template('feedback.html', feedbacks=feedbacks)

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        pricer=predictprice(request)
        ypred = ' ₹ {:,.2f}'.format(pricer)
        return jsonify(result=ypred)
    else:
        return render_template('Predict.html') 

def predictprice(request):

    cars_name = request.form.get('brand') 
    cars_brand = cars_name.split(' ')[0]
    model = request.form.get('modeltype')
    model_year = int(request.form.get('regyear')) 
    car_type = request.form['gearbox']
    kms = float(request.form['kms'])
    owner = float(request.form['owner'])
    gasoliene_type = request.form['fuel']
    city = request.form.get('cityname') 
    state = request.form.get('statename')  

    new_row = {'cars_name':[cars_name],	'cars_brand':[cars_brand], 'model':[model],	'model_year':[model_year],
        	'car_type':[car_type], 'kms':[kms], 'owner':[owner], 'gasoliene_type':[gasoliene_type], 
            'city':[city], 'state':[state]}
    
    res_row = {'cars_name':cars_name,	'cars_brand':cars_brand, 'model':model,	'model_year':model_year,
        	'car_type':car_type, 'kms':kms, 'owner':owner, 'gasoliene_type':gasoliene_type, 
            'city':city, 'state':state}

    print(new_row)
    print("hi")
    #new_df = pd.DataFrame(new_row)
    #print(new_df)

    new_df = pd.DataFrame(new_row)
    print(new_df)
    # Encode the user inputs using the stored encoded data
    labels = ['cars_name', 'cars_brand', 'model', 'model_year', 'gasoliene_type', 'car_type',  'city', 'state']    
    for i in labels:
        print("hello")
        label = LabelEncoder()
        label.classes_=np.load('Data/'+str('classes'+i+'.npy'), allow_pickle=True)
        tr = label.transform(new_df[i])
        new_df[i]=tr
        #tr = label.transform(new_row[i])
        res_row[i]=int(tr[0])

    print(res_row)

    field = [list(res_row.keys())]
    value = [list(res_row.values())]
    #t = [[cars_name, cars_brand, model_year, car_type, kms, owner, gasoliene_type, city, state]]
    payload_scoring = {"input_data": [{"fields": field, "values": value}]}

    response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/5664a664-73fe-4670-b0f5-c6dbe2bf152e/predictions?version=2022-11-17', json=payload_scoring,
 headers={'Authorization': 'Bearer ' + mltoken})
    print("Scoring response")
    print(response_scoring.json())


    pred = response_scoring.json()
    print(response_scoring.json())
    #y_prediction = model_rand.predict(new_df)
    y_prediction = pred['predictions'][0]['values'][0][0]
    print(y_prediction)

    # Inserting the new search data and results
    newsearch =  ResaleQuery(cars_name = cars_name, cars_brand = cars_brand,model = model, model_year = model_year,
                            car_type = car_type,kms = kms,owner = owner,gasoliene_type = gasoliene_type,
                            city = city,state = state,price = y_prediction)

    db.session.add(newsearch)
    db.session.commit()
    return y_prediction 

if  __name__ == '__main__':
    
    if not os.path.exists("Data/ResaleDB.db"):  
        db.create_all()
    print("Starting Flask Application")
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='localhost', debug=False, threaded=False)
    print("Stopping Application")
