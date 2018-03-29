# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class PaymentLine(models.Model):

    _inherit = 'account.payment.line'

    pay_with_discount = fields.Boolean(
        default=False,
    )
    discount_due_date = fields.Date(
        compute='_compute_discount_due_date',
    )
    discount_amount = fields.Monetary(
        default=0.0
    )
    original_amount_currency = fields.Monetary(
        readonly=True,
    )

    @api.multi
    @api.constrains(
        'pay_with_discount',
        'move_line_id',
    )
    def _check_pay_with_discount(self):
        for rec in self:
            if not rec.pay_with_discount:
                continue
            move_line = rec.move_line_id
            invoice = move_line and move_line.invoice_id or False
            if not invoice or not invoice.has_discount:
                raise ValidationError(
                    _("You can't pay with a discount if the payment line is "
                      "not linked to an invoice which has a discount."))

    @api.onchange(
        'discount_amount',
        'original_amount_currency',
        'pay_with_discount',
    )
    def _onchange_pay_with_discount(self):
        if self.pay_with_discount:
            self.amount_currency = (
                self.original_amount_currency - self.discount_amount)
        else:
            self.amount_currency = self.original_amount_currency
