from odoo import api, fields, models, _


class CompanyDomain(models.Model):
    _inherit = 'product.category'

    company_id = fields.Many2one(
        'res.company', 'Company', index=True)

    # def _get_current_company(self, **kwargs):
    #     """Get the most appropriate company for this product.
    #
    #     If the company is set on the product, directly return it. Otherwise,
    #     fallback to a contextual company.
    #
    #     :param kwargs: kwargs forwarded to the fallback method.
    #
    #     :return: the most appropriate company for this product
    #     :rtype: recordset of one `res.company`
    #     """
    #     self.ensure_one()
    #     return self.company_id or self._get_current_company_fallback(**kwargs)
    #
    # def _get_current_company_fallback(self, **kwargs):
    #     """Fallback to get the most appropriate company for this product.
    #
    #     This should only be called from `_get_current_company` but is defined
    #     separately to allow override.
    #
    #     The final fallback will be the current user's company.
    #
    #     :return: the fallback company for this product
    #     :rtype: recordset of one `res.company`
    #     """
    #     self.ensure_one()
    #     return self.env.company
