import json
from pathlib import Path
from typing import Dict, List, Tuple, Union

from pymusas.lexicon_collection import LexiconType, MWELexiconCollection
from pymusas.rankers.lexicon_entry import LexicalMatch, RankingMetaData
from pymusas.taggers.rules.mwe import MWERule


DATA_DIR = Path(__file__, '..', '..', '..', 'data').resolve()
TAGGER_DATA_DIR = Path(DATA_DIR, 'taggers')

BASIC_LEXICON = Path(TAGGER_DATA_DIR, 'mwe_basic_lexicon.tsv')
BASIC_DATA = Path(TAGGER_DATA_DIR, 'rule_based_mwe_basic_input_output.json')

WILDCARD_LEXICON = Path(TAGGER_DATA_DIR, 'mwe_wildcard_lexicon.tsv')
WILDCARD_DATA = Path(TAGGER_DATA_DIR, 'rule_based_mwe_wildcard_input_output.json')


def generate_tag_test_data(test_data_file: Path, mwe_lexicon_file: Path
                           ) -> Tuple[List[str],
                                      List[str],
                                      List[str],
                                      Dict[str, List[str]],
                                      List[List[RankingMetaData]]
                                      ]:
    '''
    Given the test data stored at `test_data_file`, and the MWE lexicon
    at `mwe_lexicon_file`, it returns this data as a Tuple of length 5:

    1. A List of `tokens`, from the `test_data_file`.
    2. A List of `lemmas`, from the `test_data_file`.
    3. A List of `POS tags`, from the `test_data_file`.
    4. The MWE lexicon generated by parsing the `mwe_lexicon_file` to the
    `pymusas.lexicon_collection.MWELexiconCollection.from_tsv` method.
    5. A list of a list of expected
    :class:`pymusas.rankers.lexicon_entry.RankingMetaData` objects.

    # Parameters

    test_data_file : `Path`
        A JSON file containing an Array of Objects. Each object must contain the
        following properties/keys:
        1. token, type str
        2. lemma, type str
        3. pos, type str
        4. ranking_meta_data_objects, type List[List[RankingMetaData]] - This
        has to be written as a JSON object that is then converted to a
        RankingMetaData object in Python.

    mwe_lexicon_file : `Path`
        A TSV file that can be converted into a
        :class:`pymusas.lexicon_collection.MWELexiconCollection` by using the
        class method :func:`pymusas.lexicon_collection.MWELexiconCollection.from_tsv`
    
    # Returns

    `Tuple[List[str], List[str], List[str], Dict[str, List[str]],
           List[List[RankingMetaData]]]`
    '''
    def json_to_ranking_meta_data(json_object: Dict[str, Union[str, int, bool]]
                                  ) -> RankingMetaData:
        
        assert isinstance(json_object['lexicon_type'], str)
        lexicon_type = getattr(LexiconType, json_object['lexicon_type'])
        assert isinstance(lexicon_type, LexiconType)

        n_gram_length = json_object['lexicon_n_gram_length']
        assert isinstance(n_gram_length, int)

        wildcard_count = json_object['wildcard_count']
        assert isinstance(wildcard_count, int)

        exclude_pos_information = json_object['exclude_pos_information']
        assert isinstance(exclude_pos_information, bool)

        assert isinstance(json_object['lexical_match'], str)
        lexical_match = getattr(LexicalMatch, json_object['lexical_match'])
        assert isinstance(lexical_match, LexicalMatch)

        start_index = json_object['token_match_start_index']
        assert isinstance(start_index, int)

        end_index = json_object['token_match_end_index']
        assert isinstance(end_index, int)

        lexicon_entry_match = json_object['lexicon_entry_match']
        assert isinstance(lexicon_entry_match, str)

        return RankingMetaData(lexicon_type, n_gram_length, wildcard_count,
                               exclude_pos_information, lexical_match,
                               start_index, end_index, lexicon_entry_match)
    
    test_tokens: List[str] = []
    test_lemmas: List[str] = []
    test_pos_tags: List[str] = []
    test_ranking_meta_data: List[List[RankingMetaData]] = []
    
    with test_data_file.open('r') as test_data_fp:
        for token_data in json.load(test_data_fp):
            test_tokens.append(token_data['token'])
            test_lemmas.append(token_data['lemma'])
            test_pos_tags.append(token_data['pos'])
            
            token_ranking_meta_data: List[RankingMetaData] = []
            ranking_meta_data_objects = token_data['ranking_meta_data_objects']
            for ranking_object in ranking_meta_data_objects:
                ranking_object = json_to_ranking_meta_data(ranking_object)
                token_ranking_meta_data.append(ranking_object)
            test_ranking_meta_data.append(token_ranking_meta_data)
            
    lexicon_lookup = MWELexiconCollection.from_tsv(mwe_lexicon_file)
    
    return (test_tokens, test_lemmas, test_pos_tags, lexicon_lookup,
            test_ranking_meta_data)


def compare_token_ranking_meta_data(token_ranking_meta_data_1: List[List[RankingMetaData]],
                                    token_ranking_meta_data_2: List[List[RankingMetaData]]
                                    ) -> None:
    '''
    This tests if the two token ranking meta data lists are equal to each other.

    # Raises

    `AssertionError`
        If the two lists are not of same length.
    `AssertionError`
        If each inner list is not of same length.
    `AssertionError`
        If each inner list when converted to a set are not equal to each other.
    '''
    assert len(token_ranking_meta_data_1) == len(token_ranking_meta_data_2)

    index = 0
    for ranking_meta_data_1, ranking_meta_data_2 in zip(token_ranking_meta_data_1,
                                                        token_ranking_meta_data_2):
        assert len(ranking_meta_data_1) == len(ranking_meta_data_2), index
        assert set(ranking_meta_data_1) == set(ranking_meta_data_2), index


def test_mwe_rule__NON_SPECIAL_CASES() -> None:
    '''
    This tests MWE Rule when using only NON SPECIAL CASES, which are direct
    matches, i.e. does not use any special syntax like wildcards.
    '''
    (tokens, lemmas, pos_tags, mwe_lexicon,
     expected_ranking_meta_data) = generate_tag_test_data(BASIC_DATA, BASIC_LEXICON)
    
    # Test that it returns a list of empty lists.
    mwe_rule = MWERule({})
    empty_list: List[List[RankingMetaData]] = [[] for _ in tokens]
    assert empty_list == mwe_rule(tokens, lemmas, pos_tags)

    # Test that it returns a list of one empty list, as we have no tokens to
    # tag
    assert [] == mwe_rule([], [], [])

    # Test that in the case of only tagging one token we have an empty list,
    # as one token is not enough to create a MWE
    assert [[]] == mwe_rule(['test'], ['test'], ['det'])

    # Test that it covers all of the non special syntax cases, e.g. all of the
    # cases that do not contain a wildcard or curly braces.
    mwe_rule = MWERule(mwe_lexicon)
    compare_token_ranking_meta_data(expected_ranking_meta_data,
                                    mwe_rule(tokens, lemmas, pos_tags))


def test_mwe_rules_WILDCARD_CASES() -> None:
    '''
    This tests MWE Rule when using only WILDCARD cases, e.g. `ski_noun *_noun`
    '''
    (tokens, lemmas, pos_tags, mwe_lexicon,
     expected_ranking_meta_data) = generate_tag_test_data(WILDCARD_DATA, WILDCARD_LEXICON)
    
    mwe_rule = MWERule(mwe_lexicon)
    compare_token_ranking_meta_data(expected_ranking_meta_data,
                                    mwe_rule(tokens, lemmas, pos_tags))
