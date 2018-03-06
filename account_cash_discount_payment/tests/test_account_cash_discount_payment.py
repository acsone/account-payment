# -*- coding: utf-8 -*-
# Copyright 2014 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.account_cash_discount_base.tests.common import \
    TestAccountCashDiscountCommon
from odoo.fields import Date


class TestAccountCashDiscountPayment(TestAccountCashDiscountCommon):

    @classmethod
    def setUpClass(cls):
        super(TestAccountCashDiscountPayment, cls).setUpClass()
        cls.PaymentLineCreate = cls.env['account.payment.line.create']
        cls.PaymentOrder = cls.env['account.payment.order']

        cls.payment_mode_out = cls.env.ref(
            'account_payment_mode.payment_mode_outbound_ct1')

    def create_simple_invoice(
            self, date, payment_mode, amount, discount_percent):
        invoice = self.AccountInvoice.create({
            'partner_id': self.partner_agrolait.id,
            'account_id': self.pay_account.id,
            'company_id': self.company.id,
            'journal_id': self.sales_journal.id,
            'type': 'in_invoice',
            'date_invoice': date,
            'discount_due_date': date,
            'discount_percent': discount_percent,
            'payment_mode_id': payment_mode.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': "Test",
                    'quantity': 1,
                    'account_id': self.pay_account.id,
                    'price_unit': amount,
                })
            ]
        })
        invoice.compute_taxes()
        return invoice

    def test_invoice_payment_discount(self):
        invoice_date = Date.today()
        invoice = self.create_simple_invoice(
            invoice_date, self.payment_mode_out, 2000, 25)
        invoice.action_invoice_open()

        move = invoice.move_id
        move.post()

        payment_order = self.PaymentOrder.create({
            'payment_mode_id': self.payment_mode_out.id,
            'payment_type': 'outbound',
        })

        payment_line_wizard = self.PaymentLineCreate.with_context(
            active_model=payment_order._name,
            active_id=payment_order.id,
        ).create({
            'cash_discount_date_start': invoice_date,
            'cash_discount_date_end': invoice_date,
            'cash_discount_date': True,
            'journal_ids': [(6, 0, [self.sales_journal.id])],
        })
        self.assertEqual(payment_line_wizard.order_id, payment_order)

        payment_line_wizard.populate()
        move_lines = payment_line_wizard.move_line_ids
        self.assertEqual(len(move_lines), 1)

        move_line = move_lines[0]
        self.assertAlmostEqual(move_line.discount_amount, 500, 2)

        payment_line_wizard.create_payment_lines()

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        move_line = payment_order.payment_line_ids[0]
        self.assertAlmostEqual(move_line.discount_amount, 500, 2)
        self.assertAlmostEqual(move_line.amount_currency, 1500, 2)
