

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

Prepared by: Brandon Low
"""



import re
import pandas as pd
import os
import csv

CATEGORISE_BALANCE_SHEET_TERMS = {
                        'cash and cash equivalents': ['cash','cash & cash equivalents', 'cash and cash equivalents', 'cash and cash equivalents - end of period', 'cash and cash equivalents at end of period'],
                        'short-term investments': ['short term investments','short-term marketable securities','short-term investments','Short-term investments'],
                        'accounts receivable': ['accounts receivable, net','accounts receivable'],
                        'other receivables': ['other receivables'],
                        'trade receivables': ['trade accounts receivable','trade accounts receivable, net','trade receivables'],
                        'notes receivable': ['notes receiveble','notes receivable'],
                        'assets from discontinued operations': ['assets from discontinued operations'],
                        'prepaid expenses': ['prepaid expenses'],
                        'prepaid expenses and other current liabilities': ['prepaid expenses and other current assets'],
                        'net deferred tax assets, current' : ['net deferred tax assets, current'],
                        'net assets of discontinued operations': ['net assets of discontinued operations', 'current assets of discontinued operations'],
                        'inventory': ['inventories, net','inventory', 'inventories'],
                        'costs and estimated earnings in excess of billings': ['costs and estimated earnings in excess of billings'],
                        'software platform': ['readyop software platform'], #TODO Find a way to add this to other
                        'software license': ['purchased software licenses, net of accumulated amortization'],
                        'readyop customer list': ['readyop customer list'],   #TODO Find a way to add this to other
                        'assets held for sale': ['assets held for sale'],
                        'other current assets': ['other current assets'],
                        'total current assets:' : ['total current assets'],
                        'maintenance and other inventory, net': ['maintenance and other inventory, net'],
                        'in-process research and development': ['in-process research and development'],
                        'property and equipment, net': ['property, plant and equipment, net','property and equipment, net of accumulated depreciation and amortization','property and equipment, net'],
                        'intangible assets': ['other intangible assets, net','intangible assets','intangible assets, net'],
                        'goodwill': ['goodwill'],
                        'other assets': ['other long-term assets','other assets','other assets, net'],
                        'deferred income taxes': ['deferred income tax liability','deferred income taxes'],
                        'deferred commissions': ['deferred commissions, net'],
                        'refundable income taxes': ['refundable income taxes'],
                        'long-term investments': ['long-term marketable securities','investments', 'long-term investments'],
                        'investments in unconsolidated affiliates': ['investments in unconsolidated affiliates'],
                        'net deferred tax assets, non-current': ['long-term deferred tax assets, net','net deferred tax assets, non-current'],
                        'total other assets': ['other assets, net','total other assets'],
                        'total assets': ['assets, total','assets','total assets'],

                        'accounts payable': ['trade accounts payable','accounts payable', 'accounts payable and accrued liabilities'],
                        'accrued payroll': ['accrued compensation and benefits','accrued payroll', 'accrued payroll and related expenses'],
                        'due to shareholder': ['due to shareholder'],
                        'tax payable': ['tax payable','taxes payable'],
                        'income taxes payable': ['income taxes payable'],
                        'accrued taxes': ['accrued taxes'],
                        'net deferred tax liabilities': ['net deferred tax liabilities'],
                        'accrued commissions': ['accrued commissions'],
                        'other accrued expenses': ['accrued expenses','accrued expenses and other liabilities','other accrued expenses','other accrued liabilities'],
                        'billings in excess of costs and estimated earnings': ['billings in excess of costs and estimated earnings'],
                        'current installments of long-term debt': ['current maturities of debt','current portion of long-term debt','current installments of long-term debt'],
                        'loan': ['loans','loan', 'loans payable'],
                        'notes payable - stockholders': ['notes payable - stockholders'],
                        'customer deposits': ['customer deposits'],
                        'deferred revenue': ['deferred revenue, current portion','deferred revenue'],
                        'warranty reserve': ['warranty reserve'],
                        'current liabilities of discontinued operations': ['liabilities from discontinued operations, current portion','current liabilities of discontinued operations'],
                        'liabilities held for sale - current': ['liabilities held for sale'],
                        'current portion of capital lease obligation': ['current portion of capital lease obligation'],
                        'other current liabilities': ['other current liabilities','other current liabilities'],
                        'total current liabilities': ['other longterm liabilities','total current liabilities'],
                        'deferred revenue, net of current portion': ['deferred revenue, net of current portion'],
                        'long-term debt': ['notes payable, less current portion','long-term debt','long-term debt, net','long-term liabilities','long term debt'],
                        'long-term deferred tax liabilities': ['long-term deferred tax liabilities'],
                        'capital lease obligation, net of current portion': ['capital lease obligation, net of current portion'],
                        'pension and postretirement benefit liabilities': ['pension obligations','pension and other post retirement benefit obligations','pension liabilities','pension and postretirement benefit costs','pension obligations','long term pension and postretirement liabilities','pension and postretirement benefit liabilities'],
                        'deferred compensation liability': ['deferred compensation liability'],
                        'liabilities from discontinued operations': ['liabilities from discontinued operations','liabilities from discontinued operatios, net of current portion'],
                        'liabilities held for sale - non current': ['other liabilities held for sale'],
                        'other liabilities': ['environmental remediation liability','other long-term liabilities','other liabilities', 'other non-current liabilities'],
                        'total long term liabilities': ['total long term liabilities','total non-current liabilities'],

                        'retained earnings': ['retained earnings'],
                        'stockholders equity before treasury stock': ['stockholders equity before treasury stock'],
                        'common stock': ['class a common stock','common stock', 'common stock and additional paid-in capital'], #TODO I have put all 'started with' common stock to be common stock, not sure if this is right move or not
                        'stock': ['stock held in trust'],
                        'preferred stock': ['preferred stock'],
                        'treasury stock': ['treasury stock'],
                        'capital in excess of par value': ['capital in excess of par value'],
                        'additional paid in capital': ['additional paid-in capital','additional paid in capital'],
                        'commitments and contingencies': ['contingent consideration','commitments and contingencies'],
                        'accumulated other comprehensive income': ['accumulated other comprehensive income'],
                        'accumulated deficit': ['accumulated deficit','accumulated other comprehensive loss'],
                        'deficit from discontinued operations': ['deficit from discontinued operations'],
                        'series a stock': ['series a preferred stock'],
                        'series b stock': ['series b preferred stock'],
                        'series c stock': ['series c preferred stock'],
                        'series d stock': ['series d preferred stock'],
                        'series e stock': ['series e convertible preferred stock'],
                        'total stockholders equity': ['total equity','total stockholders equity', "total shareholders' equity", 'total shareholders equity'],
                        'total stockholders deficit': ['total stockholders deficit'],
                        'total liabilities': ['total liabilities'],
                        'total liabilities and stockholders deficit': ['total liabilities and stockholders deficit'],
                        'total liabilities and stockholders equity': ['total liabilities and shareholders equity','total liabilities and equity','total liabilities and stockholders equity', "total liabilities and shareholders' equity"]}

CATEGORISE_INCOME_STATEMENT_TERMS = {
                        'revenue': ['income','revenues   related parties','sales, net','revenue from contract with customer, including assessed tax','external revenue','management fee revenue','net revenue', 'total net revenue','total sales','revenues   net of returns and allowances','sales','sales to external customers','revenues from intercompany sales   eliminated from sales above','revenues from external customer','total revenues','net revenues','revenue, net','revenues, net','revenues','revenue', 'total revenue','gross sales', 'total net sales','net sales'],
                        'cost of goods sold': ['cost of good','total costs of revenue','cost of revenues   related party','total cost of revenue','cost of revenues','cost of products sold','cost of revenue', 'cost of goods sold','cost of sales'],
                        'gross profit': ['gross margin','gross profit'],
                        'equity in income from joint ventures': ['equity in income from joint ventures'],
                        'engineering and technical support': ['engineering and technical support'],
                        'goodwill, impairment loss': ['goodwill, impairment loss'],
                        'general, selling and administrative': ['general & administrative','selling, general & administrative expenses','general & administrative','selling expenses','selling and administrative expenses','general administrative expense','selling, general and administrative expenses','selling, general and administrative, and transaction costs','general and admin. expenses','selling, general & administrative','selling, general, and administrative expenses','general and administration','selling, administrative and engineering expenses','general and administrative','administrative expenses', 'general and administrative expenses'],
                        'stock compensation expense': ['stock compensation expense'],
                        'impairment of intangible assets': ['impairment of intangible assets','impairment on intangible property'],
                        'impairment of assets': ['asset impairment charges'],
                        'consulting fees and professional fees': ['consulting   related party','consulting','professional and consulting expenses','professional fees and other corporate expenses','professional fees','consulting and professional services','consulting fees  related party','consulting fees'],
                        'depreciation and amortization': ['total depreciation and amortization','amortization and depreciation','depreciation and amortization'],
                        'depreciation': ['depreciation expense','depreciation'],
                        'research and development': ['research & development','research and development expenses','research and development'],
                        'interest income': ['interest income'],
                        'salary and wages': ['salaries and wages','related party salary and wages'],
                        'sales and marketing':['sales and marketing'],
                        'acquisition related costs': ['acquisition related costs'],
                        'other operating expenses': ['other expense','gains, losses and other items, net'],
                        'total operating expenses':['operating expenses','cost and expenses, total','total operating expenses','total expenses'],
                        'operating income': ["income / loss from operations","loss from continued operations","operating loss before income taxes","earnings before income tax expense", "loss before provision for income taxes", 'earnings before income tax expense','net loss before provision for income taxes','income from continuing operations before income taxes',"operating income/","net income from operations","income from continuing operations","net loss from operations",'net income before other expenses and income taxes','income from operations before taxes','net loss before income taxes','income from operations before income taxes','net income before income taxes','loss from continuing operations before income taxes','income before taxes','net loss before income tax','income before income taxes', 'income before income tax expense','loss before income taxes','income (loss) before income taxes',"operating profit","income from continued operations",'total operating revenues','income from operations','operating loss','operating income','income (loss) from continued operations', 'loss from operations'],
                        'other income': ['total other income , net','other income'],
                        'debt forgiveness income': ['debt forgiveness income'],
                        'interest': ['total interest and other expense','interest and debt expense','interest expense, net','interest expense', 'interest and other expense'],
                        'foreign currency transaction gain , before tax': ['foreign currency translation gain','foreign currency transaction gain , before tax'],
                        'total other income': ['other, net','total other income'],
                        'total other expense': ['other expense, net','total other expense','total other expenses'],
                        'income tax': ['provision for income taxes','income tax','income tax expense','income taxes (benefit)','income tax provision'],
                        'net income (loss) from continuing operations': ['income from continuing operations, net of tax','net income from continuing operations','net income (loss) from continuing operations'],
                        'net income attributable to noncontrolling interests' : ['net income attributable to noncontrolling interests'],
                        'net income attributable to ntic': ['net income attributable to ntic'],
                        'income (loss) from discontinued operations': ['income from discontinued operations, net of tax','loss from discontinued operations'],
                        'gain on settlement of debt': ['gain on settlement of debt'],
                        'net income (loss)' : ['net income / loss','net income after income taxes','net income attributable to parent','net loss and comprehensive loss','net income attributable to dolby laboratories, inc.','net income/','net income attributable to cal maine foods, inc.','net','net earnings','net earnings including noncontrolling interest','consolidated net income','net earnings','net income attributable to biogen inc.','net loss for the period','net loss after tax','net income (loss)', 'net loss', 'net income'],
                        'net income per share, basic': ['net income per share','net income per share basic', 'net loss per share   basic'],
                        'loss per common share, basic and diluted': ['loss per common share   basic and diluted'],
                        'weighted average number of shares outstanding, basic': ['weighted average number of shares outstanding, basic'],
                        'weighted average number of shares outstanding, diluted': ['weighted average number of shares outstanding, diluted'],
                        'weighted average number of common shares outstanding, basic and diluted': ['weighted average number of common shares outstanding', 'weighted average common shares outstanding   basic and diluted'],
}


def main():
    #This initialises the dataframes where all the data will be stored.
    df_balance_sheet, df_income_statement = initialise_dataframes()

    #This is where the data is stored
    source_directory = r'C:\Users\blow\Desktop\Work\Play\CompanyData'
    list_of_company_folders = os.listdir(source_directory)

    #iterates through the list of company folders
    for company_folder in list_of_company_folders:
        company_files = os.listdir(os.path.join(source_directory, company_folder))

        #iterates through the list of files for a specific company
        for file in company_files:
            code, file_type = get_file_name(file)

            #This looks at the balance sheet
            if file_type == 'balance sheet':
                dict_of_terms = CATEGORISE_BALANCE_SHEET_TERMS
                data = read_files(source_directory, company_folder, file)
                output_row = parse_data(data,dict_of_terms, company_folder, code, file_type)
                df_temp = pd.DataFrame(output_row, index=None)
                # We add to the dataframe after processing each company file
                df_balance_sheet = df_balance_sheet.append(df_temp, ignore_index=True)

            #This looks at income statement
            if file_type == 'statements of operations and comprehensive income (loss)':
                dict_of_terms = CATEGORISE_INCOME_STATEMENT_TERMS
                data = read_files(source_directory, company_folder, file)
                output_row = parse_data(data,dict_of_terms, company_folder, code, file_type)
                df_temp = pd.DataFrame(output_row,index=None)
                df_income_statement = df_income_statement.append(df_temp, ignore_index=True)

    #This function ensures that the dates are in the correct order
    df_balance_sheet = sort_dates(df_balance_sheet)
    df_income_statement = sort_dates(df_income_statement)

    #This function drops duplicate entries if a company files the same date under a different balance sheet. This
    #function keeps the latest filing date

    df_balance_sheet = drop_duplicates(df_balance_sheet)
    df_income_statement = drop_duplicates(df_income_statement)

        df_balance_sheet.to_csv('./output balance sheet.csv', index=False)
    df_income_statement.to_csv('./output income statement.csv', index = False)

def initialise_dataframes():
    #We start by initialising the dataframe for the balance sheet
    df_balance_sheet = pd.DataFrame(columns=CATEGORISE_BALANCE_SHEET_TERMS.keys())
    df_balance_sheet['Company Name'] = ""
    df_balance_sheet['Dates'] = ""
    df_balance_sheet["Latest filing date"] = ""
    df_balance_sheet['Code'] = ""

    # These lines just shuffle around the columns so that 'Company Name', 'Dates' and 'Type' appear at the start of the dataframe
    cols = df_balance_sheet.columns.tolist()
    cols = cols[-4:] + cols[:-4]
    df_balance_sheet = df_balance_sheet[cols]

    #Does the same thing for Income statement
    df_income_statement = pd.DataFrame(columns=CATEGORISE_INCOME_STATEMENT_TERMS.keys())
    df_income_statement['Company Name'] = ""
    df_income_statement['Dates'] = ""
    df_income_statement["Latest filing date"] = ""
    df_income_statement['Code'] = ""
    cols = df_income_statement.columns.tolist()
    cols = cols[-4:] + cols[:-4]
    df_income_statement = df_income_statement[cols]

    return df_balance_sheet, df_income_statement



def read_files(source_directory,company_folder, file):

    """
    :param source_directory: Directory where all the Companies are stored
    :param company_folder: Directory where all the individual company files are stored
    :param file: File that contains information about the individual company. E.g Balance sheet of XYZ company

    :return: data, a parameter that reads the data
    """
    data = open(os.path.join(source_directory, company_folder, file))
    data = csv.reader(data)
    return data

def get_file_name(file):

    """
    :param file: File that contains information about the individual company. E.g Balance sheet of XYZ company

    :return: code: Whether the file is a 10k or 10Q file
    :return: file_type: Whether the file is a balance sheet
    """
    try:
        [code, _datestring, sec_type] = file.split('_')
        sec_type = sec_type.replace('Consolidated ', '').lower()
        file_name = '{}_{}'.format(code, sec_type)
        file_type = sec_type
        return code,file_type

    except:
        traceback.print_exc()

def check_if_date(row):

    """
    :param row: This is a line in the financial statement that we are looking at
    :return: True if it is a date, False if it is not a date.

    This function takes in a line in the financial statement and uses regular expressions to classify if the row in question
    is a date or if it is not a date. If it is a date, it will return true. Else, it will return false.
    """

    date_regexes = {
        'year': r"(2\s?0|1\s?9)\s?[0-9]\s?[0-9]$",
        'year_with_currency': r"(2\s?0|1\s?9)\s?[0-9]\s?[0-9]\s\sUSD"
    }

    # Define list of regular expressions to match

    if row[0] == 'Category' and all([re.search(date_regexes['year'], x) or not i for (i, x) in enumerate(row)]):
        return True

    if row[0] == 'Category' and all([re.search(date_regexes['year_with_currency'], x) or not i for (i, x) in enumerate(row)]):
        return True

    else:
        return False


def sanitise(key):
    """

    :param key:  This is the line in the balance sheet that we are looking to standardize
    :return: key: This is the standarized line in the balance sheet that we return to be parsed.

    This function takes in a line in the balance sheet. For example 'Cash and cash equivalents' and makes it into
    'cash and cash equivalents'.

    This makes the line in the balance sheet more standarised and easier for the programme to read.
    """

    sanitise_regexes = {
        'currency': r"^[$£]$",
        'brackets': r"(?:\s+/\s+)?[\(\[].*?[\)\]](?:\s+/\s+)?",
        'spaces': r"\s+",
        'date_spec': r"\s+at\s+[a-z]{3}\.?\s+[0-9]{1,2},?\s+(?:2\s?0|1\s?9)\s?[0-9]\s?[0-9]",
        'loss': r"(?:net|other).*loss",
        'negative': r"\s*(?:\s+un|no(?:t|n)?)-?\s*",
        'currency_spec': r"\s+of\s+[^\w]*[0-9]+"
    }

    key = key.lower().strip()
    key = re.sub(sanitise_regexes['brackets'], '', key)
    key = re.sub(sanitise_regexes['spaces'], ' ', key)
    key = re.sub(sanitise_regexes['date_spec'], '', key)
    key = re.split(sanitise_regexes['currency_spec'], key)[0]
    key = key.replace('â€™', '')
    key = key.replace(' -â â', '')
    key = key.replace(', shares', '')
    key = key.replace('\u00e2\u20ac\u201c', '-')
    key = key.replace('\u2019', '\'')
    key = key.replace("-", " ")

    if ':' in key:
        key = key.split(':')[0]
    if key.endswith('respectively'):
        key = key.split(',')[0]

    if key.startswith('common stock'):
        key = 'common stock'

    if key.startswith('preferred stock'):
        key = 'preferred stock'

    if key.startswith('treasury stock'):
        key = 'treasury stock'

    key = key.replace("'","")
    key = key.strip()

    #print(f'This is the sanitised key {key}')
    return key




def categorise_row(row, company_folder, dict_of_terms, file_type):
    """
    :param row: This is a row containing data about an individual company
    :param company_folder: This is the name of the company
    :param dict_of_terms: This is the list of terms that we are parsing through. It is either balance sheet data or income statement data
    :param file_type: This is the type of data that we are looking at. It is either balance sheet or income statmement.
    :return: key: name of the row

    for example cash and cash equivalents is the name of the row and it appears in the CATEGORISE_BALANCE_SHEET_TERMS
    listed above, this function will return key = cash and cash equivalents
    """
    # We first make the row into a readable format
    term = row[0]
    term = sanitise(row[0])

    for key, values in dict_of_terms.items():

        if term in values:
            return key

    if term not in dict_of_terms.values():
        print(f'{term}, from {company_folder} is not in {file_type} terms')

def parse_data(data,dict_of_terms, company_folder, code, file_type):
    """
    :param data: This is the data in the file, for example balance sheet about the individual company
    :param dict_of_terms: This is the list of terms that we are parsing through. It is either balance sheet data or income statement data
    :param company_folder: This is the name of the company
    :param code: This is whether the file is a 10K or 10Q

    :return: output_row: This is a line of data about a company
    """
    output_row = {}
    # This iterates through all the rows of data and adds it to the dictionary called output_row
    for row in data:

        # This function checks if the row is a date (check_if_date) and if the date hasn't been seen before.
        if check_if_date(row):
            output_row['Dates'] = row[1:]
            output_row["Latest filing date"] = row[1]
            continue

        key = categorise_row(row, company_folder, dict_of_terms, file_type)

        #This section of the code checks if the key has already been added to the dictionary. If it has been added, sum the values together.
        #If the two values are the same, skip this step because it means the values are duplicated.
        #If the value is "" it will return the error, cannot convert to float. I have just made it equal to 0.0.
        if key in output_row.keys():
            for i in range(len(output_row[key])):

                try:
                    output_row[key][i] = float(output_row[key][i])
                except ValueError:
                    output_row[key][i] = 0.0

                try:
                    row[i+1] = float(row[i+1])
                except ValueError:
                    row[i+1] = 0.0

                if float(output_row[key][i]) == float(row[i + 1]):
                    continue
                output_row[key][i] = output_row[key][i] + row[i+1]
        else:
            output_row[key] = row[1:]

    output_row['Company Name'] = company_folder
    output_row['Code'] = code
    return output_row


def sort_dates(df):
    #This line extracts the relevant portion of the dates and disregards the rest. For example: Date will become Feb. 31, 2019
    df["Dates"] = df["Dates"].str.extract("([\w]{3}[.]{0,1} [\w]{1,2}[,]{0,1} [\w]{4})")

    #This line drops the "." in the date. For example: Date is now Feb 31, 2019
    df["Dates"] = df["Dates"].str.replace(".", "", regex=False)

    #This ensures that the dates are in a "Date" format.
    df["Dates"] = pd.to_datetime(df["Dates"])


    #Repeat the same for the "Latest filing date" column
    df["Latest filing date"] = df["Latest filing date"].str.extract("([\w]{3}[.]{0,1} [\w]{1,2}[,]{0,1} [\w]{4})")
    df["Latest filing date"] = df["Latest filing date"].str.replace(".", "", regex=False)
    df["Latest filing date"] = pd.to_datetime(df["Latest filing date"])

    return df

def drop_duplicates(df):
    df = df.sort_values(by=['Company Name', 'Dates', 'Latest filing date']).drop_duplicates(subset=['Company Name', 'Dates'], keep='last')

    return df

if __name__ == '__main__':
    main()