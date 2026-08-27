"""
Lab 1.

Language detection
"""

# pylint:disable=unused-argument
import json
from typing import Sequence

FreqDictType = dict[str, float]
"""Type alias for frequency dictionary."""


ProfileType = tuple[str, FreqDictType, int]
"""Type alias for profile of a text."""

# Mark 4.


def tokenize(text: str) -> Sequence[str] | None:
    """
    Splits a text ito tokens, converts the tokens into lowercase,
    removes punctuation and other symbols from words

    Args:
       text (str): Text

    Returns:
        Sequence[str] | None: Sequence of lower-cased tokens without punctuation.
        Returns None if input text is not a string.
    """
    if not isinstance(text, str):
        return None
    invaluable_trash = """`~!@#$%^&*()_-+={[]}|\\:;"\'<,>.?/1234567890"""
    text = text.lower()
    for symbols in invaluable_trash:
        text = text.replace(symbols, "")
    return text.split()


def remove_stop_words(tokens: Sequence[str], stop_words: Sequence[str]) -> Sequence[str] | None:
    """
    Removes stop words

    Args:
        tokens (Sequence[str]): Sequence of tokens
        stop_words (Sequence[str]): Sequence of stop words (can be empty)
    Returns:
        Sequence[str] | None: Sequence of tokens without stop words.
        Returns None in case of incorrect input types.
    """
    if not (isinstance(tokens, Sequence) and isinstance(stop_words, Sequence)):
        return None

    if len(stop_words) > 0 and not all(isinstance(stop, str) for stop in stop_words):
        return None

    new_tokens = []
    for word in tokens:
        if not isinstance(word, str):
            return None
        if word not in stop_words:
            new_tokens.append(word)
    return new_tokens


def calculate_frequencies(tokens: Sequence[str]) -> dict[str, float] | None:
    """
    Calculates frequencies of given tokens

    Args:
        tokens (Sequence[str]): Sequence of tokens
    Returns:
        dict[str, float] | None: Dictionary with frequencies.
        Returns None in case of incorrect input types.
    """
    if not isinstance(tokens, Sequence):
        return None
    frequency_dictionary = {}
    for word in tokens:
        if isinstance(word, str):
            if word not in frequency_dictionary:
                frequency_dictionary[word] = 0
            frequency_dictionary[word] += 1
        else:
            return None

    num_tokens = len(tokens)

    return {key: value / num_tokens for key, value in frequency_dictionary.items()}


def get_top_n_words(freq_dict: dict[str, float], top_n: int) -> Sequence[str] | None:
    """
    Finds the most common words

    Args:
        freq_dict (dict[str, float]): Dictionary with frequencies
        top_n (int): Number of the most common words

    Returns:
        Sequence[str] | None: Sequence of the most common words.
        Returns None in case of incorrect input types.
    """
    if not isinstance(freq_dict, dict) or not isinstance(top_n, int):
        return None
    top_n_words = sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)
    return [k for (k, _) in top_n_words][:top_n]


# Mark 6.


def create_language_profile(
    language: str,
    text: str,
    stop_words: Sequence[str],
) -> ProfileType | None:
    """
    Creates a language profile

    Args:
        language (str): Language name
        text (str): Text
        stop_words (Sequence[str]): Sequence of stop words (can be empty)

    Returns:
        ProfileType | None: Language profile.
        Returns None in case of incorrect input types.
    """
    if (
        not isinstance(language, str)
        or not isinstance(text, str)
        or not isinstance(stop_words, Sequence)
    ):
        return None

    tokens = tokenize(text)
    if tokens:
        tokens = remove_stop_words(tokens, stop_words)

    if not tokens:
        return None

    frequency_dict = calculate_frequencies(tokens)

    if not frequency_dict:
        return None
    return language, frequency_dict, len(frequency_dict.keys())


def check_profile(profile: ProfileType) -> bool:
    """
    Checks profile structure

    Args:
        profile (ProfileType): Profile to check

    Returns:
        bool: Returns True if the profile has right structure and types,
        otherwise returns False.
    """
    if not (
        isinstance(profile, tuple)
        and len(profile) == 3
        and isinstance(profile[0], str)
        and isinstance(profile[1], dict)
        and isinstance(profile[2], int)
    ):
        return False

    if not all(
        isinstance(token, str) and isinstance(freq, float) for token, freq in profile[1].items()
    ):
        return False

    return True


