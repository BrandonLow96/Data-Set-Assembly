"""
This code processes balance sheet data in order to fit company data into a normalised balance sheet.

This code outputs a CSV file with the first row corresponding to the lines that make up a balance sheet financial statement

Progress
3/11/2020 - Wrote code so that it outputs a spreadsheet that works for the first company , 3DX Industries Inc
4/11/2020 - Added more terms to the CATEGORISE_BALANCE_SHEET_TEMRS list
09/11/2020 - added some terms to classify income statement
10/11/2020 - Streamlined the code, added more terms to the CATEGORISE_INCOME_STATEMENT_TERMS
27/11/2020 - added more terms to the CATEGORISE_INCOME_STATEMENT_TERMS, added a section which sums values together if the key is repeated.
28/11/2020 - Ensured that all revenue, net income and total asset terms were captured by the code
24/12/2020 - Ensured dates are in correct format. Ensured code only captures latest filing if duplicate date filings exist
28/02/2021 - Changed code methodology, switched to a cosine distance + KNN methodology to capture filings

Prepared by Brandon Low
"""
# Importing our modules

import pandas as pd
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from sklearn.neighbors import NearestNeighbors
from ftfy import fix_text
import numpy as np

THRESHOLD = 0.6


def main():

    # Obtaining the company data information for example the income statement
    source_directory = (
        r"C:\Users\blow\Desktop\Work\Quant_project\Scrape_Code\Data Directory"
    )

    # This lists out all the company folders
    list_of_company_folders = os.listdir(source_directory)

    # This allows us to obtain the terms that will appear in a normal income statement
    clean_income_statement_terms = pd.read_excel(
        os.getcwd() + "\\Clean income statement.xlsx"
    )
    clean_income_statement_terms = clean_income_statement_terms.iloc[:, 0:1]
    clean_unique_income_statement_terms = clean_income_statement_terms[
        "income statement terms"
    ].unique()

    # This allows us to obtain the terms that will appear in a normal balance sheet
    clean_balance_sheet_terms = pd.read_excel(
        os.getcwd() + "\\Clean balance sheet.xlsx"
    )
    clean_balance_sheet_terms = clean_balance_sheet_terms.iloc[:, 0:1]
    clean_unique_balance_sheet_terms = clean_balance_sheet_terms[
        "balance sheet terms"
    ].unique()

    df_income_statement = initialise_dataframe(clean_unique_income_statement_terms)
    df_balance_sheet = initialise_dataframe(clean_unique_balance_sheet_terms)

    for company_folder in list_of_company_folders:
        company_files = os.listdir(os.path.join(source_directory, company_folder))
        for file in company_files:
            code, cik, sic, file_type = get_file_name(file)
            if file_type == "statements of operations and comprehensive income (loss)":

                # This allows us to get the names of each term in the respective report
                names = pd.read_csv(
                    os.path.join(source_directory, company_folder, file)
                )

                # This uses the algorithm to get the matches
                matches = match_data(
                    names,
                    clean_income_statement_terms,
                    clean_unique_income_statement_terms,
                )

                # This filters all matches by the threshold value, lower is better
                matches = matches[(matches["Match confidence"] < THRESHOLD)]

                # This creates a dataframe with all the matches values
                merged_df = clean_data(matches, company_folder, names, code, cik, sic)

                # This appends it to the income statement dataframe
                df_income_statement = df_income_statement.append(
                    merged_df, ignore_index=True
                )

            if file_type == "balance sheet":
                # This allows us to get the names of each term in the respective report
                names = pd.read_csv(
                    os.path.join(source_directory, company_folder, file)
                )

                # This uses the algorithm to get the matches
                matches = match_data(
                    names,
                    clean_balance_sheet_terms,
                    clean_unique_balance_sheet_terms,
                )

                # This filters all matches by the threshold value, lower is better
                matches = matches[(matches["Match confidence"] < THRESHOLD)]

                # This creates a dataframe with all the matches values
                merged_df = clean_data(matches, company_folder, names, code, cik, sic)

                # This appends it to the income statement dataframe
                df_balance_sheet = df_balance_sheet.append(merged_df, ignore_index=True)

    # Combining duplicated data
    df_income_statement = combine_duplicated_income_statement_data(df_income_statement)
    df_income_statement = drop_duplicated_dates(df_income_statement)

    df_balance_sheet = drop_duplicated_dates(df_balance_sheet)

    print("Converting data to csv")
    df_income_statement.to_csv("./output income statement.csv", index=False)
    df_balance_sheet.to_csv("./output balance sheet.csv", index=False)


