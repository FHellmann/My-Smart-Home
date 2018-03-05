#!/usr/bin/python
"""
    Author: Fabio Hellmann <info@fabio-hellmann.de>
"""

from flask_restplus import Resource, fields

from . import api
from ..core.rf.rx_service import RxService
from ..core.rf.tx_service import TxService

rx_service = RxService()
tx_service = TxService()

api_rf = api.namespace('/rf', description='The radio frequency interface')

protocol_model = api.model('Protocol', {
    'pulselength': fields.Integer(readOnly=True, description='The pulse length of this protocol'),
    'sync_high': fields.Integer(readOnly=True, description='The sync high of this protocol'),
    'sync_low': fields.Integer(readOnly=True, description='The sync low of this protocol'),
    'zero_high': fields.Integer(readOnly=True, description='The zero high of this protocol'),
    'zero_low': fields.Integer(readOnly=True, description='The zero low of this protocol'),
    'one_high': fields.Integer(readOnly=True, description='The one high of this protocol'),
    'one_low': fields.Integer(readOnly=True, description='The one low of this protocol')
})

signal_model = api.model('Signal', {
    'time': fields.Integer(readOnly=True, description='The time when the signal was received'),
    'code': fields.Integer(readOnly=True, description='The code of the received signal'),
    'pulselength': fields.Integer(readOnly=True, description='The pulse length the signal was received over'),
    'bit_length': fields.Integer(readOnly=True, description='The bit length of the received signal'),
    'protocol': fields.Nested(protocol_model, skipNone=False, allow_null=False, readOnly=True,
                              description='The protocol of the received signal')
})


@api.response(404, 'No Signal found')
@api_rf.route('/signals')
class SignalResource(Resource):

    @api_rf.route('/<int:since>')
    @api_rf.marshal_list_with(signal_model)
    def get(self, since):
        return rx_service.get_results(since)

    @api_rf.response(201, 'Signal send successful')
    @api_rf.response(500, 'Failed to send signal')
    @api_rf.expect(signal_model, validate=True)
    @api_rf.marshal_with(signal_model)
    def post(self, signal):
        if tx_service.send(signal):
            return None, 201
        return None, 500
