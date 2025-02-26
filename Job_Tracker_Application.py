import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark import Session
import toml

## Creating the title for the Streamlit Website 
st.title('❄️ Job Application Tracking System - V1')
st.caption('This is an application used to save job applications applied!')
## Loading in the Credential
# Load Snowflake configurations from secrets.toml file
with open("secrets.toml", "r") as f:
    config = toml.load(f)

# Extract Snowflake credentials
snowflake_config = {
    "user": config["snowflake"]["username"],
    "password": config["snowflake"]["password"],
    "account": config["snowflake"]["account"]
}

# Establish Snowflake session
@st.cache_resource
def create_session():
    return Session.builder.configs(snowflake_config).create()

session = create_session()
st.success("Connected to Snowflake!")

# Load data table
def load_data(table_name):
    st.write(f"Here's some example data from `{table_name}`:")
    table = session.table(table_name)
    table = table.limit(100)
    table = table.collect()
    return pd.DataFrame(table)

# Select and display data table
table_name = "JOB_APPS.PUBLIC.APPLICATIONS_TABLE"

def refresh_data():
    df = load_data(table_name)
    df.reset_index(inplace=True)  # Ensure index column is available
    st.dataframe(df)
    return df

with st.expander("See Table"):
    df = refresh_data()

## Adding user input to the database using sidebar
st.sidebar.subheader("Add New Job Application")
User_Input = st.sidebar.text_input("User:")
role = st.sidebar.text_input("Role:")
company = st.sidebar.text_input("Company:")
city = st.sidebar.text_input("City:")
state = st.sidebar.text_input("State:")
role_function = st.sidebar.text_input("Role Function:")
industry = st.sidebar.text_input("Industry:")
date_applied = st.sidebar.date_input("Date Applied:")
referral = st.sidebar.text_input("Referral (Y/N):")
outcome = st.sidebar.text_input("Outcome:")

if st.sidebar.button("Save to Database"):
    if User_Input and role and company and city and state and role_function and industry and date_applied and referral and outcome:
        query = f"""
        INSERT INTO {table_name} (USER_INPUT, ROLE, COMPANY, CITY, STATE, ROLE_FUNCTION, INDUSTRY, DATE_APPLIED, REFERRAL, OUTCOME)
        VALUES ('{User_Input}', '{role}', '{company}', '{city}', '{state}', '{role_function}', '{industry}', '{date_applied}', '{referral}', '{outcome}')
        """
        session.sql(query).collect()
        st.sidebar.success("Job application saved successfully!")
        df = refresh_data()
    else:
        st.sidebar.error("Please fill in all fields.")

## Deleting a record from the database by index
st.sidebar.subheader("Delete Job Application by Index")
delete_index = st.sidebar.number_input("Enter Index to Delete:", min_value=0, step=1)

if st.sidebar.button("Delete Record"):
    if not df.empty and delete_index in df.index:
        row_to_delete = df.iloc[delete_index]
        delete_query = f"DELETE FROM {table_name} WHERE ROLE = '{row_to_delete['ROLE']}' AND COMPANY = '{row_to_delete['COMPANY']}' AND DATE_APPLIED = '{row_to_delete['DATE_APPLIED']}'"
        session.sql(delete_query).collect()
        st.sidebar.success("Record deleted successfully!")
        df = refresh_data()
    else:
        st.sidebar.error("Invalid index. Please enter a valid index.")

## Modifying a record in the database by index
st.sidebar.subheader("Modify Job Application by Index")
modify_index = st.sidebar.number_input("Enter Index to Modify:", min_value=0, step=1)

if modify_index in df.index:
    row_to_modify = df.iloc[modify_index]
    new_user = st.sidebar.text_input("New User:", row_to_modify["USER_INPUT"])
    new_role = st.sidebar.text_input("New Role:", row_to_modify["ROLE"])
    new_company = st.sidebar.text_input("New Company:", row_to_modify["COMPANY"])
    new_city = st.sidebar.text_input("New City:", row_to_modify["CITY"])
    new_state = st.sidebar.text_input("New State:", row_to_modify["STATE"])
    new_role_function = st.sidebar.text_input("New Role Function:", row_to_modify["ROLE_FUNCTION"])
    new_industry = st.sidebar.text_input("New Industry:", row_to_modify["INDUSTRY"])
    new_date_applied = st.sidebar.date_input("New Date Applied:", row_to_modify["DATE_APPLIED"])
    new_referral = st.sidebar.text_input("New Referral (Y/N):", row_to_modify["REFERRAL"])
    new_outcome = st.sidebar.text_input("New Outcome:", row_to_modify["OUTCOME"])

    if st.sidebar.button("Update Record"):
        update_query = f"""
        UPDATE {table_name} 
        SET USER_INPUT = '{new_user}', ROLE = '{new_role}', COMPANY = '{new_company}', CITY = '{new_city}', STATE = '{new_state}', 
            ROLE_FUNCTION = '{new_role_function}', INDUSTRY = '{new_industry}', DATE_APPLIED = '{new_date_applied}', 
            REFERRAL = '{new_referral}', OUTCOME = '{new_outcome}'
        WHERE ROLE = '{row_to_modify['ROLE']}' AND COMPANY = '{row_to_modify['COMPANY']}' AND DATE_APPLIED = '{row_to_modify['DATE_APPLIED']}'
        """
        session.sql(update_query).collect()
        st.sidebar.success("Record updated successfully!")
        df = refresh_data()



## Bar chart showing count of applications per user
st.subheader("Job Applications per User")
x_axis_option = st.radio("Select X-Axis Variable:", ["USER_INPUT", "ROLE", "COMPANY", "CITY"])

if not df.empty:
    user_counts = df[x_axis_option].value_counts().reset_index()
    user_counts.columns = [x_axis_option, "Application Count"]
    chart = alt.Chart(user_counts).mark_bar().encode(
        x=alt.X(x_axis_option, sort="-y"),
        y="Application Count",
        tooltip=[x_axis_option, "Application Count"]
    ).properties(width=600, height=400)
    st.altair_chart(chart, use_container_width=True)
else:
    st.write("No data available to display chart.")


## Line Chart of Job Applications Over Time
st.subheader("Job Applications Over Time")

if not df.empty:
    df["DATE_APPLIED"] = pd.to_datetime(df["DATE_APPLIED"])  # Ensure DATE_APPLIED is in datetime format

    # Grouping data by DATE_APPLIED and USER_INPUT
    date_counts = df.groupby(["DATE_APPLIED", "USER_INPUT"]).size().reset_index(name="Application Count")

    line_chart = alt.Chart(date_counts).mark_line(point=True).encode(
        x=alt.X("DATE_APPLIED:T", title="Date Applied"),
        y=alt.Y("Application Count", title="Number of Applications"),
        color="USER_INPUT",
        tooltip=["DATE_APPLIED", "USER_INPUT", "Application Count"]
    ).properties(width=800, height=400)

    st.altair_chart(line_chart, use_container_width=True)
else:
    st.write("No data available to display chart.")
