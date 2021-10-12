# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Pre-init cash discount fields on account.move")
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        columns = [
            ("amount_total_with_discount", "float"),
            ("discount_amount", "float"),
            ("refunds_discount_amount", "float"),
            ("has_discount", "boolean"),
        ]

        for col_name, col_type in columns:
            if not openupgrade.column_exists(env.cr, "account_invoice", col_name):
                continue
            field_spec = [
                (
                    col_name,
                    "account.move",
                    False,
                    col_type,
                    False,
                    "account_cash_discount_base",
                ),
            ]
            openupgrade.add_fields(env, field_spec)
        query = """
            update account_move
            set has_discount = ai.has_discount,
            amount_total_with_discount = ai.amount_total_with_discount,
            refunds_discount_amount = ai.refunds_discount_amount,
            discount_amount = ai.discount_amount
            FROM account_invoice ai
            JOIN account_move am on am.id = ai.move_id
            WHERE ai.has_discount = True
        """
        openupgrade.logged_query(env.cr, query)