def compare_profiles_by_top_n(
    unknown_profile: ProfileType,
    profile_to_compare: ProfileType,
    top_n: int,
) -> float | None:
    """
    Compares profiles and calculates the distance using top n words

    Args:
        unknown_profile (ProfileType): Unknown profile
        profile_to_compare (ProfileType): Profile of a known language
        top_n (int): Number of the most common words
    Returns:
        float | None: The distance between profiles.
        Returns None in case of incorrect input types.
    """
    if not (
        check_profile(unknown_profile)
        and check_profile(profile_to_compare)
        and isinstance(top_n, int)
    ):
        return None

    top_n_words_unknown = get_top_n_words(unknown_profile[1], top_n)
    top_n_words_compare = get_top_n_words(profile_to_compare[1], top_n)
    if top_n_words_compare is None or top_n_words_unknown is None:
        return None

    common_tokens = set(top_n_words_unknown) & set(top_n_words_compare)
    return len(common_tokens) / len(top_n_words_unknown)


def detect_language_by_top_n(
    unknown_profile: ProfileType,
    profile_1: ProfileType,
    profile_2: ProfileType,
    top_n: int,
) -> str | None:
    """
    Detects the language of an unknown profile

    Args:
        unknown_profile (ProfileType): Unknown profile
        profile_1 (ProfileType): Profile for comparison
        profile_2 (ProfileType): Another profile for comparison
        top_n (int): Number of the most common words

    Returns:
        str | None: Unknown profile language.
        Returns None in case of incorrect input types.
    """
    if not (
        check_profile(unknown_profile)
        and check_profile(profile_1)
        and check_profile(profile_2)
        and isinstance(top_n, int)
    ):
        return None

    share_the_first_language = compare_profiles_by_top_n(unknown_profile, profile_1, top_n)
    share_the_second_language = compare_profiles_by_top_n(unknown_profile, profile_2, top_n)

    if share_the_first_language is None or share_the_second_language is None:
        return None
    if share_the_first_language == share_the_second_language:
        language_name = sorted([profile_1[0], profile_2[0]])[0]
    elif share_the_first_language > share_the_second_language:
        language_name = profile_1[0]
    else:
        language_name = profile_2[0]
    return language_name


# Mark 8


def calculate_mse(predicted: Sequence[float], actual: Sequence[float]) -> float | None:
    """
    Calculates mean squared error between predicted and actual values.

    Args:
        predicted (Sequence[float]): Sequence of predicted values
        actual (Sequence[float]): Sequence of actual values

    Returns:
        float | None: The score
        Returns None in case of incorrect input types.
    """
    if (
        len(predicted) != len(actual)
        or not isinstance(predicted, Sequence)
        or not isinstance(actual, Sequence)
    ):
        return None

    score = 0.0

    for i, pred in enumerate(predicted):
        score += (actual[i] - pred) ** 2
    score /= len(predicted)

    return score


def compare_profiles_by_mse(
    unknown_profile: ProfileType,
    profile_to_compare: ProfileType,
) -> float | None:
    """
    Compares profiles and calculates the distance using symbols.

    Args:
        unknown_profile (ProfileType): Unknown profile
        profile_to_compare (ProfileType): Profile
            to compare the unknown profile with

    Returns:
        float | None: The distance between the profiles.
        In case of corrupt input arguments or lack of keys 'name' and
        'freq' in arguments, None is returned.
    """
    if not (check_profile(unknown_profile) and check_profile(profile_to_compare)):
        return None

    all_unique_symbols = set((list(unknown_profile[1].keys()) + list(profile_to_compare[1].keys())))

    predicted = []
    actual = []
    for symbol in all_unique_symbols:
        predicted.append(unknown_profile[1].get(symbol, 0.0))
        actual.append(profile_to_compare[1].get(symbol, 0.0))

    return calculate_mse(predicted, actual)


def detect_language_by_mse(
    unknown_profile: ProfileType,
    profile_1: ProfileType,
    profile_2: ProfileType,
) -> str | None:
    """
    Detects the language of an unknown profile.

    Args:
        unknown_profile (ProfileType): Profile
            to determine the language of
        profile_1 (ProfileType): Known profile
        profile_2 (ProfileType): Another known profile

    Returns:
        str | None: Unknown profile language.
        Returns None in case of incorrect input types.
    """
    if not (
        check_profile(unknown_profile) and check_profile(profile_1) and check_profile(profile_2)
    ):
        return None

    profile_1_comparison = compare_profiles_by_mse(profile_1, unknown_profile)
    profile_2_comparison = compare_profiles_by_mse(profile_2, unknown_profile)

    distances = {
        profile_1[0]: profile_1_comparison,
        profile_2[0]: profile_2_comparison,
    }

    return sorted(distances, key=lambda x: distances.get(x) or 0)[0]


# Mark 10


