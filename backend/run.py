#! /usr/bin/env python
from app import app, Config, Mqtt



if __name__ == "__main__":   
    # RUN FLASK APP
    app.run(host="0.0.0.0", port=8080, debug=False)
    
