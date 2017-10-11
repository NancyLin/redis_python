# !/usr/bin/env python
# -*- coding: utf-8 -*-

# 设置一个字典，将大部分日志的安全级别映射为字符串
SEVERITY = {
	logging.DEBUG: 'debug',
	logging.INFO: 'info',
	logging.WARNING: 'warning',
	logging.ERROR: 'error',
	logging.CRITICAL: 'critical',
}

# 将日志的安全级别转换为简单的字符串
SEVERITY.update((name, name) for name in SEVERITY.values())

def log_recent