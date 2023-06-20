# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        self.ensure_one()
        values = super()._prepare_payment_line_vals(payment_order)

        if self.discount_date and self.discount_percentage:
            today = fields.Date.today()
            pay_with_discount = self.discount_date >= today
            values["pay_with_discount"] = pay_with_discount
            if pay_with_discount:

                # compute discount amount
                if self.currency_id:
                    amount_residual = self.amount_residual_currency
                else:
                    amount_residual = self.amount_residual

                if self.company_id.early_pay_discount_computation in (
                    "excluded",
                    "mixed",
                ):
                    base_amount = amount_residual / (
                        (
                            self.move_id.amount_tax_signed
                            + self.move_id.amount_untaxed_signed
                        )
                        / self.move_id.amount_untaxed_signed
                    )
                else:
                    base_amount = amount_residual

                if self.move_id.is_invoice():
                    base_amount *= -1
                    amount_residual *= -1
                # apply discount
                discount = base_amount * (self.discount_percentage / 100)
                amount_with_discount = amount_residual - discount
                values["amount_currency"] = amount_with_discount
                # update discount_amount_currency on aml
                self.discount_amount_currency = (
                    self.move_id.amount_total_in_currency_signed + discount
                )
                self.discount_balance = self.move_id.amount_total_signed + discount
        return values
