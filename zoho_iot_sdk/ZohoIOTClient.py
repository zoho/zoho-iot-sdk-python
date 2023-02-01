#!/usr/bin/env python3

class ZohoIoTClient:
    def __init__(self, message):
        self.message = message

    def print(self, prefix):
        result = (self.stringAppender(prefix, self.message))
        print(result)
        return result

    def stringAppender(self, str1, str2):
        return str1 + str2