def initialise_dataframe(clean_unique_income_statement_terms):
    # TODO change variables to neutral name because this applies for the other statements as well
    df_income_statement = pd.DataFrame(columns=clean_unique_income_statement_terms)
    df_income_statement["Company Name"] = ""
    df_income_statement["Dates"] = ""
    df_income_statement["Latest filing date"] = ""
    df_income_statement["Code"] = ""
    df_income_statement["CIK"] = ""
    df_income_statement["SIC"] = ""
    cols = df_income_statement.columns.tolist()
    cols = cols[-6:] + cols[:-6]
    df_income_statement = df_income_statement[cols]

    return df_income_statement


def get_file_name(file):

    """
    :param file: File that contains information about the individual company. E.g Balance sheet of XYZ company

    :return: code: Whether the file is a 10k or 10Q file
    :return: file_type: Whether the file is a balance sheet
    """
    try:
        [code, _datestring, cik, sic, sec_type] = file.split("_")
        sec_type = sec_type.replace("Consolidated ", "").lower()
        file_name = "{}_{}".format(code, sec_type)
        file_type = sec_type
        return code, cik, sic, file_type

    except:
        traceback.print_exc()


def match_data(names, clean_statement_terms, clean_unique_statement_terms):
    print("Vecorizing the data - this could take a few minutes for large datasets...")
    vectorizer = TfidfVectorizer(min_df=1, analyzer=ngrams, lowercase=False)
    tfidf = vectorizer.fit_transform(clean_unique_statement_terms)
    print("Vecorizing completed...")

    nbrs = NearestNeighbors(n_neighbors=2, n_jobs=-1).fit(tfidf)

    org_column = "Category"  # column to match against in the messy data
    names.dropna(
        subset=[org_column], inplace=True
    )  # Drops the rows of the income statement where the 'category' is blank
    unique_org = set(names[org_column].values)  # set used for increased performance

    print("getting nearest n...")
    distances, indices = getNearestN(unique_org, vectorizer, nbrs)

    unique_org = list(unique_org)  # need to convert back to a list
    print("finding matches...")
    matches = []
    for i, j in enumerate(indices):

        temp = [
            distances[i][0],
            clean_statement_terms.values[j][0][0],
            unique_org[i],
        ]
        matches.append(temp)

    print("Building data frame...")
    matches = pd.DataFrame(
        matches,
        columns=["Match confidence", "Matched name", "Original name"],
    )
    print("Done")

    return matches


def clean_data(matches, company_folder, names, code, cik, sic):
    matches = matches.sort_values(
        by=["Matched name", "Match confidence"]
    ).drop_duplicates(subset=["Matched name"])
    sliced_names = names.loc[names["Category"].isin(matches["Original name"])]

    # join on 'Category' and 'Original name
    merged_df = matches.merge(
        sliced_names,
        how="left",
        left_on="Original name",
        right_on="Category",
    )

    # Sometimes the original statement will have multiple lines of the same name. This drops all the duplicated names and keeps the first occurance
    merged_df = merged_df.drop_duplicates(subset=["Matched name"])

    # drop the original name column, sets index to 'Matched name', the information we are interested in, and transposes

    merged_df = (
        merged_df.drop(columns=["Original name", "Category", "Match confidence"])
        .set_index("Matched name")
        .T
    )

    # This adds the company name to the dataframe
    merged_df["Company Name"] = company_folder

    # This adds the CIK number to the dataframe
    merged_df["Code"] = code
    merged_df["CIK"] = cik
    merged_df["SIC"] = sic

    merged_df = merged_df.reset_index()
    merged_df.rename(columns={"index": "Dates"}, inplace=True)

    # This adds the Latest filing date to the dataframe, allows us to remove filings and keep the most recent filing

    # Sort dates in descending order
    merged_df = sort_dates(merged_df)

    # Add latest filing dates, the date of the most recent filing
    merged_df["Latest filing date"] = merged_df.at[0, "Dates"]

    print(company_folder)
    print(merged_df)

    return merged_df


