# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.model import ModelSQL, ModelView


class Move(ModelSQL, ModelView):
    _name = 'stock.move'

    def _get_update_planned_date_domain(self):
        """Return the domain expression for selection of moves to update
        planned date.
        """
        ir_date_obj = self.pool.get('ir.date')

        today = ir_date_obj.today()
        return [
            'AND',
            [
                ('from_location.type', '=', 'supplier'),
                ('shipment_in', '=', False),
                ('state', '=', 'draft'),
                ('planned_date', '<', today),
            ],
            [
            'OR', [('purchase_line', '=', False)],
                  [('purchase_line.purchase.party.update_planned_date', '=',
                        True)],
            ]
        ]

    def update_supply_planned_date(self):
        """
        Update the `planned_date` of all moves from a supplier location
        which have a `planned_date` before today to the current date.
        """
        ir_date_obj = self.pool.get('ir.date')

        today = ir_date_obj.today()
        domain = self._get_update_planned_date_domain()
        moves_to_update_ids = self.search(domain)
        self.write(moves_to_update_ids, {'planned_date': today})

Move()
