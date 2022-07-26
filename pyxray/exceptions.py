#!/usr/bin/env python
# -*- coding: utf-8 -*-

class XrayScannerError(Exception):
    """
    Exception error class for XrayScannerError class

    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

    def __repr__(self):
        return f"XrayScannerError exception {self.value}"


class XrayScannerTimeout(XrayScannerError):
    """
    Exception error class for XrayScannerTimeout class

    """
