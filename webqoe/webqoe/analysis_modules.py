#!/usr/bin/python3

import numpy
import operator


def analyze_traces(traces):
    r = {}
    for trace in traces:
        for hop in trace:
            if hop['trace_ip_addr'] in r:
                r[hop['trace_ip_addr']]['hop_nr'].append(hop['trace_hop_nr'])
            else:
                r[hop['trace_ip_addr']] = {'rtt': [], 'hop_nr': [hop['trace_hop_nr']]}
            try:
                r[hop['trace_ip_addr']]['rtt'].append(hop['trace_rtt_avg'])
            except KeyError:
                r[hop['trace_ip_addr']]['rtt'].append(None)
    res = {}
    count = 0
    for k, v in r.items():
        if v['rtt'].count(None) == len(v['rtt']):
            count += len(v['rtt'])
            continue
        res[k] = {'hits': len(v['hop_nr']), 'hop_nr': list(set(v['hop_nr'])),
                  'stats': {'mean': numpy.around(numpy.mean(v['rtt']), decimals=4),
                            'std': numpy.around(numpy.std(v['rtt']), decimals=4),
                            'min': numpy.around(numpy.min(v['rtt']), decimals=4),
                            'max': numpy.around(numpy.max(v['rtt']), decimals=4)
                            }
                  }
        # res[k].update({'no_info': count})

    return res


def top_five_secondary(dic, traces):
    return sorted(dic.items(), key=operator.itemgetter(1), reverse=True)[:5]  # Top 5