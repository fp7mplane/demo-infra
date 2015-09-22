#!/usr/bin/python3

import psycopg2
import re

params = {
  'database': 'mplane',
  'user': 'admin',
  'password': 'secret',
  'host': '192.168.45.80',
  'port': 6453
}
tabname = "mplanetable"


class DinoDBConn:
    def __init__(self, params,tabname):
        self.conn = psycopg2.connect(**params)
        self.tabname = tabname
        self.attributes = self.get_table_description()

    def quit(self):
        self.conn.close()

    def query(self, query):
        cur = self.conn.cursor()
        cur.execute(query)
        res = cur.fetchall()
        cur.close()
        return res

    def get_table_description(self):
        res = self.query("describe {}".format(self.tabname))
        return [x[0] for x in res]

    def get_sessions_id(self, howmany=None):
        if not howmany:
             q = '''select distinct sid, probe_id, session_url, session_start from {}
                    order by session_start asc'''.format(self.tabname)
        else:
             q = '''select distinct sid, probe_id, session_url, session_start from {0} limit {1}
                    order by session_start asc'''.format(self.tabname, int(howmany))
        return self.query(q)

    def get_complete_session(self, dic): 
        session = Session(self.attributes)
        q = '''select * from {0} where sid = {1} and probe_id = {2} 
               and session_url = '{3}' and session_start = '{4}' '''\
               .format(self.tabname, dic['sid'], dic['probe_id'], dic['session_url'], dic['session_start'])
        all_ = self.query(q)
        for tup in all_:
            session.fill_attributes({k: v for k, v in zip(self.attributes, list(tup))})
        return session


class Session:
    def __init__(self, list_):
        self._check = set()  # for tracking inserted attributes
        self.attributes = list_
        self.ping = []
        self.trace = []
        self.location = {}
        self.secondary = []
        self.local_diagnosis = {}
        self.other = {}

    def fill_attributes(self, dic):
        ping_raw = {k:v for k,v in dic.items() if re.match('ping_', k) and v is not None}
        if ping_raw:
            self.ping.append(ping_raw)
            self._check |= set([k for k in ping_raw])   # union
        trace_raw = {k:v for k,v in dic.items() if re.match('trace', k) and v is not None}    # 'trace_endpoints' missing if no trace_enpoints
        if trace_raw:
            self.trace.append(trace_raw)
            self._check |= set([k for k in trace_raw])
        self.location = {k:v for k,v in dic.items() if re.match('location', k)}
        self._check |= set([k for k in self.location])
        secondary = {k:v for k,v in dic.items() if re.match('secondary', k) and v is not None}
        if secondary:
            self.secondary.append(secondary)
            self._check |= set([k for k in secondary])
        local_diag = {k:v for k,v in dic.items() if re.match('local_diag', k) and v is not None}  # 'local_diag_details' missing if no problem
        if not self.local_diagnosis:
            self.local_diagnosis = local_diag
            self._check |= set([k for k in local_diag])
        remaining = {k:v for k, v in dic.items() if k not in self._check}
        self.other = attrdict(remaining)

        
class attrdict(dict):
    def __getattr__(self, k):
        return self[k]

    def __setattr__(self, k, v):
        self[k] = v


class Extractor:
    def __init__(self, url):
        self.dinodb = DinoDBConn(params, tabname)
        self.url = url

    def extract(self, howmany=None):
        res = []
        id_ = ['sid', 'probe_id', 'session_url', 'session_start']
        sessions_id = self.dinodb.get_sessions_id(howmany)
        for id_session in sessions_id:
            dic = {k: v for k, v in zip(id_, list(id_session))}
            if re.search(self.url, dic['session_url']):
                session = self.dinodb.get_complete_session(dic)
                res.append(session)
        return res

    def close(self):
        self.dinodb.quit()
        
if __name__ == "__main__":
    e = Extractor('www.google.com')
    res = e.extract(howmany=1)
    e.close()
    print(res)

