from collections import namedtuple

from .diagnosis import DiagnosisManager
from .extract import Extractor

dbname = 'reasoner.db'


class Result:
    def __init__(self, sid, probe_id, session_url, session_start, diagnosis):
        self.sid = sid
        self.probe_id = probe_id
        self.session_url = session_url
        self.session_start = str(session_start)
        self.diagnosis = diagnosis


class Reasoner:
    
    def __init__(self):
        self.sessions_list = []
        self.dm = None

    def extract_data_for_url(self, url):
        e = Extractor(url)
        self.sessions_list = e.extract()

    def build_from_old(self, already):
        res = []
        for tup in already:
            sid = tup[0]
            url = tup[1]
            session_start = tup[2]
            probe_id = tup[3]
            diag = tup[4]
            res.append(Result(sid, probe_id, url, session_start, diag).__dict__)
        return res

    @staticmethod
    def _process_passive(dic):
        passive = namedtuple('passive', ['probe_id', 'sid', 'server_ip', 'session_start', 'full_load_time', 'page_dim',
                                         'mem_percent', 'cpu_percent'])
        passive.sid = dic['sid']
        passive.probe_id = dic['probe_id']
        passive.server_ip = dic['server_ip']
        passive.session_start = dic['session_start']
        passive.full_load_time = dic['full_load_time']
        passive.page_dim = dic['page_dim']
        passive.mem_percent = dic['mem_percent']
        passive.cpu_percent = dic['cpu_percent']
        return passive

    def gather_measurements(self):
        measurements = []
        for session in self.sessions_list:
            # ['secondary', 'local_diagnosis', 'ping', '_check', 'trace', 'attributes', 'location', 'other']
            metric = namedtuple('metrics', ['passive', 'ping', 'trace', 'secondary'])
            metric.passive = Reasoner._process_passive(session.other)
            metric.secondary = session.secondary
            metric.ping = session.ping
            metric.trace = session.trace
            measurements.append(metric)
        return measurements

    def filterout_diagnosed(self, requestingprobe, measurements, already_diagnosed):
        filtered = []
        for m in measurements:
            if m.passive.probe_id != requestingprobe:
                continue
            for tup in already_diagnosed:
                # tup = (sid, url, when_browsed, probe_id, diagnosis)
                if m.passive.sid == tup[0] and str(m.passive.session_start) == tup[2]:
                    break
            else:
                filtered.append(m)
        return filtered

    def diagnose(self, probe_id, url, globaldiag=False):
        self.dm = DiagnosisManager(url)
        already_diagnosed = self.dm.get_diagnosed_sessions(probe_id)
        self.extract_data_for_url(url)
        measurements = self.gather_measurements()  # all the measurements for a single url

        result = []

        filtered = self.filterout_diagnosed(probe_id, measurements, already_diagnosed)
        if not globaldiag:
            if not filtered:
                print("no new sessions to diagnose")
                result = self.build_from_old(already_diagnosed)
            else:
                for m in filtered:
                    diag = self.dm.run_diagnosis(probe_id, m)
                    result.append(Result(m.passive.sid, probe_id, url, m.passive.session_start, diag).__dict__)
        else:
            result = self.global_diagnose(url, measurements)
        return result

    def global_diagnose(self, url, measurements):
        diag = self.dm.global_diagnosis(measurements)
        return diag



if __name__ == "__main__":
    url = 'www.google.com'
    probe = 1190855395
    r = Reasoner()
    res = r.diagnose(probe, url, globaldiag=True)
    #print(res)
