# -*- coding: utf-8 -*-
# Copyright 2014 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo.tests.common import SavepointCase
from odoo.exceptions import UserError
from odoo.fields import Date


class TestAccountCashDiscountBase(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountCashDiscountBase, cls).setUpClass()
        cls.Account = cls.env['account.account']
        cls.AccountInvoice = cls.env['account.invoice']
        cls.Tax = cls.env['account.tax']

        cls.company = cls.env.ref('base.main_company')
        cls.partner_agrolait = cls.env.ref('base.res_partner_2')

        cls.recv_account_type = cls.env.ref(
            'account.data_account_type_receivable')
        cls.exp_account_type = cls.env.ref(
            'account.data_account_type_expenses')

        cls.recv_account = cls.Account.search([
            ('user_type_id', '=', cls.recv_account_type.id)
        ], limit=1)
        cls.exp_account = cls.Account.search([
            ('user_type_id', '=', cls.exp_account_type.id)
        ], limit=1)

        cls.tax_10_s = cls.Tax.create({
            'sequence': 30,
            'name': 'Tax 10.0% (Percentage of Price)',
            'amount': 10.0,
            'amount_type': 'percent',
            'include_base_amount': False,
            'type_tax_use': 'sale',
        })

    def create_simple_invoice(self, amount):
        invoice = self.AccountInvoice.create({
            'partner_id': self.partner_agrolait.id,
            'account_id': self.exp_account.id,
            'company_id': self.company.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': "Test",
                    'quantity': 1,
                    'account_id': self.exp_account.id,
                    'price_unit': amount,
                    'invoice_line_tax_ids': [(6, 0, [self.tax_10_s.id])],
                })
            ]
        })
        invoice.compute_taxes()
        return invoice

    def test_compute_discount_untaxed(self):
        self.company.cash_discount_base_amount_type = 'untaxed'
        invoice = self.create_simple_invoice(1000)

        invoice.discount_percent = 0
        self.assertEqual(invoice.discount_amount, 0)
        self.assertEqual(invoice.amount_total_with_discount, 1100)

        invoice.discount_percent = 10
        self.assertEqual(invoice.discount_amount, 100)
        self.assertEqual(invoice.amount_total_with_discount, 1000)

    def test_compute_discount_total(self):
        self.company.cash_discount_base_amount_type = 'total'
        invoice = self.create_simple_invoice(1000)

        invoice.discount_percent = 0
        self.assertEqual(invoice.discount_amount, 0)
        self.assertEqual(invoice.amount_total_with_discount, 1100)

        invoice.discount_percent = 10
        self.assertEqual(invoice.discount_amount, 110)
        self.assertEqual(invoice.amount_total_with_discount, 990)

    def test_discount_delay_1(self):
        days_delay = 10
        today = datetime.today()
        today_10_days_later = today + relativedelta(days=days_delay)

        invoice = self.create_simple_invoice(100)
        invoice.discount_delay = days_delay
        invoice._onchange_discount_delay()
        self.assertFalse(invoice.discount_due_date)

        invoice.invalidate_cache()
        invoice.discount_percent = 10
        invoice._onchange_discount_delay()
        self.assertEqual(
            invoice.discount_due_date, Date.to_string(today_10_days_later))

    def test_discount_delay_2(self):
        invoice = self.create_simple_invoice(100)
        invoice.discount_percent = 10

        with self.assertRaises(UserError), self.env.cr.savepoint():
            invoice.action_invoice_open()

        invoice.discount_delay = 10
        invoice._onchange_discount_delay()
        self.assertTrue(invoice.discount_due_date)

        invoice.action_invoice_open()
