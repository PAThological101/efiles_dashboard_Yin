import pandas as pd
import numpy as np

import datetime as dt   #sets dt to be the name of datetime module
from datetime import datetime  #sets datetime to be the name of the class datetime
# the above lines of code refer to two different datetimes

import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
#import plotly.io as pio#Enables export to HTML
##pio.renderers.default='svg'#instead of pio.renderers.default='notebook' as rendered is not a notebook
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template#not recognizing template on replit

import dash_auth

import datetime as dt   #sets dt to be the name of datetime module
from datetime import datetime  #sets datetime to be the name of the class datetime
# the above lines of code refer to two different datetimes

import warnings
warnings.filterwarnings('ignore', category=FutureWarning)



###############################################################################################################################################################
########################################################  Connect to initial dataframes  #######################################################################
###############################################################################################################################################################

late = (pd.read_excel('Data/late.xlsx', skiprows=17)
        .query("Reviewer in ['Yin Man', 'Pauline Dong', 'Lucia Kim', 'Jennifer Carroll', 'Maxine Armstrong', 'Vanessa Coffey', 'Malika Ladha', 'Vivien Fong', 'Jehan Lalani Carbone', 'Danielle Anthony', 'Peter Yoo', 'Tommy Lam', 'Lucy Liu', 'Emily Ahola', 'Hanae Mohamed', 'Andrei Rotarus', 'Crystal Chui', 'Alan Lu', 'Arthur Zych', 'Ghazaleh EA', 'Elyanna Penafiel', 'Pete Quinn', 'Lara Said', 'Ken Ruan', 'Kate Lam']")
        .fillna(0)
        .rename({"num_late_new":"First", "num_late_rev":"Revision", "late_letters_new":"Late First Letters", "late_letters_rev":"Late Revision Letters" }, axis = 1)
        )

cei = pd.read_csv("Data/cei_repo.csv", skiprows=14)
sub = pd.read_csv("Data/sub_repo.csv", skiprows=41)

#For "getting to yes" table
sub1 = pd.read_csv("Data/sub_repo.csv", skiprows=41)

#For "getting to yes" graph
sub2 = pd.read_csv("Data/sub_repo.csv", skiprows=41)

#for tags:
tags = pd.read_csv('Data/tags_repo.csv', skiprows = 32)
tags2 = pd.read_csv('Data/tags_repo.csv', skiprows = 32)

###############################################################################################################################################################
###########################################################  DATA WRANGLING  ##################################################################################
###############################################################################################################################################################

#Wrangling needed for late reviews tab and cei tab. Whenever merging, the keys need to be the same dtype.
cei['efilesSubmissionid'] = cei['efilesSubmissionid'].astype(str)

###############################################################################################################################################################
#########################################################  DATA WRANGLING  FOR SUB ############################################################################
###############################################################################################################################################################

#Needed since some IsEnabled = 0 when people leave PAAB
sub['IsEnabled'] = 1

#Whenever merging, the keys need to be the same dtype.
sub['efilesSubmissionid'] = sub['efilesSubmissionid'].astype(str) 
# Keep early since needed for later for the code to work (i.e., merger code).    

#REPEAT EACH ROW BY THE NUMBER OF ITTERATIONS
#The `repeats(df['numIterations'])` function repeats a row by the number in the numIterations columns.
#But there is a catch. A column value of 1 does not cause a repeat, a column value of 2 causes 1 repeat, and so on. This is a problem since no iterations has a value of zero. A value of 1 means there is one iteration, and the row should be repeated once.
#So we first need to add 1 to each iteration value.
sub['numIterations'] = sub['numIterations'] + 1 
#sub = sub.loc[sub.index.repeat(sub['numIterations'])].reset_index(drop=True)

#TELL PANDAS HOW TO FIGURE OUT WHAT YEAR IT IS AND STORE THAT IN A VARIABLE CALLED `thisYear`
# Store the present year in a variable without hardcoding it (so that it changes automatically)
# the 1st says "From the datetime, focus on the date and fetch me the date corresponding to today"
# the 2nd line says "from today's date, fetch me the year"
todaysDate = dt.date.today()
thisYear = todaysDate.year

# TELL PANDAS HOW TO FILTER THE ROWS to `thisYear`
# you need to spell out datetime in to_datetime() as that is the name of that pandas function (i.e., referring to the function as opposed to the datetime module which you assigned an alias of dt to). 
# In the 2nd line, you contracted datetime to dt since thats how the module was imported.
# In the 2nd line you are saying "retrive the rows for which the datetime is subs.DateSubmitted has a year that equals the variable thisYear (which you defined above to change automatically each year)"
sub['DateSubmitted'] = pd.to_datetime(sub['DateSubmitted'])#function to convert this column's data type to datetime
subThisYr = sub[sub['DateSubmitted'].dt.year == thisYear]

##############################################
### Wrangling for subs monthly by reviewer ###
##############################################

#Going to need to organize by month so lets create a column for it
subThisYr['Month'] = subThisYr['DateSubmitted'].dt.strftime('%b')

subMonthlyByReviewer = subThisYr.groupby(['Month', 'Reviewer'])[['IsEnabled']].sum().unstack().fillna(0).astype(int).reindex()
# you use unstack() otherwise all months are in the same column for each reviewer
# you use fillna(0) otherwise you get NaN for each cell that has no value. In this case, you know that there is no value since it is zero.
# you use astype(int) since you get floats by default (the extra decimal adds pointless clutter)
# you use reindex() so that the month becomes the index. If you use your typical reset_index() your index is labelled 'Reviewer'.
month_dict = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}

#To put months in order:
subMonthlyByReviewer = subMonthlyByReviewer.sort_values('Month', key = lambda x : x.apply (lambda x : month_dict[x]))

# The above results in a multi-level index for columns. That will get messy so merge into a single level.
subMonthlyByReviewer.columns = [" ".join(c) for c in subMonthlyByReviewer.columns]

# Each column name now begins with "totSubs ", lets remove that prefix 
# use the python string method .str.replace() for the prefix while you'd use .str.rstrip() for a suffix
# The great thing is that these only impact these methods act on the column names that have the prefix/suffix and ignore the others (i.e., no error breaks the code if a name does not have the prefix/suffix)
subMonthlyByReviewer.columns = subMonthlyByReviewer.columns.str.replace('IsEnabled ','')
subMonthlyByReviewer

# With the transpose() function, flip the columns with the rows to make it easier to read.
# transpose() does not permanently change the dataframe, so you need to set it to a variable to make it permanent.
subMonthlyByReviewer = subMonthlyByReviewer.transpose()

#the `transpose()` function will make the reviewer names the index of the dataframe. That will create trouble later as Dash's DataTable does not handle the dataframe's index as a column (i.e, the "Reviewer" column won't be displayed in the dash app)
#To resolve this issue, you can reset the index of the dataframe, which will add the "Reviewer" column back into the dataframe. 
subMonthlyByReviewer = subMonthlyByReviewer.reset_index().rename(columns={'index': 'Reviewer'})

