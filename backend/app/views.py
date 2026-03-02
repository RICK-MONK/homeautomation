"""
Flask Documentation:     https://flask.palletsprojects.com/
Jinja2 Documentation:    https://jinja.palletsprojects.com/
Werkzeug Documentation:  https://werkzeug.palletsprojects.com/
This file creates your application.
"""

# from crypt import methods
import site 

from app import app, Config,  mongo, Mqtt
from flask import escape, render_template, request, jsonify, send_file, redirect, make_response, send_from_directory 
from json import dumps, loads 
from werkzeug.utils import secure_filename
from datetime import datetime,timedelta, timezone
from os import getcwd
from os.path import join, exists
from time import time, ctime
from math import floor
 



#####################################
#   Routing for your application    #
#####################################


def is_valid_passcode(passcode):
    return isinstance(passcode, str) and passcode.isdigit() and len(passcode) == 4


@app.route('/api/set/combination', methods=['POST'])
def set_combination():
    try:
        passcode = request.form.get("passcode", "").strip()
        print(f"PASSCODE RECEIVED: {passcode}")

        if (not passcode.isdigit()) or len(passcode) != 4:
            return jsonify({"status":"failed","data":"failed"}), 400

        ok = mongo.set_passcode(passcode)
        if ok:
            return jsonify({"status":"complete","data":"complete"}), 200

        return jsonify({"status":"failed","data":"failed"}), 500
    except Exception as e:
        print(f"set_combination error: {e}")
        return jsonify({"status":"failed","data":"failed"}), 500


@app.route('/api/check/combination', methods=['POST'])
def check_combination():
    try:
        passcode = request.form.get("passcode", "").strip()
        if (not passcode.isdigit()) or len(passcode) != 4:
            return jsonify({"status":"failed","data":"failed"}), 400

        count = mongo.check_passcode(passcode)
        if count > 0:
            return jsonify({"status":"complete","data":"complete"}), 200
        return jsonify({"status":"failed","data":"failed"}), 200
    except Exception as e:
        print(f"check_combination error: {e}")
        return jsonify({"status":"failed","data":"failed"}), 500


@app.route('/api/update', methods=['POST'])
def update():
    try:
        payload = request.get_json(silent=True)
        required = {"id", "type", "radar", "waterheight", "reserve", "percentage"}
        if not isinstance(payload, dict) or not required.issubset(set(payload.keys())):
            return jsonify({"status":"failed","data":"failed"}), 400

        modified = dict(payload)
        modified["timestamp"] = int(time())
        payload_json = dumps(modified)

        # Arduino note: hardware_wamos.ino HOST_IP must be the backend machine LAN IP, not localhost.
        topic = "elet2415/radar"
        print(f"/api/update MQTT publish -> topic: {topic}, payload_size: {len(payload_json)} bytes")
        published = Mqtt.publish(topic, payload_json)
        inserted = mongo.insert_radar(modified)

        if published and inserted:
            return jsonify({"status":"complete","data":"complete"})
        return jsonify({"status":"failed","data":"failed"}), 500
    except Exception as e:
        print(f"/api/update error: {str(e)}")
        return jsonify({"status":"failed","data":"failed"}), 500


@app.route('/api/reserve/<start>/<end>', methods=['GET'])
def reserve(start, end):
    try:
        start_ts = int(start)
        end_ts = int(end)
        data = mongo.get_radar_range(start_ts, end_ts)
        if len(data) > 0:
            return jsonify({"status":"found","data": data})
        return jsonify({"status":"failed","data": 0})
    except Exception:
        return jsonify({"status":"failed","data": 0}), 500


@app.route('/api/avg/<start>/<end>', methods=['GET'])
def average(start, end):
    try:
        start_ts = int(start)
        end_ts = int(end)
        data = mongo.avg_reserve(start_ts, end_ts)
        if len(data) > 0 and "average" in data[0] and data[0]["average"] is not None:
            return jsonify({"status":"found","data": data[0]["average"]})
        return jsonify({"status":"failed","data": 0})
    except Exception:
        return jsonify({"status":"failed","data": 0}), 500






@app.route('/api/file/get/<filename>', methods=['GET']) 
def get_images(filename):   
    '''Returns requested file from uploads folder'''
   
    if request.method == "GET":
        directory   = join( getcwd(), Config.UPLOADS_FOLDER) 
        filePath    = join( getcwd(), Config.UPLOADS_FOLDER, filename) 

        # RETURN FILE IF IT EXISTS IN FOLDER
        if exists(filePath):        
            return send_from_directory(directory, filename)
        
        # FILE DOES NOT EXIST
        return jsonify({"status":"file not found"}), 404


@app.route('/api/file/upload',methods=["POST"])  
def upload():
    '''Saves a file to the uploads folder'''
    
    if request.method == "POST": 
        file     = request.files['file']
        filename = secure_filename(file.filename)
        file.save(join(getcwd(),Config.UPLOADS_FOLDER , filename))
        return jsonify({"status":"File upload successful", "filename":f"{filename}" })

 


###############################################################
# The functions below should be applicable to all Flask apps. #
###############################################################


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also tell the browser not to cache the rendered page. If we wanted
    to we could change max-age to 600 seconds which would be 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response

@app.errorhandler(405)
def page_not_found(error):
    """Custom 404 page."""    
    return jsonify({"status": 404}), 404



