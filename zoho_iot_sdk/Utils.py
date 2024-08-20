#!/usr/bin/env python3

class Utils:
    @staticmethod
    def is_blank(data):
        if isinstance(data, str) and data is not None and data.strip() != "":
            return False
        return True

    @staticmethod
    def is_json_blank(json_data):
        if isinstance(json_data, dict) and bool(json_data):
            return False
        return True
