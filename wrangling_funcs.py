"""
Some functions for wrangling NCBI metadata
"""
import pandas as pd
import numpy as np
import re


def clean_string(string):
    """
    Metadata in the NCBI dataframe is inconsistent. To try and extract some useful information we need to clean
    strings after splitting up the metadata to make them readable. This function is used to clean strings that will
    be turned into column names.

    :param string: A string that was split from a longer string on '||'.
    :return: A consistent, all lower case, string that contains no special characters and uses '_' instead of spaces.
    """
    cleaned = string.strip().lower().replace(' ', '_')
    done = ''.join(['_' if c in '/:-,\\' else '' if c in ' ()?' else c for c in cleaned])
    return done


def test_clean_string():
    assert clean_string('geographic location (country and/or sea)') == 'geographic_location_country_and_or_sea'
    assert clean_string('geographic location (latitude)') == 'geographic_location_latitude'
    assert clean_string('host health state') == 'host_health_state'
    assert clean_string('ENA last update') == 'ena_last_update'


def find_columns(keywords, dataframe, exclude_keywords=None):
    """
    This function find keywords in the columns of the NCBI metadata dataframe that we created. We will combine the
    columns downstream into a single column because the metadata is inconsistent and may contain many different
    columns that exist largely out of NaN values.

    :param keywords: Words that will be used to find columns.
    :param dataframe: The dataframe to be searched
    :param exclude_keywords: Keywords to exclude from the search
    :return: A set of strings that contain the column names
    """
    if exclude_keywords is None:
        exclude_keywords = []
    matches = set()

    for column in dataframe.columns:
        keyword_found = any(word in column for word in keywords)
        exclude_keyword_found = any(word in column for word in exclude_keywords)

        if keyword_found and not exclude_keyword_found:
            matches.add(column)

    return matches


def test_find_columns():
    input_df = pd.DataFrame({'geo_location': [1, 2, 3],
                             'geographic': [4, 5, 6],
                             'env': [1, 2, 3],
                             'sample': [1, 2, 3],
                             'location': [1, 2, 3]})

    result = find_columns(['geo', 'location'], input_df)
    assert result == {'geo_location', 'location', 'geographic'}

    result = find_columns(['geo'], input_df, ['geographic'])
    assert result == {'geo_location'}


def combine_columns(df, matches, new_column_name):
    """
    This function combines specified columns from a dataframe. It handles NaN values if they are present. Because the
    columns in the metadata are inconsistent we sweep the columns of the dataframe based on keywords and combine all
    possible useful information into a single column here.

    :param df: Dataframe that contains the columns to be combined
    :param matches: List of strings with column names
    :param new_column_name: Name of the new combined column
    :return: The dataframe with the new column
    """

    def join_non_nan_values(row):
        non_nan_values = [str(val) for val in row if not pd.isna(val)]
        return ','.join(non_nan_values) if non_nan_values else np.nan

    df[new_column_name] = df[matches].apply(join_non_nan_values, axis=1)

    return df


def test_combine_columns():
    input_df = pd.DataFrame({'geo_location': [np.nan, np.nan, np.nan],
                             'geographic': ['1', '2', '3'],
                             'location': ['1', '2', np.nan],
                             'sample': ['1', '2', '3']})
    matches = ['geo_location', 'geographic', 'location']
    new_name = 'inferred_location'

    correct_df = pd.DataFrame({'geo_location': [np.nan, np.nan, np.nan],
                               'geographic': ['1', '2', '3'],
                               'location': ['1', '2', np.nan],
                               'sample': ['1', '2', '3'],
                               'inferred_location': ["1,1", "2,2", "3"]})

    assert correct_df.equals(combine_columns(input_df, matches, new_name))


def read_insdc():
    """
    Reads in a file containing countries and areas specified by INSDC and turns it into a dictionary
    :return: {'Country/Area': ['Country/Area', 'Continent']}
    """
    insdc_dict = {}
    with open('Data/insdc_country_or_area.csv') as file:
        file.readline()  # skip header
        for line in file:
            line = line.strip().split(',')
            insdc_dict[line[0]] = [line[0], line[1]]
    return insdc_dict


def clean_geo(location):
    """
    Clean geographic data from the NCBI. Country names and area names are based on the Country and Area list from INSDC.
    :param location: A string that can contain continents country names or other geographic information
    :return: Continent, country, extra information
    """
    if pd.isna(location):
        return pd.NA, pd.NA, pd.NA

    continent, country, city = pd.NA, pd.NA, pd.NA
    continents = ['Europe', 'North America', 'South America', 'Asia', 'Oceana', 'Antarctica', 'Africa']
    location = list(set(re.split('[:,]', location)))
    insdc_dict = read_insdc()

    found_country = False
    for item in location:
        item = item.strip()
        try:
            name_and_continent = insdc_dict[item]
        except KeyError:
            name_and_continent = [pd.NA, pd.NA]
        if not pd.isna(name_and_continent[0]):
            found_country = True
            country = name_and_continent[0]
            continent = name_and_continent[1]
        elif item in continents and not found_country:
            continent = item
        else:
            city = item
    return continent, country, city


def test_clean_geo():
    assert clean_geo("Japan:Aichi") == ("Asia", "Japan", "Aichi")
    assert clean_geo("Airag-nur,Mongolia") == ("Asia", "Mongolia", "Airag-nur")
    assert clean_geo("Akerebiata,Nigeria") == ("Africa", "Nigeria", "Akerebiata")
    assert clean_geo("Netherlands: Amsterdam") == ("Europe", "Netherlands", "Amsterdam")
    assert clean_geo("Zambia") == ("Africa", "Zambia", pd.NA)
    assert clean_geo("West Bank") == ("Asia", "West Bank", pd.NA)
    assert clean_geo("South Africa, Gauteng") == ("Africa", "South Africa", "Gauteng")


def clean_source(string):
    """
    Removes duplicates and numeric strings from the combined isolation source column
    :param string: String with potential duplicate words and numeric strings
    :return: Clean unique strings seperated by commas
    """
    if pd.isna(string):
        result = np.nan
    else:
        string = string.strip().split(',')
        string = set(string)
        string = list(string)
        result = [item for item in string if not any(char.isdigit() for char in item)]
        if len(result) == 0:
            result = np.nan
        else:
            result = ','.join(result)
    return result
