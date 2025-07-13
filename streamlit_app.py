# Import python packages
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# Write directly to the app
st.title(f":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("""Choose the fruits you want in your custom Smoothie!.""")

# Get name input
name_on_order = st.text_input('Name on Smoothie:')
if name_on_order:
    st.write("The name on your Smoothie will be:", name_on_order)

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

# Query Snowflake fruit options
my_data_frame = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'))

# Convert Snowpark DF to Pandas DF
pd_df = my_data_frame.to_pandas()

# Extract just the fruit names
fruit_options = pd_df['FRUIT_NAME'].tolist()

# Create multiselect input
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_options,
    max_selections=5
)

# If user selects fruits, fetch and display info
ingredients_string = ''
if ingredients_list:
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ', '

        # Get corresponding search key
        match_row = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen]

        if not match_row.empty:
            search_on = match_row['SEARCH_ON'].values[0]

            if pd.notna(search_on) and str(search_on).strip() != '':
                st.subheader(fruit_chosen + ' Nutrition Information')
                try:
                    smoothiefroot_response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
                    smoothiefroot_response.raise_for_status()
                    st.json(smoothiefroot_response.json())
                except requests.RequestException as e:
                    st.warning(f"Could not fetch info for {fruit_chosen}. Error: {e}")
            else:
                st.warning(f"No valid search value found for {fruit_chosen}.")
        else:
            st.warning(f"{fruit_chosen} not found in data.")

# Clean trailing comma and space
ingredients_string = ingredients_string.rstrip(', ')

# Create SQL insert statement
my_insert_stmt = f"""
    insert into smoothies.public.orders(ingredients, name_on_order)
    values (%s, %s)
"""

# Show submit button only when needed
if ingredients_list and name_on_order:
    time_to_insert = st.button('Submit Order')
    if time_to_insert:
        try:
            session.cursor().execute(my_insert_stmt, (ingredients_string, name_on_order))
            st.success(f'Your Smoothie is ordered, {name_on_order}!', icon="✅")
        except Exception as e:
            st.error(f"Order submission failed. Error: {e}")
else:
    st.info("Enter your name and select ingredients to enable the order button.")