# You'll get an error when you try to find the sum across columns since one of your columns is a string datatype (i.e., Reviewer). So limit the sum to numeric only. 
subMonthlyByReviewer['Reviewer Total']=subMonthlyByReviewer.sum(axis='columns', numeric_only=True)

# add a row for totals of each numeric colums
subMonthlyByReviewer.loc['Month Total'] = subMonthlyByReviewer.sum(numeric_only=True) 
#best-practice to use numeric_only=True to avoid error from trying to sum the reviewer column


subMonthlyByReviewer = subMonthlyByReviewer.sort_values(by='Reviewer Total', ascending=False)

#months = subsThisYr.Month.nunique()#automatically adjusting number of months so far this year
subMonthlyByReviewer['Percent']=(subMonthlyByReviewer['Reviewer Total']/subMonthlyByReviewer.iloc[0]['Reviewer Total'])*100

#you had a dozen decimal places LOL. Fix that:
subMonthlyByReviewer['Percent'] = subMonthlyByReviewer['Percent'].round(2)

# Convert all numeric columns (except the last one) to integers
numeric_cols = subMonthlyByReviewer.select_dtypes(include=['float64']).columns
numeric_cols = numeric_cols[:-1]  # Exclude the last column

# To dispose of all the floats except "Percent"
subMonthlyByReviewer[numeric_cols] = subMonthlyByReviewer[numeric_cols].astype(int)
#The table is now stored under `subMonthlyByReviewer`

##############################################
#### New Column for breakdown of sub type ####
##############################################

#Ultimately for bar chart showing the type of submissions that make up each reviewer's total submission volume

#create a list of conditions (the order matters. i.e., for each row, pandas stops going down the list of conditions as soon as one is met):
conditions = [
    (subThisYr['IsRenewal'] == 1),
    (subThisYr['numIterations'] > 1),
    (subThisYr['isMinorRev'] == 1),
    (subThisYr['IsModularSubmission'] == 1),
    (subThisYr['IsSeriesChild'] == 1),
    (subThisYr['isNovel'] ==1),
    (subThisYr['IsRenewal'] !=1) & (subThisYr['numIterations'] == 1) & (subThisYr['isMinorRev'] != 1) & (subThisYr['IsModularSubmission'] != 1) & (subThisYr['IsSeriesChild'] != 1) & (subThisYr['isNovel'] !=1)              
]

#create a list of the values we want to assign to each condition
values = ['Renewal', 'Iteration', 'Minor Revision', 'Modular Submission', 'Series Child', 'Novel', 'All others']

#create a new column and use `np.select()` to assign the values to the corresponding conditions  
subThisYr['Type'] = np.select(conditions, values)


############################################################################################################################
#### Wrangling for eventual bar chart comparing reviewer volume at each level of new content pages (selected by slider) ####
############################################################################################################################


#create a python list of the ranges for the future categories
page_ranges = [0, 2, 4, 7, 11, 20, 30, 40, 50, float('inf')]#float('inf') means 'to positive infinity'


#create a new colummn "NewContentRange" based on the existing column "PagesOfNewContent". Pass the python list page_ranges into the bin parameter.
subThisYr["NewContentRange"] = pd.cut(subThisYr["PagesOfNewContent"], bins=page_ranges, labels=['<2', '2-3', '4-6', '7-10','11-19','20-29','30-39','40-49','50+'])
subThisYr.NewContentRange.fillna('<2', inplace=True)#Need inplace=True or the effect won't carry over to future operations!! Still a bit over 2000 NaN prior to running this. Eliminating renewals removed 12k of them!!

subThisYr.sort_values(by='NewContentRange', inplace=True)#Needed so that the values in the animation slide ruler are in sequential order. Again, you need inplace=True


############################################################################################
####### For bar chart comparing average # of comments per file across each reviewer ########
############################################################################################

comments = subThisYr.groupby(["Reviewer"])[["numComments", "IsEnabled"]].sum().reset_index()
comments["avg number of comments per docket"] = comments["numComments"]/comments["IsEnabled"]




###############################################################################################################################################################
#########################################################  DATA WRANGLING  FOR LATE ############################################################################
###############################################################################################################################################################


######################################################################
################## Create late_sub_merge dataframe ###################
######################################################################

late = (pd.read_excel('Data/late.xlsx', skiprows=17)
        .query("Reviewer in ['Yin Man', 'Pauline Dong', 'Lucia Kim', 'Jennifer Carroll', 'Maxine Armstrong', 'Vanessa Coffey', 'Malika Ladha', 'Vivien Fong', 'Jehan Lalani Carbone', 'Danielle Anthony', 'Peter Yoo', 'Tommy Lam', 'Lucy Liu', 'Emily Ahola', 'Hanae Mohamed', 'Andrei Rotarus', 'Crystal Chui', 'Alan Lu', 'Arthur Zych', 'Ghazaleh EA', 'Elyanna Penafiel', 'Pete Quinn', 'Lara Said', 'Ken Ruan', 'Kate Lam']")
        .fillna(0)
        .rename({"num_late_new":"First", "num_late_rev":"Revision", "late_letters_new":"Late First Letters", "late_letters_rev":"Late Revision Letters" }, axis = 1)
        )


#Duplicate the two columns of interest
late['Late First Letters Copy'] = late.loc[:, 'Late First Letters']#duplicate this column
late['Late Revision Letters Copy'] = late.loc[:, 'Late Revision Letters']#duplicate this columns

#replace 0 with nan so that you can then combine the columns separated by ',' except for nan
late['Late First Letters Copy'].replace(0, np.nan, inplace=True)
late['Late Revision Letters Copy'].replace(0, np.nan, inplace=True)
late['letterid'] = late[['Late First Letters Copy', 'Late Revision Letters Copy']].apply(lambda x: ','.join(x[x.notnull()]), axis=1)   

#create new row for each coma separated efilesSubmissionId
late = (late.assign(LetterId = late['letterid'].str.split(','))
        .explode('LetterId')
        .reset_index(drop=True))

#Use `str.split()` method to split the string after a stated character (a dash in this case as the file numbers are in the xxxxx-01 format), then use the `str.get() method to get the first part of the split string
late['efilesSubmissionid'] = late['LetterId'].str.split('-').str.get(0)#`str.get('0')` gets the string segment before the stated character while `str.get(-1)` gets the element after the stated character
late['LetterType'] = late['LetterId'].str.split('-').str.get(-1)

#late['LetterType'] = late.loc[:, 'LetterId']#duplicate this column
late.loc[late['LetterType'] == '01', 'LetterType'] = "New Letter" 
late.loc[late['LetterType'] != 'New Letter', 'LetterType'] = "Revision Letter" 


#late['efilesSubmissionid'].count()#48
#late['efilesSubmissionid'].nunique()#38
#print(late['efilesSubmissionid'].duplicated())
#late

