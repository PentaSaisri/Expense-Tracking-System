Readme.txt
----------------------------------------------------------------------------------------------------
Software requirements (Please make sure you have the following softwares installed on your system)

Python (Make sure you select the add to path option at the beginning of the installation)
Xampp server
Vs Code (Only if you want to make any changes to the code)

Xampp server & Database setup:
Step 1: Open Xampp control panel
Step 2: Start the Apache & MySQL (Make sure the module name is turned into green color and ports are active)
Step 3: Open http://localhost/phpmyadmin
Step 4: Create a new database by clicking on new from the left navigation menu 
Step 5: Enter the database name "expense_tracker" and click on create.


Code setup & Run:
Step 1: Unzip the code folder
Step 2: Right click inside the folder in any empty space and click on command prompt or in the address bar enter cmd

Command prompt
Step 3: Enter "code ." - This will open the vs code.
Step 4: Enter "pip install -r requirements.txt"
Step 5: python app.py
Step 6: You should be seeing (Running on http://127.0.0.1:8000) Click on the link or copy and paste the link on the browser (google chrome preferred).


Note:
Make sure the database connection url in the app.py is correct line no. 14