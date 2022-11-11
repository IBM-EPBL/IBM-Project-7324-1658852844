import pandas as pd
import numpy as np
from flask import Flask, render_template, Response, request, jsonify
import pickle
from sklearn.preprocessing import LabelEncoder
import DBHelper
import os

app = Flask(__name__)
filename = 'Data/resale_model.sav'
model_rand = pickle.load(open(filename, 'rb'))

@app.route('/')
def index():
    return render_template('Index.html') 

@app.route('/registeruser', methods = ["POST","GET"])  
def registeruser():
    if request.method == "POST":  
        name = request.form["username"]  
        email = request.form["email"]  
        password = request.form["userpassword"]
        msg=DBHelper.save(name, email, password)
        return jsonify(result=msg)
    else:
        return jsonify(result="Error")


@app.route('/loginuser', methods = ["POST"])  
def loginuser():
    if request.method == "POST":  
        useremail = request.form["useremail"]  
        userpassword = request.form["userpassword"]
        msg = DBHelper.login(useremail, userpassword)
        return jsonify(result=msg)
    else:
        return jsonify(result="Error")

@app.route('/register', methods = ["GET"])  
def register(): 
    return render_template('Register.html') 

@app.route('/login', methods = ["GET"])  
def login(): 
    return render_template('Login.html') 

@app.route('/predict', methods=['GET', 'POST'])
def predict4():
    if request.method == 'POST':
        pricer=predictprice(request)
        ypred = '€{:.2f}'.format(pricer[0])
        return jsonify(result=ypred)
    else:
        return render_template('Predict.html') 

@app.route('/y_predict', methods=['POST'])
def y_predict():
    y_prediction = predictprice(request)
    return render_template('resalepredictDesign1.html', ypred = 'The resale value predicted is €{:.2f}'.format(y_prediction[0]))

@app.route('/json_predict', methods=['POST'])
def j_predict():
    y_prediction = predictprice(request)
    result='result'
    ypred = 'The resale value predicted is €{:.2f}'.format(y_prediction[0])
    return jsonify(result=ypred)

def predictprice(request):

    regyear = int(request.form.get('regyear'))
    regmonth = int(request.form.get('regmonth'))
    powerps = float(request.form['powerps'])
    kms = float(request.form['kms'])
    gearbox = request.form['gearbox']
    damage = request.form['dam']
    model = request.form.get('modeltype')
    brand = request.form.get('brand') 
    fuelType = request.form.get('fuel')   
    vehicletype = request.form.get('vehicletype')

    new_row = {'yearOfRegistration':regyear,'powerPS':powerps, 'kilometer':kms,
            'monthOfRegistration':regmonth, 'gearbox':gearbox, 'notRepairedDamage':damage,
            'model':model, 'brand':brand, 'fuelType':fuelType, 'vehicleType':vehicletype}
    print(new_row)

    new_df = pd.DataFrame(columns = ['vehicleType', 'yearOfRegistration', 'gearbox',
                                'powerPS', 'model', 'kilometer', 'monthOfRegistration', 'fuelType',
                                'brand', 'notRepairedDamage'])

    new_df = new_df.append(new_row,ignore_index =True)
    labels = ['gearbox', 'notRepairedDamage', 'model', 'brand', 'fuelType', 'vehicleType']
    mapper = {}
    for i in labels:
        mapper[i] = LabelEncoder()
        mapper[i].classes_=np.load('Data/'+str('classes'+i+'.npy'), allow_pickle=True)
        tr = mapper[i].fit_transform(new_df[i])
        new_df.loc[:, i+'_Labels'] = pd.Series(tr, index=new_df.index)

    labeled = new_df[['yearOfRegistration'
                        ,'powerPS'
                        ,'kilometer'
                        ,'monthOfRegistration'
                        ]
                    +[x+'_Labels' for x in labels]]
    X = labeled.values

    print(X)
    y_prediction = model_rand.predict(X)
    print(y_prediction)
    
    return y_prediction 

if  __name__ == '__main__':
    if not os.path.exists("Data/Resale.db"):
        DBHelper.initdb()
    print("Starting Flask Application")
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='localhost', debug=False, threaded=False)
    print("Stopping Application")
