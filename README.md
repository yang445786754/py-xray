# python-xray

A python 3 library which helps in using chaitin's community xray web scanner. This tool convert command line into python functions. 

For example in xray if you want to scan for url `http://xxx.xx/` you would to something like this
```bash
./xray_linux_amd64 --config ./configs/config.yaml webscan url http://xxx.xx/
```

But in this python-xray script you would do something like this
```python
import pyxray

# xray = pyxray.XrayWebScanner(['/path/to/your/xray-software-dir/xray_linux_amd64'])
xray = pyxray.XrayWebScanner()  # default: find it from your PATH
res = xray.webscan(urls=['http://xxx.xx/'])
res = xray.webscan_with_crawler(urls=['http://xxx.xx/'])

print(res)
```
> NOTE: xray_search_path must be an iterable object
