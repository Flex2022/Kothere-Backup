from odoo import fields, models, api, _
from datetime import date, timedelta, datetime
from odoo.tools.misc import xlwt
from io import  BytesIO
import io
import base64



class HrLeaveReportWiz(models.TransientModel):
    _name = 'hr.leave.report.wiz'
    _description = 'Hr Leave Report Wizard'


    def print_hr_leave_report(self):

        filename = 'Hr Leave Report' + '.xls'
        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Hr Leave Report')
        font = xlwt.Font()
        font.bold = True
        for_left = xlwt.easyxf(
            "font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
        multi_record = xlwt.easyxf(
            "font: color black; borders: top double, bottom double, left double, right double; align: horiz center")
        multi_record_center = xlwt.easyxf(
            "font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz center;pattern: pattern solid, fore_colour Blue")
        for_right = xlwt.easyxf(
            "font: bold 1, color black; borders: top double; align: horiz center")
        for_left_noborder = xlwt.easyxf(
            "font: bold 1, color black; borders: top double; align: horiz center")
        for_right_noborder = xlwt.easyxf(
            "font: bold 1, color black; align: horiz center")
        
        data_table = xlwt.easyxf(
            "font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left;pattern: pattern solid, fore_colour Blue ;"
            )
        GREEN_TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 250;'
            'align: vertical center, horizontal center, wrap on;'
            'borders: top double, bottom double, left double, right double;'
        )
        Employee_Details = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 250, color black;'
            'align: vertical center, horizontal left, wrap on;'
            'borders: top double, bottom double, left double, right double;'
        )
        manager_Details = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 250, color blue;'
            'align: vertical center, horizontal left, wrap on;'
            'borders: top double, bottom double, left double, right double;'
        )
        comment = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 250, color blue;'
            'align: vertical center, horizontal left, wrap on;'
            
        )
        style = xlwt.easyxf(
            'font:height 400, bold True, name Arial; align: horiz center, vert center;borders: top medium,right medium,bottom medium,left medium')
    
        alignment = xlwt.Alignment()  # Create Alignment
        alignment.horz = xlwt.Alignment.HORZ_RIGHT
        style = xlwt.easyxf('align: wrap yes')
        style.num_format_str = '0.00'

        hr_leave = self.env['hr.leave'].browse(self._context.get('active_ids',[]))

        if len(hr_leave.ids) == 1:
            worksheet.row(0).height = 500
            worksheet.row(11).height = 500
            worksheet.row(12).height = 500
            worksheet.row(13).height = 500
            worksheet.row(14).height = 500
            worksheet.row(15).height = 500
            worksheet.row(16).height = 500
            worksheet.row(18).height = 700
            worksheet.col(0).width = 15000
            worksheet.col(1).width = 31000
        
            worksheet.write_merge(0, 0, 0, 1, 'Requested Leaves', GREEN_TABLE_HEADER)
            worksheet.write_merge(2, 2, 0, 1, 'Employee Details', Employee_Details)

            row = 3

            worksheet.write(row, 0, 'Name' or '', for_left)
            worksheet.write(row+1, 0, 'Position' or '', for_left)
            worksheet.write(row+2, 0, 'Department' or '', for_left)
            worksheet.write(row+3, 0, 'Email id ' or '', for_left)

            worksheet.write(row, 1, hr_leave.employee_id.name or '', for_left)
            worksheet.write(row+1, 1, hr_leave.employee_id.job_id.name or '', for_left)
            worksheet.write(row+2, 1, hr_leave.employee_id.department_id.name or '', for_left)
            worksheet.write(row+3, 1, hr_leave.employee_id.work_email or '', for_left)


            worksheet.write(row+8, 0, 'Type ' or '', data_table)
            worksheet.write(row+9, 0, 'Description ' or '', data_table)
            worksheet.write(row+10, 0, 'Period ' or '', data_table)
            worksheet.write(row+11, 0, 'Days' or '', data_table)
            worksheet.write(row+12, 0, 'Apply Date' or '', data_table)
            worksheet.write(row+13, 0, 'Status' or '', data_table)

            worksheet.write(row+8, 1, hr_leave.holiday_status_id.name or '', for_left)
            worksheet.write(row+9, 1, hr_leave.name or '', for_left)
            worksheet.write(row+10, 1, str(hr_leave.request_date_from.strftime('%m-%d-%Y')) +' To '+str(hr_leave.request_date_to.strftime('%m-%d-%Y')) or '', for_left)
            worksheet.write(row+11, 1, hr_leave.number_of_days or '', for_left)
            worksheet.write(row+12, 1, str(hr_leave.create_date) or '', for_left)
            worksheet.write(row+13, 1, hr_leave.state or '', for_left)

            worksheet.write_merge(18, 18, 0, 1, 'Manager Response :', manager_Details)
            worksheet.write_merge(19, 22, 0, 1, '', comment)

            worksheet.write(25, 0, 'Manager' or '', for_left_noborder)
            worksheet.write(25, 1, hr_leave.employee_id.name  or '', for_right)
            worksheet.write(26, 1, hr_leave.employee_id.job_id.name or '', for_right_noborder)
        

        if len(hr_leave.ids) > 1:
            worksheet.row(0).height = 500
            worksheet.row(2).height = 500
            worksheet.col(0).width = 7000
            worksheet.col(1).width = 7000
            worksheet.col(2).width = 7000
            worksheet.col(3).width = 7000
            worksheet.col(4).width = 7000
            worksheet.col(5).width = 7000
            worksheet.col(6).width = 7000


            worksheet.write_merge(0, 0, 0, 6, 'Requested Leaves', GREEN_TABLE_HEADER)
            
            row=2
            worksheet.write(row, 0, 'Employee Name' or '', multi_record_center)
            worksheet.write(row, 1, 'Type' or '', multi_record_center)
            worksheet.write(row, 2, 'Description' or '', multi_record_center)
            worksheet.write(row, 3, 'Period' or '', multi_record_center)
            worksheet.write(row, 4, 'Days' or '', multi_record_center)
            worksheet.write(row, 5, 'Apply Date' or '', multi_record_center)
            worksheet.write(row, 6, 'Status' or '', multi_record_center)

            row=3
            for data in hr_leave:
                worksheet.write(row, 0, data.employee_id.name or '', multi_record)
                worksheet.write(row, 1, data.holiday_status_id.name or '', multi_record)
                worksheet.write(row, 2, data.name or '', multi_record)
                worksheet.write(row, 3, str(data.request_date_from.strftime('%m-%d-%Y')) +' To '+str(data.request_date_to.strftime('%m-%d-%Y')) or '', multi_record)
                worksheet.write(row, 4, data.number_of_days or '', multi_record)
                worksheet.write(row, 5, str(data.create_date) or '', multi_record)
                worksheet.write(row, 6, data.state or '', multi_record)
                row+=1


        fp = io.BytesIO()
        workbook.save(fp)
        hr_leave_id = self.env['excel.report'].create({
            'excel_file': base64.encodebytes(fp.getvalue()),
            'file_name': filename
        })
        fp.close()
        
        return{
            'view_mode': 'form',
            'res_id':hr_leave_id.id,
            'res_model': 'excel.report',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }


