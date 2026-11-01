"""邀约状态机：顺序、分支与首次相处奖励由服务器验证。"""
def allowed(item,state,character):
 return state['affection'][character]>=item.get('min_affection',0) and (not item.get('relationship') or state['relationships'][character]==item['relationship'])
def apply_outing(state,payload,catalog):
 character=payload['character'];story=next(s for s in catalog['invitations']['stories'] if s['character']==character)
 session=state['outings'].get(character,{'node':story['start'],'choices':[],'endings':[]})
 if payload.get('restart'):
  if not isinstance(payload['restart'],bool):raise ValueError('邀约重玩字段无效')
  state['outings'][character]={**session,'node':story['start'],'choices':[]};return
 node=next(n for n in story['nodes'] if n['id']==session['node'])
 if payload['node_id']!=node['id'] or not allowed(node,state,character):raise ValueError('邀约步骤不匹配或未解锁')
 choice=next(c for c in node['choices'] if c['id']==payload['choice_id'])
 target=next(n for n in story['nodes'] if n['id']==choice['next'])
 if not allowed(choice,state,character) or not allowed(target,state,character):raise ValueError('邀约分支尚未解锁')
 # 旧事件没有版本字段，保留当时的零奖励语义。奖励只取服务端目录。
 if payload.get('story_revision') == 2:
  moments=state.setdefault('bond_moments',{}).setdefault(character,[])
  for key in [node['id']]+(['ending'] if target.get('ending') else []):
   moment=story.get('bond_moments',{}).get(key)
   if moment and key not in moments:
    points=state.setdefault('bond_points',{});before=points.get(character,0)
    points[character]=min(catalog['invitations'].get('bond_cap',21),before+moment['points'])
    moments.append(key)
    state['affection'][character]=min(100,state['affection'][character]+points[character]-before)
 endings=list(session['endings'])
 if target.get('ending') and target['id'] not in endings:endings.append(target['id'])
 choices=session['choices']+[choice['id']]
 memories={**session.get('memories',{}),node['id']:session['choices'],target['id']:choices}
 state['outings'][character]={**session,'node':target['id'],'choices':choices,'endings':endings,'memories':memories}
