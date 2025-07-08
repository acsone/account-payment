# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PaymentReturn(models.Model):
    _inherit = "payment.return"

    def _check_payment_returned_mandate(self):
        self.ensure_one()
        for return_line in (
            line for line in self.line_ids if line.reason_id.revoke_mandates
        ):
            for payment_aml in return_line.move_line_ids:
                invoice_amls = payment_aml.matched_debit_ids.mapped("debit_move_id")
                invoice_amls.mapped("move_id")._payment_returned(return_line)

    def action_confirm(self):
        self.ensure_one()
        self._check_payment_returned_mandate()
        return super().action_confirm()
