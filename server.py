#!/usr/bin/env python
from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask.ext.jsonpify import jsonify

import bugzilla
import sys
import datetime

app = Flask(__name__)
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
day = 1

date = str(year) + "-" + str(month) + "-" + str(day)
end_date = str(year) + "-" + str(month+1) + "-" + str(day)


class Consultants(Resource):
    def get(self):
        #return {'consultants': [consultant for consultant in consultants]}
        return jsonify(consultants)

class Bugs(Resource):
    def get(self):
        bug_list = {} 
        for consultant in consultants:
            # pick bug_id and summary from the bug object in the query
            result = consultant_query_by_date(consultant, date, end_date)
            bug_list[consultant] = {'bugs':[{'id': bug.id, 'topic': bug.summary} for bug in result], 'count': len(result)}
        return bug_list


def consultant_query_by_date(alias, date, end_date):
    print(alias)
    print(date)
    print(end_date)
    
    query_url = ("https://bugzilla.redhat.com/buglist.cgi?email1={}&emailreporter1=1&emailtype1=substring&f1=creation_ts&f2=creation_ts&list_id=8596295&o1=greaterthan&o2=lessthan&query_format=advanced&v1={}&v2={}".format(alias,date, end_date))
    
    query = bz.url_to_query(query_url)
    bugs = bz.query(query)
    return bugs
    

api.add_resource(Consultants, '/consultants')
api.add_resource(Bugs, '/bugs')
@app.route('/bugs/<consultant>')
def list_bugs_for_consultant(consultant):
        bug_list = {} 
        result = consultant_query_by_date(consultant, date, end_date)
        print(result)
        bug_list[consultant] = {'bugs':[{'id': bug.id, 'topic': bug.summary} for bug in result], 'count': len(result)}
        return jsonify(bug_list[consultant])


if __name__ == '__main__':
    app.run(port=5002)
