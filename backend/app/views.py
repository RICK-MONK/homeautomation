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
        if not isinstance(payload, dict):
            raw_body = request.get_data(as_text=True).strip()
            if raw_body:
                try:
                    payload = loads(raw_body)
                except Exception:
                    print(f"/api/update invalid JSON body: {raw_body}")
            else:
                print("/api/update empty body")

        required = {"id", "type", "radar", "waterheight", "reserve", "percentage"}
        if not isinstance(payload, dict):
            return jsonify({"status":"failed","data":"invalid_json"}), 400

        missing = sorted(list(required.difference(set(payload.keys()))))
        if missing:
            print(f"/api/update missing keys: {missing}; payload={payload}")
            return jsonify({"status":"failed","data":"missing_keys","missing":missing}), 400

        modified = dict(payload)
        modified["timestamp"] = int(time())
        payload_json = dumps(modified)

        inserted = mongo.insert_radar(modified)
        print(f"RADAR INSERT: {inserted}")
        if not inserted:
            return jsonify({"status":"failed","data":"failed"}), 500

        # MQTT is best-effort; API succeeds when DB insert succeeds.
        topic = "elet2415/radar"
        try:
            print(f"/api/update MQTT publish -> topic: {topic}, payload_size: {len(payload_json)} bytes")
            published = Mqtt.publish(topic, payload_json)
            print(f"/api/update MQTT publish result: {published}")
        except Exception as e:
            print(f"MQTT publish failed (ignored): {e}")

        return jsonify({"status":"complete","data":"complete"})
    except Exception as e:
        print(f"/api/update error: {str(e)}")
        return jsonify({"status":"failed","data":"failed"}), 500


@app.route('/api/reserve/<start>/<end>', methods=['GET'])
def reserve(start, end):
    try:
        # URL params arrive as strings; normalize to integer epoch seconds.
        start_ts = int(float(start))
        end_ts = int(float(end))
        docs = mongo.get_radar_range(start_ts, end_ts)
        return jsonify({"status":"found","data": docs}), 200
    except Exception as e:
        print(f"/api/reserve error: {e}")
        return jsonify({"status":"failed","data": 0}), 500


@app.route('/api/avg/<start>/<end>', methods=['GET'])
def average(start, end):
    try:
        # URL params arrive as strings; normalize to integer epoch seconds.
        start_ts = int(float(start))
        end_ts = int(float(end))
        avg_list = mongo.avg_reserve(start_ts, end_ts)
        avg = 0
        if isinstance(avg_list, list) and len(avg_list) > 0:
            avg = avg_list[0].get("average", 0) or 0
        return jsonify({"status":"found","data": float(avg)}), 200
    except Exception as e:
        print(f"/api/avg error: {e}")
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



