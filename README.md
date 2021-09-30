# siglent_bin2csv
Utility to dump waveform traces from Siglent SDS2000X+ scope over LAN/VISA connection to python numpy array

Based off vendor provided code with improved speed.
Dump a single trace with 200 megasamples over 100Mbit ethernet in 50 seconds.

Usage:
Capture the trace on the scope. Stop the trigger.

Run the following script to dump the trace:

```python
from siglent_bin2csv import siglent_bin2csv
import pyvisa as visa
import matplotlib.pyplot as plt
import pandas as pd

SDS_RSC = "TCPIP0::192.168.1.39::inst0::INSTR"
sds = visa.ResourceManager().open_resource(SDS_RSC)

bin2csv = siglent_bin2csv(sds)
time, voltage = bin2csv.get_trace(1)

df = pd.DataFrame({'time':time, 'voltage':voltage})
df.to_csv("trace.csv")
plt.plot(time, voltage)
```
