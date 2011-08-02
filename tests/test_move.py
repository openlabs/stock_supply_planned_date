#!/usr/bin/env python
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from __future__ import with_statement

import sys, os
DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
     '..', '..', '..', '..', '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

import unittest
import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.transaction import Transaction


class MoveUpdateTestCase(unittest.TestCase):
    """
    Test Stock Move Update Planned Date
    """

    def setUp(self):
        trytond.tests.test_tryton.install_module('stock_supply_planned_date')
        self.product = POOL.get('product.product')
        self.category = POOL.get('product.category')
        self.uom = POOL.get('product.uom')
        self.location = POOL.get('stock.location')
        self.move = POOL.get('stock.move')
        self.company = POOL.get('company.company')
        self.user = POOL.get('res.user')
        self.purchase = POOL.get('purchase.purchase')
        self.party = POOL.get('party.party')
        self.account = POOL.get('account.account')
        self.account_type = POOL.get('account.account.type')
        self.account_template_obj = POOL.get('account.account.template')
        self.account_journal_obj = POOL.get('account.journal')
        self.create_chart_account_obj = POOL.get(
            'account.account.create_chart_account', type="wizard")
        self.payment_term = POOL.get('account.invoice.payment_term')
        self.ir_model_data = POOL.get('ir.model.data')

    def test0010move_update_test(self):
        """Test update_planned_date"""
        with Transaction().start(DB_NAME, USER, CONTEXT) as transaction:
            category_id = self.category.create({
                'name': 'Test Move.update_planned_dates',
                })
            unit_id, = self.uom.search([('name', '=', 'Unit')])
            product_id = self.product.create({
                'name': 'Test Move.update_planned_dates',
                'type': 'stockable',
                'category': category_id,
                'cost_price_method': 'fixed',
                'default_uom': unit_id,
                })
            supplier_id, = self.location.search([('code', '=', 'SUP')])
            customer_id, = self.location.search([('code', '=', 'CUS')])
            storage_id, = self.location.search([('code', '=', 'STO')])
            company_id, = self.company.search([('name', '=', 'B2CK')])
            currency_id = self.company.read(company_id,
                    ['currency'])['currency']
            self.user.write(USER, {
                'main_company': company_id,
                'company': company_id,
                })
            cron_user = self.ir_model_data.get_id(
                'stock_supply', 'user_generate_request')
            self.user.write(cron_user, {
                'main_company': company_id,
                'company': company_id,
                })

            today = datetime.date.today()

            values = {
                'product': product_id,
                'uom': unit_id,
                'quantity': 5,
                'company': company_id,
                'unit_price': Decimal('1'),
                'currency': currency_id,
                }
            combinations = (
                (supplier_id, storage_id, -5, 'done'),
                (supplier_id, storage_id, -4, 'draft'),
                (storage_id, customer_id, 0, 'done'),
                (storage_id, customer_id, -4, 'draft'),
                (storage_id, customer_id, 5, 'draft'),
                (supplier_id, storage_id, 7, 'draft'),
            )

            for combination in combinations:
                values.update({
                    'from_location': combination[0],
                    'to_location': combination[1],
                    'planned_date': today + relativedelta(days=combination[2]),
                    'state': combination[3]
                })
                self.move.create(values)


            self.assertEqual(
                self.move.search([
                        ('state', '=', 'draft'),
                        ('planned_date', '<', today),
                    ], count=True), 2)



            with Transaction().set_user(cron_user):
                self.move.update_supply_planned_date()

            self.assertEqual(
                self.move.search([
                        ('state', '=', 'draft'),
                        ('planned_date', '<', today),
                    ], count=True), 1)
            self.assertEqual(
                self.move.search([
                        ('state', '=', 'draft'),
                        ('from_location.type', '=', 'supplier'),
                        ('planned_date', '<', today),
                    ], count=True), 0)

    def setup_chart_of_accounts(self, company):
        account_template, = self.account_template_obj.search(
            [('parent', '=', False)])

        wiz_id = self.create_chart_account_obj.create()
        self.create_chart_account_obj.execute(wiz_id, {}, 'account')
        self.create_chart_account_obj.execute(wiz_id,
            {
                'form': {
                    'account_template': account_template,
                    'company': company,
                    }
            }, 'create_account'
        )

    def test0020_party_flag(self):
        """Assert that the `update_planned_date` flag on party is respected 
        when the move planned date update is done
        """
        with Transaction().start(DB_NAME, USER, CONTEXT) as transaction:
            category_id = self.category.create({
                'name': 'Test Move.update_planned_dates',
                })
            unit_id, = self.uom.search([('name', '=', 'Unit')])

            supplier_id, = self.location.search([('code', '=', 'SUP')])
            customer_id, = self.location.search([('code', '=', 'CUS')])
            storage_id, = self.location.search([('code', '=', 'STO')])
            warehouse_id, = self.location.search([('code', '=', 'WH')])
            company_id, = self.company.search([('name', '=', 'B2CK')])

            self.user.write(USER, {
                'main_company': company_id,
                'company': company_id,
                })
            cron_user = self.ir_model_data.get_id(
                'stock_supply', 'user_generate_request')
            self.user.write(cron_user, {
                'main_company': company_id,
                'company': company_id,
                })

            # Setup the chart of accounts which will setup useful accounts
            # required to create party and purchase
            self.setup_chart_of_accounts(company_id)
            payable_id, = self.account.search([('kind', '=', 'payable')])
            receivable_id, = self.account.search([('kind', '=', 'receivable')])
            account_expense, = self.account.search([('kind', '=', 'expense')])

            currency_id = self.company.read(company_id,
                    ['currency'])['currency']
            payment_term = self.payment_term.create({
                'name': 'Default',
                'lines': [
                    ('create', {'type': 'remainder'})
                ]
                })

            # Create a product to test
            product_id = self.product.create({
                'name': 'Test Move.update_planned_dates',
                'type': 'stockable',
                'category': category_id,
                'cost_price_method': 'fixed',
                'default_uom': unit_id,
                'purchase_uom': unit_id,
                'purchasable': True,
                'account_expense': account_expense,
                })

            # Create two parties one with the update flag and other without it
            party_wo_update_id = self.party.create({
                'name': 'Test Party w/o update flag',
                'update_planned_date': False,
                'account_receivable': receivable_id,
                'account_payable': payable_id,
                })
            party_wo_update = self.party.browse(party_wo_update_id)
            party_with_update_id = self.party.create({
                'name': 'Test Party with update flag',
                'account_receivable': receivable_id,
                'account_payable': payable_id,
                })
            party_with_update = self.party.browse(party_with_update_id)

            today = datetime.date.today()
            past_date = today + relativedelta(days=-5)

            # Create purchases on the past date
            ids = []
            default_values = {
                'company': company_id,
                'warehouse': warehouse_id,
                'currency': currency_id,
                'lines': [
                    ('create', {
                        'type': 'line',
                        'quantity': 1,
                        'unit': unit_id,
                        'product': product_id,
                        'unit_price': Decimal('1'),
                        'description': 'Test Purchase',
                        })
                ]
            }
            # Create first order with party w/o update flag
            values = default_values.copy()
            values['party'] = party_wo_update.id
            values['invoice_address'] = party_wo_update.addresses[0].id
            ids.append(self.purchase.create(values))
            # Create second order with party who has update flag
            values = default_values.copy()
            values['party'] = party_with_update.id
            values['invoice_address'] = party_with_update.addresses[0].id
            ids.append(self.purchase.create(values))
            # Confirm both orders
            with Transaction().set_context(company=company_id):
                self.purchase.workflow_trigger_validate(ids, 'quotation')
                self.purchase.workflow_trigger_validate(ids, 'confirm')

            orders = self.purchase.browse(ids)
            move_ids = self.move.search([])
            self.move.write(move_ids, {'planned_date': past_date})
            moves = self.move.browse(move_ids)

            # Do the tests
            self.assertEqual(len(moves), 2)
            for move in moves:
                self.assertEqual(move.planned_date, past_date)

            cron_user = self.ir_model_data.get_id(
                'stock_supply', 'user_generate_request')

            with Transaction().set_user(cron_user):
                self.move.update_supply_planned_date()

            # Re-read the browse record
            moves = self.move.browse(move_ids)

            past_moves = self.move.search([
                    ('state', '=', 'draft'),
                    ('planned_date', '<', today),
                    ])
            self.assertEqual(len(past_moves), 1)
            past_move = self.move.browse(past_moves[0])
            self.assertEqual(past_move.supplier.update_planned_date, False)

            self.assertEqual(
                self.move.search([
                        ('state', '=', 'draft'),
                        ('planned_date', '<=', today),
                    ], count=True), 2)


def suite():
    suite = trytond.tests.test_tryton.suite()

    # Needed for the creation of company
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)

    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(MoveUpdateTestCase)
    )
    return suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
