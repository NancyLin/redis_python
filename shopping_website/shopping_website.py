# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
获取并返回令牌对应的用户

@param {object}
@param {string} token

@return {string} 用户id
"""
def checkToken(conn, token):
	return conn.hget('login:', token)