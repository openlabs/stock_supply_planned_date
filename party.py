# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.model import ModelSQL, ModelView,fields


class Party(ModelSQL, ModelView):
    _name = 'party.party'

    update_planned_date = fields.Boolean('Update Planned Date',
        help="Flag to indicate if draft purchase stock moves "
            "from the party should be updated to current date automatically."
        )

    def default_update_planned_date(self):
        return True

Party()
