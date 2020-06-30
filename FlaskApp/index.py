from flask import Flask, render_template, url_for, request, redirect
from werkzeug.utils import secure_filename
from csv import reader
import os
import ipaddress
import socket
import json

# function imports

from functions.transactions import check_transaction, send_single_transaction
from functions.housekeeping import check_port, allowed_file, generate_network_information_csv_file, read_network_information_file, connect_neighbours, create_nodes, initialize_benchmark


app = Flask(__name__)
number_nodes = 0
adjacency_matrix = []
node_ports = []
node_names = []


app.config["NETWORK_CSV_UPLOADS"] = os.getcwd() + r"\static\uploads\nodes"
app.config["ALLOWED_FILE_EXTENSION"] = ["CSV"]

# routes

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/setupNetworkTopology")
def setup_network_topology():
    return render_template('setup_network_topology.html')

@app.route("/setupNetworkTopologyRandom", methods=["GET", "POST"])
def setup_network_topology_random():
    if request.method == 'POST':
        req = request.form

        #filename = req.get("filename")
        number_nodes = req.get("number-nodes")
        network_topology = req.get("network-topology")

        if not number_nodes or not network_topology:
            return redirect(url_for("setup_network_topology"))

        generate_network_information_csv_file(number_nodes, network_topology)

        return redirect(url_for("upload_network_topology"))

    return render_template('setup_network_topology_random.html')

@app.route("/setupNetworkTopologyUpload")
@app.route("/uploadNetworkTopology", methods=["GET", "POST"])
def upload_network_topology():
    if request.method == "POST":
        if request.files:
            csv = request.files["csv"]

            if csv.filename == "":
                print("The CSV file must have a filename.")
                return redirect(request.url)

            if not allowed_file(csv.filename):
                print("That File Extension is not allowed.")
                return redirect(request.url)

            filename = secure_filename(csv.filename)
            file_path = os.path.join(app.config["NETWORK_CSV_UPLOADS"], filename)
            csv.save(file_path)

            number_nodes, adjacency_matrix = read_network_information_file(file_path)

            node_names, node_ports = create_nodes(number_nodes)

            connect_neighbours(node_ports, adjacency_matrix)
            #initialize_benchmark()
            print(done)
            os.remove(file_path)


    #@app.route("/")

    return render_template('upload_network_topology.html')


if __name__ == '__main__':
    app.run(debug=True)