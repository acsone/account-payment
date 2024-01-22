# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PaymentLine(models.Model):

    _inherit = "account.payment.line"

    def _prepare_account_payment_vals(self):
        """Prepare the dictionary to create an account payment record from a set of
        payment lines.
        """
        payment_vals = super()._prepare_account_payment_vals()

        conversion_rate = self.env["res.currency"]._get_conversion_rate(
            self.currency_id,
            self.company_currency_id,
            self.company_id,
            payment_vals["date"],
        )

        epd_aml_values_list = []
        for rec in self:
            if rec.pay_with_discount:
                aml = rec.move_line_id
                epd_aml_values_list.append(
                    {
                        "aml": aml,
                        "amount_currency": -aml.amount_residual_currency,
                        "balance": aml.company_currency_id.round(
                            -aml.amount_residual_currency * conversion_rate
                        ),
                    }
                )

        open_balance = (
            sum(
                rec._get_amount_after_discount()[0]
                for rec in self.mapped("move_line_id")
            )
            * conversion_rate
        )

        if epd_aml_values_list:
            early_payment_values = rec.env[
                "account.move"
            ]._get_invoice_counterpart_amls_for_early_payment_discount(
                epd_aml_values_list, open_balance
            )
            payment_vals["write_off_line_vals"] = []
            for r in early_payment_values.values():
                payment_vals["write_off_line_vals"] += r

        return payment_vals
