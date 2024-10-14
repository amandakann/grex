import itertools
import json
import rbo

def parse_json(json_file):
    rules = []
    with open(json_file) as f:
        data = json.load(f)
        for corpus in data:
            for rule in data[corpus]['rules']:
                rules.append(rule['pattern'])
    return rules

def rbo_sim(r1, r2):
    return rbo.RankingSimilarity(r1, r2).rbo(p=0.9)

if __name__ == '__main__':
    rules1 = parse_json('output/table2_15k_16.json')
    rules2 = parse_json('output/table2_15k_17.json')
    rules3 = parse_json('output/table2_15k_18.json')
    all_rules = [rules1, rules2, rules3]
    for comb in itertools.combinations(all_rules, 2):
        print(round(rbo_sim(*comb),3))