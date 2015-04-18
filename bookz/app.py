from flask import Flask, request, render_template
import requests

app = Flask(__name__) #, template_folder='bookz/templates')

@app.route('/')
def login():
    return render_template('index.html', static_url_path='')

@app.route('/shutdown', methods=['POST'])
def shutdown():
	shutdown_server()
	return 'Server shutting down...'

def start_server():
    app.run(debug=True)

def shutdown_server():
	func = request.environ.get('werkzeug.server.shutdown')
	if func is None:
		raise RuntimeError('Not running with the Werkzeug Server??')
	func()

# TODO: get the server port and append it here...
def stop_server():
	try:
		requests.post(
			'http://127.0.0.1:5000/shutdown')
	except requests.exceptions.ConnectionError as e:
		print 'Not detecting a started server..'
