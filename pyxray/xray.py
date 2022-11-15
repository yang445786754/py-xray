#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
xray.py

Source code : https://github.com/yang445786754/py-xray

Author :

* Tony_9410 - tony_9410@foxmail.com

#! 你需要自行准备下载准备Xray Community软件

"""

import json
import os
import re
import sys
import uuid
import shlex
import copy

import subprocess

from .exceptions import XrayScannerError, XrayScannerTimeout


__author__ = "Tony_9410 (tony_9410@foxmail.com)"
__version__ = "0.1.1"
__last_modification__ = "2022.07.26"


class XrayWebScanner:
    """长亭科技 XRAY community 客户端"""
    def __init__(
        self,
        xray_search_path=(
            os.path.join(os.path.dirname(__file__), "./xray_linux_amd64"),
            "xray_linux_amd64",
            "/usr/bin/xray_linux_amd64",
            "/usr/local/bin/xray_linux_amd64",
            "/sw/bin/xray_linux_amd64",
            "/opt/local/bin/xray_linux_amd64",
        ),
        config_path='/tmp/xray_config.yaml'
    ):
        self._xray_cache_path = "/tmp"
        self._xray_instance_id = uuid.uuid4().hex
        self._xray_path = ""  # xray path
        self._scan_result = {}
        self._xray_version_number = 0  # xray version number
        self._xray_subversion_number = 0  # xray subversion number
        self._xray_last_output = ""  # last full ascii xray output
        self._xray_last_command_line = ""  # last full ascii xray command line
        is_xray_found = False  # true if we have found xray
        self._xray_config_path = config_path

        self.urls_path = os.path.join(
            self._xray_cache_path,
            'xray_' + self._xray_instance_id + '_urls.txt'
        )
        self.results_path = os.path.join(
            self._xray_cache_path,
            'xray_' + self._xray_instance_id + '_results.json'
        )

        # regex used to detect xray (http or https)
        regex = re.compile(r"Version: [0-9]*\.[0-9]*\.[0-9]*/.*/COMMUNITY.*")

        for xray_path in xray_search_path:
            try:
                if (
                    sys.platform.startswith("freebsd")
                    or sys.platform.startswith("linux")
                    or sys.platform.startswith("darwin")
                ):
                    p = subprocess.Popen(
                        [xray_path, "version"],
                        bufsize=10000,
                        stdout=subprocess.PIPE,
                        close_fds=True,
                    )
                else:
                    p = subprocess.Popen(
                        [xray_path, "version"], bufsize=10000,
                        stdout=subprocess.PIPE
                    )

            except OSError:
                pass
            else:
                self._xray_path = xray_path  # save path
                break
        else:
            raise XrayScannerError(
                "xray program was not found in path. PATH"
                f" is : {os.getenv('PATH')}"
            )

        self._xray_last_output = bytes.decode(p.communicate()[0])  # sav stdout
        for line in self._xray_last_output.split(os.linesep):
            rv = rsv = None
            if regex.match(line) is not None:
                is_xray_found = True
                # Search for version number
                regex_version = re.compile("[0-9]+")
                regex_subversion = re.compile(r"\.[0-9]+")

                rv = regex_version.search(line)
                rsv = regex_subversion.search(line)

            if rv is not None and rsv is not None:
                # extract version/subversion
                self._xray_version_number = int(line[rv.start(): rv.end()])
                self._xray_subversion_number = int(
                    line[rsv.start() + 1: rsv.end()]
                )
                break

        if not is_xray_found:
            raise XrayScannerError("xray program was not found in path")
        return

    def _prepare_for_scan(self, urls):
        """创建扫描URL文件，清理之前扫描的结果文件，保证没有相同的文件"""
        with open(self.urls_path, 'w') as f:
            f.writelines(map(lambda x: x + '\n', urls))
        try:
            if os.access(self.results_path, os.F_OK):
                os.remove(self.results_path)
        except Exception:
            ...

    @property
    def xray_version(self):
        return (self._xray_version_number, self._xray_subversion_number)

    def webscan(self, urls=[], arguments="", timeout=0):
        if isinstance(urls, list):
            urls = [x.strip() for x in urls]
        elif isinstance(urls, str):
            urls = shlex.split(urls)
        else:
            raise XrayScannerError('url 参数异常')

        # make url-file
        self._prepare_for_scan(urls=urls)

        # set configs
        config_args = ['--config', self._xray_config_path]

        f_args = shlex.split(arguments)

        # excute scan
        args = (
            [self._xray_path]
            + config_args
            + ['webscan']
            + f_args
            + ['--url-file', self.urls_path]
            + ['--json-output', self.results_path]
        )
        self._xray_last_command_line = shlex.join(args)

        p = subprocess.Popen(
            args,
            bufsize=100000,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # wait until finished
        # get output
        # Terminate after user timeout
        if timeout == 0:
            (self._xray_last_output, xray_err) = p.communicate()
        else:
            try:
                (self._xray_last_output, xray_err) = p.communicate(
                    timeout=timeout)
            except subprocess.TimeoutExpired:
                p.kill()
                raise XrayScannerTimeout("Timeout from xray process")

        xray_err = bytes.decode(xray_err)

        xray_err_keep_trace = []
        xray_warn_keep_trace = []
        if len(xray_err) > 0:
            regex_warning = re.compile("^[WARN] .*", re.IGNORECASE)
            for line in xray_err.split(os.linesep):
                if len(line) > 0:
                    rgw = regex_warning.search(line)
                    if rgw is not None:
                        xray_warn_keep_trace.append(line + os.linesep)
                    else:
                        xray_err_keep_trace.append(xray_err)

        return self.analyse_xray_json_scan(
            xray_err=xray_err,
            xray_err_keep_trace=xray_err_keep_trace,
            xray_warn_keep_trace=xray_warn_keep_trace,
        )

    def webscan_with_crawler(self, urls=[], arguments="", timeout=0):
        if isinstance(urls, list):
            urls = [x.strip() for x in urls]
        elif isinstance(urls, str):
            urls = shlex.split(urls)
        else:
            raise XrayScannerError('url 参数异常')

        # set configs
        config_args = ['--config', self._xray_config_path]

        f_args = shlex.split(arguments)

        xray_err_keep_trace = []
        xray_warn_keep_trace = []

        scan_results_ = []

        # excute scan
        for url in urls:
            args = (
                [self._xray_path]
                + config_args
                + ['webscan']
                + f_args
                + ['--basic-crawler', url]
                + ['--json-output', self.results_path]
            )
            self._xray_last_command_line = shlex.join(args)

            p = subprocess.Popen(
                args,
                bufsize=100000,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # wait until finished
            # get output
            # Terminate after user timeout
            if timeout == 0:
                (self._xray_last_output, xray_err) = p.communicate()
            else:
                try:
                    (self._xray_last_output, xray_err) = p.communicate(
                        timeout=timeout)
                except subprocess.TimeoutExpired:
                    p.kill()
                    raise XrayScannerTimeout("Timeout from xray process")

            xray_err = bytes.decode(xray_err)

            if len(xray_err) > 0:
                regex_warning = re.compile("^[WARN] .*", re.IGNORECASE)
                for line in xray_err.split(os.linesep):
                    if len(line) > 0:
                        rgw = regex_warning.search(line)
                        if rgw is not None:
                            xray_warn_keep_trace.append(line + os.linesep)
                        else:
                            xray_err_keep_trace.append(xray_err)

            scan_results_.append(self.analyse_xray_json_scan(
                xray_err=xray_err,
                xray_err_keep_trace=xray_err_keep_trace,
                xray_warn_keep_trace=xray_warn_keep_trace,
            ))
        
        return self._merge_scan_results(scan_results_)

    @staticmethod
    def _merge_scan_results(scan_results):
        if not scan_results:
            return None

        result_ = copy.deepcopy(scan_results[0])

        result_['scan']['vulns'] = []
        result_['xray']['command_line'] = []
        result_['xray']['scaninfo']['error'] = []
        result_['xray']['scaninfo']['warning'] = []
        result_['xray']['scanstats']['is_safe'] = True
        result_['xray']['scanstats']['total_vulns'] = 0

        for scan_result in scan_results:
            # merge vulns
            result_['scan']['vulns'].extend(scan_result['scan']['vulns'])

            # merge state
            result_['xray']['command_line'].append(
                scan_result['xray']['command_line'])
            result_['xray']['scanstats']['total_vulns'] += \
                scan_result['xray']['scanstats']['total_vulns']
            result_['xray']['scanstats']['is_safe'] = \
                result_['xray']['scanstats']['is_safe'] and \
                    scan_result['xray']['scanstats']['is_safe']
            
            bool(scan_result["xray"]["scaninfo"].get("error", None)) and \
                result_["xray"]["scaninfo"]["error"].append(
                scan_result["xray"]["scaninfo"].get("error", ""))
            bool(scan_result["xray"]["scaninfo"].get("warning", None)) and \
                result_["xray"]["scaninfo"]["warning"].append(
                scan_result["xray"]["scaninfo"].get("warning", ""))

        return result_


    def check_xray_finished(self):
        keywords = self._xray_last_output[-31:-1]
        return keywords == b'controller released, task done'

    def analyse_xray_json_scan(
        self,
        xray_err="",
        xray_err_keep_trace="",
        xray_warn_keep_trace="",
    ):
        if not self.check_xray_finished():
            if xray_err.__len__() > 0:
                raise XrayScannerError(xray_err)
            else:
                raise XrayScannerError(self._xray_last_output)

        scan_results = {}

        if not os.access(self.results_path, os.F_OK):
            results = []
        else:
            with open(self.results_path, 'r') as f:
                results = json.load(f)

        scan_results['xray'] = {
            'command_line': self._xray_last_command_line,
            'scaninfo': {},
            'scanstats': {
                'is_safe': not bool(results),
                'total_vulns': results.__len__()
            }
        }

        # if there was an error
        if len(xray_err_keep_trace) > 0:
            scan_results["xray"]["scaninfo"]["error"] = xray_err_keep_trace

        # if there was a warning
        if len(xray_warn_keep_trace) > 0:
            scan_results["xray"]["scaninfo"]["warning"] = xray_warn_keep_trace

        scan_results["scan"] = {}
        scan_results["scan"]["vulns"] = []
        for item in results:
            scan_results["scan"]["vulns"].append({
                'vuln_name': item['plugin'],
                'target': item['target']['url'],
                'payload': item['detail']['payload'],
                'request_payload': item['detail']['snapshot'][0][0],
                'response_payload': item['detail']['snapshot'][0][1],
                'event_time': item['create_time']
            })
        self._scan_result = scan_results  # store for later use
        return scan_results

    def __del__(self):
        """
        Cleanup when deleted
        """
        for path in [self.urls_path, self.results_path]:
            try:
                if os.access(path, os.F_OK):
                    os.remove(path)
            except Exception:
                ...
