import collections
import os
import sys
import glob
import json
import random

import numpy as np
from scipy.stats import chisquare
import scipy
import skglm

import pyximport
pyximport.install()
import pyautogramm.features

import pyautogramm.data
import time

def extractor(filtered_deps,
        feature_predicate,
        feature_name,
        feature_value,
        alphas,
        seed,
        max_degree=2,
        min_feature_occurence=5):
    feature_set = pyautogramm.features.FeatureSet()

    feature_set.add_feature(pyautogramm.features.AllSingletonFeatures(
        predicate=lambda name: (feature_predicate(1, name) and name != feature_name)
    ))
    for degree in range(2, max_degree + 1):
        feature_set.add_feature(pyautogramm.features.AllProductFeatures(
            degree=degree,
            min_occurences=min_feature_occurence,
            predicate=lambda name, degree=degree: (feature_predicate(degree, name) and name != feature_name)
        ))

    feature_set.init_from_data(filtered_deps)
    X = feature_set.build_features(filtered_deps, sparse=True)
    if X.shape[1] == 0:
        raise RuntimeError("No extracted feature")

    # build targets
    y = np.empty((len(filtered_deps),))
    for i, dep in enumerate(filtered_deps):
        assert type(dep[feature_name]) == str
        y[i] = 1 if dep[feature_name] == feature_value else 0

    filtered_deps_len = len(filtered_deps)
    n_yes = int(y.sum())
    extraction = dict()
    extraction["filtered_deps_len"] = filtered_deps_len
    extraction["n_yes"] = n_yes
    extraction["seed"] = seed
    extraction["intercepts"] = list()

    # extract rules
    all_rules = set()
    ordered_rules = list()

    for j, alpha in enumerate(alphas):
        print(f"Extracting rules ({j+1} / {len(alphas)})", flush=True)
        model = skglm.SparseLogisticRegression(
            alpha=alpha,
            fit_intercept=True,
            max_iter=20,
            max_epochs=1000,
        )
        model.fit(X, y)
        extraction["intercepts"].append((alpha, model.intercept_))

        for name, (value, idx) in feature_set.feature_weights(model.coef_[0]).items():
            if name not in all_rules:
                all_rules.add(name)
                col = np.asarray(X[:, idx].todense())
                idx_col = col.squeeze(1)

                with_feature_selector = idx_col > 0
                without_feature_selector = np.logical_not(with_feature_selector)

                matched = y[with_feature_selector]
                n_matched = len(matched)
                n_pattern_positive_occurence = matched.sum()
                n_pattern_negative_occurence = n_matched - n_pattern_positive_occurence

                mu = (n_yes/filtered_deps_len)
                a = (n_pattern_positive_occurence/n_matched)
                gstat =  2 * n_matched * (
                        ( (a * np.log(a)) if a > 0 else 0) - a * np.log(mu)
                        + ( ((1 - a) * np.log(1 - a)) if (1 - a) > 0 else 0) - (1 - a) * np.log(1 - mu)
                        )
                p_value = 1 - scipy.stats.chi2.cdf(gstat,1)
                cramers_phi = np.sqrt((gstat/n_matched))

                expected = (n_matched*n_yes) / filtered_deps_len
                delta_observed_expected = n_pattern_positive_occurence - expected

                if n_pattern_positive_occurence/n_matched > int(y.sum())/filtered_deps_len:
                    decision = 'yes'
                    coverage = (n_pattern_positive_occurence/n_yes)*100
                    presicion = (n_pattern_positive_occurence/n_matched)*100
                else:
                    decision = 'no'
                    coverage = (n_pattern_negative_occurence/(filtered_deps_len - n_yes))*100
                    presicion = (n_pattern_negative_occurence/n_matched)*100
                
                ordered_rules.append({
                    "pattern": ",".join(sorted(name.split(","))),
                    "n_pattern_occurence": idx_col.sum(),
                    "n_pattern_positive_occurence": n_pattern_positive_occurence,
                    "decision": decision,
                    "alpha": alpha,
                    "value": value,
                    "coverage": coverage,
                    "precision": presicion,
                    "delta": delta_observed_expected,
                    "g-statistic": gstat,
                    "p-value": p_value,
                    "cramers_phi": cramers_phi
                })

    extraction["rules"] = ordered_rules
    return(extraction)

