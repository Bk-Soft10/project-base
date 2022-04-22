'''
Created on Nov 2, 2020

@author: Zuhair Hammadi
'''
from odoo import http
from odoo.http import request

orginal__handle_exception = http.JsonRequest._handle_exception

def _handle_exception(self, exception):
    request.env.cr.rollback()  # @UndefinedVariable
            
    return orginal__handle_exception(self, exception)

http.JsonRequest._handle_exception = _handle_exception