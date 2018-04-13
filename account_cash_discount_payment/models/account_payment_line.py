# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class PaymentLine(models.Model):

    _inherit = 'account.payment.line'

    pay_with_discount = fields.Boolean(
        default=False,
    )
    pay_with_discount_allowed = fields.Boolean(
        compute='_compute_pay_with_discount_allowed',
    )
    toggle_pay_with_discount_allowed = fields.Boolean(
        compute='_compute_toggle_pay_with_discount_allowed',
    )
    discount_due_date = fields.Date(
        related='move_line_id.invoice_id.discount_due_date',
        readonly=True,
    )
    discount_amount = fields.Monetary(
        related='move_line_id.invoice_id.discount_amount',
        readonly=True,
    )

    @api.multi
    def _compute_pay_with_discount_allowed(self):
        for rec in self:
            rec.pay_with_discount_allowed = (
                rec.move_line_id and
                rec.move_line_id.invoice_id and
                rec.move_line_id.invoice_id.has_discount
            )

    @api.multi
    def _compute_toggle_pay_with_discount_allowed(self):
        for rec in self:
            rec.toggle_pay_with_discount_allowed = (
                rec.pay_with_discount_allowed and
                rec.order_id.state not in ('uploaded', 'cancelled')
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
            if not rec.pay_with_discount_allowed:
                raise ValidationError(
                    _("You can't pay with a discount if the payment line is "
                      "not linked to an invoice which has a discount."))

    @api.onchange(
        'discount_amount',
        'move_line_id',
        'pay_with_discount',
    )
    def _onchange_pay_with_discount(self):
        """
        This onchange should be executed completely only when the payment line
        is linked to a move line which is linked to an invoice which has a
        discount.

        If the above condition is ok, the amount will change based on the
        invoice total and invoice discount amount.
        """
        self._check_pay_with_discount()
        invoice = self.move_line_id.invoice_id
        if self.pay_with_discount:
            self.amount_currency = invoice.amount_total_with_discount
        else:
            self.amount_currency = invoice.amount_total

    @api.multi
    def _check_toggle_pay_with_discount_allowed(self):
        for rec in self:
            if not rec.toggle_pay_with_discount_allowed:
                raise UserError(
                    _("You can change the pay with discount value only if "
                      "there is a linked invoice with a discount and if the "
                      "payment order is not done. (Payment Order: %s)") % (
                        rec.order_id.name)
                )

    @api.multi
    def toggle_pay_with_discount(self):
        self.ensure_one()
        self._check_toggle_pay_with_discount_allowed()
        self.pay_with_discount = not self.pay_with_discount
        self._onchange_pay_with_discount()
