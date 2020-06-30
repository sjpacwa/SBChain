from flask import Flask, render_template, url_for, request, redirect
from werkzeug.utils import secure_filename
from csv import reader
import os
import ipaddress
import socket
import json

# function imports
os.chdir(r'./functions')
from transactions import check_transaction, send_single_transaction
from housekeeping import check_port, allowed_file
os.chdir('..')

app = Flask(__name__)
nodes = []
invalid_nodes = []
transaction_details = []
invalid_transaction_details = []


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html', title='About')


app.config["NODE_CSV_UPLOADS"] = os.getcwd() + r"\static\uploads\nodes"
app.config["ALLOWED_FILE_EXTENSION"] = ["CSV"]


@app.route("/register-nodes", methods=["GET", "POST"])
def upload_nodes_csv():
    if request.method == 'POST':
        if request.files:

            csv = request.files["csv"]

            if csv.filename == "":
                print("The CSV file must have a filename.")
                return redirect(request.url)

            if not allowed_file(csv.filename):
                print("That File Extension is not allowed.")
                return redirect(request.url)

            filename = secure_filename(csv.filename)
            file_path = os.path.join(app.config["NODE_CSV_UPLOADS"], filename)
            csv.save(file_path)
            print("Csv File saved")

            with open(file_path, 'r') as file_object:
                flag = True
                csv_reader = reader(file_object)
                for row in csv_reader:
                    if flag:
                        flag = False
                        continue
                    ip = row[0]
                    port = str(row[1])
                    if check_port(ip, port):
                        nodes.append((ip, port))
                    else:
                        invalid_nodes.append((ip, port))
            os.remove(file_path)
            # TODO
            # return redirect("nodesuploaded.html")
            return redirect(request.url)

    return render_template('register_nodes.html', title='register nodes')


@app.route("/send-transaction", methods=["GET", "POST"])
def send_transaction():
    print(nodes)
    if request.method == "POST":
        req = request.form

        # transaction properties
        sender = req["sender"]
        recipient = req.get("recipient")
        amount = int(req.get("amount"))

        if not check_transaction(sender, recipient, amount):
            return render_template('wrong_transaction.html')

        transaction = (sender, recipient, amount)

        # node properties
        ip = req.get("ip")
        port_number = int(req.get("port"))

        if not check_port(ip, port_number):
            return render_template('wrong_node.html')

        node = (ip, port_number)

        send_single_transaction(transaction, (ip, port_number))

        # TODO
        
        return redirect(request.url)

    return render_template("send_transaction.html")


def in_nodes(ip, port):
    for node in nodes:
        if node[0] == ip and node[1] == port:
            return True
    return False

def check_node(node):
    ip = node[0]
    port = node[1]
    return check_port(ip, port) and in_nodes(ip, port)


@app.route("/send-transactions", methods=["GET", "POST"])
def send_transactions():
    if request.method == 'POST':
        if request.files:

            csv = request.files["csv"]

            # TODO create check file format function
            if csv.filename == "":
                print("The CSV file must have a filename.")
                return redirect(request.url)

            if not allowed_file(csv.filename):
                print("That File Extension is not allowed.")
                return redirect(request.url)

            # TODO create file saving function
            filename = secure_filename(csv.filename)
            file_path = os.path.join(app.config["NODE_CSV_UPLOADS"], filename)
            csv.save(file_path)
            print("Csv File saved")

            with open(file_path, 'r') as file_object:
                flag = True
                csv_reader = reader(file_object)
                for row in csv_reader:
                    if flag:
                        flag = False
                        continue
                    transaction = (row[0], row[1], row[2])
                    node = (row[3], row[4])
                    transaction_details.append((transaction, node))
                    # if check_node(node) and check_transaction(transaction[0], transaction[1], transaction[2]):
                    #     transaction_details.append((transaction, node))
                    # else:
                    #     invalid_transaction_details.append((transaction, node))
            print("Transaction extracted.")
            print("Sending transactions.....")
            for transaction_detail in transaction_details:
                print("here")
                print(nodes)
                send_single_transaction(transaction_detail[0], transaction_detail[1])
            os.remove(file_path)
            # TODO
            # return redirect("transactions-uploaded.html")
            return redirect(request.url)

    return render_template('send_transactions.html', title='Send Transactions')


if __name__ == '__main__':
    app.run(debug=True)