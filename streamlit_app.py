# Import required packages
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# App title and intro
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Get user input
name_on_order = st.text_input('Name on Smoothie:')
if name_on_order:
    st.write("The name on your Smoothie will be:", name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Get fruit options from Snowflake
snowpark_df = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))
fruit_df = snowpark_df.to_pandas()

# Create list of fruit names for the multiselect widget
fruit_list = fruit_df['FRUIT_NAME'].tolist()

# Let user pick ingredients
selected_fruits = st.multiselect(
    'Choose up to 5 ingredients:',
    options=fruit_list,
    max_selections=5
)

# Display API info if fruits are selected
ingredients_string = ''
if selected_fruits:
    for fruit in selected_fruits:
        # Add to ingredient list
        ingredients_string += fruit + ', '

        # Safely extract the corresponding search key
        match_row = fruit_df[fruit_df['FRUIT_NAME'] == fruit]
        if not match_row.empty:
            search_key = match_row['SEARCH_ON'].values[0]

            # Call external API and show info
            try:
                response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_key}")
                response.raise_for_status()
                nutrition_data = response.json()
                st.subheader(f"{fruit} Nutrition Information")
                st.json(nutrition_data)
            except requests.RequestException as e:
                st.warning(f"Could not fetch info for {fruit}. Error: {e}")
        else:
            st.warning(f"No search value found for {fruit}.")

# Remove trailing comma from ingredients string
ingredients_string = ingredients_string.rstrip(', ')

# Submit to database
if selected_fruits and name_on_order:
    if st.button("Submit Order"):
        try:
            # Use parameterized query to avoid SQL injection
            session.table("smoothies.public.orders").insert(
                values={"INGREDIENTS": ingredients_string, "NAME_ON_ORDER": name_on_order}
            )
            st.success(f"Your Smoothie is ordered, {name_on_order}!", icon="✅")
        except Exception as e:
            st.error(f"Order submission failed. Error: {e}")
else:
    st.info("Enter a name and select ingredients to enable order submission.")
