# mPlane Protocol Reference Implementation
# tStat component code
#
# (c) 2015 mPlane Consortium (http://www.ict-mplane.eu)
#               Author: Goran Lazendic
#               
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.


from datetime import *
from time import sleep
import os
import configparser
import mplane.model
import mplane.scheduler
import mplane.utils
from multiprocessing import Process
import psutil
import sys
import xml.etree.cElementTree as ET
import subprocess
from mplane.components.tstat.tstat_exporters import tstat_rrd_exporter
from mplane.components.tstat.tstat_exporters import tstat_streaming_exporter


"""
Implements ADTool capabilities and services

"""

def services(config_path):
    services = []
    print("adpath " + config_path)
    if config_path is not None:
        
        services.append(adToolService(adtool_capability(), adtool_path=config_path))
    else:
        raise ValueError("missing 'ad_path' parameter for adTool capabilities")
    return services

def adtool_capability():
    cap = mplane.model.Capability(label="adtool-log_tcp_complete", when = "now ... future")
    cap.add_metadata("System_type", "ADTool")
    cap.add_metadata("System_ID", "ADTool-Proxy")
    cap.add_metadata("System_version", "0.1")
    cap.add_parameter("database.host")
    cap.add_parameter("database.port")
    cap.add_parameter("database.dbname")
    cap.add_parameter("database.user")
    
    return cap




