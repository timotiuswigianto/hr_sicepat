# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Sicepat Ekspres Indonesia (<http://www.sicepat.com>).
#    @author: - Timotius Wigianto <https://github.com/timotiuswigianto/>
#             - Pambudi Satria <pambudi.satria@yahoo.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp

class SalaryStructure(models.Model):
    _name = 'hr.salary.structure'
    
    name = fields.Char(string='Number', readonly=True)
    request_id = fields.Many2one('res.users', string='Requestor', readonly=True,
        default=lambda self: self.env.user)
    tanggal = fields.Date(default=lambda self: fields.Date.context_today(self), readonly=True,
        states={'draft': [('readonly', False)], 'submit': [('readonly', False)]})
    department_id = fields.Many2one('hr.department', string='Nama Cabang', required=True, readonly=True,
        states={'draft': [('readonly', False)], 'submit': [('readonly', False)]})
    state = fields.Selection([
        ('draft','Open'),
        ('submit','Submit'),
        ('reject','Reject'),
        ('approved','Approved'),
        ], string='State', readonly=True, default='draft')
    structure_line = fields.One2many('salary.structure.line', 'structure_id', readonly=True,
        states={'draft': [('readonly', False)], 'submit': [('readonly', False)]})
    
    @api.multi
    def action_submit(self):
        self.state = 'submit'

    @api.multi
    def action_approve(self):
        self.state = 'approved'
        
    @api.multi
    def action_reject(self):
        self.state = 'reject'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].get("salary.structure.amt")
        return super(SalaryStructure, self).create(vals)


CODE2INPUT = {
    'MEAL': 'uang_makan',
    'TRANSPORT': 'transport',
    'PERSISTANCE': 'uang_kerajinan',
    'OPER': 'tunj_operasional',
    'ALLOW': 'tunj_jabatan',
    'BIKE': 'service_motor'
}

class SalaryStructureLine(models.Model):
    _name = 'salary.structure.line'
    _rec_name = 'structure_id'

    structure_id = fields.Many2one('hr.salary.structure', string='Salary Structure')
    jabatan_id = fields.Many2one('hr.job', string='Jabatan', required=True)
    uang_makan = fields.Float(digits=dp.get_precision('Payroll'), string='Uang Makan')
    transport = fields.Float(digits=dp.get_precision('Payroll'), string='Transport')
    uang_kerajinan = fields.Float(digits=dp.get_precision('Payroll'), string='Uang Kerajinan')
    tunj_operasional = fields.Float(digits=dp.get_precision('Payroll'), string='Tunjangan Operasional')
    tunj_jabatan = fields.Float(digits=dp.get_precision('Payroll'), string='Tunjangan Jabatan')
    service_motor = fields.Float(digits=dp.get_precision('Payroll'), string='Service Motor')
    tanggal = fields.Date(related='structure_id.tanggal', store=True)
    department_id = fields.Many2one('hr.department', string='Nama Cabang', related='structure_id.department_id')
    state = fields.Selection(related='structure_id.state', store=True, default='draft')

    def get_structure_line(self, cr, uid, employee, date_from, date_to, context=None):
        """
        @param employee: browse record of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the salary structure lines for the given employee that need to be considered for the given dates
        """
        clause_1 = ['&',('tanggal', '<=', date_to),('tanggal','>=', date_from)]
        clause_final = [('department_id','=',employee.department_id.id), ('jabatan_id','=',employee.job_id.id), ('state','=','approved')] + clause_1
        struc_line_ids = self.search(cr, uid, clause_final, order='tanggal desc', context=context)
        return struc_line_ids

    def get_amount(self, cr, uid, ids, code, context=None):
        """
        @param code: char field
        @return: returns amount based on code
        """
        struct_line = self.browse(cr, uid, ids, context)
        return struct_line[0][CODE2INPUT.get(code)]

    def get_condition(self, cr, uid, code, context=None):
        """
        @param code: char field
        @return: returns True or False
        """
        if code:
            if code in CODE2INPUT:
                return True
        return False

class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = super(HRPayslip, self).get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)

        contract_obj = self.pool.get('hr.contract')
        employee_obj = self.pool.get('hr.employee')
        struct_line = self.pool.get('salary.structure.line')
        
        employee_id = contract_obj.browse(cr, uid, contract_ids, context=context)[0].employee_id.id
        employee = employee_obj.browse(cr, uid, employee_id, context=context)
        
        for result in res:
            if struct_line.get_condition(cr, uid, result.get('code'), context=context):
                struct_line_ids = struct_line.get_structure_line(cr, uid, employee, date_from, date_to, context=context)
                if struct_line_ids:
                    result['amount'] = struct_line.get_amount(cr, uid, struct_line_ids, result['code'], context=context)

        return res