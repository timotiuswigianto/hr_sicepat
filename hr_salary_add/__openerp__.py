# -*- coding: utf-8 -*-
{
    'name': "hr_salary_add",

    'summary': "Courses, Sessions, Subscriptions",

    'description': "...",

    'author': "Your Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': ["views/hr_salary_particular.xml"],
    # only loaded in demonstration mode
    'demo': [],
    'images': [],
    'application': True,
}