import json,unittest
from pathlib import Path
from web.backend.skill_interactions import evaluate_interaction

class SkillInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c=json.loads((Path(__file__).resolve().parents[2]/'data/curriculum/catalog.json').read_text(encoding='utf-8'))
        cls.points=[p for p in c['points'] if p.get('interaction',{}).get('type')!='reasoning_clues' and p.get('interaction')]

    def test_structure_requires_each_card_once(self):
        spec=next(p['interaction'] for p in self.points if p['interaction']['type']=='structure_order')
        self.assertTrue(evaluate_interaction(spec,spec['solution']))
        self.assertFalse(evaluate_interaction(spec,list(reversed(spec['solution']))))
        with self.assertRaises(ValueError):evaluate_interaction(spec,[spec['solution'][0]]*3)

    def test_mapping_rejects_duplicates_and_missing_functions(self):
        for p in self.points:
            spec=p['interaction']
            if spec['type']=='structure_order':continue
            self.assertTrue(evaluate_interaction(spec,spec['solution']))
            invalid={k:next(iter(spec['solution'].values())) for k in spec['solution']}
            with self.assertRaises(ValueError):evaluate_interaction(spec,invalid)
            with self.assertRaises(ValueError):evaluate_interaction(spec,{})

if __name__=='__main__':unittest.main()