def save_profile(profile: ProfileType, save_path: str) -> bool:
    """
    Saves a language profile

    Args:
        profile (ProfileType): Profile
        save_path (str): Path to the folder to save profile

    Returns:
        bool: False in case of incorrect input types or if the profile
        is missing obligatory keys. True if the profile is saved.
    """
    if not check_profile(profile) or not isinstance(save_path, str):
        return False

    profile_dict = {"name": profile[0], "freq": profile[1], "n_words": profile[2]}

    with open(f"{save_path}/{profile[0]}.json", "w", encoding="utf-8") as file:
        json.dump(profile_dict, file, indent=4)
        file.write("\n")
    return True


def load_profile(path_to_file: str) -> ProfileType | None:
    """
    Loads a language profile.

    Args:
        path_to_file (str): Path to the language profile

    Returns:
        ProfileType | None: Loaded profile.
        Returns None in case of incorrect input types.
    """
    if not isinstance(path_to_file, str):
        return None
    with open(path_to_file, "r", encoding="utf-8") as file:
        res = json.load(file)

    if not isinstance(res, dict):
        return None

    if "name" not in res or "freq" not in res or "n_words" not in res:
        return None
    profile = (res["name"], res["freq"], res["n_words"])

    if not check_profile(profile):
        return None
    return profile


def collect_profiles(
    paths_to_profiles: Sequence[str],
) -> Sequence[ProfileType] | None:
    """
    Collects profiles for a given path.

    Args:
        paths_to_profiles (Sequence[str]): Sequence of paths to the profiles

    Returns:
        Sequence[ProfileType] | None: Sequence of loaded profiles.
        Returns None in case of incorrect input types.
    """
    if not isinstance(paths_to_profiles, Sequence):
        return None

    known_profiles = []
    for filename in paths_to_profiles:
        if not isinstance(filename, str):
            return None
        profile = load_profile(filename)
        if profile is None:
            continue
        known_profiles.append(profile)
    return known_profiles


def detect_language_advanced(
    unknown_profile: ProfileType,
    known_profiles: Sequence[ProfileType],
    top_n: int,
) -> Sequence[tuple[str, dict[str, float]]] | None:
    """
    Detects the language of an unknown profile.

    Args:
        unknown_profile (ProfileType): Profile
            to determine the language of
        known_profiles (Sequence[ProfileType]): Known profiles
        top_n (int): Number of popular words

    Returns:
        Sequence[tuple[str, dict[str, float]]] | None: Sorted sequence of tuples
        containing a language and a distance via both metrics.
        The sequence is sorted by best MSE value, then by best Top-N value.
        Returns None in case of incorrect input types.
    """
    if not check_profile(unknown_profile) or not isinstance(known_profiles, Sequence):
        return None

    comparisons = []
    for known_profile in known_profiles:
        if not check_profile(known_profile):
            return None
        top_n_distance = compare_profiles_by_top_n(unknown_profile, known_profile, top_n)
        mse_distance = compare_profiles_by_mse(unknown_profile, known_profile)
        if top_n_distance is not None and mse_distance is not None:
            comparisons.append((known_profile[0], {"MSE": mse_distance, "Top-N": top_n_distance}))

    return sorted(comparisons, key=lambda x: (x[1]["MSE"], -x[1]["Top-N"]))


def print_report(
    unknown_profile: ProfileType,
    metrics_stats: Sequence[tuple[str, dict[str, float]]],
    top_n: int,
) -> None:
    """
    Prints report for detection of language.

    Args:
        unknown_profile (ProfileType): Profile
        metrics_stats (Sequence[tuple[str, dict[str, float]]]): Sequence with distances for
            available language comparison and metrics
        top_n (int): Number of popular words

    In case of incorrect type inputs, does not print anything.
    """
    if not (
        isinstance(metrics_stats, Sequence)
        and check_profile(unknown_profile)
        and isinstance(top_n, int)
    ):
        return
    for metrics_stat in metrics_stats:
        if not (
            isinstance(metrics_stat, tuple)
            and isinstance(metrics_stat[0], str)
            and isinstance(metrics_stat[1], dict)
        ):
            return

    length_of_tokens = []
    for token in unknown_profile[1].keys():
        length_of_tokens.append(len(token))
    average_token_length = sum(length_of_tokens) / unknown_profile[2]

    print(sorted(unknown_profile[1].keys()))
    popular = get_top_n_words(unknown_profile[1], top_n)
    if popular:
        popular = sorted(popular)

    print(
        "Unknown language stats\n"
        "======================\n"
        f"Popular words: {popular}\n"
        f"Max length word: {max(unknown_profile[1].keys(), key=len)}\n"
        f"Min length word: {min(unknown_profile[1].keys(), key=len)}\n"
        f"Average token length: {round(average_token_length, 5)}\n\n"
        "Language scores"
        "---------------"
    )
    for detection in metrics_stats:
        print(
            f"{detection[0]}: MSE {detection[1]["MSE"]:.5f}  "
            f"Top-N Score {detection[1]["Top-N"]:.5f}"
        )
