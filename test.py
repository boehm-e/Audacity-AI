import json
import pyaudacity as pa

infos = pa.do("GetInfo: Type=Tracks Format=JSON")
print(infos)


