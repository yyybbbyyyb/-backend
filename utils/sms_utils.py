from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import RpcRequest
from backend.settings import ALIYUN_SMS
import json


def send_sms(phone_numbers, template_params, sign_name=None, template_code=None):
    client = AcsClient(
        ALIYUN_SMS['access_key_id'],
        ALIYUN_SMS['access_key_secret']
    )
    request = RpcRequest('Dysmsapi', '2017-05-25', 'SendSms')
    request.set_method('POST')

    if sign_name is None:
        sign_name = ALIYUN_SMS['sign_name']
    if template_code is None:
        template_code = ALIYUN_SMS['template_code']

    request.add_query_param('PhoneNumbers', phone_numbers)
    request.add_query_param('SignName', sign_name)
    request.add_query_param('TemplateCode', template_code)
    request.add_query_param('TemplateParam', template_params)

    response = client.do_action_with_exception(request)

    return json.loads(response.decode('utf-8'))
