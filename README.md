# python-xray

A python 3 library witch helps in using chaitin's community xray web scanner. This tool convert command line into python functions. 

For example in xray if you want to scan for url `http://xxx.xx/` you would to something like this
```bash
./xray_linux_amd64 --config ./configs/config.yaml webscan url http://xxx.xx/
```

But in this python-xray script you would do something like this
```python
import pyxray
xray = pyxray.XrayWebScanner()
xray.webscan(urls=['http://xxx.xx/'])
```
