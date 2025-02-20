# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timedelta


class InvoiceReportXlsx(models.AbstractModel):
    _name = "report.flex_detailed_partner_ledger.report_dpl_xlsx"
    _inherit = 'report.report_xlsx.abstract'
    _description = "Detailed partner ledger"

    def _get_initial_balance(self, partner_id, to_date):
        domain = [
            ('company_id', '=', self.env.company.id),
            ('partner_id', '=', partner_id),
            ('parent_state', '=', 'posted'),
            ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
            ('date', '<', to_date)
        ]
        initial_balance = self.env["account.move.line"].read_group(
            domain=domain,
            fields=["balance:sum"],
            groupby=["partner_id"],
        )
        return initial_balance and initial_balance[0]['balance'] or 0


    def generate_xlsx_report(self, workbook, data, objs):
        date_from_str = data['form'].get('date_from', False)
        date_to_str = data['form'].get('date_to', False)
        partner_id = data['form'].get('partner_id', False)
        partner = self.env['res.partner'].browse(partner_id[0])
        base_domain = [
            ('move_id.company_id', '=', self.env.company.id),
            ('move_id.state', '=', 'posted'),
        ]
        initial_balance = 0
        if date_from_str:
            base_domain += [('date', '>=', date_from_str)]
            initial_balance = self._get_initial_balance(partner.id, date_from_str)
        if date_to_str:
            base_domain += [('date', '<=', date_to_str)]
        domain_inv = base_domain + [
            ('move_id.partner_id', '=', partner.id),
            ('move_id.move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']),
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
                # 'debit': line.credit,
                # 'credit': line.debit,
                # 'balance': -line.balance,
                'debit': line.price_total if line.move_type in ('out_invoice', 'in_refund') else 0,
                'credit': line.price_total if line.move_type in ('in_invoice', 'out_refund') else 0,
                'balance': line.price_total * (1 if line.move_type in ('out_invoice', 'in_refund') else -1),
            })
        domain_entry = base_domain + [
            ('partner_id', '=', partner.id),
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
            lines_by_move_id.setdefault((line['move_id']),
                                        {'lines': [], 'total_debit': 0, 'total_credit': 0, 'total_balance': 0})
            lines_by_move_id[line['move_id']]['lines'].append(line)
            lines_by_move_id[line['move_id']]['total_debit'] += line['debit']
            lines_by_move_id[line['move_id']]['total_credit'] += line['credit']
            lines_by_move_id[line['move_id']]['total_balance'] += line['balance']
        line_groups = sorted(lines_by_move_id.values(), key=lambda group: group['lines'][0]['date'], reverse=False)
        data = {
            'partner_name': partner.name,
            'partner_code': 'partner_code' in partner and partner.partner_code or '',
            'date_from': date_from_str,
            'date_to': date_to_str,
            'company_name': self.env.company.name,
            # 'currency_name': self.env.company.currency_id.name,
            # 'current_year': fields.Date.today().year,
            # 'current_date': fields.Date.today(),
            # 'current_time': fields.Datetime.now().strftime('%I:%M %p'),
            'initial_balance': initial_balance,
            'line_groups': line_groups,
            # 'lines_by_move_id': lines_by_move_id,

        }

        sheet = workbook.add_worksheet("Detailed Partner Ledger")
        format_filters = workbook.add_format(
            {'font_size': 10, 'bold': True, 'align': 'center', 'bg_color': '#BFBFBF', 'font_color': 'black',
             'valign': 'vcenter', 'border': 1, 'border_color': 'silver'})
        header = workbook.add_format(
            {'font_size': 10, 'bold': True, 'align': 'center', 'bg_color': '#34618E', 'font_color': 'white',
             'valign': 'vcenter', 'border': 1})
        bl_init = workbook.add_format(
            {'font_size': 10, 'bold': False, 'align': 'center', 'bg_color': '#CFCFCF', 'font_color': 'black',
             'border': 1})
        bl_init.set_left(5)
        bl_init.set_left_color('red')
        body1 = workbook.add_format(
            {'font_size': 10, 'bold': False, 'align': 'center', 'bg_color': '#deecec', 'border': 1})
        body2 = workbook.add_format(
            {'font_size': 10, 'bold': False, 'align': 'center', 'bg_color': 'white', 'border': 1})

        sheet.right_to_left()
        sheet.set_column('A:A', 25)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:H', 15)
        sheet.merge_range('A1:H1', 'Detailed Partner Ledger', header)

        # sheet.write(4, 0, 'From', body1)
        sheet.write('A2', 'اسم العميل', format_filters)
        sheet.merge_range('B2:C2', f"{partner.display_name or ''}", format_filters)

        sheet.write('A3', 'من تاريخ', format_filters)
        sheet.merge_range('B3:C3', f"{date_from_str or ''}", format_filters)

        # sheet.write(4, 0, 'From', body1)
        sheet.write('F2', 'الرصيد الافتتاحي', format_filters)
        sheet.merge_range('G2:H2', f"{data['initial_balance'] or ''}", format_filters)

        sheet.write('F3', 'الي تاريخ', format_filters)
        sheet.merge_range('G3:H3', f"{date_to_str or ''}", format_filters)

        row = 4
        col = 0
        sheet.write(row, col, 'مستند \n تاريخ \n حركة', header)
        sheet.write(row, col+1, 'اسم الصنف', header)
        sheet.write(row, col+2, 'الكمية', header)
        sheet.write(row, col+3, 'السعر', header)
        sheet.write(row, col+4, 'القيمة', header)
        sheet.write(row, col+5, 'مدين', header)
        sheet.write(row, col+6, 'دائن', header)
        sheet.write(row, col+7, 'رصيد', header)

        accumulated_balance = data['initial_balance']
        row += 1
        body_format = body1
        for group in line_groups:
            first_line = group['lines'][0]
            lines_count = len(group['lines'])
            accumulated_balance += group['total_balance']

            body_format = body_format == body1 and body2 or body1
            if lines_count > 1:
                A_cell = f"A{row+1}:A{row+lines_count}"
                F_cell = f"F{row+1}:F{row+lines_count}"
                G_cell = f"G{row+1}:G{row+lines_count}"
                H_cell = f"H{row+1}:H{row+lines_count}"

            else:
                A_cell = f"A{row+1}"
                F_cell = f"F{row+1}"
                G_cell = f"G{row+1}"
                H_cell = f"H{row+1}"

            if lines_count > 1:
                sheet.merge_range(A_cell, f"{first_line['move_name']} \n {first_line['date']} \n {first_line['journal_name']}", body_format)
            else:
                sheet.write(A_cell, f"{first_line['move_name']} \n {first_line['date']} \n {first_line['journal_name']}", body_format)
            sheet.write(row, col+1, f"{first_line['name']}", body_format)
            sheet.write(row, col+2, f"{first_line['quantity']}", body_format)
            sheet.write(row, col+3, f"{first_line['price_unit']}", body_format)
            sheet.write(row, col+4, f"{first_line['price_total']}", body_format)
            if lines_count > 1:
                sheet.merge_range(F_cell, f"{group['total_debit']}", body_format)
                sheet.merge_range(G_cell, f"{group['total_credit']}", body_format)
                sheet.merge_range(H_cell, f"{accumulated_balance}", body_format)
            else:
                sheet.write(F_cell, f"{group['total_debit']}", body_format)
                sheet.write(G_cell, f"{group['total_credit']}", body_format)
                sheet.write(H_cell, f"{accumulated_balance}", body_format)
            row += 1
            for line in group['lines'][1:]:
                sheet.write(row, col+1, f"{line['name']}", body_format)
                sheet.write(row, col+2, f"{line['quantity']}", body_format)
                sheet.write(row, col+3, f"{line['price_unit']}", body_format)
                sheet.write(row, col+4, f"{line['price_total']}", body_format)
                row += 1
