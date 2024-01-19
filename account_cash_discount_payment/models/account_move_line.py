# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def _get_amount_after_discount(self):
        # utiliser compute term? pas besoin
        # sur le montant residuel - note de credit
        percentage = 1 - (self.discount_percentage / 100.0)
        amount_residual = (
            self.amount_residual - self.move_id._get_refunds_amount_total()
        )

        if self.move_id.is_invoice():
            amount_residual *= -1

        discount_amount = self.currency_id.round(amount_residual * percentage)

        return discount_amount

    def _prepare_payment_line_vals(self, payment_order):
        self.ensure_one()
        values = super()._prepare_payment_line_vals(payment_order)

        if self.discount_date and self.discount_percentage:
            today = fields.Date.today()
            pay_with_discount = self.discount_date >= today
            values["pay_with_discount"] = pay_with_discount
            if pay_with_discount:
                values["amount_currency"] = self._get_amount_after_discount()
        return values
