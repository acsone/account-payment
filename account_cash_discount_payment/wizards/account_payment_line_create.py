# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentLineCreate(models.TransientModel):

    _inherit = 'account.payment.line.create'

    cash_discount_date = fields.Boolean(
        string="Cash Discount Due Date",
        default=False,
    )
    cash_discount_date_start = fields.Date()
    cash_discount_date_end = fields.Date()

    @api.multi
    def _clean_maturity_date_domain(self, domain):
        """
        This method cleans the domain populated by _prepare_move_line_domain.
        If the user want to search entries based on a discount due date, this
        method will remove the date_maturity domain part.
        """
        self.ensure_one()
        maturity_1st_elem = '|'
        maturity_2nd_elem = ('date_maturity', '<=', self.due_date)
        maturity_3rd_elem = ('date_maturity', '=', False)

        pos = 0
        while pos < len(domain):
            pop_elems = (
                pos < len(domain) - 2 and
                domain[pos] == maturity_1st_elem and
                domain[pos + 1] == maturity_2nd_elem and
                domain[pos + 2] == maturity_3rd_elem
            )

            if pop_elems:
                for i in range(3):
                    domain.pop(pos)
                break
            pos += 1
        return domain

    @api.multi
    def _prepare_move_line_domain(self):
        self.ensure_one()
        domain = super(
            AccountPaymentLineCreate, self
        )._prepare_move_line_domain()

        if not self.cash_discount_date:
            return domain

        if self.date_type == 'due':
            domain = self._clean_maturity_date_domain(domain)
            date_start = self.cash_discount_date_start
            date_end = self.cash_discount_date_end
            domain += [
                ('invoice_id.discount_due_date', '>=', date_start),
                ('invoice_id.discount_due_date', '<=', date_end),
            ]
        return domain
