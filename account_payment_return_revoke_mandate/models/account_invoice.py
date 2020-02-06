# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.multi
    def _payment_returned(self, return_line):
        super()._payment_returned(return_line)
        if return_line.reason_id.revoke_mandates and self.mandate_id:
            try:
                self.mandate_id.cancel()
                msg = (
                    "Mandate revoked in payment return %s"
                    % return_line.return_id.name
                )
                self.mandate_id.message_post(body=msg)
            except UserError:
                # May happen if the mandate is not in draft or valid state
                pass