#sub = pd.read_csv("sub_repo.csv", skiprows=41) ALREADY ABOVE

#merge the datasets. To do so, you must first make the column key the same datatype in both datasets
late['efilesSubmissionid'] = late['efilesSubmissionid'].astype(str)
#sub['efilesSubmissionid'] = sub['efilesSubmissionid'].astype(str) 

late_sub_merge = pd.merge(late.loc[:,['Reviewer', 'LetterId', 'efilesSubmissionid', 'LetterType']], sub.loc[:,['efilesSubmissionid', 'UrgencyLevel', 'Product']], on='efilesSubmissionid', how="inner") 
late_sub_merge['IsEnabled'] = 1

###ANONYMIZED REVIEWERS
# Manually created dictionary mapping from reviewers to letters (so that alphabet letter appears in place of reviewer name)
reviewer_map = {
    'Yin Man': 'A',
    'Pauline Dong': 'B',
    'Lucia Kim': 'C',
    'Jennifer Carroll': 'D',
    'Maxine Armstrong': 'E',
    'Vanessa Coffey': 'F',
    'Malika Ladha': 'G',
    'Vivien Fong': 'H',
    'Jehan Lalani Carbone': 'I',
    'Danielle Anthony': 'J',
    'Peter Yoo': 'K',
    'Tommy Lam': 'L',
    'Lucy Liu': 'M',
    'Emily Ahola': 'N',
    'Hanae Mohamed': 'O',
    'Andrei Rotarus': 'P',
    'Crystal Chui': 'Q',
    'Alan Lu': 'R',
    'Arthur Zych': 'S',
    'Ghazaleh EA': 'T',
    'Elyanna Penafiel': 'U',
    'Pete Quinn': 'V',
    'Lara Said': 'W',
    'Ken Ruan': 'X',
    'Kate Lam': 'Y'
}

# Replace the 'Reviewer' column values with the mapped letters
late_sub_merge['Reviewer'] = late_sub_merge['Reviewer'].map(reviewer_map)

######################################################################
###################### Wrangle data FOR CEI ##########################
######################################################################


# Load your data
# Make sure your data is in the correct format, CSV files are just placeholders

subForCEI = sub[sub.CEI_Q1 > 0]

#######cei['efilesSubmissionid'] = cei['efilesSubmissionid'].astype(str)#Key must be same dtype in both merged dataframea

#pd.set_option('display.max_columns', None)
cei_sub_merge = pd.merge(cei, subForCEI, on="efilesSubmissionid", how="right")
cei_sub_merge = cei_sub_merge[['CEI_Q1', 'Q1Comment', 'CEI_Q2', 'Q2Comment', 'CEI_Q3', 'Q3Comment', 'Q4Comment', 'CEI_Q5', 'Q5Comment', 'Reviewer', "status"]]
cei_sub_merge['Count'] = 1
cei_sub_merge_quant = cei_sub_merge[cei_sub_merge["status"] != 'Quick Complete'].copy()

#anonymize the dropdown options:
#Basically you want to accomplish the following:
# cei_sub_merge_quant["Reviewer"] = cei_sub_merge_quant["Reviewer"].map(reviewer_map)
# While this works, it results in a warning that pandas isn't certain whether you're working with a `view` or `copy` of the DataFrame.
# The following eliminates the warning. The `.loc` accessor is a more explicit way of modifying the DataFrame. It assures pandas that you're modifying the DataFrame itself and not a temporary view or copy.  
cei_sub_merge_quant.loc[:, "Reviewer"] = cei_sub_merge_quant["Reviewer"].map(reviewer_map)
# had you been working with a copy, you could have been explicit by adding `.copy()` as you did immediately above

avg_scores = cei_sub_merge_quant.groupby("Reviewer").agg({"CEI_Q5": "mean", "Count": "size"}).reset_index()
avg_scores.columns = ["Reviewer", "Mean Q5 Score", "Count of completed CEIs"]
avg_scores["Mean Q5 Score"] = avg_scores["Mean Q5 Score"].round(2)

#prep to pass the anonymized values into the dropdown selector
# it is essential that the dropdown does not have NaN values (this broke your code) and that the values we try putting in the dropdown options are strings. Filter out NaN values and ensure all reviewers are strings
valid_reviewers = [str(reviewer) for reviewer in cei_sub_merge_quant["Reviewer"].dropna().unique()]

#Prep for eventual creation of comment tables
def generate_comment_table(filtered_data, score_col, comment_col):
    df_comments = filtered_data[[score_col, comment_col]].dropna(subset=[comment_col])
    if not df_comments.empty:
        return dash_table.DataTable(
            columns=[
                {"name": score_col, "id": score_col},
                {"name": comment_col, "id": comment_col}                
            ],
            data=df_comments.to_dict('records'),
            sort_action="native",
            sort_mode="single",
            style_cell={'textAlign': 'left'},
            style_header={
                'backgroundColor': "#ececec",
                'fontWeight': 'bold'
            },
            #style_table={'overflowX': 'scroll'},
            #page_size=10,
        )
    return html.Div(f"No comments available for {comment_col}")

###########################################################################################################################################################
#############################################################  Wrangling for getting to Yes  ##############################################################
###########################################################################################################################################################
#table 1
revision_to_approval_overall = (
    sub1
    .query("Reviewer in ['Yin Man', 'Pauline Dong', 'Lucia Kim', 'Jennifer Carroll', 'Maxine Armstrong', 'Vanessa Coffey', 'Malika Ladha', 'Vivien Fong', 'Jehan Lalani Carbone', 'Danielle Anthony', 'Peter Yoo', 'Tommy Lam', 'Lucy Liu', 'Emily Ahola', 'Hanae Mohamed', 'Andrei Rotarus', 'Crystal Chui', 'Alan Lu', 'Arthur Zych', 'Ghazaleh EA', 'Elyanna Penafiel', 'Pete Quinn', 'Lara Said', 'Ken Ruan', 'Kate Lam']")
    .groupby("Reviewer")
    .agg({"RevisionsTotal": "mean"})
    .round(2)
    .reset_index()
    .rename(columns={"RevisionsTotal": "Revisions to approval (overall)"})  # Renaming the column here
    .sort_values(by='Revisions to approval (overall)', ascending=True)  # Make sure to also update the column name here
)
# Replace the 'Reviewer' column values with the mapped letters from above dictionary
revision_to_approval_overall['Reviewer'] = revision_to_approval_overall['Reviewer'].map(reviewer_map)

