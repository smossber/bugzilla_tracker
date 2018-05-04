#!/usr/bin/env python
from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask.ext.jsonpify import jsonify
from werkzeug.contrib.cache import SimpleCache

import bugzilla
import sys
import datetime
import calendar
from time import strptime


app = Flask(__name__)
#app.cache = Cache(app,config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': '/tmp'})
cache = SimpleCache()
api = Api(app)

URL = "bugzilla.redhat.com"
bz = bugzilla.Bugzilla(URL,'')

try:
    reporters_file = r'reporters.txt'
    f = open(reporters_file,'r')
    reporters = f.read().splitlines()
except IOError:
    print "Could not open reporters.txt .."
    sys.exit(1)
f.close()
consultants = reporters


# Default is to show the current month
now = datetime.datetime.now()
year = now.year
month = now.month
first_day = 1
last_day = calendar.monthrange(year, month)[1]
date = str(year) + "-" + str(month) + "-" + str(first_day)
end_date = str(year) + "-" + str(month) + "-" + str(last_day)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

class Consultants(Resource):
    def get(self):
        #return {'consultants': [consultant for consultant in consultants]}
        return jsonify(consultants)

#class Bugs(Resource):
#    def get(self):
#        bug_list = {} 
#        for consultant in consultants:
#            # pick bug_id and summary from the bug object in the query
#            result = consultant_query_by_date(consultant, date, end_date)
#            bug_list[consultant] = {'bugs':[{'id': bug.id, 'topic': bug.summary} for bug in result], 'count': len(result)}
#        return bug_list


def consultant_query_by_date(alias, date, end_date):
    print(alias)
    print(date)
    print(end_date)
    query_url = ("https://bugzilla.redhat.com/buglist.cgi?email1={}&emailreporter1=1&emailtype1=substring&f1=creation_ts&f2=creation_ts&list_id=8596295&o1=greaterthaneq&o2=lessthaneq&query_format=advanced&v1={}&v2={}".format(alias,date, end_date))
    
    query = bz.url_to_query(query_url)
    bugs = bz.query(query)
    return bugs
    

api.add_resource(Consultants, '/consultants')
#api.add_resource(Bugs, '/bugs')


#@app.cache.memoize(timeout=50)
@app.route('/bugs')
def list_bugs_for_month(consultant = None):
    # If consultant is passed, override consultants list to only contain one
    if request.args.get('consultant'):
        print "got a consultant specified"
        print ""
        try: 
            consultant = request.args.get('consultant')
        except Exception:
            raise InvalidUsage("Invalid consultant", status_code=400)
    

    # convert the month into number    
    if request.args.get('month'):
        try:
            global month
            month = request.args.get('month')
            month = month[:3]
            month = strptime(month,'%b').tm_mon
        except:
            raise InvalidUsage("Not a valid month. Try the format jan, feb, mar, apr, jun, jul, aug, sep, oct, nov, dec", status_code=400)
    
    last_day = calendar.monthrange(year, month)[1]
    date = str(year) + "-" + str(month) + "-" + str(first_day)
    end_date = str(year) + "-" + str(month) + "-" + str(last_day)

    if consultant is not None: 
        cache_name = str(month) + consultant
    else:
        cache_name = str(month)
    
    print "Cache name %s" % cache_name
    bug_list = cache.get(cache_name)
    if bug_list is None: 
        bug_list = {} 
        if consultant is None:
            for consultant in consultants:
                result = consultant_query_by_date(consultant, date, end_date)
                bug_list[consultant] = {'bugs':[{'id': bug.id, 'topic': bug.summary} for bug in result], 'count': len(result)}
                cache.set(cache_name, bug_list, timeout= 5* 60)
        else:
                result = consultant_query_by_date(consultant, date, end_date)
                bug_list[consultant] = {'bugs':[{'id': bug.id, 'topic': bug.summary} for bug in result], 'count': len(result)}
                cache.set(cache_name, bug_list, timeout= 5* 60)

    return jsonify(bug_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5002)
