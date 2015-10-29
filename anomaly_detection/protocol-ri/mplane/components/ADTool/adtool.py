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
    cap.add_parameter("database.password")
    cap.add_parameter("database.features_table")
    cap.add_parameter("database.flags_table")
    cap.add_parameter("mPlane.supervisor")
    cap.add_parameter("analysis.start")
    cap.add_parameter("analysis.end")
    cap.add_parameter("analysis.granularity")
    cap.add_parameter("analysis.variable")
    cap.add_parameter("analysis.feature")
    cap.add_parameter("refset.width")
    cap.add_parameter("refset.guard")
    cap.add_parameter("refset.min_distr_size")
    cap.add_parameter("refset.min_refset_size")
    cap.add_parameter("refset.slack_var")
    cap.add_parameter("refset.m")
    cap.add_parameter("refset.k")
    
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
            process.kill()
            #for child in parent.children(recursive=True):
            #    child.kill()
            parent.kill()

        return
    
    def generateXML(self,dt,spec):
        dbhost=dbport=dbname=dbuser=dbpass=dbfeat=dbflags=msv = None
        anastart=anaend=anagran=anavar=anafeat = None
        refwidth=refguard=refmds=refmrs=refslvar=refm=refk = None
        print(">>generateXML<<   ts: " + dt)
        outfile = dt + ".xml"
        
        
        for el in spec.parameter_names():
            print("params: " + el)
            val = str(spec.get_parameter_value(el))
            if el == "database.host":
                dbhost = val
            elif el == "database.port":
                dbport = val
            elif el == "database.dbname":
                dbname = val
            elif el == "database.user":
                dbuser = val
            elif el == "database.password":
                dbpass = val
            elif el == "database.features_table":
                dbfeat = val
            elif el == "database.flags_table":
                dbflags = val
            elif el == "mPlane.supervisor":
                msv = "http://" + val
            elif el == "analysis.start":
                anastart = val
            elif el == "analysis.end":
                anaend = val
            elif el == "analysis.granularity":
                anagran = val
            elif el == "analysis.variable":
                anavar = val
            elif el == "analysis.feature":
                anafeat = val
            elif el == "refset.width":
                refwidth = val
            elif el == "refset.guard":
                refguard = val
            elif el == "refset.min_distr_size":
                refmds = val
            elif el == "refset.min_refset_size":
                refmrs = val
            elif el == "refset.slack_var":
                refslvar = val
            elif el == "refset.m":
                refm = val
            elif el == "refset.k":
                refk = val
                
        tree = ET.ElementTree(file=self.ad_path)
        for elem in tree.iter():
            print(elem.tag, elem.attrib,elem.text)
            if( "Description"== elem.tag):
    	        elem.text = "ADTool xml generator"
            elif( "Database"== elem.tag):
    	        elem.set("host",dbhost)
    	        elem.set("port",dbport)
    	        elem.set("dbname",dbname)
    	        elem.set("user",dbuser)
    	        elem.set("password",dbpass)
            elif("features_table" == elem.tag):
                elem.text = dbfeat
            elif("supervisor" == elem.tag):
                elem.text = msv
            elif("flags_table" == elem.tag):
                elem.text = dbflags
            elif("start" == elem.tag):
                elem.text = anastart
            elif("end" == elem.tag):
                elem.text = anaend
            elif("granularity" == elem.tag):
                elem.text = anagran
            elif("variable" == elem.tag):
                elem.text = anavar
            elif("feature" == elem.tag):
                elem.text = anafeat
            elif("width" == elem.tag):
                elem.text = refwidth
            elif("guard" == elem.tag):
                elem.text = refguard
            elif("min_distr_size" == elem.tag):
                elem.text = refmds
            elif("min_refset_size" == elem.tag):
                elem.text = refmrs
            elif("slack_var" == elem.tag):
                elem.text = refslvar
            elif("m" == elem.tag):
                elem.text = refm
            elif("k" == elem.tag):
                elem.text = refk
    	        
        outFile = open(outfile, 'wb')
        print(">>>>>>>>>>>>>>>>>>>>>>>>>generateXML<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        #tree.write(sys.stdout,encoding="unicode")
        tree.write(outFile)
       

    def run(self, spec, check_interrupt):
        """
        Execute this Service

        """
        (start_time , end_time) = spec._when.datetimes()
        duration = spec.when().duration().total_seconds()
        dt = datetime.utcnow()
        ddt = str(dt.timestamp())
        print("Current ts: " + ddt)
        outfile = ddt + ".xml"

        

        process = None
        # check which capability family 
        if "adtool-log" in spec.get_label():
            # start measurement changing the tstat conf file
            #self.change_conf(spec.get_label(), True)
            print("HOHOHHOHOHOHHOHO")
            self.generateXML(ddt,spec)
            shell_command = './mplane/components/ADTool/ADTool_files/adtool_dummy.pl  --config=' + outfile
            print ("Command : %s" %shell_command)
            process = subprocess.Popen(shell_command, stdout=subprocess.PIPE, shell=True)
            

        
       
        else:
            raise ValueError("Capability family doesn't exist")

        self.wait_and_stop(end_time, check_interrupt, spec, process)

        # wait for specification execution
        if "adtool-log" in spec.get_label():
            # terminate adtool measurement
            print("adtool_log Disabled \n")
        

        res = self.fill_res(spec, start_time, end_time)

        return res



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
