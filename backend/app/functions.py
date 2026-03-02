 #!/usr/bin/python3


#################################################################################################################################################
#                                                    CLASSES CONTAINING ALL THE APP FUNCTIONS                                                                                                    #
#################################################################################################################################################


class DB:

    def __init__(self,Config):

        from math import floor
        from os import getcwd
        from os.path import join
        from json import loads, dumps, dump
        from datetime import timedelta, datetime, timezone 
        from pymongo import MongoClient , errors, ReturnDocument
        from urllib import parse
        from urllib.request import  urlopen 
        from bson.objectid import ObjectId  
       
      
        self.Config                         = Config
        self.getcwd                         = getcwd
        self.join                           = join 
        self.floor                      	= floor 
        self.loads                      	= loads
        self.dumps                      	= dumps
        self.dump                       	= dump  
        self.datetime                       = datetime
        self.ObjectId                       = ObjectId 
        self.server			                = Config.DB_SERVER or "localhost"
        try:
            self.port                       = int(Config.DB_PORT) if Config.DB_PORT is not None else 27017
        except (TypeError, ValueError):
            self.port                       = 27017
        self.username                   	= parse.quote_plus(str(Config.DB_USERNAME or ""))
        self.password                   	= parse.quote_plus(str(Config.DB_PASSWORD or ""))
        self.remoteMongo                	= MongoClient
        self.ReturnDocument                 = ReturnDocument
        self.PyMongoError               	= errors.PyMongoError
        self.BulkWriteError             	= errors.BulkWriteError  
        self.tls                            = False # MUST SET TO TRUE IN PRODUCTION
        self.client                         = self.remoteMongo(self._mongo_uri(), tls=self.tls, serverSelectionTimeoutMS=5000)
        self.db                             = self.client["ELET2415"]


    def __del__(self):
            # Delete class instance to free resources
            if hasattr(self, "client") and self.client:
                self.client.close()
 


    ####################
    # LAB 4 FUNCTIONS  #
    ####################
    
    # 1. CREATE FUNCTION TO INSERT DATA IN TO THE RADAR COLLECTION
    def _mongo_uri(self):
        # Supports explicit URI and authenticated/unauthenticated host+port configs.
        if getattr(self.Config, "MONGO_URI", None):
            return self.Config.MONGO_URI
        if self.Config.DB_USERNAME and self.Config.DB_PASSWORD:
            return f"mongodb://{self.username}:{self.password}@{self.server}:{self.port}/?authSource=admin"
        return f"mongodb://{self.server}:{self.port}/"

    def _collection(self, collection_name):
        client = self.remoteMongo(self._mongo_uri(), tls=self.tls, serverSelectionTimeoutMS=5000)
        db = client["ELET2415"]
        return client, db[collection_name]

    def insert_radar(self, data):
        client = None
        try:
            client, radar = self._collection("radar")
            result = radar.insert_one(data)
            return result.inserted_id is not None
        except self.PyMongoError:
            return False
        finally:
            if client:
                client.close()

    
    # 2. CREATE FUNCTION TO RETRIEVE ALL DOCUMENTS FROM RADAR COLLECT BETWEEN SPECIFIED DATE RANGE. MUST RETURN A LIST OF DOCUMENTS
    def get_radar_range(self, start, end):
        client = None
        try:
            client, radar = self._collection("radar")
            query = {"timestamp": {"$gte": start, "$lte": end}}
            return list(radar.find(query, {"_id": 0}))
        except self.PyMongoError:
            return []
        finally:
            if client:
                client.close()


    # 3. CREATE A FUNCTION TO COMPUTE THE ARITHMETIC AVERAGE ON THE 'reserve' FEILED/VARIABLE, USING ALL DOCUMENTS FOUND BETWEEN SPECIFIED START AND END TIMESTAMPS. RETURNS A LIST WITH A SINGLE OBJECT INSIDE
    def avg_reserve(self, start, end):
        client = None
        try:
            client, radar = self._collection("radar")
            pipeline = [
                {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
                {"$group": {"_id": None, "average": {"$avg": "$reserve"}}},
                {"$project": {"_id": 0, "average": 1}}
            ]
            return list(radar.aggregate(pipeline))
        except self.PyMongoError:
            return []
        finally:
            if client:
                client.close()
    
    
    # 4. CREATE A FUNCTION THAT INSERT/UPDATE A SINGLE DOCUMENT IN THE 'code' COLLECTION WITH THE PROVIDED PASSCODE
    def set_passcode(self, passcode):
        client = None
        try:
            client, code = self._collection("code")
            updated = code.find_one_and_update(
                {"type": "passcode"},
                {"$set": {"type": "passcode", "code": passcode}},
                upsert=True,
                return_document=self.ReturnDocument.AFTER
            )
            return updated is not None
        except self.PyMongoError:
            return False
        finally:
            if client:
                client.close()
   
    
    # 5. CREATE A FUNCTION THAT RETURNS A COUNT, OF THE NUMBER OF DOCUMENTS FOUND IN THE 'code' COLLECTION WHERE THE 'code' FEILD EQUALS TO THE PROVIDED PASSCODE.
    #    REMEMBER, THE SCHEMA FOR THE SINGLE DOCUMENT IN THE 'code' COLLECTION IS {"type":"passcode","code":"0070"}
    def check_passcode(self, passcode):
        client = None
        try:
            client, code = self._collection("code")
            return code.count_documents({"type": "passcode", "code": passcode})
        except self.PyMongoError:
            return 0
        finally:
            if client:
                client.close()

    # Backward-compatible aliases
    def get_radar_between(self, start, end):
        return self.get_radar_range(start, end)

    def get_average_reserve_between(self, start, end):
        return self.avg_reserve(start, end)

    def upsert_passcode(self, passcode):
        return self.set_passcode(passcode)

    def count_matching_passcode(self, passcode):
        return self.check_passcode(passcode)


   



def main():
    from config import Config
    from time import time, ctime, sleep
    from math import floor
    from datetime import datetime, timedelta
    one = DB(Config)
 
 
    start = time() 
    end = time()
    print(f"completed in: {end - start} seconds")
    
if __name__ == '__main__':
    main()


    
