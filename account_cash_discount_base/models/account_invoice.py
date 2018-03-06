# -*- coding: utf-8 -*-
# Copyright 2014 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

READONLY_STATES = {
    'draft': [('readonly', False)],
}


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    discount_percent = fields.Float(
        string="Cash Discount (%)",
        readonly=True,
        states=READONLY_STATES,
    )
    amount_total_with_discount = fields.Monetary(
        string="Total (with discount)",
        compute='_compute_amount_total_with_discount',
    )
    discount_amount = fields.Monetary(
        string="Discount Amount",
        compute='_compute_discount_amount',
    )
    discount_delay = fields.Integer(
        string="Discount Delay (days)",
        readonly=True,
        states=READONLY_STATES
    )
    discount_due_date = fields.Date(
        readonly=True,
        states=READONLY_STATES
    )
    discount_due_date_readonly = fields.Date(
        string="Discount Due Date",
        compute='_compute_discount_due_date',
    )
    force_discount_amount = fields.Boolean(
        string="Force Discount Amount",
        states=READONLY_STATES
    )
    forced_discount_amount = fields.Monetary(
        readonly=True,
        states=READONLY_STATES,
    )

    @api.multi
    @api.depends(
        'amount_total',
        'amount_untaxed',
        'discount_percent',
        'force_discount_amount',
        'forced_discount_amount',
        'company_id.cash_discount_base_amount_type',
    )
    def _compute_discount_amount(self):
        for rec in self:
            discount_amount = 0.0
            if rec.force_discount_amount:
                discount_amount = rec.forced_discount_amount
            elif rec.discount_percent != 0.0:
                base_amount_type = \
                    rec.company_id.cash_discount_base_amount_type
                base_amount = (
                    base_amount_type == 'untaxed' and
                    rec.amount_untaxed or rec.amount_total)
                discount_amount = (
                    base_amount * (0.0 + rec.discount_percent / 100))
            rec.discount_amount = discount_amount

    @api.multi
    @api.depends(
        'amount_total',
        'discount_amount',
    )
    def _compute_amount_total_with_discount(self):
        for rec in self:
            rec.amount_total_with_discount = \
                rec.amount_total - rec.discount_amount

    @api.multi
    @api.depends(
        'discount_due_date',
    )
    def _compute_discount_due_date(self):
        for rec in self:
            rec.discount_due_date_readonly = rec.discount_due_date

    @api.multi
    @api.onchange('discount_delay')
    def _onchange_discount_delay(self):
        date_today = datetime.today()
        for rec in self:
            if rec.discount_amount == 0 or rec.discount_delay == 0:
                continue
            if rec.date_invoice:
                date_invoice = fields.Date.from_string(rec.date_invoice)
            else:
                date_invoice = date_today
            due_date = date_invoice + timedelta(days=rec.discount_delay)
            rec.discount_due_date = due_date

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            inv._onchange_discount_delay()
            if not inv.discount_due_date and inv.discount_amount != 0.0:
                raise UserError(_(
                    "You can't set a discount amount if there is no "
                    "discount due date. (Invoice ID: %s)"
                ) % (inv.id,))
        return res
