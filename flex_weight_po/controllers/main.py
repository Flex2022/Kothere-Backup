import json

from odoo import http
from odoo.http import request


class GetWeigh(http.Controller):

    @http.route('/api/set_weigh', type='json', auth='none', methods=['POST'], csrf=False)
    def set_weigh(self, **kwargs):
        """
        Set the weight for a specific user.
        :param kwargs: Contains the weight and user_id.
        :return: JSON response with success message or error.
        """
        try:

            weight = kwargs.get('weight')
            user_id = kwargs.get('user_id')
            if not weight or not user_id:
                return json.dumps({"error": "Weight and User ID are required."})

            request.env['base.weight.po'].create({
                'weight': weight,
                'user_id': user_id
            })
            return json.dumps({"success": "Weight set successfully."})
        except Exception as e:
            return json.dumps({"error": str(e)})