#table 2
revision_to_approval_novel = (
    sub1
    .query("isNovel == 1")
    .query("Reviewer in ['Yin Man', 'Pauline Dong', 'Lucia Kim', 'Jennifer Carroll', 'Maxine Armstrong', 'Vanessa Coffey', 'Malika Ladha', 'Vivien Fong', 'Jehan Lalani Carbone', 'Danielle Anthony', 'Peter Yoo', 'Tommy Lam', 'Lucy Liu', 'Emily Ahola', 'Hanae Mohamed', 'Andrei Rotarus', 'Crystal Chui', 'Alan Lu', 'Arthur Zych', 'Ghazaleh EA', 'Elyanna Penafiel', 'Pete Quinn', 'Lara Said', 'Ken Ruan', 'Kate Lam']")
    .groupby("Reviewer")
    .agg({"RevisionsTotal": "mean"})
    .round(2)
    .reset_index()
    .rename(columns={"RevisionsTotal": "Revisions to approval (novel subs only)"})  # Renaming the column here
    .sort_values(by='Revisions to approval (novel subs only)', ascending=True)  # Make sure to also update the column name here
)
# Replace the 'Reviewer' column values with the mapped letters from above dictionary
revision_to_approval_novel['Reviewer'] = revision_to_approval_novel['Reviewer'].map(reviewer_map)

#table 3
tot_PAAB_days_to_approval = (
    sub1
    .query("Reviewer in ['Yin Man', 'Pauline Dong', 'Lucia Kim', 'Jennifer Carroll', 'Maxine Armstrong', 'Vanessa Coffey', 'Malika Ladha', 'Vivien Fong', 'Jehan Lalani Carbone', 'Danielle Anthony', 'Peter Yoo', 'Tommy Lam', 'Lucy Liu', 'Emily Ahola', 'Hanae Mohamed', 'Andrei Rotarus', 'Crystal Chui', 'Alan Lu', 'Arthur Zych', 'Ghazaleh EA', 'Elyanna Penafiel', 'Pete Quinn', 'Lara Said', 'Ken Ruan', 'Kate Lam']")
    .query("Status == 6 and Date > '2023-02-09'")  # Filtering for dates after the end of February
    .groupby("Reviewer")
    .agg({"paabFromSubmitted": "mean"})
    .round(2)
    .reset_index()
    .rename(columns={"paabFromSubmitted": "Avg PAAB days from distribution to approval (overall)"})  # Renaming the column here
    .sort_values(by='Avg PAAB days from distribution to approval (overall)', ascending=True)  # Make sure to also update the column name here
)
# Replace the 'Reviewer' column values with the mapped letters from above dictionary
tot_PAAB_days_to_approval['Reviewer'] = tot_PAAB_days_to_approval['Reviewer'].map(reviewer_map)

#table 4
novel_PAAB_days_to_approval = (
    sub1
    .query("isNovel == 1")
    .query("Reviewer in ['Yin Man', 'Pauline Dong', 'Lucia Kim', 'Jennifer Carroll', 'Maxine Armstrong', 'Vanessa Coffey', 'Malika Ladha', 'Vivien Fong', 'Jehan Lalani Carbone', 'Danielle Anthony', 'Peter Yoo', 'Tommy Lam', 'Lucy Liu', 'Emily Ahola', 'Hanae Mohamed', 'Andrei Rotarus', 'Crystal Chui', 'Alan Lu', 'Arthur Zych', 'Ghazaleh EA', 'Elyanna Penafiel', 'Pete Quinn', 'Lara Said', 'Ken Ruan', 'Kate Lam']")
    .query("Status == 6 and Date > '2023-02-09'")  # Filtering for dates after the end of February
    .groupby("Reviewer")
    .agg({"paabFromSubmitted": "mean"})
    .round(2)
    .reset_index()
    .rename(columns={"paabFromSubmitted": "Avg PAAB days from distribution to approval (novel)"})  # Renaming the column here
    .sort_values(by='Avg PAAB days from distribution to approval (novel)', ascending=True)  # Make sure to also update the column name here
)
# Replace the 'Reviewer' column values with the mapped letters from above dictionary
novel_PAAB_days_to_approval['Reviewer'] = novel_PAAB_days_to_approval['Reviewer'].map(reviewer_map)

#table 5
tot_days_to_approval = (
    sub1
    .query("Reviewer in ['Yin Man', 'Pauline Dong', 'Lucia Kim', 'Jennifer Carroll', 'Maxine Armstrong', 'Vanessa Coffey', 'Malika Ladha', 'Vivien Fong', 'Jehan Lalani Carbone', 'Danielle Anthony', 'Peter Yoo', 'Tommy Lam', 'Lucy Liu', 'Emily Ahola', 'Hanae Mohamed', 'Andrei Rotarus', 'Crystal Chui', 'Alan Lu', 'Arthur Zych', 'Ghazaleh EA', 'Elyanna Penafiel', 'Pete Quinn', 'Lara Said', 'Ken Ruan', 'Kate Lam']")
    .query("Status == 6 and Date > '2023-02-09'")  # Filtering for dates after the end of February
    .assign(TotalFromSubmitted=lambda x: x['paabFromSubmitted'] + x['clientFromSubmitted'])  # Creating a new column that is the sum of 'paabFromSubmitted' and 'clientFromSubmitted'
    .groupby("Reviewer")
    .agg({"TotalFromSubmitted": "mean"})  # Calculating the mean of the new column
    .round(2)
    .reset_index()
    .rename(columns={"TotalFromSubmitted": "Avg total days from distribution to approval (overall)"})  # Renaming the column to reflect the new calculation
    .sort_values(by='Avg total days from distribution to approval (overall)', ascending=True)  # Sorting by the new column
)
# Replace the 'Reviewer' column values with the mapped letters from above dictionary
tot_days_to_approval['Reviewer'] = tot_days_to_approval['Reviewer'].map(reviewer_map)

#table 6
novel_days_to_approval = (
    sub1
    .query("isNovel == 1")
    .query("Reviewer in ['Yin Man', 'Pauline Dong', 'Lucia Kim', 'Jennifer Carroll', 'Maxine Armstrong', 'Vanessa Coffey', 'Malika Ladha', 'Vivien Fong', 'Jehan Lalani Carbone', 'Danielle Anthony', 'Peter Yoo', 'Tommy Lam', 'Lucy Liu', 'Emily Ahola', 'Hanae Mohamed', 'Andrei Rotarus', 'Crystal Chui', 'Alan Lu', 'Arthur Zych', 'Ghazaleh EA', 'Elyanna Penafiel', 'Pete Quinn', 'Lara Said', 'Ken Ruan', 'Kate Lam']")
    .query("Status == 6 and Date > '2023-02-09'")  # Filtering for dates after the end of February
    .assign(TotalFromSubmitted=lambda x: x['paabFromSubmitted'] + x['clientFromSubmitted'])  # Creating a new column that is the sum of 'paabFromSubmitted' and 'clientFromSubmitted'
    .groupby("Reviewer")
    .agg({"TotalFromSubmitted": "mean"})  # Calculating the mean of the new column
    .round(2)
    .reset_index()
    .rename(columns={"TotalFromSubmitted": "Avg total days from distribution to approval (novel)"})  # Renaming the column to reflect the new calculation
    .sort_values(by='Avg total days from distribution to approval (novel)', ascending=True)  # Sorting by the new column
)
# Replace the 'Reviewer' column values with the mapped letters from above dictionary
novel_days_to_approval['Reviewer'] = novel_days_to_approval['Reviewer'].map(reviewer_map)