def feature_activation_rule_extractor(
        sud_path,
        output_path,
        dependency_predicate,
        feature_predicate,
        feature_name,
        feature_value,
        alphas,
        dep_constraint,
        seed,
        splits=1,
        max_degree=2,
        min_feature_occurence=5,
        treebank_filters=None,
        error_stream=sys.stderr
):
    treebank_paths = glob.glob(os.path.join(sud_path, "*"))

    # filter
    if treebank_filters is not None:
        treebank_paths = [path for path in treebank_paths if any(path.find(f) > 0 for f in treebank_filters)]

    extracted_data = dict()
    for i, treebank_path in enumerate(treebank_paths):
        treebank_name = os.path.basename(treebank_path)

        # find all conllu files for treebank
        conllu_paths = glob.glob(os.path.join(treebank_path, "*.conllu"))
        if len(conllu_paths) == 0:
            print("Skipping treebank %s because there is no conllu file!" % treebank_name, file=error_stream, flush=True)
            continue

        output_pre = "%s\t(%i / %i):\t" % (treebank_name, i+1, len(treebank_paths))

        # Read data
        print("%s%s" % (output_pre, "reading data"), flush=True)
        deps = list()
        for conllu_path in conllu_paths:
            data = pyautogramm.data.read(conllu_path)
            deps.extend(
                pyautogramm.data.extract_dependencies(
                    data,
                    split_head_rel=True,
                    add_closed_pos_tags_lemma=True,
                    add_similar_pos_tags=True
                )
            )

        # filter deps
        print("%s%s" % (output_pre, "filtering dependencies"), flush=True)
        filtered_deps = list()
        for dep in deps:
            if dependency_predicate(dep) and feature_name in dep:
                filtered_deps.append(dep)

        if len(filtered_deps) == 0:
            print("Skipping treebank %s because there is no dependency to analyse!" % treebank_name, file=error_stream, flush=True)
            continue

        print("%s%s" % (output_pre, "Number of dependencies after filtering: %i / %i" % (len(filtered_deps), len(deps))), flush=True)

        if dep_constraint > 0:
            print("%s%s" % (output_pre, f"constraining data to {dep_constraint} dependencies (random seed {seed})"), flush=True)
            if len(filtered_deps) < dep_constraint:
                print(f"Treebank {treebank_name} has fewer dependencies than specified constraint! ({len(filtered_deps)} / {dep_constraint})", file=error_stream, flush=True)
            else:
                random.seed(a=seed)
                filtered_deps = random.sample(population=filtered_deps, k=dep_constraint)

        # Split filtered_deps into 3 equal parts
        if splits > 1:
            split_size = len(filtered_deps) // splits
            print(f"splitting data into {splits} parts of size {split_size}", flush=True)
            split_deps = [filtered_deps[i * split_size:(i + 1) * split_size] for i in range(splits)]
            for j, split in enumerate(split_deps):
                print(f"extracting features for split {j+1} / {splits}", flush=True)
                try:
                    extracted_data[treebank_name + f"_{j+1}"] = extractor(split, feature_predicate, feature_name, feature_value, alphas, seed, max_degree, min_feature_occurence)
                except RuntimeError:
                    print(f"Skipping treebank {treebank_name} (split {j+1}) because there is no extracted feature!", file=error_stream, flush=True)
                    continue

        # extract features
        else:
            print("%s%s" % (output_pre, "extracting features"), flush=True)
            try:
                extracted_data[treebank_name] = extractor(filtered_deps, feature_predicate, feature_name, feature_value, alphas, seed, max_degree, min_feature_occurence)
            except RuntimeError:
                print("Skipping treebank %s because there is no extracted feature!" % treebank_name, file=error_stream, flush=True)
                continue


    print("Done.", flush=True)
    with open(output_path, 'w') as out_stream:
        json.dump(extracted_data, out_stream)
