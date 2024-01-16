# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name": "Most Buying Products",
    "version": "17.0.0.0",
    "category": "Extra Tools",
    "summary": "Print most buying product xls report top buying product pdf report most purchased product report most sold products top buying products most buying product excel report top buying product report most buying purchase product report top buying products",
    "description": """The Most Buying Product Odoo app designed to provide businesses with valuable insights into their sales patterns by generating comprehensive reports on the most frequently buying products. The app allowing businesses to define the time range for analysis and option to generate report by product, product category and product price, User also have option to limit record in report.""",
    "license": "OPL-1",
    "author": "BrowseInfo",
    "website": "https://www.browseinfo.com",
    "depends": ["base",
                "crm",
                "sale",
                "account",
                "purchase",
                "sale_management",
                "sale_purchase_stock",
                ],
    "data": [
            "security/ir.model.access.csv",
            "wizard/top_product_wizard_view.xml",
            "wizard/save_file_wizard_view.xml",
            "views/purchase_order_view.xml",
            "report/top_product_report_template.xml",
            "report/top_product_report.xml",
        ],

    "auto_install": False,
    "application": True,
    "installable": True,
    'live_test_url':'https://youtu.be/hFgGdnCcB6Q',
    "images":['static/description/Most-Buying-Product.gif'],
}


