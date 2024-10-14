###########################
# Morphological agreement #
###########################


# 1. Number agreement between a verb (head) and a noun (mod)

# python autogramm_agreement.py \
# 	--treebank /Users/amanda/data/sud-treebanks-v2.14 \
# 	--json html/agreement_verb_noun_number.json \
# 	--error html/agreement_verb_noun_number_errors.txt \
# 	--treebank-filter SUD_French-GSD,SUD_French-ParisStories,SUD_Spanish-AnCora,SUD_English-GUM \
#     --feature1=head.Number \
#     --feature2=dep.Number \
#     --dep-filter=gov.upos=VERB,dep.upos=NOUN \
#     --feature-filter=number,gov.upos,mod.upos


# 2. Number agreement between any head and mod

# python autogramm_agreement.py \
# 	--treebank /Users/amanda/data/sud-treebanks-v2.14 \
# 	--json html/agreement_number.json \
# 	--error html/agreement_number_errors.txt \
# 	--treebank-filter SUD_French-GSD,SUD_French-ParisStories,SUD_Spanish-AnCora,SUD_English-GUM \
#     --feature1=gov.Number \
#     --feature2=dep.Number \
#     --feature-filter=number


#################
# Linearization #
#################


# 1. When is the head in a subj relation before the modifier?

# python autogramm_activation.py \
# 	--treebank /Users/amanda/data/sud-treebanks-v2.14 \
# 	--json html/activation_subj_head_before.json \
# 	--error html/activation_subj_head_before.txt \
# 	--treebank-filter SUD_French-GSD \
#     --feature-name=gov.position \
#     --feature-value=before_dep \
#     --dep-filter=gov.rel_synt=subj \
#     --feature-filter=gov.rel_synt

# 2. When is the head in a comp:obj relation after the modifier?

# python autogramm_activation.py \
# 	--treebank /Users/amanda/data/sud-treebanks-v2.14 \
# 	--json html/activation_comp_obj_head_after_1k.json \
# 	--error html/activation_comp_obj_head_after_1k.txt \
# 	--treebank-filter SUD_French-GSD \
#     --feature-name=gov.position \
#     --feature-value=after_dep \
#     --dep-filter=gov.rel_synt=comp:obj \
#     --feature-filter=gov.rel_synt \
#     --dep-constraint=1000 \
#     --seed=16

#################
#  Replication  #
#################

# Table 2
python autogramm_activation.py \
	--treebank /Users/amanda/data/sud-treebanks-v2.14 \
	--json output/table2_15k_18.json \
	--error output/table2_15k_18.txt \
	--treebank-filter SUD_Spanish-AnCora \
    --feature-name=gov.position \
    --feature-value=after_dep \
    --dep-filter=gov.upos=NOUN,dep.upos=ADJ \
    --feature-filter=gov.rel_synt \
    --dep-constraint=15000 \
    --seed=18

# Table 3 – not quite the same
# python autogramm_activation.py \
# 	--treebank /Users/amanda/data/sud-treebanks-v2.14 \
# 	--json html/table3_1k.json \
# 	--error html/table3_1k.txt \
# 	--treebank-filter SUD_Wolof-WTB \
#     --feature-name=gov.position \
#     --feature-value=before_dep \
#     --dep-filter=gov.rel_synt=comp:obj \
#     --feature-filter=gov.rel_synt \
#     --dep-constraint=1000