########  Merging the above 6 tables #######
# Merge the overall revision to approval with the novel revision to approval
merged_yes = pd.merge(
    revision_to_approval_overall,
    revision_to_approval_novel,
    on="Reviewer",
    how="outer"
)

# Merge the result with the total PAAB days to approval
merged_yes = pd.merge(
    merged_yes,
    tot_PAAB_days_to_approval,
    on="Reviewer",
    how="outer"
)

# Merge the result with the novel PAAB days to approval
merged_yes = pd.merge(
    merged_yes,
    novel_PAAB_days_to_approval,
    on="Reviewer",
    how="outer"
)

# Merge the result with the total days to approval
merged_yes = pd.merge(
    merged_yes,
    tot_days_to_approval,
    on="Reviewer",
    how="outer"
)

# Finally, merge the result with the novel days to approval
merged_yes = pd.merge(
    merged_yes,
    novel_days_to_approval,
    on="Reviewer",
    how="outer"
)
#The final table is called merged_yes


####### Now the graph!! #####
# create a python list of the ranges for the future categories
page_ranges = [0, 2, 4, 7, 11, 20, 30, 40, 50, float('inf')]  # float('inf') means 'to positive infinity'
# create a new colummn "NewContentRange" based on the existing column "PagesOfNewContent". 
sub2["NewContentRange"] = pd.cut(sub2["PagesOfNewContent"], bins=page_ranges, labels=['<2', '2-3', '4-6', '7-10','11-19','20-29','30-39','40-49','50+'])
sub2.NewContentRange.fillna('<2', inplace=True)
# Group by "Reviewer" and "NewContentRange", then calculate the mean of "RevisionsTotal"
avg_revisions = sub2.groupby(["Reviewer", "NewContentRange"]).agg({"RevisionsTotal": "mean"}).round(2).reset_index()
# Replace the 'Reviewer' column values with the mapped letters from above dictionary
avg_revisions['Reviewer'] = avg_revisions['Reviewer'].map(reviewer_map)
fig_rev_to_approval = px.bar(
    avg_revisions,
    x='Reviewer',
    y='RevisionsTotal',
    animation_frame='NewContentRange',
    hover_data=['Reviewer', 'NewContentRange', 'RevisionsTotal']
)
# Update the layout
fig_rev_to_approval.update_layout(
    height=800,
    yaxis_title='Avg Revisions To Approval', 
    xaxis_title='Reviewer',
    yaxis=dict(range=[0, 10])# otherwise bars get too big
)
# Remove the updatemenus
fig_rev_to_approval.layout.pop("updatemenus", None)
### Graph is called fig_rev_to_approval 



##############################################################################################################################################################
##########################################################################  Tags  ############################################################################
##############################################################################################################################################################

# Number of file clarification phone calls
tags['ReviewerName'] = tags['ReviewerName'].map(reviewer_map)
dfCalls = tags[tags['Duration']!=0].copy()#not looking to change df
dfCalls['IsEnabled'] = 1
figCalls = px.bar(
    dfCalls,
    x='ReviewerName',
    y='IsEnabled',
    hover_data=['TicketID', 'ProductName']
).update_layout(yaxis_title="# of review calls<br>associated with the reviewer's dockets")
#).update_layout(plot_bgcolor="rgba(0,0,0,0)", yaxis_title='# of review calls')
#graph name is figCalls

#Number of each reviewer tag issued
dfTag = tags2.dropna(subset = ['Tag'])
dfTagPythonList = dfTag.assign(Tag=dfTag['Tag'].str.split(','))##turn the comma separated values in the tag column into python lists
dfTagExplode = dfTagPythonList.explode('Tag')#explode the python list such that each list containing more than one tag are separate rows containing a single tag 
dfTagExplode['Tag'] = dfTagExplode['Tag'].astype("category")# set the datatype for the tag column as categorical data
dfTagExplode['IsEnabled'] = 1#for counting later
a = ' Reviewer -  30 Comments or more'
b = ' Reviewer - Confrontational Client'
c = ' Reviewer - Discreditable'
d = ' Reviewer - Misleading Submission Info'
e = ' Reviewer - Misrepresentation of facts'
f = ' Reviewer - Poor Submission'
g = ' Reviewer - Previously Rejected Claims'
h = ' Reviewer - Prior APS client distributed does not match prior approval'
i = ' Reviewer - Push back on clear no'
j = ' Reviewer - Undeclared Unsolicited Change'
k = ' Reviewer - Declared Unsolicited Change'
revTag = dfTagExplode[(dfTagExplode['Tag'] == a) | (dfTagExplode['Tag'] == b) | (dfTagExplode['Tag'] == c) | (dfTagExplode['Tag'] == d) | (dfTagExplode['Tag'] == e) | (dfTagExplode['Tag'] == f) | (dfTagExplode['Tag'] == g) | (dfTagExplode['Tag'] == h) | (dfTagExplode['Tag'] == i) | (dfTagExplode['Tag'] == j) | (dfTagExplode['Tag'] == k)]
#px.histogram(revTag, x ='Tag')
revTag = revTag.copy()
revTag['IsEnabled'] = 1
figRevTag = px.bar(
    revTag,
    x='Tag',
    y='IsEnabled',
    color='SubmissionCompanyName',
    hover_data=['TicketID', 'SubmissionCompanyName', 'ProductName', 'TherapeuticArea', 'Manufacturer']
).update_layout(yaxis_title='# of each tag issued by the review team', height=1050)
# graph name is figRevTag

#Number of tags issued by each reviewer
revTag = revTag.copy()
revTag['ReviewerName'] = revTag['ReviewerName'].map(reviewer_map)
revTag['Tag'] = revTag['Tag'].astype(str)
figRevTag2 = px.bar(
    revTag,
    x='ReviewerName',
    y='IsEnabled',
    color='Tag',
    hover_data=['TicketID', 'SubmissionCompanyName', 'ProductName', 'TherapeuticArea', 'Manufacturer']
).update_layout(yaxis_title='# of tags issued by each reviewer', xaxis_title='Reviewer', height=800)
# graph name is figRevTag2

#Escalation by agency
aa = ' Reviewer - Escalation -- Other Solution'
bb = ' Reviewer - Escalation -- PAAB Overturned'
cc = ' Reviewer - Escalation -- PAAB sustained'
escalations = dfTagExplode[(dfTagExplode['Tag'] == aa) | (dfTagExplode['Tag'] == bb) | (dfTagExplode['Tag'] == cc)]
#px.histogram(escalations, x='Tag')
figEsc = px.bar(
    escalations,
    x='Tag',
    y='IsEnabled',
    color='SubmissionCompanyName',
    hover_data=['TicketID', 'SubmissionCompanyName', 'ProductName', 'TherapeuticArea', 'Manufacturer']
).update_layout(yaxis_title='# of escalations', xaxis_title='Escalation outcome tag')
#graph name is figEsc

