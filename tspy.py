from pymongo import MongoClient
import subprocess
from datetime import datetime  
import time
import os
import argparse

class TSDB_CLIENT(object):
    def __init__(self, dbname, interval, mode):
        self.tsdbname = dbname
        self.interval = interval
        self.dbclient = MongoClient('localhost', 27017)
        self.filename = "metrics.txt"
        self.mode = mode
        self.tsdb_collection = self.dbclient.tsdb_meta

        if mode == 1:
            data = self.get_metrics_data()    
            now = int(time.time())
            tsdb_meta_obj = {
                'interval': interval,
                'start': now,
                'end': now,
                'pid': os.getppid(),
                'metrics': data.keys(),
            }
            self.tsdb_collection.tsdb_meta.insert(tsdb_meta_obj)

    def get_metrics(self):
        for doc in self.tsdb_collection.tsdb_meta.find():    
            metrics = []
            for metric in doc["metrics"]:
                ma = metric.encode('ascii')
                metrics.append(ma)
            print(metrics)
            break

    def tsdb_write_metrics(self, timestamp, nummetrics):
        cmd = "./home/oleg/projects/tsdb_project/tsdb_src/tsdb-tool -s " + str(self.interval) +" -f " + self.tsdbname + " -t " + str(timestamp) + " -N " + str(nummetrics) + " " + self.filename
        print(subprocess.check_output(cmd, shell=True))

    def tsdb_read_metric_range(self, metric, ts_start, ts_end):
        cmd = "/home/oleg/projects/tsdb_project/tsdb_src/tsdb-tool -s " + str(self.interval) +" -f " + self.tsdbname + " -R " + metric + " " + str(ts_start) + " " + str(ts_end)
        res = subprocess.check_output(cmd, shell=True)
        tsdata = []
        for r in res.split('\n'):
            if (r == ''):
                break
            ts, val = r.split(',')
            tsdata.append({int(ts):int(val)})
        return tsdata

    def tsdb_read_metric_single(self, metric, timestamp) :
        cmd = "./tsdb-tool -s " + str(self.interval) +" -f " + self.tsdbname + " -t " + str(timestamp) + " -g " + metric
        print(subprocess.check_output(cmd, shell=True))

    def get_metrics_data(self):
        data = {}
        # Get System data
        data["memtotal"] = subprocess.check_output("cat /proc/meminfo | grep MemTotal", shell=True).split()[1]
        data["memfree"] = subprocess.check_output('cat /proc/meminfo | grep MemFree', shell=True).split()[1]
        data["swaptotal"] = subprocess.check_output('cat /proc/meminfo | grep SwapTotal', shell=True).split()[1]
        data["swapfree"] = subprocess.check_output('cat /proc/meminfo | grep SwapFree', shell=True).split()[1]
        data["loadavg"] = str(int(float(subprocess.check_output('cat /proc/loadavg', shell=True).split()[0])*100))
        Sar = subprocess.check_output('sar -n DEV 1 1 | grep -i enp1s0 | tail -n1', shell=True)
        data["sarrx"] = str(int(float(Sar.split()[6])*100))
        data["sartx"] = str(int(float(Sar.split()[6])*100))
        df = subprocess.check_output('df -h | grep /dev/sda1', shell=True)
        data["dfoccupied"] = df.split()[2][:-1]
        data["dffree"] = df.split()[3][:-1]
        data["dffoccuppercent"] = df.split()[4][:-1]

        # Get data from the DB
        data["companies_count"] = str(self.dbclient.companies.companies.count())
        data["sales_count"] = str(self.dbclient.zillow_scraps.sales.count())
        data["rentals_count"] = str(self.dbclient.zillow_scraps.rentals.count())
        data["zestimate_count"] = str(self.dbclient.zillow_scraps.zestimate.count())
        return data

    def create_data_file(self, ts):
        data = self.get_metrics_data()
        f = open(self.filename, "w") 
        print(ts)
        for key,val in data.items():
            f.write(key+"="+val+"\n")
        f.close()
        return len(data)

    def read_value(self, metric, ts):
        self.tsdb_read_metric_single(metric, ts)
    
    def read_range_values(self, metric):
        tsdata = []
        for doc in self.tsdb_collection.tsdb_meta.find():
            tsdata += self.tsdb_read_metric_range(metric, doc["start"], doc["end"])
        #range_obj = {str(metric): tsdata}
        print(tsdata)

    def run_daemon(self):
        while True:
            ts = int(time.time())
            print(ts)
            datalen = self.create_data_file(ts)
            self.tsdb_write_metrics(ts, datalen)
            pid = os.getppid()
            self.tsdb_collection.tsdb_meta.update(
                {'pid': pid}, 
                {
                    '$set': {
                        'end': ts
                    }
                }, upsert=False)
            time.sleep(self.interval)
        
if __name__=="__main__":
    argparser = argparse.ArgumentParser()
    mode_help = """
        Modes :
        1: Daemon mode,
        2: Read signle value,
        3: Read range value,
        4: Get metrics
    """
    argparser.add_argument('TSDB', default ='RUNTSDB', nargs='?', )
    argparser.add_argument('Interval', type=int)
    argparser.add_argument('Mode', type=int, help = mode_help)
    argparser.add_argument('Metric', nargs='?')
    argparser.add_argument('Timestamp', type=int, nargs='?')

    args = argparser.parse_args()
    #print(args)
    tsdb_client = TSDB_CLIENT(args.TSDB, args.Interval, args.Mode)
    if args.Mode == 1:
        tsdb_client.run_daemon()
    elif args.Mode == 2:
        tsdb_client.read_value(args.Metric, args.Timestamp)
    elif args.Mode == 3:
        tsdb_client.read_range_values(args.Metric)
    elif args.Mode == 4:
        tsdb_client.get_metrics()