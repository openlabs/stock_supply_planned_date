# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.


{
    "name" : "Stock Update Planned Date",
    "version" : "2.0.0.1",
    "author" : "Openlabs Technologies & Consulting (P) Limited",
    'email': 'info@openlabs.co.in',
    'website': 'http://www.openlabs.co.in/',
    "description": """Updates planned date of late incoming stock moves.""",
    "depends" : [
        "stock_supply",
        "ir",
    ],
    "xml" : [
        "party.xml",
        "move.xml",
    ],
    'translation': [
    ],
}
