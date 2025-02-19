from flask import Flask, request, redirect, url_for, session, render_template 
import requests
import time
import json
import os
from dotenv import load_dotenv, set_key
from flask import jsonify , session
from flask_cors import CORS  # Import CORS
import psycopg2
import sqlite3 

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

# Load environment variables from .env file
load_dotenv()




DATABASE_URL = os.getenv('DATABASE_URL')  # Set this in your environment or .env file





# Replace these with your actual Zoho details
client_id = os.getenv('ZOHO_CLIENT_ID')
client_secret = os.getenv('ZOHO_CLIENT_SECRET')
redirect_uri = os.getenv('ZOHO_REDIRECT_URI')
auth_url = 'https://accounts.zoho.com/oauth/v2/auth'
token_url = 'https://accounts.zoho.com/oauth/v2/token'
api_url = 'https://people.zoho.com/people/api/forms/employee/getRecords'

@app.route('/')
def index():
    scope = 'ZOHOPEOPLE.forms.ALL'
    auth_request_url = f"{auth_url}?scope={scope}&client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&access_type=offline"
    return redirect(auth_request_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return 'Error: No code found in the callback URL', 400

    token_data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    response = requests.post(token_url, data=token_data)
    response_json = response.json()

    if response.status_code != 200:
        return f"Error: {response_json.get('error', 'Unknown error')}", 400
    
    access_token = response_json.get('access_token')
    if not access_token:
        return 'Error: Access token not found', 400
 
   
    set_key('.env', 'ZOHO_ACCESS_TOKEN', access_token)

    # Store the token in session for immediate use
    session['access_token'] = access_token
    return redirect(url_for('fetch_bulk_records'))

# @app.route('/fetch_bulk_records')
# def fetch_bulk_records():
#     access_token = session.get('access_token') or os.getenv('ZOHO_ACCESS_TOKEN')
#     if not access_token:
#         return 'Error: Access token not found', 400

#     headers = {'Authorization': f'Zoho-oauthtoken {access_token}', 'Content-Type': 'application/json'}
#     params = {'sIndex': 1, 'limit': 100}
#     all_records = []

#     while True:
#         response = requests.get(api_url, headers=headers, params=params)
#         response_json = response.json()

#         if response.status_code == 200:
#             employee_data = response_json.get("response", {}).get("result", [])

#             if not employee_data:
#                 break

#             all_records.extend(employee_data)
#             params['sIndex'] += 100  # Move to the next set of records
#         elif response.status_code == 429:
#             retry_after = int(response.headers.get('Retry-After', 60))
#             time.sleep(retry_after)
#         else:
#             return f"Error fetching records: {json.dumps(response_json)}"

#     # Format the records to a structured JSON format before passing to template
#     formatted_records = []
#     for record in all_records:
#         formatted_record = {
#             "records": record,
#             'EmployeeID': record.get('Employee_ID', 'N/A'),
#             'FirstName': record.get('First_Name', 'N/A'),
#             'LastName': record.get('Last_Name', 'N/A'),
#             'EmailID': record.get('Email_ID', 'N/A'),
#             'Department': record.get('Department', 'N/A'),
#             'Photo': record.get('Photo', 'default.jpg'),  # Default photo if not available
#         }

#         print('let go',formatted_record)
#         formatted_records.append(formatted_record)

#     return jsonify(formatted_records)
#     return render_template('employees.html', employees=formatted_records)

# @app.route('/public/employees')
# def public_employees():
#     # Use the stored access token from .env
#     access_token = os.getenv('ZOHO_ACCESS_TOKEN')

#     if not access_token:
#         return 'Error: Access token not found', 400

#     headers = {'Authorization': f'Zoho-oauthtoken {access_token}', 'Content-Type': 'application/json'}
#     params = {'sIndex': 1, 'limit': 100}
#     all_records = []

#     # Fetch employee data
#     while True:
#         response = requests.get(api_url, headers=headers, params=params)
#         response_json = response.json()

#         if response.status_code == 200:
#             employee_data = response_json.get("response", {}).get("result", [])

#             if not employee_data:
#                 break

#             all_records.extend(employee_data)
#             params['sIndex'] += 100  # Move to the next set of records
#         elif response.status_code == 429:
#             retry_after = int(response.headers.get('Retry-After', 60))
#             time.sleep(retry_after)
#         else:
#             return f"Error fetching records: {json.dumps(response_json)}"

#     # Format the records for rendering
#     formatted_records = []
#     for record in all_records:
#         formatted_record = {
#              "records": record,
#             'EmployeeID': record.get('Employee_ID', 'N/A'),
#             'FirstName': record.get('First_Name', 'N/A'),
#             'LastName': record.get('Last_Name', 'N/A'),
#             'EmailID': record.get('Email_ID', 'N/A'),
#             'Department': record.get('Department', 'N/A'),
#             'Photo': record.get('Photo', 'default.jpg'),
#         }
#         formatted_records.append(formatted_record)

#     # Render the public employee data
#     return render_template('public_employees.html', employees=formatted_records)


@app.route('/employee/<employee_id>')
def fetch_employee(employee_id):
    # Retrieve the access token from session or .env
    access_token = session.get('access_token') or os.getenv('ZOHO_ACCESS_TOKEN')
    if not access_token:
        return 'Error: Access token not found', 400

    # Set up headers for the API request
    headers = {'Authorization': f'Zoho-oauthtoken {access_token}', 'Content-Type': 'application/json'}
    
    # Send the GET request to the Zoho API
    url = f"{api_url}?criteria=Employee_ID=='{employee_id}'"
    response = requests.get(url, headers=headers)
    response_json = response.json()

    if response.status_code == 200:
        # Get the employee data from the response
        employee_data = response_json.get("response", {}).get("result", [])
        
        # Check if the employee_data contains the employee_id you're interested in
        for record in employee_data:
            # Assuming the employee ID is the key in the dictionary (based on the structure of the data)
            if employee_id in record:
                # Print the data of the specific employee
                
                jsondata = jsonify(record[employee_id])  # Optionally return as JSON response
                employee_details = record[employee_id]
                
                # Return the employee details to the template
                return render_template('employee_detail.html', employees=employee_details)
        
        # If no matching employee was found
        return 'Error: Employee not found', 404
    else:
        return 'Error: Unable to fetch employee data', 500



@app.route('/api/employees', methods=['GET'])
def fetch_bulk_recordsx():
    access_token = session.get('access_token') or os.getenv('ZOHO_ACCESS_TOKEN')
    if not access_token:
        return 'Error: Access token not found', 400

    headers = {'Authorization': f'Zoho-oauthtoken {access_token}', 'Content-Type': 'application/json'}
    params = {'sIndex': 1, 'limit': 100}
    all_records = []

    while True:
        response = requests.get(api_url, headers=headers, params=params)
        response_json = response.json()

        if response.status_code == 200:
            employee_data = response_json.get("response", {}).get("result", [])

            if not employee_data:
                break

            all_records.extend(employee_data)
            params['sIndex'] += 100  # Move to the next set of records
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
        else:
            return f"Error fetching records: {json.dumps(response_json)}"

    # Format the records to a structured JSON format before passing to template
    formatted_records = []
    for record in all_records:
        formatted_record = {
            "records": record,
            'EmployeeID': record.get('Employee_ID', 'N/A'),
            'FirstName': record.get('First_Name', 'N/A'),
            'LastName': record.get('Last_Name', 'N/A'),
            'EmailID': record.get('Email_ID', 'N/A'),
            'Department': record.get('Department', 'N/A'),
            'Photo': record.get('Photo', 'default.jpg'),  # Default photo if not available
        }
        formatted_records.append(formatted_record)

    return jsonify(formatted_records)


@app.route('/api/hello', methods=['GET'])
def hello_world():
    return jsonify({'message': 'Hello World'})



# Database URL (ensure this is set correctly for Onrender)
DATABASE_URL = os.getenv('DATABASE_URL')  # Set this in your environment or .env file

 
# Function to get database connection
import psycopg2

def get_db_connection():
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
        # Alter the table and add a new column "about"
        # cursor.execute("""
        #     ALTER TABLE employee_table
        #     ALTER COLUMN employee_id TYPE VARCHAR(100);

        #     -- Check if the column "about" exists and alter it to VARCHAR(10000) if it does
        #     DO $$
        #     BEGIN
        #         IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
        #                        WHERE table_name = 'employee_table' AND column_name = 'about') THEN
        #             ALTER TABLE employee_table ADD COLUMN about TEXT;
        #         END IF;
        #     END $$;

        #     -- Change the "about" column data type to VARCHAR(10000)
        #     ALTER TABLE employee_table
        #     ALTER COLUMN about TYPE VARCHAR(10000);
        # """)
        conn.commit()  # Commit the changes
        
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None



@app.route('/fetch_bulk_records')
def fetch_bulk_records():
    access_token = session.get('access_token') or os.getenv('ZOHO_ACCESS_TOKEN')
    if not access_token:
        return 'Error: Access token not found', 400

    headers = {'Authorization': f'Zoho-oauthtoken {access_token}', 'Content-Type': 'application/json'}
    params = {'sIndex': 1, 'limit': 100}
    all_records = []

    while True:
        response = requests.get(api_url, headers=headers, params=params)
        response_json = response.json()

        if response.status_code == 200:
            employee_data = response_json.get("response", {}).get("result", [])

            if not employee_data:
                break

            all_records.extend(employee_data)
            params['sIndex'] += 100  # Move to the next set of records
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
        else:
            return f"Error fetching records: {json.dumps(response_json)}"

    # Get DB connection
    conn = get_db_connection()
    if not conn:
        return 'Error: Could not connect to the database', 500

    cursor = conn.cursor()

    # List to hold all formatted records to return later
    formatted_records = []

    for record in all_records:
        formatted_record = {
            "records": record,  # Assuming `record` is a dictionary
        }

        # Iterate through all keys in 'records'
        for employee_key, employee_data_list in formatted_record['records'].items():
            if isinstance(employee_data_list, list):  # Ensure it's a list
                # Iterate over each employee record in the list
                for employee_data in employee_data_list:
                    # Extracting specific information for each employee

                  
                    employee_id = employee_data.get('EmployeeID', 'N/A')  # Can now handle alphanumeric
                    first_name = employee_data.get('FirstName', 'N/A')
                    last_name = employee_data.get('LastName', 'N/A')
                    email_id = employee_data.get('EmailID', 'N/A')
                    photo_url = employee_data.get('Photo', 'default.jpg')
                    photo_download_url = employee_data.get('Photo_downloadUrl', 'default.jpg')
                    about = employee_data.get('AboutMe', 'N/A')

                    # Printing the extracted information for each employee
                    print(f"Employee ID: {employee_id}")
                    print(f"First Name: {first_name}")
                    print(f"Last Name: {last_name}")
                    print(f"Email ID: {email_id}")
                    print(f"Photo URL: {photo_url}")
                    
                    print(f"about: {about}")
                    print(f"Photo 2 nd URL: {photo_download_url}")
                    print("-----")  # Separator between records

                    # Add the employee data to the list to return it
                    formatted_records.append({
                        'EmployeeID': employee_id,
                        'FirstName': first_name,
                        'LastName': last_name,
                        'EmailID': email_id,
                        'PhotoURL': photo_url,
                        'PhotoURL1': photo_download_url,
                        'about': about,
                    })

                    # Insert or update the record in the employee_table
                    cursor.execute("""
                    INSERT INTO employee_table (employee_id, first_name, last_name, email_id, photo_downloadUrl, photo_url , about)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (employee_id) 
                    DO UPDATE SET
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        email_id = EXCLUDED.email_id,
                        photo_downloadUrl = EXCLUDED.photo_downloadUrl,
                        photo_url = EXCLUDED.photo_url,
                        about = EXCLUDED.about;
                    """, (employee_id, first_name, last_name, email_id, photo_download_url, photo_url, about))
                    conn.commit()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    # Return all records
    return jsonify(formatted_records)





@app.route('/api/employeesfetch', methods=['GET'])
def get_all_employees():
    # Get DB connection
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Could not connect to the database'}), 500

    cursor = conn.cursor()

    # Query to fetch all employee records from employee_table
    cursor.execute('SELECT employee_id, first_name, last_name, email_id, photo_url ,photo_downloadUrl FROM employee_table;')

    # Fetch all records
    employees = cursor.fetchall()

    print(employees)
    # Format the records into a list of dictionaries
    formatted_employees = []
    for employee in employees:
        formatted_employees.append({
            'EmployeeID': employee[0],  # Assuming employee_id is the first column
            'FirstName': employee[1],   # Assuming first_name is the second column
            'LastName': employee[2],    # Assuming last_name is the third column
            'EmailID': employee[3],     # Assuming email_id is the fourth column
            'PhotoURL': employee[4],    # Assuming photo_url is the fifth column
             'photo_downloadUrl': employee[4], 
        })

    # Close the cursor and connection
    cursor.close()
    conn.close()

    # Return all employee records as JSON
    return jsonify(formatted_employees)
















# If you want to render the records on an HTML page:
# return render_template('employees.html', employees=formatted_records)

# return render_template('employees.html', employees=formatted_records)



  # Set this in your environment or .env file

# def get_db_connectionp():
#     # Make sure that DATABASE_URL is properly set
#     if not DATABASE_URL:
#         raise ValueError("DATABASE_URL is not set")

#     conn = sqlite3.connect(DATABASE_URL)  # Connect to the SQLite database using the DATABASE_URL
#     conn.row_factory = sqlite3.Row  # This allows access to rows like dictionaries
#     return conn

# @app.route('/api/employees', methods=['GET'])
# def get_all_employees():
#     try:
#         # Get DB connection
#         conn = get_db_connectionp()

#         # Query to fetch all employees
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM employee_table;')

#         # Fetch all records
#         employees = cursor.fetchall()

#         # Format the records into a dictionary of employees keyed by EmployeeID
#         formatted_employees = {}
#         for employee in employees:
#             # Extract the EmployeeID (assuming it's a column in the table)
#             employee_id = employee['EmployeeID']
#             formatted_employees[employee_id] = {
#                 'EmployeeID': employee['EmployeeID'],
#                 'FirstName': employee['FirstName'],
#                 'LastName': employee['LastName'],
#                 'EmailID': employee['EmailID'],
#                 'Photo': employee['Photo'],
#                 'Role': employee['Role'],
#                 # You can add any other fields you need here
#             }

#         # Close the cursor and connection
#         cursor.close()
#         conn.close()

#         # Return all employee records as JSON
#         return jsonify({'records': formatted_employees})
    
#     except Exception as e:
#         # Handle exceptions (e.g., DB connection error, query error)
#         return jsonify({'error': f'Error: {str(e)}'}), 500



if __name__ == '__main__':
    app.run(debug=True, port=5000)
