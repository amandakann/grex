import itertools
import json
import numpy as np
import rbo
from tabulate import tabulate


class RuleDB:
    def __init__(self, treebank_name, ruledict):
        treebank_elements = treebank_name.rsplit('_', 1)
        try:
            self.splitnumber = int(treebank_elements[-1])
            self.treebank = treebank_elements[0]
        except ValueError:
            self.splitnumber = None
            self.treebank = treebank_name
        self.filtered_deps_len = ruledict['filtered_deps_len']
        self.n_yes = ruledict['n_yes']
        self.seed = ruledict['seed']
        self.intercepts = ruledict['intercepts']
        self.rules = ruledict['rules']

    def list_rules(self):
        return [rule['pattern'] for rule in self.rules]

def parse_json(json_file):
    treebanks = []
    with open(json_file) as f:
        data = json.load(f)
        for treebank in data:
            treebanks.append(RuleDB(treebank, data[treebank]))
    return treebanks

def rbo_sim(r1, r2):
    return rbo.RankingSimilarity(r1.list_rules(), r2.list_rules()).rbo(p=0.75)

if __name__ == '__main__':
    jsonfiles = ['output/table2_15k_16split.json']
    top_rules = 5
    treebanks = [treebank for f in jsonfiles for treebank in parse_json(f)]
    grouped_treebanks = {key: list(group) for key, group in itertools.groupby(treebanks, key=lambda x: x.treebank)}
    for treebank, splits in grouped_treebanks.items():
        print(f'{treebank} ({len(splits)} splits of {splits[0].filtered_deps_len} dependencies)')
        rbo_values = [rbo_sim(*comb) for comb in itertools.combinations(splits, 2)]
        print(f'-RBO: mean {round(sum(rbo_values)/len(rbo_values),4)}, std {round(np.std(rbo_values),4)}')
        print('---')
        print(f'top {top_rules} rules:')
        rule_table = []
        rule_table.append([f'split {s.splitnumber}' for s in splits])
        for i in range(top_rules):
            rule_table.append([s.rules[i]['pattern'] for s in splits])
        print(tabulate(rule_table, headers='firstrow'))
        