#!/usr/bin/python
"""
    Author: Fabio Hellmann <info@fabio-hellmann.de>
"""

from flask_restplus import Namespace, Resource, fields, reqparse

from ..core.rf.rx_service import RxService
from ..core.rf.tx_service import TxService

rx_service = RxService()
tx_service = TxService()

ns_rf = Namespace('rf', description='The radio frequency interface')

protocol_model = ns_rf.model('Protocol', {
    'pulselength': fields.Integer(readOnly=True, description='The pulse length of this protocol'),
    'sync_high': fields.Integer(readOnly=True, description='The sync high of this protocol'),
    'sync_low': fields.Integer(readOnly=True, description='The sync low of this protocol'),
    'zero_high': fields.Integer(readOnly=True, description='The zero high of this protocol'),
    'zero_low': fields.Integer(readOnly=True, description='The zero low of this protocol'),
    'one_high': fields.Integer(readOnly=True, description='The one high of this protocol'),
    'one_low': fields.Integer(readOnly=True, description='The one low of this protocol')
})

signal_model = ns_rf.model('Signal', {
    'time': fields.DateTime(readOnly=True, description='The time when the signal was received'),
    'code': fields.Integer(readOnly=True, description='The code of the received signal'),
    'pulselength': fields.Integer(readOnly=True, description='The pulse length the signal was received over'),
    'bit_length': fields.Integer(readOnly=True, description='The bit length of the received signal'),
    'protocol': fields.Nested(protocol_model, skipNone=False, allow_null=False, readOnly=True,
                              description='The protocol of the received signal')
})

get_parser = reqparse.RequestParser()
get_parser.add_argument('since', type=int)

post_parser = reqparse.RequestParser()
post_parser.add_argument('signal', type=signal_model, required=True, location='form')


@ns_rf.route('/signals')
class SignalResource(Resource):

    @ns_rf.param('since', 'The time since when the signals should be fetched')
    @ns_rf.marshal_list_with(signal_model)
    def get(self):
        args = get_parser.parse_args()
        since = args['since']
        return rx_service.get_results(since)

    @ns_rf.response(201, 'Signal send successful')
    @ns_rf.response(500, 'Failed to send signal')
    @ns_rf.expect(post_parser, validate=True)
    def post(self):
        args = post_parser.args()
        signal = args['signal']
        if tx_service.send(signal):
            return None, 201
        return None, 500
