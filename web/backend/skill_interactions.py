"""校验结构化交互的完整响应，拒绝重复项、未知卡片和自报结果。"""
def evaluate_interaction(spec, response):
    if spec['type']=='structure_order':
        ids=[c['id'] for c in spec['cards']]
        if not isinstance(response,list) or not all(isinstance(x,str) for x in response) or len(response)!=len(ids) or set(response)!=set(ids):
            raise ValueError('请完整排列每张结构卡')
        return response==spec['solution']
    left=[c['id'] for c in spec.get('functions',spec.get('issues',[]))]
    right=[c['id'] for c in spec.get('sentences',spec.get('revisions',[]))]
    if not isinstance(response,dict) or set(response)!=set(left) or not all(isinstance(v,str) for v in response.values()) or set(response.values())!=set(right) or len(response)!=len(right):
        raise ValueError('请完整地一一匹配')
    return response==spec['solution']