def ngrams(string, n=2):
    string = str(string)
    string = fix_text(string)  # fix text
    string = string.encode("ascii", errors="ignore").decode()  # remove non ascii chars
    string = string.lower()
    chars_to_remove = [")", "(", ".", "|", "[", "]", "{", "}", "'"]
    rx = "[" + re.escape("".join(chars_to_remove)) + "]"
    string = re.sub(rx, "", string)
    string = string.replace("&", "and")
    string = string.replace(",", " ")
    string = string.replace("-", " ")
    string = string.title()  # normalise case - capital at start of each word
    string = re.sub(
        " +", " ", string
    ).strip()  # get rid of multiple spaces and replace with a single
    string = " " + string + " "  # pad names for ngrams...
    string = re.sub(r"[,-./]|\sBD", r"", string)
    ngrams = zip(*[string[i:] for i in range(n)])
    return ["".join(ngram) for ngram in ngrams]


def getNearestN(query, vectorizer, nbrs):
    queryTFIDF_ = vectorizer.transform(query)
    distances, indices = nbrs.kneighbors(queryTFIDF_)
    return distances, indices


def combine_duplicated_income_statement_data(df_income_statement):

    # Combining duplicated data for revenue
    df_income_statement["Total revenue"] = df_income_statement["Total revenue"].combine(
        df_income_statement["Revenue"], lambda a, b: b if np.isnan(a) else a
    )
    df_income_statement["Net revenue"] = df_income_statement["Net revenue"].combine(
        df_income_statement["Total revenue"], lambda a, b: b if np.isnan(a) else a
    )
    df_income_statement["Net sales"] = df_income_statement["Net sales"].combine(
        df_income_statement["Sales"], lambda a, b: b if np.isnan(a) else a
    )
    df_income_statement["Net revenue"] = df_income_statement["Net revenue"].combine(
        df_income_statement["Net sales"], lambda a, b: b if np.isnan(a) else a
    )
    df_income_statement["Total operating revenue"] = df_income_statement[
        "Total operating revenue"
    ].combine(
        df_income_statement["Operating revenue"], lambda a, b: b if np.isnan(a) else a
    )
    df_income_statement["Net revenue"] = df_income_statement["Net revenue"].combine(
        df_income_statement["Total operating revenue"],
        lambda a, b: b if np.isnan(a) else a,
    )

    # Combining duplicated data for cost of goods sold
    df_income_statement["Cost of goods sold"] = df_income_statement[
        "Cost of goods sold"
    ].combine(
        df_income_statement["Cost of products sold"],
        lambda a, b: b if np.isnan(a) else a,
    )
    df_income_statement["Cost of goods sold"] = df_income_statement[
        "Cost of goods sold"
    ].combine(
        df_income_statement["Cost of revenue"], lambda a, b: b if np.isnan(a) else a
    )
    df_income_statement["Cost of goods sold"] = df_income_statement[
        "Cost of goods sold"
    ].combine(
        df_income_statement["Cost of sales"], lambda a, b: b if np.isnan(a) else a
    )

    # Combining duplicated data for gross profit
    df_income_statement["Gross profit"] = df_income_statement["Gross profit"].combine(
        df_income_statement["Gross margin"], lambda a, b: b if np.isnan(a) else a
    )

    # Combining duplicated data for operating expenses
    df_income_statement["Total operating expenses"] = df_income_statement[
        "Total operating expenses"
    ].combine(
        df_income_statement["Operating expenses"], lambda a, b: b if np.isnan(a) else a
    )

    # Combining duplicated data for operating profit
    df_income_statement["Operating profit"] = df_income_statement[
        "Operating profit"
    ].combine(
        df_income_statement["Operating earnings"], lambda a, b: b if np.isnan(a) else a
    )
    df_income_statement["Operating profit"] = df_income_statement[
        "Operating profit"
    ].combine(
        df_income_statement["Operating income"], lambda a, b: b if np.isnan(a) else a
    )
    df_income_statement["Operating profit"] = df_income_statement[
        "Operating profit"
    ].combine(
        df_income_statement["Operating loss"], lambda a, b: b if np.isnan(a) else a
    )
    df_income_statement["Operating profit"] = df_income_statement[
        "Operating profit"
    ].combine(
        df_income_statement["Income from operations"],
        lambda a, b: b if np.isnan(a) else a,
    )

    # Combining duplicated data for income tax
    df_income_statement["Income tax expense"] = df_income_statement[
        "Income tax expense"
    ].combine(
        df_income_statement["Provision for income tax"],
        lambda a, b: b if np.isnan(a) else a,
    )

    # Combining duplicated data for Net income
    df_income_statement["Net income"] = df_income_statement["Net income"].combine(
        df_income_statement["Net loss"], lambda a, b: b if np.isnan(a) else a
    )

    df_income_statement["Net income"] = df_income_statement["Net income"].combine(
        df_income_statement["Net income loss"], lambda a, b: b if np.isnan(a) else a
    )

    # Drop combined columns

    df_income_statement = df_income_statement.drop(
        columns=[
            "Revenue",
            "Sales",
            "Net sales",
            "Total revenue",
            "Operating revenue",
            "Total operating revenue",
            "Cost of products sold",
            "Cost of revenue",
            "Cost of sales",
            "Gross margin",
            "Operating expenses",
            "Operating earnings",
            "Operating income",
            "Operating loss",
            "Income from operations",
            "Provision for income tax",
            "Net loss",
            "Net income loss",
        ]
    )

    return df_income_statement


