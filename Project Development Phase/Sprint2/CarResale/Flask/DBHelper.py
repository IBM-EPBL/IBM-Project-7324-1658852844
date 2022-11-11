import sqlite3
import traceback
import sys

def get_db_connection():
    conn = sqlite3.connect('Data/Resale.db')
    conn.row_factory = sqlite3.Row
    return conn

def save(name,email,password):
    msg="msg"
    try:
        with get_db_connection() as con:  
            cur = con.cursor()  
            cur.execute("INSERT into users (username, email, userpassword) values (?,?,?)",(name,email,password))  
            con.commit()  
            msg = "User successfully Added"  
        
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()  
        con.rollback()  
        msg = "We can not add the user to the system" 
        
    finally:   
        con.close() 
    return msg

def login(useremail, password):
    msg="msg"
    try:
        with get_db_connection() as con:  
            cur = con.cursor()  
            cur.execute("select 1 from users where email=? and userpassword=?",(useremail,password))   
            if  cur.fetchone() is not None:
                msg='Welcome'
            else:
                msg = 'Login failed'        
    except sqlite3.Error as er:
        print('SQLite error: %s' % (' '.join(er.args)))
        print("Exception class is: ", er.__class__)
        print('SQLite traceback: ')
        exc_type, exc_value, exc_tb = sys.exc_info()  
        con.rollback()  
        msg = 'DB Error'
        
    finally:   
        con.close() 
    return msg


def initdb():
    connection = get_db_connection()
    with open('Flask/schema.sql') as f:
        connection.executescript(f.read())
        
    cur = connection.cursor()
    cur.execute("INSERT INTO users (username, email, userpassword) VALUES (?, ?, ?)",
                ('harish', 'harishkumar.g.2019.cse@rajalakshmi.edu.in', 'harish123'))
    cur.execute("INSERT INTO users (username, email, userpassword) VALUES (?, ?, ?)",
                ('test', 'test@test.com', 'test123'))
    
    connection.commit()
    connection.close()