class adToolService(mplane.scheduler.Service):
    """
    This class handles the capabilities exposed by the proxy:
    executes them, and fills the results

    """

    def __init__(self, cap, adtool_path = None):
        super(adToolService, self).__init__(cap)
        print("adtool path  " + adtool_path)
        self.ad_path = adtool_path
        #self.generateXML(cap)

    def wait_and_stop(self, end_time, check_interrupt, spec, process):
        while (datetime.utcnow() <= end_time):
            if check_interrupt():
                break
            sleep(0.5)
        if process is not None:
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()

        return
    
    def generateXML(self,spec):
        for el in spec.parameter_names():
            print("params: " + el)
        tree = ET.ElementTree(file=self.ad_path)
        for elem in tree.iter():
            print(elem.tag, elem.attrib,elem.text)
            if( "Description"== elem.tag):
    	        elem.text = "TEST GORANNNNNN"
        #outFile = open('output.xml', 'wb')
        tree.write(sys.stdout,encoding="unicode")
       

    def run(self, spec, check_interrupt):
        """
        Execute this Service

        """
        (start_time , end_time) = spec._when.datetimes()
        duration = spec.when().duration().total_seconds()

        # crate the math code time format
        time_format = start_time.strftime("%Y-%m-%dT%H:%M:%S")

        process = None
        # check which capability family 
        if "adtool-log" in spec.get_label():
            # start measurement changing the tstat conf file
            #self.change_conf(spec.get_label(), True)
            print("HOHOHHOHOHOHHOHO")
            self.generateXML(spec)

        elif "tstat-exporter_log" in spec.get_label():
            #The math executable for export log
            repository_url = str(spec.get_parameter_value("repository.url"))
            curr_dir = os.getcwd()
            os.chdir(self.math_path)
            shell_command = 'exec ./math_probe --config math_probe.xml --repoUrl %s --startTime %s' % (repository_url,time_format)
            print ("Command : %s" %shell_command)
            process = subprocess.Popen(shell_command, stdout=subprocess.PIPE, shell=True)#, preexec_fn=os.setsid)
            os.chdir(curr_dir)
       
        else:
            raise ValueError("Capability family doesn't exist")

        self.wait_and_stop(end_time, check_interrupt, spec, process)

        # wait for specification execution
        if "tstat-log" in spec.get_label():
            # terminate measurement changing the tstat conf file
            self.change_conf(spec.get_label(), False)
        elif "tstat-exporter_streaming" in spec.get_label() :
            print("tstat-exporter_streaming Disabled \n")
        elif "tstat-exporter_rrd" in spec.get_label() :
            print("tstat-exporter_rrd Disabled \n")
        elif "tstat-exporter_log" in spec.get_label() :
            print("tstat-exporter_log Disabled \n")

        res = self.fill_res(spec, start_time, end_time)

        return res

    def change_conf(self, cap_label, enable):
        """
        Changes the needed flags in the tStat runtime.conf file

        """
        print("I am in change_conf routine " + self._fileconf)
        newlines = []
        f = open(self._fileconf, 'r')
        
        for line in f:
            #print("Line:: " + str(line))	
            # read parameter names and values (discard comments or empty lines)
            if (line[0] != '[' and line[0] != '#' and
                line[0] != '\n' and line[0] != ' '):    
                param = line.split('#')[0]
                param_name = param.split(' = ')[0]
                
                #print("Line::: " + line)
                # change flags according to the measurement requested
                if enable == True:

                    # in order to activate optional sets, the basic set (log_tcp_complete) must be active too
                    # print("Param name: " + param_name + "Cap label:  " + cap_label)
                    if ("tstat-log_tcp_complete-core" in cap_label and param_name == 'log_tcp_complete'):
                        newlines.append(line.replace('0', '1'))
                        print(str(newlines))

                    elif ("tstat-log_tcp_complete-end_to_end" in cap_label and (
                        param_name == 'tcplog_end_to_end' 
                        or param_name == 'log_tcp_complete')):
                        newlines.append(line.replace('0', '1'))

                    elif ("tstat-log_tcp_complete-tcp_options" in cap_label and (
                        param_name == 'tcplog_options' or
                        param_name == 'log_tcp_complete')):
                        newlines.append(line.replace('0', '1'))

                    elif ("tstat-log_tcp_complete-p2p_stats" in cap_label and (
                        param_name == 'tcplog_p2p' or
                        param_name == 'log_tcp_complete')):
                        newlines.append(line.replace('0', '1'))

                    elif ("tstat-log_tcp_complete-layer7" in cap_label and (
                        param_name == 'tcplog_layer7' or
                        param_name == 'log_tcp_complete')):
                        newlines.append(line.replace('0', '1'))

                    elif ("tstat-log_rrds" in cap_label and 
                        param_name == 'rrd_engine'):
                        newlines.append(line.replace('0', '1'))

                    elif ("tstat-log_http_complete" in cap_label and param_name == 'log_http_complete'):
                        newlines.append(line.replace('0', '1'))

                    else:
                        newlines.append(line)
                else:
                    # print("enable is false Param name: " + param_name)
                    if ("tstat-log_tcp_complete-end_to_end" in cap_label and param_name == 'tcplog_end_to_end'):
                        newlines.append(line.replace('1', '0'))

                    elif ("tstat-log_tcp_complete-tcp_options" in cap_label and param_name == 'tcplog_options'):
                        newlines.append(line.replace('1', '0'))

                    elif ("tstat-log_tcp_complete-p2p_stats" in cap_label and param_name == 'tcplog_p2p'):
                        newlines.append(line.replace('1', '0'))

                    elif ("tstat-log_tcp_complete-layer7" in cap_label and param_name == 'tcplog_layer7'):
                        newlines.append(line.replace('1', '0'))

                    elif ("tstat-log_rrds" in cap_label and param_name == 'rrd_engine'):
                        newlines.append(line.replace('1', '0'))

                    elif ("tstat-log_http_complete" in cap_label and param_name == 'log_http_complete'):
                        newlines.append(line.replace('1', '0'))

                    else:
                        newlines.append(line) 
            else:
                newlines.append(line)
        f.close()

        f = open(self._fileconf, 'w')
        #print("writing!!!!!! ::::  " + str(newlines))
        f.writelines(newlines)
        f.close

    def fill_res(self, spec, start, end):
        """
        Create a Result statement, fill it and return it

        """

        # derive a result from the specification
        res = mplane.model.Result(specification=spec)

        # put actual start and end time into result
        res.set_when(mplane.model.When(a = start, b = end))

        # fill result columns with DUMMY values
        for column_name in res.result_column_names():
            prim = res._resultcolumns[column_name].primitive_name()
            if prim == "natural":
                res.set_result_value(column_name, 0)
            elif prim == "string":
                res.set_result_value(column_name, "hello")
            elif prim == "real":
                res.set_result_value(column_name, 0.0)
            elif prim == "boolean":
                res.set_result_value(column_name, True)
            elif prim == "time":
                res.set_result_value(column_name, start)
            elif prim == "address":
                res.set_result_value(column_name, "192.168.0.1")
            elif prim == "url":
                res.set_result_value(column_name, "www.google.com")
        return res
