from xml.etree import ElementTree as ET
from contextlib import ExitStack
import os
import warnings
import pyconll
import stanza
from tqdm import tqdm


def parse(fin_path, fout_path, source_langs, target_langs, nlp):
    with open(fout_path, 'w', encoding='utf-8') as fout:
        tree = ET.parse(fin_path)
        root = tree.getroot()
        for chapter in tqdm(root, desc=f'Processing chapters in {os.path.basename(fin_path)}', leave=False):
            for turn in tqdm(chapter, desc=f'Processing turns in ch {chapter.get("id")}', leave=False):
                for speaker in turn:
                    source_lang = speaker.get('language', 'xx')
                    if isinstance(source_lang, str) and len(source_lang) != 2:
                        source_lang = 'xx'
                    for text in speaker.iter('text'):
                        target_lang = text.get('language', 'xx')
                        if target_lang in target_langs and source_lang in source_langs:
                            docs = [p.text for p in text.iter('p') if p.text]
                            out_docs = nlp.bulk_process(docs)
                            for d_idx, doc in enumerate(out_docs):
                                for s_idx, sentence in enumerate(doc.sentences):
                                    fout.write(f'# sent_id = {root.get("date")}.{chapter.get("id")}.{turn.get("id")}.{d_idx+1}.{s_idx+1}\n')
                                    fout.write(f'# source_lang = {source_lang}\n')
                                    fout.write(f'# text = {sentence.text}\n')
                                    for word in sentence.words:
                                        fout.write(f'{word.id}\t{word.text}\t{word.lemma}\t{word.upos}\t{word.xpos}\t{word.feats}\t{word.head}\t{word.deprel}\t_\t_\n') # TODO: replace None values with '_'
                                    fout.write('\n')

def by_source(conllu_path, by_source_files):
    try:
        fin = pyconll.load_from_file(conllu_path)
    except:
        print(f'Error parsing {conllu_path}')
        return
    for sent in fin:
        source_lang = sent.meta_value('source_lang')
        by_source_files[source_lang].write(sent.conll() + '\n\n')

def main(): 
    warnings.simplefilter(action='ignore', category=FutureWarning)

    in_dir = '/Users/amanda/data/costep_1.0.1' 
    out_dir = '/Users/amanda/data/costep_1.0.1_sv'
    fins = [os.path.join(in_dir, f) for f in os.listdir(in_dir) if f.endswith('.xml')]

    source_langs = ['da', 'fr', 'hu', 'sv']
    target_langs = ['sv']

    nlp = stanza.Pipeline(lang='sv', processors='tokenize,pos,lemma,depparse')
    
    for fin_path in tqdm(fins, desc='Processing files'):
        fout_path = os.path.join(out_dir, os.path.splitext(os.path.basename(fin_path))[0] + '.conllu')
        if not os.path.exists(fout_path):
            parse(fin_path, fout_path, source_langs, target_langs, nlp)

    by_source_dir = os.path.join(out_dir, 'by_source')
    os.makedirs(by_source_dir, exist_ok=True)
    conllus = [os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.endswith('.conllu')]

    with ExitStack() as stack:
        by_source_files = {source_lang: stack.enter_context(open(os.path.join(by_source_dir, f'{source_lang}_sv.conllu'), 'w', encoding='utf-8')) for source_lang in source_langs}
        for conllu_path in tqdm(conllus, desc=f'Splitting by source language'):
            if os.stat(conllu_path).st_size > 0:
                by_source(conllu_path, by_source_files)



if __name__ == '__main__':
    main()