def sort_dates(df):
    # This line extracts the relevant portion of the dates and disregards the rest. For example: Date will become Feb. 31, 2019
    df["Dates"] = df["Dates"].str.extract("([\w]{3}[.]{0,1} [\w]{1,2}[,]{0,1} [\w]{4})")

    # This line drops the "." in the date. For example: Date is now Feb 31, 2019
    df["Dates"] = df["Dates"].str.replace(".", "", regex=False)

    # This ensures that the dates are in a "Date" format.
    df["Dates"] = pd.to_datetime(df["Dates"])

    # Sort dates in descending order
    df = df.sort_values(by=["Dates"], ascending=False)
    # # Repeat the same for the "Latest filing date" column
    # df["Latest filing date"] = df["Latest filing date"].str.extract(
    #     "([\w]{3}[.]{0,1} [\w]{1,2}[,]{0,1} [\w]{4})"
    # )
    # df["Latest filing date"] = df["Latest filing date"].str.replace(
    #     ".", "", regex=False
    # )
    # df["Latest filing date"] = pd.to_datetime(df["Latest filing date"])

    return df


def drop_duplicated_dates(df):
    # If there is a quarterly filing and annual filing of the same date and filing date, the quarterly filing is usually less complete
    # We want to keep the annual filing, the more complete one. We sum the number of null values in each row

    df["Null"] = df.isnull().sum(axis=1)

    # We drop the row with the earlier filing date and highest null value
    df = df.sort_values(
        by=["Company Name", "Dates", "Latest filing date", "Null"],
        ascending=[True, False, False, True],
    ).drop_duplicates(subset=["Company Name", "Dates"], keep="first")
    df = df.drop(columns=["Latest filing date", "Null"])

    return df


if __name__ == "__main__":
    main()