#Escalation by reviewer
escalations = escalations.copy()
escalations['ReviewerName'] = escalations['ReviewerName'].map(reviewer_map)
figEsc2 = px.bar(
    escalations,
    x="ReviewerName",
    y="IsEnabled",
    hover_data=['TicketID', 'SubmissionCompanyName', 'ProductName', 'Manufacturer', 'Tag']
)
figEsc2.update_layout(yaxis_title='# of escalations by reviewer', xaxis_title='Reviewer').update_yaxes(dtick=1)  # This sets the y-axis increments to 1
#graph called figEsc2

#Office-wide client tags
aaa = ' Client - Confrontational PAAB representative'
bbb = ' Client - Consider changing the codeguidance'
ccc = ' Client - Incomplete review perceived to be unwarranted'
ddd = ' Client - Inconsistency perceived because objection to content previously approved for the brand was maintained after directing PAAB to the prior approval file'
eee = ' Client - Inconsistency perceived because objection was maintained after demonstrating that the same presentation was approved for a different brand'
fff = ' Client - Issue which is perceived to be new was raised late in the review'
ggg = ' Client - Late correspondence impacted client'
hhh = ' Client - PAAB did not return call at agreed upon time'
iii = ' Client - Particularly helpful comment discussion or action'
jjj = ' Client - Perceived Issue with level of expertise'
kkk = ' Client - Ruling perceived to be inconsistent with codeguidance'
lll = ' Client - The requested revision was unclear to me even following a clarification phone call'
clientTag = dfTagExplode[(dfTagExplode['Tag'] == aaa) | (dfTagExplode['Tag'] == bbb) | (dfTagExplode['Tag'] == ccc) | (dfTagExplode['Tag'] == ddd) | (dfTagExplode['Tag'] == eee) | (dfTagExplode['Tag'] == fff) | (dfTagExplode['Tag'] == ggg) | (dfTagExplode['Tag'] == hhh) | (dfTagExplode['Tag'] == iii) | (dfTagExplode['Tag'] == jjj) | (dfTagExplode['Tag'] == kkk) | (dfTagExplode['Tag'] == lll)]
#px.histogram(clientTag, x='Tag')
figClientTag = px.bar(
    clientTag,
    x='Tag',
    y='IsEnabled',
    color='SubmissionCompanyName',
    hover_data=['SubmissionCompanyName', 'TherapeuticArea', 'Manufacturer']
).update_layout(yaxis_title='# of client created tags', height=800)
#graph called figClientTag

#client tags by reviewer
# Create bar graph identifying the tag in each count. Maybe use colour for the tag. 
#clientTag['Tag'] = clientTag['Tag'].astype(str)#The bar plot was otherwise generating an error with the tags as categorical data. Categorical data in pandas often has both visible categories (the ones present in your data) and invisible categories (the ones that are possible but not present in your data). When trying to assign colors to categories, Plotly Express might get confused if there's a mismatch or unexpected behavior due to these invisible categories.
#The following two lines were needed to address warning: A value is trying to be set on a copy of a slice from a DataFrame. Try using .loc[row_indexer,col_indexer] = value instead
clientTag = clientTag.copy()
clientTag['Tag'] = clientTag['Tag'].astype(str)
clientTag['ReviewerName'] = clientTag['ReviewerName'].map(reviewer_map)
figClientTag2 = px.bar(
    clientTag,
    x='ReviewerName',
    y='IsEnabled',
    color= 'Tag',
    #title="Click on one or more types from the legend to exclude from the report",
    hover_data=['Tag']
).update_layout(yaxis_title='Client tags by reviewer (unaudited)', xaxis_title='Reviewer', legend_font_size=8)#reduced font size since graph is otherwise too narrow due to width of legend
#graph called figClientTag2

#Validated tags graph
#Just add a column called 'Valid' give value of 0 (false) or 1 (True)
auditTag = pd.read_excel('Data/auditTag.xlsx', skiprows = 1)
auditTag['IsEnabled'] = 1
auditTag['ReviewerName'] = auditTag['ReviewerName'].map(reviewer_map)
figAudited = px.bar(
    auditTag,
    x='ReviewerName',
    y='IsEnabled',
    color= 'Tag',
    hover_data=['Tag']
).update_layout(yaxis_title='Validated client tags by reviewer (audited)', xaxis_title='Reviewer', legend_font_size=8)
#graph called figAudited

##############################################################################################
#############################################  Authentication ################################
##############################################################################################

VALID_USERNAME_PASSWORD_PAIRS = {
   'PatrickM' : 'mister',
   'DanielleD' : 'apple',
   'YinM' : 'orange'
}


###############################################################################################################################################################
#######################################################  START DASH APP AND LAYOUT  ###########################################################################
###############################################################################################################################################################

table1 = dbc.Table.from_dataframe(subMonthlyByReviewer, striped=True, bordered=True, hover=True)
table2 = dbc.Table.from_dataframe(avg_scores, striped=True, bordered=True, hover=True)
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

auth = dash_auth.BasicAuth(
   app,
   VALID_USERNAME_PASSWORD_PAIRS
)

