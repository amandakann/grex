from xml.etree import ElementTree as ET
import sys
from collections import Counter
import re
import pandas as pd

def main():
    re_word = re.compile(r'\w+')
    filenames = sys.argv[1:]
    paragraph_counts = Counter()
    word_counts = Counter()
    for filename in filenames:
        tree = ET.parse(filename)
        root = tree.getroot()
        for speaker in root.iter('speaker'):
            source_lang = speaker.get('language', 'xx')
            if isinstance(source_lang, str) and len(source_lang) != 2:
                source_lang = 'xx'
            for text in speaker.iter('text'):
                target_lang = text.get('language', 'xx')
                n_words = 0
                n_paragraphs = 0
                for p in text.iter('p'):
                    n_paragraphs += 1
                    if p.text:
                        n_words += len(re_word.findall(p.text))
                paragraph_counts[(source_lang, target_lang)] += n_paragraphs
                word_counts[(source_lang, target_lang)] += n_words
    #print(paragraph_counts)
    #print(word_counts)

    source_langs = sorted({source_lang for source_lang, _ in word_counts})
    target_langs = sorted({target_lang for _, target_lang in word_counts})
    df = pd.DataFrame.from_dict({
        source_lang: [word_counts[source_lang, target_lang]
                       for target_lang in target_langs]
        for source_lang in source_langs},
                            columns=target_langs, orient='index')
    print(df)
    df.to_csv('costep.csv')

if __name__ == '__main__':
    main()

