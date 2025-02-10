# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DetailedPartnerLedger(models.TransientModel):
    _name = 'detailed.partner.ledger'
    _description = 'Detailed Partner Ledger'

    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    partner_id = fields.Many2one('res.partner', string='Customer / Vendor', required=True)

    def _get_initial_balance(self):
        domain = [
            ('company_id', '=', self.env.company.id),
            ('partner_id', '=', self.partner_id.id),
            ('parent_state', '=', 'posted'),
            ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
            ('date', '<', self.date_from)
        ]
        initial_balance = self.env["account.move.line"].read_group(
            domain=domain,
            fields=["balance:sum"],
            groupby=["partner_id"],
        )
        return initial_balance and initial_balance[0]['balance'] or 0

    def action_print_pdf(self):
        base_domain = [
            ('move_id.company_id', '=', self.env.company.id),
            ('move_id.state', '=', 'posted'),
        ]
        initial_balance = 0
        if self.date_from:
            base_domain += [('date', '>=', self.date_from)]
            initial_balance = self._get_initial_balance()
        if self.date_to:
            base_domain += [('date', '<=', self.date_to)]
        domain_inv = base_domain + [
            ('move_id.partner_id', '=', self.partner_id.id),
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund', 'out_refund', 'in_refund']),
            ('display_type', '=', 'product')
        ]
        move_lines = self.env['account.move.line'].search(domain_inv)
        report_lines = []
        for line in move_lines:
            report_lines.append({
                # 'name': line.product_id.name if line.product_id else 'N/A',
                'name': line.name or '',
                'date': line.date,
                'move_id': line.move_id.id,
                'move_name': line.move_id.name,
                'journal_name': line.journal_id.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'price_total': line.price_total,
                'debit': line.debit,
                'credit': line.credit,
                'balance': line.balance,
            })
        domain_entry = base_domain + [
            ('partner_id', '=', self.partner_id.id),
            ('move_id.move_type', '=', 'entry'),
            ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable'))
        ]
        move_lines = self.env['account.move.line'].search(domain_entry)
        for line in move_lines:
            report_lines.append({
                # 'name': line.product_id.name if line.product_id else 'N/A',
                'name': '',
                'date': line.date,
                'move_id': line.move_id.id,
                'move_name': line.move_id.name,
                'journal_name': line.journal_id.name,
                'quantity': '',
                'price_unit': '',
                'price_total': '',
                'debit': line.debit,
                'credit': line.credit,
                'balance': line.balance,
            })
        lines_by_move_id = {}
        for line in report_lines:
            lines_by_move_id.setdefault((line['move_id']), {'lines': [], 'total_debit': 0, 'total_credit': 0, 'total_balance': 0})
            lines_by_move_id[line['move_id']]['lines'].append(line)
            lines_by_move_id[line['move_id']]['total_debit'] += line['debit']
            lines_by_move_id[line['move_id']]['total_credit'] += line['credit']
            lines_by_move_id[line['move_id']]['total_balance'] += line['balance']
        line_groups = sorted(lines_by_move_id.values(), key=lambda group: group['lines'][0]['date'], reverse=False)
        data = {
            'partner_name': self.partner_id.name,
            'partner_code': 'partner_code' in self.partner_id and self.partner_id.partner_code or '',
            'date_from': self.date_from,
            'date_to': self.date_to,
            'company_name': self.env.company.name,
            # 'currency_name': self.env.company.currency_id.name,
            # 'current_year': fields.Date.today().year,
            # 'current_date': fields.Date.today(),
            # 'current_time': fields.Datetime.now().strftime('%I:%M %p'),
            'initial_balance': initial_balance,
            'line_groups': line_groups,
            # 'lines_by_move_id': lines_by_move_id,

        }
        return self.env.ref('flex_detailed_partner_ledger.action_report_detailed_partner_ledger').with_context(landscape=True).report_action(self, data=data)