app.layout = html.Div([
        html.H1("eFiles data. Dataset includes up to the end of October."),
        html.P("Click on the tab of interest:"),
        dcc.Tabs(
            id="tabs",
            children=[
######################################################################
######################## Beginning of Tab 1 ##########################
######################################################################
                dcc.Tab(
                    label="Review quantity & complexity",
                    value="tab1",
                    children=[
                       html.Br(),
                       html.H2("Total Submission Volume (as assigned to each reviewer)"),
                       html.P("The primary purpose of including reviewer names on this page is to help clarify why files will occasionally be distributed to coverage reviewers even when the primary reviewer is not off distribution. Note that files are distributed to individuals in consideration of file-load fairness, concurrent projects/responsibilities, developmental factors, and availability. Reviewer's do not exercise direct control over the volume of files they are assigned, and so relative volume is only interpreted by the team's supervisor in consideration of the complete/broader context. As an aside, anyone who has completed a submission is included (even if they are no longer part of the team) for the sake of easily auditable totals."),
                       dbc.Col([table1]),
                       html.Br(),
                       html.H2("Total Submission Volume Broken Down By Submission Type (as assigned to each reviewer)"),          
                       html.P("Click on one or more 'Types' in the legend on the right side to narrow the graph output by excluding them from the report."),
                       html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar."),
                       html.P("A novel submission is a submission that includes significant new content that require extensive review. Examples include: New product launch, new indication for an existing product, new data presentation, new studies, new creative campaign, new visuals, new APS format/functionality."),
                       dcc.Graph(figure= 
                                 px.bar(
                                    subThisYr,
                                    x='Reviewer',
                                    y='IsEnabled',
                                    color='Type',
                                    #title="Click on one or more types from the legend on the right side to exclude from the report",
                                    hover_data=['Product', 'efilesSubmissionid']#SOMEONE SHOULD REVIEW USE OF NOVEL (hence inclusion of eFile#)
                                 ).update_layout(height=900, plot_bgcolor="rgba(0,0,0,0)", yaxis_title='Total submissions', xaxis_title=None)),#making the chart taller makes the colour visible EVEN if they are counts!!)
                        html.H2("Submission Volume at Various Levels of Pages of New Content (as assigned to each reviewer)"),
                        html.P("Drag the slider below the graph to change the graph output according to the corresponding number of pages of new content."),
                        html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar."),
                        dcc.Graph(figure=
                                  (lambda f: (f["layout"].pop("updatemenus"), f)[1])(
                                        px.bar(
                                            subThisYr,
                                            x='Reviewer',
                                            y='IsEnabled',
                                            animation_frame='NewContentRange',
                                            hover_data=['Product', 'efilesSubmissionid']#SOMEONE SHOULD REVIEW USE OF NOVEL (hence inclusion of eFile#)
                                        ).update_layout(
                                            height=900,#making the chart taller makes the colour visible EVEN if they are counts!! 
                                            plot_bgcolor="rgba(0,0,0,0)", 
                                            yaxis_title='Total submissions', 
                                            xaxis_title=None
                                        )
                                    )),
                                        #Same as above
                                        #fig = px.bar(
                                        #    subThisYr,
                                        #    x='Reviewer',
                                        #    y='IsEnabled',
                                        #    animation_frame='NewContentRange',
                                        #    hover_data=['Product', 'efilesSubmissionid']#SOMEONE SHOULD REVIEW USE OF NOVEL (hence inclusion of eFile#)
                                        #).update_layout(height=800, plot_bgcolor="rgba(0,0,0,0)", yaxis_title= 'Total submissions', xaxis_title=None)#making the chart taller makes the colour visible EVEN if they are counts!!)
                        html.H2("Average Number of Comments Per eFile Docket (as assigned to each reviewer)"),
                        html.P("Hover over any bar to reveal the exact mean to two decimal places."),
                        dcc.Graph(figure=
                                 px.bar(
                                    comments,
                                    x='Reviewer',
                                    y='avg number of comments per docket'
                                ).update_layout(xaxis_title=None)
                           
                        )                         

                    ]
                ),
######################################################################
######################## Beginning of Tab 2 ##########################
######################################################################
                dcc.Tab(
                    label="Timeliness",
                    value="tab2",
                    children=[
                        html.H1("Late Review Letters Report"),
                        html.P("If you aren't on the x-axis, it's because there is no late letters associated with the files you have been assigned."),
                        html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar. This is intended to help you identify any errors that may exist in how eFiles tracked letter or submission timing."),
                        html.P("Remove the checkmark from any combination of urgency levels that you'd like to exclude from the output:"),                    
                        dcc.Checklist(
                                id="urgency",
                                options=[
                                    "STANDARD",
                                    "ARO-10",
                                    "ARO-7",
                                    "ARO-4",
                                    "ARO-2"
                                ],
                                labelStyle={'display': 'inline-block', 'padding-right':'20px'},
                                value=["STANDARD", "ARO-10", "ARO-7", "ARO-4", "ARO-2"]
                        ),
                        dcc.Graph(id="graph")
                    ]
                ),
######################################################################
######################## Beginning of Tab 3 ##########################
######################################################################
                dcc.Tab(
                    label="Customer Experience",
                    value="tab3",
                    children=[
                          html.H2("Question 5 from the CEI: Rate Your Overall Experience With This Particular Review (1=Highly -ve   10=Highly +ve). Boxplot and mean/count table"),
                          dbc.Row([
                              dbc.Col([
                                  dcc.Graph(figure=px.box(cei_sub_merge_quant, y="Reviewer", x="CEI_Q5", height=1200).update_layout(
                                      yaxis=dict(titlefont=dict(size=24), tickfont=dict(size=24)),
                                      xaxis=dict(titlefont=dict(size=24)),
                                      hoverlabel=dict(font_size=24)
                                  ))
                              ], width=8),
                              dbc.Col([
                                  table2
                              ], width=2),
                          ]),
                          html.H3("Select a reviewer:"),
                          # Construct the dropdown with the validated reviewers
                          dcc.Dropdown(
                              id="reviewer_selector",
                              options=[{'label': reviewer, 'value': reviewer} for reviewer in valid_reviewers]
                          ),
                          dcc.Graph(id="express_chart"),
                          dcc.Graph(id="subplots"),
                          html.H1("Client comments"),
                          html.P("We've only extracted elements that could reveal the file/client. We have not removed reviewer names as they may refer to a coverage reviewer."),
                          html.H3("Comments relating to perceived helpfulness and responsiveness"),
                          html.Div(id='q1-comments', className='comment-table'),
                          html.Br(),
                          html.H3("Comments relating to perceived clarity"),
                          html.Div(id='q2-comments', className='comment-table'),
                          html.Br(),
                          html.H3("Comments relating to perceived consistency"),
                          html.Div(id='q3-comments', className='comment-table'),
                          html.Br(),
                          html.H3("Other comments not covered by the above topics"),
                          html.P("NOTE: There is no numeric score associated with this field so Q5 score is included for sorting purposes"),
                          html.Div(id='q4-comments', className='comment-table'),
                          html.Br(),
                          html.H3("Comments relating to overall experience"),
                          html.Div(id='q5-comments', className='comment-table'),
                   ]
                ),

######################################################################
######################## Beginning of Tab 4 ##########################
######################################################################
                dcc.Tab(
                    label="Guiding to 'yes'",
                    value="tab4",
                    children=[
                       html.P("Sort by clicking on the column arrow direction that you wish to sort by. Multi-sort is enabled for this table so if the sort output appears not to be behaving as expected, check that you have not inadvertently kept a prior sort action active."),
                       html.P("A blank cell merely indicates insufficient data to perform the requested operation (e.g., insufficient number of approved novel submissions)."),
                       html.Div([
                            dash_table.DataTable(
                            id='table_yes',
                            columns=[{"name": i, "id": i} for i in merged_yes.columns],
                            data=merged_yes.to_dict('records'),
                            style_table={'height': '800px', 'overflowY': 'auto'},
                            sort_action="native",# Enable sorting on the front-end
                            sort_mode="multi",# Allow multi-column sorting
                            style_cell={"maxWidth":'150px'},
                            style_header={'whiteSpace':'normal', 'height':'auto'}
                            )
                        ]),
                        html.Br(),
                        html.P("For the following graph, drag the slider to the % new content range of interest to you."),
                        dcc.Graph(figure = fig_rev_to_approval),
                    ]
                ),
######################################################################
######################## Beginning of Tab 5 ##########################
######################################################################
                dcc.Tab(
                    label="Tags",
                    value="tab5",
                    children=[
                       html.H3("Number of review phone calls"),
                       html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar. Particularly the ticket ID and product name."),
                       dcc.Graph(figure = figCalls),
                       html.H3("Number of each reviewer tag"),
                       html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar. Particularly the agency, manufacturer, product, and/or ticket ID. To exclude one or more agencies, click on those agency names in the legend."),                        
                       dcc.Graph(figure = figRevTag),
                       html.Br(),
                       html.H3("Number of tags issued by each reviewer"),
                       html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar. Particularly the agency, manufacturer, product, and/or ticket ID. To exclude one or more tags, click on those tag names in the legend."),
                       dcc.Graph(figure = figRevTag2),
                       html.H3("Escalations broken down by agency"),
                       html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar. Particularly the agency, manufacturer, product, and/or ticket ID. To exclude one or more agencies, click on those agency names in the legend."),
                       dcc.Graph(figure = figEsc),
                       html.H3("Escalations broken down by reviewer"),
                       html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar."),
                       dcc.Graph(figure = figEsc2),
                       html.H3("Office-wide client tags"),
                       html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar. Particularly the agency, manufacturer, product, and/or ticket ID. To exclude one or more agencies, click on those agency names in the legend."),
                       dcc.Graph(figure = figClientTag),
                       html.Br(),
                       html.H3("Client tags broken down by reviewer"),
                       html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar. Particularly the agency, manufacturer, product, and/or ticket ID. To exclude one or more tags, click on those tag names in the legend."),
                       dcc.Graph(figure = figClientTag2),
                       html.Br(),
                       html.H3("Validated client tags broken down by reviewer"),
                       html.P("Hover over any bar to reveal metadata about each submission that makes up that bar as you move your mouse up or down the bar. Particularly the agency, manufacturer, product, and/or ticket ID. To exclude one or more tags, click on those tag names in the legend."),
                       dcc.Graph(figure = figAudited)
                    ]
                ),
#######################################################################
############################# End of tabs #############################
#######################################################################
            ], style={'padding': '40px'}#Closing python list of [dcc.Tab(),...,dcc.Tab()] in dcc.Tabs() children argument
        )#Closure for the dcc.Tabs()
    ]#Square bracket closure for Html.Div([])
)#Round bracket closure for Html.Div([])

