import json
import os
import pyconll

def enrich_extraction(extraction, supplement):
    ids = set(supplement['sent_ids'])
    directory = '/Users/amanda/data/sud-treebanks-v2.14/SUD_Spanish-AnCora/'
    for corpus in [f for f in os.listdir(directory) if f.endswith('.conllu')]:
        for sentence in pyconll.iter_from_file(directory + corpus):
            if sentence.id in ids:
                pass
    return extraction


def main(input_file):
    output = dict()
    # Load the extraction
    with open(input_file, "r") as f:
        extraction = json.load(f)

    # Load the supplement
    with open(input_file[:-5] + '_supplement.json', "r") as f:
        supplement = json.load(f)

    assert len(extraction) == len(supplement)
    for corpus in extraction.keys():
        output[corpus] = enrich_extraction(extraction[corpus], supplement[corpus])
        print(f"{output[corpus]['rules'][0]['pattern']}: {output[corpus]['rules'][0]['n_pattern_positive_occurence']}/{output[corpus]['rules'][0]['n_pattern_occurence']}")
    # Save the enriched extraction
    # with open(input_file[:-5] + '_enriched.json', "w") as f:
    #     json.dump(extraction, f)

if __name__ == "__main__":
    main("output/table2_1k_test2.json")
