# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

DISCOUNT_ALLOWED_TYPES = (
    "in_invoice",
    "in_refund",
    "out_invoice",
)


class AccountMove(models.Model):

    _inherit = "account.move"

    def write(self, vals):
        res = super().write(vals)
        if "invoice_payment_term_id" in vals:
            self.line_ids.write({"discount_updated": False})
        return res

    def _get_payment_move_lines(self):
        self.ensure_one()
        lines = []
        for line in self.line_ids:
            account_type = line.account_id.account_type
            if account_type not in ("asset_receivable", "liability_payable"):
                continue
            for rp in line.matched_credit_ids:
                lines.append((rp.credit_move_id,rp.credit_amount_currency))
            for rp in line.matched_debit_ids:
                lines.append((rp.debit_move_id,rp.debit_amount_currency))
        return lines

    def _get_refunds_amount_total(self):
        self.ensure_one()
        refunds_discount_total = 0.0
        refunds_amount_total = 0.0
        inv_type = self.move_type
        expected_refund_type = False
        if inv_type in DISCOUNT_ALLOWED_TYPES and inv_type.endswith("invoice"):
            expected_refund_type = inv_type.replace("invoice", "refund")
        for (pmove_line,reconciled_amount) in self._get_payment_move_lines():
            pmove_line_move = pmove_line.move_id
            if pmove_line_move and pmove_line_move.move_type == expected_refund_type:
                discount_amount = pmove_line.discount_amount_currency * (reconciled_amount/pmove_line.amount_currency)

                refunds_discount_total += abs(reconciled_amount) - abs(
                    discount_amount
                )
                refunds_amount_total += reconciled_amount
        return {"discount": refunds_discount_total, "total": refunds_amount_total}