#######################################################################
################## callback and function for LATE #####################
#######################################################################
@app.callback(
    Output("graph","figure"),
    Input("urgency", "value")
)

def plot_rev_hist(selected_levels):
  late_sub_merge_filtered_by_urgency_level = late_sub_merge[late_sub_merge["UrgencyLevel"].isin(selected_levels)]#used `isin()` to accomodate filtering by a list (i.e., the list of selected levels)
  fig = px.bar(
    late_sub_merge_filtered_by_urgency_level,
    x='Reviewer',
    y='IsEnabled',
    color='LetterType',
    hover_data=['LetterId', 'UrgencyLevel', 'Product'],
    color_discrete_sequence=['red', 'pink'],
    category_orders={"LetterType": ["New Letter", "Revision Letter"]}
  ).update_layout(yaxis_title='Total count of late letters')

  return fig

#######################################################################
################### callback and function for CEI #####################
#######################################################################

@app.callback(
    [Output("express_chart", "figure"),
     Output("subplots", "figure"),
     Output('q1-comments', 'children'),
     Output('q2-comments', 'children'),
     Output('q3-comments', 'children'),
     Output('q4-comments', 'children'),
     Output('q5-comments', 'children')],
    [Input("reviewer_selector", "value")]
)

def update_charts(selected_reviewer):
    if selected_reviewer is None:
        return go.Figure(), go.Figure(), html.Div(), html.Div(), html.Div(), html.Div(), html.Div()

    #For selected_reviewer show CEI_Q5 bar chart 
    filtered_data = cei_sub_merge_quant[cei_sub_merge_quant["Reviewer"] == selected_reviewer]
    df_temp = filtered_data["CEI_Q5"].value_counts(normalize=True).reset_index()
    df_temp.columns = ['CEI_Q5', 'proportion']

    fig = px.bar(
        df_temp,
        x="CEI_Q5",
        y="proportion",
        title="Rate Your <span style='color: purple'>Overall Experience</span> With This Particular Review<br>              (1=Highly -ve        10=Highly +ve)<br>Scores that do not appear have a proportion of zero.",
    )

    fig.update_layout(
    xaxis_title="Overall Experience Score (out of 10)",
    yaxis_title="Proportion of submissions",
    #height= 500,
    showlegend= False,
    yaxis_title_font=dict(size=18),
    xaxis_title_font=dict(size=18)
    )
    
    fig.update_xaxes(tickmode='linear')#otherwise only even numbers appear

    #For selected_reviewer show subplots 
    sub_fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Staff Were <span style='color:blue'>Helpful</span> &<br>Responsive",
                    "Communications Were<br><span style='color:red'>Clear</span> & Actionable",
                    "Perceived level of<br>review <span style='color:#00A86B'>consistency</span>"),
        shared_yaxes=True
    )

    q1 = filtered_data["CEI_Q1"].value_counts(normalize=True).sort_index()
    q2 = filtered_data["CEI_Q2"].value_counts(normalize=True).sort_index()
    q3 = filtered_data["CEI_Q3"].value_counts(normalize=True).sort_index()

    sub_fig.add_trace(go.Bar(x=q1.index, y=q1.values * 100), row=1, col=1)
    sub_fig.add_trace(go.Bar(x=q2.index, y=q2.values * 100), row=1, col=2)
    sub_fig.add_trace(go.Bar(x=q3.index, y=q3.values * 100), row=1, col=3)
   
    sub_fig.update_xaxes(tickmode='linear')#otherwise only even numbers appear

    sub_fig.update_layout(showlegend=False, height=400, yaxis_title="Percentage of<br> submissions (%)")

    #For  selected_reviewer show comment tables
    q1_table = generate_comment_table(filtered_data, 'CEI_Q1', 'Q1Comment')
    q2_table = generate_comment_table(filtered_data, 'CEI_Q2', 'Q2Comment')
    q3_table = generate_comment_table(filtered_data, 'CEI_Q3', 'Q3Comment')
    q4_table = generate_comment_table(filtered_data, 'CEI_Q5', 'Q4Comment')
    q5_table = generate_comment_table(filtered_data, 'CEI_Q5', 'Q5Comment') 


    return fig, sub_fig, q1_table, q2_table, q3_table, q4_table, q5_table

###############################################################################################################################################################
################################################################  RUN APP  ####################################################################################
###############################################################################################################################################################

if __name__ == '__main__':
  app.run_server(host='0.0.0.0', port=8053, debug=False)