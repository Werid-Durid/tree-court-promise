"""讲义课程练习独立判题，保留实际输入，不接受客户端自报正确性。"""
import unicodedata,re
from decimal import Decimal,InvalidOperation
from fractions import Fraction
def normalize(value):return ''.join(unicodedata.normalize('NFKC',str(value)).lower().split()).rstrip('。.!！')
def evaluate(exercise,response):
    if exercise['type']=='choice':
        if type(response) is not int or not 0<=response<len(exercise['choices']):raise ValueError('请选择有效的练习选项')
        return response==exercise['answer']
    if not isinstance(response,str) or not 1<=len(response.strip())<=250:raise ValueError('请填写不超过250字的答案')
    value=normalize(response)
    if value in [normalize(a) for a in exercise.get('accepted_answers',[exercise['answer']])]:return True
    # 高数只解析有限长度的有理数字面量；不 eval 表达式，不接受任意代码或函数。
    if exercise.get('answer_format')=='rational':
        literal=r'[+-]?\d{1,12}(?:/\d{1,12}|\.\d{1,12})?'
        if re.fullmatch(literal,value) and re.fullmatch(literal,str(exercise['answer'])):
            try:return Fraction(value)==Fraction(str(exercise['answer']))
            except (ValueError,ZeroDivisionError):return False
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)',value):return False
    try:return Decimal(value)==Decimal(str(exercise['answer']))
    except InvalidOperation:return False
