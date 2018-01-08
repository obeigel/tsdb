# tsdb
TSDB is a simple time series DB, allowing to store pairs of metrics with its numeric values

The code is the copy from
https://github.com/gar1t/tsdb
- based on http://luca.ntop.org/tsdb.pdf

I have added tsdb-tool.c that enables operation of the DB.
tsdb.py provides external API and meta data storage in Mongo DB.

4 modes to operate with a script: 
1. run as a daemon and collect system metrics (like memory usage, CPU usage, networking stats, disk usage stats, load average),
Mongo DB counts/stats. Any other DB stats can be added to the script, as additional systme and other metrics / stats data.

2. Read single value based on metric name and the timestamp. Metrics with start and end measurement timestamps are stored in Mongo DB collection.

3. Range query for the metric - list all the measurements recorded in TSDB.

4. List of metrics, fetched from Mongo DB

I have written a web app that shows a chart graph for certain metric. This app resides on other github repo - take a look for a demo.

