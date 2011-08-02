# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView


class PurchaseRequest(ModelSQL, ModelView):
    _name = 'purchase.request'

    def generate_requests(self):
        move_obj = self.pool.get('stock.move')
        move_obj.update_supply_planned_date()
        return super(PurchaseRequest, self).generate_requests()

PurchaseRequest()
