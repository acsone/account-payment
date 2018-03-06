# -*- coding: utf-8 -*-
# Copyright 2014 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class PaymentLine(models.Model):

    _inherit = 'account.payment.line'

    discount_due_date = fields.Date(
        compute='_compute_discount_due_date',
    )
    discount_amount = fields.Monetary(
        default=0.0
    )

    @api.multi
    @api.depends(
        'move_line_id.invoice_id'
    )
    def _compute_discount_due_date(self):
        if self.move_line_id and self.move_line_id.invoice_id:
            invoice = self.move_line_id.invoice_id
            self.discount_due_date = invoice.discount_due_date
